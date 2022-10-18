import PAGES from "./pages.js";
import api from "./api.js";
import connect from "./db.js";
import * as State from "./state.js";
import * as translation from "./translation.js";
import { translate as _ } from "./translation.js";
import * as ui from "./ui.js";


/**
 * Formats a string with replacement tokens.
 *
 * A replacement token is any string enclosed in brackets (`"{"` and `"}"`).
 * Use `"\"` to escape a token.
 *
 * The last argument to this method is the token map. This is an object where
 * the keys are tokens and the values their replacements.
 *
 * Empty tokens are positional tokens: instead of being looked up in `tokens`,
 * their index is mapped to the arguments to this method.
 */
String.prototype.format = function() {
    const tokens = arguments[arguments.length - 1];
    const max = arguments.length;
    let i = 0;
    return this.replaceAll(
        /\\\{|{([^}]*)}/g,
        (m, n) => {
            if (m === "\\{") {
                return "{";
            } else if (!n && i < max) {
                return arguments[i++];
            } else if (n in tokens) {
                return tokens[n];
            } else {
                throw `unknown token: ${!!n ? n : "[" + (i + 1) + "]"}`;
            }
        },
    );
};


const load = async () => {
    const errorManager = async (e) => {
        try {
            console.error(e, e.stack);
        } catch (e) {}

        const connectionError = e.reason === "connection";
        const title = connectionError
            ? _("Jave is not jivin'")
            : _("An unexpected error occurred");
        const message = connectionError
            ? _("Inane Jave does not appear to be listening. "
                    + "Please make sure the app is running!")
            : _("The error message is: {}").format(e.message && e.filename
                ? `${e.message}; ${e.filename}:${e.lineno}`
                : e.reason);

        const response = await ui.message(
            title,
            message,
            [
                {name: "ignore", text: _("Ignore"), classes: ["cancel"]},
                {name: "reload", text: _("Reload"), classes: ["ok"]},
            ]);
        if (response === "reload") {
            location.reload();
        }
    };

    const loadState = async () => {
        const db = await connect();
        return await State.load(
            async () => {
                return await db.load() || {};
            },
            async (v) => await db.store(v));
    };

    const loadTranslations = async (state) => {
        try {
            const lang = new URLSearchParams(location.search).get("lang")
                ?? navigator.language.toLowerCase();
            await translation.load(lang);
            translation.apply(document.body);
        } catch (e) {
            // No translation available
        }
        return state
    };

    const loadPages = async (state) => {
        await Promise.all(Object.entries(PAGES)
            .filter(([_, page]) => typeof page !== "function")
            .map(async ([name, page]) => {
                const url = `./pages/${name.replace(/:/, "-")}.html`;
                page.html = (await fetch(url)
                    .then(r => r.text())
                    .then(s => (new window.DOMParser()).parseFromString(
                        s,
                        "text/html"))
                    .then(translation.applyEvent))
                    .body.innerHTML;
            }));
        return state;
    }

    const refresh = async () => {
        const page = await ui.update(state);

        if (state.notificationWS) {
            state.notificationWS.close();
            state.notificationWS = undefined;
        }
        const notificationURL = page?.notificationURL?.call(null, page);
        if (notificationURL) {
            const root = api.base().replace(/^http/, "ws");
            const ws = new WebSocket(`${root}/${notificationURL}`);
            ws.onmessage = async (message) => {
                const data = JSON.parse(message.data);
                state.applyEvent(data);
                await page.notify?.call(null, page, state, data);
                ui.applyEvent(data);
            };
            ws.onerror = (error) => console.log({error});
            state.notificationURL = notificationURL;
            state.notificationWS = ws;
        }
    };

    const state = await loadState().then(loadTranslations).then(loadPages);

    window.addEventListener("error", errorManager);
    window.addEventListener("unhandledrejection", errorManager);

    window.addEventListener("hashchange", async (e) => {
        e.preventDefault();
        await refresh();
    });

    api.defaultErrorHandler(errorManager);

    await refresh();
};


if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
        navigator.serviceWorker.register("./service.js", {
            scope: api.BASE_URL,
        });
        navigator.serviceWorker.addEventListener("message", async (event) => {
            const db = await connect();
            const state = await State.load(
                async () => await db.load(),
                async (v) => db.store(v),
                async () => db.clear());
        });
        await navigator.serviceWorker.ready;
        await load();
    });
} else {
    window.addEventListener("load", load);
}
