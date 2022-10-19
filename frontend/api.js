import { translate as _ } from "./translation.js";

/**
 * The base URL for API requests.
 */
export const BASE_URL = "api";

/**
 * The default error handler.
 *
 * This method is called when the server responds with a status code of 500 or
 * greater.
 */
let DEFAULT_ERROR_HANDLER = async (e) => alert(e);


const module = {
    /**
     * Sets the default error handler.
     *
     * @param handler
     *     The new default error handler.
     */
    defaultErrorHandler: (handler) => {
        DEFAULT_ERROR_HANDLER = handler;
    },

    /**
     * The class added to the body when a connection error occurs.
     */
    ERROR_CLASS: "error",

    project: {
        /**
         * Creates a new entity.
         *
         * @param state
         *     The application state.
         * @param project
         *     A filled-in project description.
         * @return the newly created entity
         */
        create: (state, project) =>
                module.post(
            "project", project.json())
            .then(state
                .project()
                .create)
            .then(module.storeT(state))
            .catch(module.onError),

        /**
         * Retrieves a single entity.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         * @return the entity
         */
        get: (state, id) => module.get(
            "project/{}".format(id))
            .then(state
                .project(id)
                .update)
            .then(module.storeT(state))
            .catch(module.orElse(id, id => state.project(id)))
            .catch(module.onError),

        /**
         * Updates an entity.
         *
         * @param state
         *     The application state.
         * @param project
         *     A filled-in project description.
         * @return the updated entity
         */
        update: (state, project) => module.put(
            "project/{}".format(project.id), project.json())
            .then(state
                .project(id)
                .update)
            .then(module.storeT(state))
            .catch(module.onError),

        /**
         * Deletes an entity.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         */
        remove: (state, id) => module.remove(
            "project/{}".format(id))
            .then(state
                .project(id)
                .remove)
            .then(module.storeT(state))
            .catch(module.onError),

        /**
         * Lists all projects.
         *
         * @param state
         *     The application state.
         * @return a list of all projects
         */
        all: (state) => module.get(
            "project")
            .then(rs => {
                state.project().filter(rs.map(r => r.id));
                return rs.map(
                    r => state
                        .project(r.id)
                        .update(r));
            })
            .then(module.storeT(state))
            .catch(module.orElse(undefined, () => state.project().all()))
            .catch(module.onError),

        /**
         * Retrieves the prompts for a project.
         *
         * @param state
         *     The application state.
         * @param id
         *     The project ID.
         * @return a list of all prompts
         */
        prompts: (state, id) => module.get(
            "project/{}/prompts".format(id))
            .then(rs => state
                .project(id)
                .withPrompts(rs.map(
                    r => state
                        .prompt(r.id)
                        .update(r))))
            .then(module.storeT(state))
            .catch(module.orElse(id, id => state.project(id), p => p.prompts))
            .catch(module.onError),

        /**
         * The URL of a project icon.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         */
        iconURL: (id) => `${BASE_URL}/project/${id}/icon`,
    },

    prompt: {
        /**
         * Creates a new entity.
         *
         * @param state
         *     The application state.
         * @param prompt
         *     The prompt to create.
         * @param steps
         *     The number of timesteps for generated images.
         * @param seed
         *     A random seed.
         * @param strength
         *     The strength of the transformation.
         * @return the newly created entity
         */
        create: (state, prompt, steps, seed, strength) => module.post(
            "project/{}/prompts".format(prompt.project), {
                text: prompt.text,
                steps,
                seed,
                strength})
            .then(state
                .prompt()
                .create)
            .then(module.storeT(state))
            .catch(module.onError),

        /**
         * Retrieves a single entity.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         * @return the entity
         */
        get: (state, id) => module.get(
            "prompt/{}".format(id))
            .then(state
                .prompt(id)
                .update)
            .then(module.storeT(state))
            .catch(module.orElse(id, id => state.prompt(id)))
            .catch(module.onError),

        /**
         * Deletes an entity.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         */
        remove: (state, id) => module.remove(
            "prompt/{}".format(id))
            .then(state
                .prompt(id)
                .update)
            .then(module.storeT(state))
            .catch(module.onError),

        /**
         * Retrieves the images for a prompt.
         *
         * @param state
         *     The application state.
         * @param id
         *     The prompt ID.
         * @return a list of all images
         */
        images: (state, id) => module.get(
            "prompt/{}/images".format(id)
            .then(r => state
                .prompt(id)
                .images(r)))
            .then(module.storeT(state))
            .catch(module.onError),

        /**
         * Starts generation of a new image for a prompt.
         *
         * @param state
         *     The application state.
         * @param id
         *     The prompt ID.
         */
        generate: (state, id) => module.post(
            "prompt/{}/generate-next".format(id))
            .catch(module.onError),

        /**
         * The URL of a prompt icon.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         */
        iconURL: (id) => `${BASE_URL}/prompt/${id}/icon`,
    },

    image: {
        /**
         * Creates an image by uploading files.
         *
         * @param state
         *     The application state.
         * @param files
         *     The files to upload.
         * @return a list of IDs corresponding to the images
         */
        create: (state, files) => module.req("image", {
            method: "POST",
            body: Array.from(files).reduce(
                (acc, file, i) => acc.append("image" + i, file) ?? acc,
                new FormData())})
            .catch(module.onError),

        /**
         * The URL of an image resource.
         *
         * @param state
         *     The application state.
         * @param id
         *     The entity ID.
         */
        url: (id) => `${BASE_URL}/image/${id}/png`,
    },

    /**
     * A wrapper for `fetch` with method `GET` taking `BASE_URL` into account.
     *
     * This function automatically parses the response as JSON.
     */
    get: (resource) => module.req(resource, {
        method: "GET",
    }),

    /**
     * A wrapper for `fetch` with method `DELETE` taking `BASE_URL` into account.
     *
     * This function automatically parses the response as JSON.
     */
    remove: (resource) => module.req(resource, {
        method: "DELETE",
    }),

    /**
     * A wrapper for `fetch` with method `POST` taking `BASE_URL` into account.
     *
     * This function automatically parses the response as JSON.
     */
    post: (resource, data) => module.req(resource, {
        method: "POST",
        body: !!data ? JSON.stringify(data) : null,
        headers: {
            "Content-Type": "application/json",
        },
    }),

    /**
     * A wrapper for `fetch` with method `PUT` taking `BASE_URL` into account.
     *
     * This function automatically parses the response as JSON.
     */
    put: (resource, data)  => module.req(resource, {
        method: "PUT",
        body: JSON.stringify(data),
        headers: {
            "Content-Type": "application/json",
        },
    }),

    /**
     * A wrapper for `fetch` taking `BASE_URL` into account.
     *
     * This function automatically parses the response as JSON and handles
     * connection errors.
     *
     * @param resource
     *     The relative path.
     * @param init
     *     The initialisation value passed to `fetch`.
     */
    req: async (resource, init) => await fetch(
            `${module.base()}/${resource}`,
            init,
        ).then((r) => {
            if (r.status >= 500) {
                throw r.statusText;
            } else {
                return r;
            }
        })
        .then(async r => {
            if (!r.ok) {
                throw await r.text();
            } else if (r.headers.get("Content-Type")
                    .startsWith("application/json")) {
                return await r.json();
            } else {
                return await r.text();
            }
        }),

    /**
     * The base URL for all API requests.
     */
    base: () => {
        return document.location.href
            .replace(/#.*$/, "")
            .replace(/[^/]*$/, "") + BASE_URL;
    },

    /**
     * Generates a function that stores the application state and then returns
     * its argument.
     *
     * @param state
     *     The application state.
     * @return a function
     */
    storeT: (state) => {
        return async (e) => {
            await state.store();
            return e;
        };
    },

    /**
     * Generates a function that attempts to get a cached version of an entity.
     *
     * If none exists, the exception that is passed to the generated function
     * is reraised.
     *
     * @param initial
     *     The initial value.
     * @param generator
     *     Functions generating an entity given an ID. The value returned must
     *     have an attribute `exists` that is set if the entity is to be kept.
     *     The functions will be called in order on the result of the previous
     *     function.
     * @return a function
     */
    orElse: (initial, ...generators) => e => generators.reduce(
        (acc, generator) => {
            const result = generator(acc);
            switch (result?.constructor) {
                case Array:
                    if (!result.every(r => r.exists)) {
                        throw e;
                    }
                    break;
                case Object:
                    if (!result.exists) {
                        throw e;
                    }
                    break;
                default:
                    throw e;
            }
            return result;
        },
        initial),

    /**
     * An error handker used when all else fails.
     */
    onError: e => DEFAULT_ERROR_HANDLER({e, reason: "connection"}),
};

export default module;
