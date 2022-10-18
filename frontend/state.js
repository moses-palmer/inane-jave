class State {
    /**
     * Constructs an application state from a set of values.
     *
     * @param state
     *     The current state.
     * @param store
     *     An asynchronous function to store the state to the backend.
     * @param clear
     *     An asynchronous function to clear the state from the backend.
     */
    constructor(state, store) {
        this._state = state;
        this._store = store;

        if (this._state.project === undefined) {
           this._state.project = {};
        }
        if (this._state.prompt === undefined) {
           this._state.prompt = {};
        }
    }

    /**
     * Stores the application state to the database.
     */
    async store() {
        await this._store(this._state);
        return this;
    }

    /**
     * Loads a project from the cached state.
     *
     * If no ID is provided, an object with the following methods is returned:
     * *   `create` - Creates a project from a backend response.
     * *   `empty` - Creates an empty project that can be populated and JSON
     *     encoded.
     * *   `filter` - Removes all projects whose ID's are not present in a
     *     list.
     *
     * @param id
     *     The project ID.
     * @return a project entity.
     */
    project(id) {
        if (id === undefined) {
            const self = this;
            return {
                create: r => self.project(r.id).update(r),
                empty: () => entity(
                    this, "project", undefined, PROJECT, PROJECT_INV),
                filter: ids => Object.keys(self._state.project).forEach(id => {
                    if (ids.indexOf(id) < 0) {
                        delete self._state.project[id];
                    }
                }),
            };
        } else {
            return entity(this, "project", id, PROJECT, PROJECT_INV);
        }
    }

    /**
     * Loads a prompt from the cached state.
     *
     * If no ID is provided, an object with the following methods is returned:
     * *   `create` - Creates a prompt from a backend response.
     * *   `empty` - Creates an empty prompt that can be populated and JSON
     *     encoded.
     *
     * @param id
     *     The prompt ID.
     * @return a prompt entity.
     */
    prompt(id) {
        if (id === undefined) {
            const self = this;
            return {
                create: r => self.prompt(r.id).update(r),
                empty: () => entity(
                    this, "prompt", undefined, PROMPT, PROMPT_INV),
            };
        } else {
            return entity(this, "prompt", id, PROMPT, PROMPT_INV);
        }
    }

    /**
     * Updates the application state given a websocket event.
     *
     * @param event
     *     The received event.
     */
    applyEvent(event) {
        switch (event.image?.kind) {
            case "completed":
                this.prompt(event.image.data.prompt.id)
                    .withProgress(event.image.data.progress)
                    .store();
                break;
        }
    }
}


/**
 * A mapping from project fields used in the frontend to fields used in the
 * backend.
 */
const PROJECT = {
    id: "id",
    description: "description",
    imageHeight: "image_height",
    imageWidth: "image_width",
    name: "name",
    prompts: {
        get: (value, state, id) => value.prompts?.map(id => state.prompt(id))
            ?? [],
        set: (value, state, id, t) => {
            value.prompts = t.map(prompt => prompt.id);
        },
    },
};


/**
 * PROJECT inversed.
 */
const PROJECT_INV = Object.fromEntries(Object.entries(PROJECT)
    .filter(([k, v]) => typeof(v) === "string")
    .map(([k, v]) => [v, k]));


/**
 * A mapping from prompt fields used in the frontend to fields used in the
 * backend.
 */
const PROMPT = {
    id: "id",
    completed: {
        get: (value, state, id) => value.progress >= 1.0,
    },
    images: undefined,
    progress: undefined,
    project: "project",
    text: "text",
};


/**
 * PROMPT inversed.
 */
const PROMPT_INV = Object.fromEntries(Object.entries(PROMPT)
    .filter(([k, v]) => typeof(v) === "string")
    .map(([k, v]) => [v, k]));


/**
 * Constructs an entity.
 *
 * The returned object will correspond to `state[type][id]`, and have accessors
 * for all the listed fields as well as a function `store` that will store the
 * entire application state and a function `remove` that will remove the entity
 * and store the new state.
 *
 * @param state
 *     The application state.
 * @param type
 *     The type of entity.
 * @param id
 *     The entity ID.
 * @param frontToBack
 *     A listing of all fields as a mapping from frontend name to backend name.
 *     Keys with the value `undefined` are igenored.
 * @param backToFront
 *     A listing of all fields as a mapping from backend name to frontend name.
 *     Keys with the value `undefined` are igenored.
 */
const entity = (state, type, id, frontToBack, backToFront) => {
    const value = id === undefined
        ? {}
        : state._state[type][id] || { id };
    let detached = id === undefined;
    if (!detached) {
        state._state[type][id] = value;
    }

    const self = {
        clone: () => {
            const result = { ...self };
            delete result.id;
            return result;
        },
        json: () => map(value, frontToBack),
        remove: detached ? undefined : async () => {
            delete state._state[type][id];
            await state.store();
        },
        store: detached ? undefined : async () => {
            await state.store();
            return self;
        },
        update: r => {
            for (const [k, v] of Object.entries(map(r, backToFront))) {
                value[k] = v;
            }
            return self;
        },
    };

    const descriptor = (k, v) => {
        switch (v?.constructor) {
            case Object: return detached ? {} : {
                get: () => v.get(value, state, id),
                set: (t) => v.set(value, state, id, t),
            };
            case undefined:
            case String: return {
                get: () => value[k],
                set: (t) => value[k] = t,
            };
        }
    };

    Object.entries(frontToBack)
        .forEach(([k, v]) => {
            Object.defineProperty(self, k, descriptor(k, v));
            self[k.replace(/(^.)/, m => `with${m.toUpperCase()}`)] = v => {
                self[k] = v;
                return self;
            };
        });

    return self;
};


/**
 * Loads the current application state.
 *
 * @param load
 *     An asynchronous function loading the state.
 * @param store
 *     An asynchronous function taking the current state and storing it.
 * @param clear
 *     An asynchronous function clearing the state.
 */
export const load = async (load, store, clear) => {
    try {
        return new State(await load(), store, clear);
    } catch (e) {
        console.log(`failed to load state: ${e}`);
        return new State({}, store, clear);
    }
};


/**
 * Determines whether a node is a leaf in a template.
 *
 * @param node
 *     The node to check.
 */
const leaf = (node) => node === null || node === undefined || !(false
    || (node.constructor === Array && node.length > 0)
    || (node.constructor === Object && Object.keys(node).length > 0));


/**
 * Merges one object into another.
 *
 * @param target
 *     The target object.
 * @param source
 *     The source object.
 */
const merge = (target, source) => Object.entries(source)
    .forEach(([k, node]) => {
        if (leaf(node)) {
            target[k] = source[k];
        } else {
            if (!(k in target)) {
                target[k] = {};
            }
            merge(target[k], source[k]);
        }
    });


/**
 * Maps an object so that the `data[k]` becomes `data[mapping[k]]`.
 *
 * If `mapping[k]` is not a string, the field is ignored.
 *
 * @param data
 *     The data to remap.
 * @param mapping
 *     The mapping.
 * @return a mapped object
 */
const map = (data, mapping) => Object.fromEntries(Object.entries(mapping)
    .filter(([k, v]) => typeof(v) === "string")
    .map(([k, v]) => [v, data[k]]));
