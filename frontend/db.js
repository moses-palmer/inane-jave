/**
 * The name of the database to use.
 */
const NAME = "ijave";

/**
 * Our current schema version
 */
const VERSION = 1;

/**
 * The key used for the current state.
 */
const KEY = "current";

/**
 * The object store names.
 */
const T = {
    /**
     * Application state.
     *
     * This object store contains an object keyed on `KEY`.
     */
    STATE: "state",
};


export class Database {
    /**
     * Constructs a database instance.
     */
    constructor(db) {
        this._db = db;
    }

    /**
     * Loads the current application state from the database.
     */
    async load() {
        const trans = this._db.transaction(T.STATE);
        return await get(trans, T.STATE, KEY);
    }

    /**
     * Stores the current state into the database.
     */
    async store(state) {
        const trans = this._db.transaction(T.STATE, "readwrite");
        await put(trans, T.STATE, KEY, flatten(state));
    }

    /**
     * Clears the entire database.
     */
    async clear() {
        const trans = this._db.transaction(T.STATE, "readwrite");
        await schedule(trans.objectStore(T.STATE).clear());
    }
}


/**
 * Opens a connection to the database.
 *
 * This method ensures that the database is upgraded if completed.
 *
 * @returns a `Database` instance
 * @throws an error event wrapped as `{type: eventName, event: eventData}`,
 *     where `eventName` is "error" or "blocked"
 */
export default async () => {
    const req = indexedDB.open(Database.NAME, Database.VERSION);
    return new Database((await new Promise((resolve, reject) => {
        req.addEventListener("error", reject);
        req.addEventListener("success", resolve);
        req.addEventListener(
            "upgradeneeded",
            async (e) => {
                await upgrade(req.result, e.oldVersion);
                resolve(e);
            });
    })).target.result);
};


/**
 * Reads a value from an object store.
 *
 * @param trans
 *     An open transaction.
 * @param store
 *     The name of an object store.
 * @param key
 *     The key of the item to retrieve.
 * @returns an item
 * @throws an error event wrapped as `{type: eventName, event: eventData}`
 */
const get = async (trans, store, key) => (await schedule(
    trans.objectStore(store).get(key))).target.result;


/**
 * Writes a value to an object store.
 *
 * @param trans
 *     An open transaction.
 * @param store
 *     The name of an object store.
 * @param key
 *     The key of the item to write.
 * @param value
 *     The value to put.
 * @throws an error event wrapped as `{type: eventName, event: eventData}`
 */
const put = async (trans, store, key, value) => await schedule(
    trans.objectStore(store).put(value, key));


/**
 * Schedules a request for asynchronous completion.
 *
 * @param req
 *     The request to await.
 * @returns a success event
 * @throws an error event
 */
const schedule = async (req) => await new Promise(
    (resolve, reject) => {
        req.addEventListener("success", resolve);
        req.addEventListener("error", reject)
    });


/**
 * Flattens an object so that it can be JSON serialised.
 *
 * @param i
 *     The object to flatten.
 * @return a simple object
 */
const flatten = (i) => {
    switch (i.constructor) {
        case Boolean:
        case Number:
        case String:
            return i;
        case Array:
            return i.flatMap(v => {
                const value = v ?? flatten(v);
                return (value !== undefined)
                    ? [value]
                    : [];
            });
        case Object:
            return Object.fromEntries(Object.entries(i).flatMap(([k, v]) => {
                const value = v ?? flatten(v);
                return (value !== undefined)
                    ? [[k, value]]
                    : [];
            }));
    }
};

/**
 * Upgrades the database to to the current schema.
 *
 * @param db
 *     The database instance.
 * @param fromVersion
 *     The version from which to upgrade.
 */
const upgrade = async (db, fromVersion) => {
    const v1 = async () => db.createObjectStore(T.STATE);

    switch (fromVersion) {
    case 0:
        await v1();
        // Fall-through
    case 1:
        // Current
        return;
    default:
        console.error(`unknown database version: ${fromVersion}`);
    }
};
