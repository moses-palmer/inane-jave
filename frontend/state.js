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
    }

    /**
     * Stores the application state to the database.
     */
    async store() {
        await this._store(this._state);
        return this;
    }
}


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
