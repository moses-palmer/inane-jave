import io
import logging
import os
import threading

from math import log, sqrt

import numpy as np
import PIL.Image as im
import tensorflow as tf

from keras_cv.models.generative.stable_diffusion.clip_tokenizer import (
    SimpleTokenizer)
from keras_cv.models.generative.stable_diffusion.constants import (
    _ALPHAS_CUMPROD)
from keras_cv.models.generative.stable_diffusion.constants import (
    _UNCONDITIONAL_TOKENS)
from keras_cv.models.generative.stable_diffusion.decoder import (
    Decoder)
from keras_cv.models.generative.stable_diffusion.diffusion_model import (
    DiffusionModel)
from keras_cv.models.generative.stable_diffusion.text_encoder import (
    TextEncoder)
from tensorflow import keras

from .. import timer
from . import normalize, Input, Output, Task

LOG = logging.getLogger(__name__)

#: The maximum prompt length.
MAX_PROMPT_LENGTH = 77

#: Whether to JIT compile the models for better runtime performance.
#:
#: Enabling this will yield a performance increase around 15%, but compile time
#: increases.
JIT_COMPILE = True

#: The base URL for the weights.
WEIGHTS_BASE = 'https://huggingface.co/fchollet/stable-diffusion/resolve/main/'

#: The text encoder weights.
ENCODER_WEIGHTS = {
    'origin': WEIGHTS_BASE + 'kcv_encoder.h5',
    'file_hash': '4789e63e07c0e54d6a34a29b45ce81ec'
                 'e27060c499a709d556c7755b42bb0dc4'}

#: The model weights.
MODEL_WEIGHTS = {
    'origin': WEIGHTS_BASE + 'kcv_diffusion_model.h5',
    'file_hash': '8799ff9763de13d7f30a683d653018e1'
                 '14ed24a6a819667da4f5ee10f9e805fe'}

#: The decoder weights.
DECODER_WEIGHTS = {
    'origin': WEIGHTS_BASE + 'kcv_decoder.h5',
    'file_hash': 'ad350a65cc8bc4a80c8103367e039a33'
                 '29b4231c2469a1093869a345f55b1962'}


#: Positions used to generate a context vector.
POSITION_IDS = tf.convert_to_tensor(
    [list(range(MAX_PROMPT_LENGTH))],
    dtype=tf.int32)

#: Our unconditional tokens.
UNCONDITIONAL_TOKENS = tf.convert_to_tensor(
    [_UNCONDITIONAL_TOKENS],
    dtype=tf.int32)


class Generator:
    def __init__(self):
        self._model_cache = ModelCache()

        # Unless this path is provided, SimpleTokenizer will download it every
        # time
        bpe_path = os.path.expanduser(
            '~/.keras/datasets/bpe_simple_vocab_16e6.txt.gz')
        if not os.path.exists(bpe_path):
            bpe_path = None
        self._tokenizer = SimpleTokenizer(bpe_path)

        self._text_encoder = TextEncoder(MAX_PROMPT_LENGTH)

        # Load weights
        weights_file = keras.utils.get_file(**ENCODER_WEIGHTS)
        LOG.info('Loading weights from %s', weights_file)
        self._text_encoder.load_weights(weights_file)

        # Encode unconditional tokens and positions
        self._unconditional_ctx = self._text_encoder.predict_on_batch([
            UNCONDITIONAL_TOKENS,
            POSITION_IDS])

    def generate(self, input: Input) -> Output:
        (task, cached) = (input.task, input.cached)

        LOG.info(
            'Starting image transformation for %s, %d / %d',
            task, cached.step + 1, cached.steps)

        with timer() as duration:
            # If we have no previous encoded data, start with a random sample
            if cached.latent is not None:
                latent_prev = self._deserialize(cached.latent)
            else:
                latent_prev = tf.random.stateless_normal(
                    (1, task.height // 8, task.width // 8, 4),
                    seed=[task.seed, 1])

            # Acquire models and decoders; this will require a compilation step
            # for previously unhandled resolutions
            (model, decoder) = self._model_cache[(task.width, task.height)]

            # Transform the encoded data and generate an image
            tokens = self._tokenize(task)
            ctx = self._text_encoder.predict_on_batch([tokens, POSITION_IDS])
            latent = self._transform(
                model, cached.step, cached.steps, cached.strength, latent_prev,
                ctx)
            image_data = self._decode(decoder, latent)

        cached.step += 1
        cached.latent = self._serialize(latent)

        LOG.info('Completed image generation for %s in %s s', task, duration())

        return Output(
            task=task,
            cached=cached,
            content_type='image/png',
            image_data=image_data)

    def _tokenize(self, task: Task) -> tf.Tensor:
        """Tokenises the prompt text.

        :param task: The current task.

        :return: a tensor
        """
        inputs = self._tokenizer.encode(task.prompt.text)

        if len(inputs) > MAX_PROMPT_LENGTH:
            raise ValueError('prompt is too long')

        else:
            padding_length = MAX_PROMPT_LENGTH - len(inputs)
            return tf.convert_to_tensor(
                [inputs + [_UNCONDITIONAL_TOKENS[1]] * padding_length],
                dtype=tf.int32)

    def _transform(
            self, model: DiffusionModel, step: int, steps: int,
            strength: float, latent: tf.Tensor, ctx: tf.Tensor) -> tf.Tensor:
        """Generates the next image.

        :param model: The diffusion model to use.

        :param step: The current step.

        :param steps: The total number of steps.

        :param strength: The strength of the transformation.

        :param latent: The current encoded image.

        :param ctx: The encoded prompt.

        :return: a tensor
        """
        timestep = self._timestep(step, steps)
        timestep_prev = self._timestep(step + 1, steps)
        alpha = self._alpha(timestep)
        alpha_prev = self._alpha(timestep_prev)

        e = self._embedding(timestep)

        a = model.predict_on_batch([latent, e, self._unconditional_ctx])
        b = model.predict_on_batch([latent, e, ctx])
        c = a + strength * (b - a)
        d = (latent - sqrt(1 - alpha) * c) / sqrt(alpha)

        return c * sqrt(1 - alpha_prev) + sqrt(alpha_prev) * d

    def _decode(self, decoder: DiffusionModel, latent: tf.Tensor) -> bytes:
        """Converts encoded data to an image.

        :param decoder: The decoder model.

        :param latent: The data to convert.

        :return: encoded image data
        """
        decoded = ((decoder.predict_on_batch(latent) + 1) / 2) * 255
        data = np.clip(decoded, 0, 255).astype('uint8').squeeze()
        image = im.fromarray(data, mode='RGB')
        with io.BytesIO() as out:
            image.save(out, format='PNG')
            return out.getvalue()

    def _deserialize(self, data: bytes) -> np.array:
        """Deserialises data into a numpy array.

        :param data: The data to serialise.

        :return: a numpy array
        """
        with io.BytesIO(data) as f:
            return np.load(f)

    def _serialize(self, data: np.array) -> bytes:
        """Serialises a numpy array.

        :param data: The array to serialise.

        :return: bytes
        """
        with io.BytesIO() as f:
            np.save(f, data)
            return f.getvalue()

    def _embedding(
            self, timestep: int, dim=320, max_period=10000) -> tf.Tensor:
        arguments = tf.convert_to_tensor([timestep], dtype=tf.float32) \
            * tf.math.exp(
                -log(max_period) * tf.range(
                    0,
                    dim // 2,
                    dtype=tf.float32) / (dim // 2))
        return tf.reshape(
            tf.concat([tf.math.cos(arguments), tf.math.sin(arguments)], 0),
            [1, -1])

    def _timestep(self, step: int, steps: int) -> int:
        """Calculates the timestep for a task.

        :param step: The index of the image being generated.

        :param steps: The total number of steps to generate.

        :return: a timestep

        :raise ValueError: if ``step`` is out of range
        """
        if step < 0 or step > steps:
            raise ValueError('image step out of range: {}'.format(step))
        else:
            return 1 + (len(_ALPHAS_CUMPROD) // steps) * (steps - step - 1)

    def _alpha(self, timestep: int) -> float:
        """Returns the cumulative alpha for a timestep.

        If ``timestep`` is less than ``0``, ``1.0`` is returned.

        :param timestep: The timestep.

        :return: a cumulative alpha value
        """
        if timestep >= 0:
            return _ALPHAS_CUMPROD[timestep]
        else:
            return 1.0


class ModelCache:
    """A simple synchonised cache for models and decoders keyed on normalised
    image dimensions.
    """
    def __init__(self):
        self._cache = {}
        self._lock = threading.RLock()

        self._model_weights_path = keras.utils.get_file(**MODEL_WEIGHTS)
        self._decoder_weights_path = keras.utils.get_file(**DECODER_WEIGHTS)

    def __getitem__(self, key: (int, int)) -> (DiffusionModel, Decoder):
        key = (normalize(key[0]), normalize(key[1]))
        with self._lock:
            if key not in self._cache:
                LOG.info('Generating and compiling model for %s', key)

                (width, height) = key

                model = DiffusionModel(height, width, MAX_PROMPT_LENGTH)
                model.compile(jit_compile=JIT_COMPILE)
                model.load_weights(self._model_weights_path)

                decoder = Decoder(height, width)
                decoder.compile(jit_compile=JIT_COMPILE)
                decoder.load_weights(self._decoder_weights_path)

                self._cache[key] = (model, decoder)

            return self._cache[key]
