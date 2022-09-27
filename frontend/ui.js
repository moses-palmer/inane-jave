import api from "./api.js";
import PAGES from "./pages.js";
import { translate as _ } from "./translation.js";


/**
 * The selector used to find elements relating to the application state.
 */
export const APP_SELECTOR = ".app";

/**
 * A class name applied to elements somehow corresponding to a a project.
 */
export const PROJECT_CLASS = "project";

/**
 * A class name applied to elements somehow corresponding to a prompt.
 */
export const PROMPT_CLASS = "prompt";

/**
 * The selecor used to find the main element.
 */
const MAIN_SELECTOR = "#main";

/**
 * The element that contains messages.
 */
const MESSAGES_EL = "messages";

/**
 * The class used for templates
 */
const TEMPLATE_CLASS = "template";

/**
 * The message box class.
 */
const MESSAGE_BOX_CLASS = "message-box";

/**
 * The message box button template class.
 */
const BUTTON_CLASS = "button";

/**
 * The generic message class.
 */
const MESSAGE_CLASS = "message";

/**
 * The selector used to find managed elements.
 */
const MANAGED_ELS = ".managed";

/**
 * The class added to the message overlay when messages are active.
 */
const ACTIVE_CLASS = "active";

/**
 * The class added to the message overlay when messages are fading away.
 */
const FADING_CLASS = "fading";


/**
 * Updates the UI and displays the page based on the location hash.
 *
 * When a page has been successfully called, the `onReady` handler is called.
 */
export const update = async (state) => {
    // The page is encoded as the hash
    const path = location.hash.substring(1);
    const parts = path.split("/");
    const name = parts[0].replaceAll("_", "-");
    const args = parts.slice(1);
    const page = PAGES[parts[0]] || PAGES[await PAGES.calculate(state)];

    // Clear the body class list and remove the current page element
    document.body.classList.forEach(className => {
        const parts = className.split("-");
        parts.pop();
        if (PAGES[parts.join("-")]) {
            document.body.classList.remove(className);
        }
    });
    document.querySelectorAll(APP_SELECTOR)
        .forEach(el => el.remove());

    // Apply the state and update the body class and children
    try {
        // Generate the page context
        const context = await page.initialize(state, ...args);

        // Generate the page document
        const html = page.html.replaceAll(
            /\$\{([^}]+)\}/g,
            (_, path) => path.split(".").reduce(
                (acc, p) => p === "*" ? acc : acc ? acc[p] : null,
                {state, context}));

        page.context = context;
        page.doc = (new DOMParser).parseFromString(html, "text/html");

        await page.show.call(null, page, state);
        document.body.classList.add(`${name}-page`);
        document.querySelector(MAIN_SELECTOR).append(
            page.doc.querySelector(APP_SELECTOR));
        page.doc = document.querySelector(APP_SELECTOR);

        return page;
    } catch (e) {
        if (typeof e === "string") {
            location.hash = "#" + e;
        } else if (location.hash.length > 1) {
            console.trace(e);
            location.hash = "#";
        } else {
            throw e;
        }
    }
};


/**
 * Selects all managed elements under an element.
 *
 * Managed elements are input or output elements managed from code.
 *
 * @param el
 *     The main element, created from a template.
 * @param classes
 *     Additional classes.
 */
export const managed = (el, classes) => el.querySelectorAll(
    MANAGED_ELS + (!!classes ? `.${classes}` : ""));


/**
 * Displays a simple message box.
 *
 * @param caption
 *     The message caption.
 * @param text
 *     The message text.
 * @param buttons a list of buttons described by the attributes `name`, `text`,
 *     `classes`. `name` is the string this function resolves to if the button
 *     is clicked. `text` is the button text. `classes` is a list of classes to
 *     apply to the button. This defaults to the single button _OK_.
 * @return a promise resolving to a button name
 */
export const message = async (caption, text, buttons) => {
    const message = messageBoxTemplate(
        `.${MESSAGE_CLASS}.${TEMPLATE_CLASS}`)
        .content.cloneNode(true);
    const [captionEl, textEl] = managed(message);
    captionEl.innerText = caption;
    textEl.innerText = text;

    const top = document.getElementById(MESSAGES_EL);
    const messageBox = messageBoxTemplate(
        `.${MESSAGE_BOX_CLASS}`)
        .cloneNode(true);
    const buttonTemplate = messageBoxTemplate(
        `.${MESSAGE_BOX_CLASS}.${BUTTON_CLASS}.${TEMPLATE_CLASS}`);
    const messageCount = () => top.querySelectorAll(
        `.${MESSAGE_BOX_CLASS}:not(.${TEMPLATE_CLASS})`).length;

    const [messageEl, buttonsEl] = managed(messageBox);
    messageEl.appendChild(message);

    return await new Promise((resolve) => {
        (buttons || [{text: _("OK")}]).forEach(({name, text, classes}) => {
            const el = buttonTemplate.content.cloneNode(true);
            const input = el.querySelector("input");
            input.value = text;
            input.className = classes ? classes.join(" ") : "";
            input.addEventListener("click", () => {
                messageBox.parentNode.removeChild(messageBox);
                if (messageCount() === 0) {
                    top.addEventListener("animationend", () => {
                        top.classList.remove(FADING_CLASS);
                        if (messageCount() === 0) {
                            top.classList.remove(ACTIVE_CLASS);
                        }
                        resolve(name);
                    }, {once: true, passive: true});
                    top.classList.add(FADING_CLASS);
                } else {
                    resolve(name);
                }
            });
            buttonsEl.appendChild(el);

        });

        top.appendChild(messageBox);
        top.classList.add(ACTIVE_CLASS);
        top.classList.remove(FADING_CLASS);
    });
};

/**
 * Converts an entity ID to a class name.
 *
 * @param uuid
 *     The entity reference to convert.
 * @return a valid class name
 */
export const className = (uuid) => `id${uuid}`;


/**
 * Converts a date to a date string.
 *
 * @param state
 *     The application state.
 * @param time
 *     The timestamp.
 */
export const date = (state, time) => new Intl.DateTimeFormat(
    "default", {dateStyle: "medium"}).format(time);


/**
 * Converts a date to a timestamp string.
 *
 * @param state
 *     The application state.
 * @param time
 *     The timestamp.
 */
export const timestamp = (state, time) => new Intl.DateTimeFormat(
    "default", {dateStyle: "medium", timeStyle: "short"}).format(time);


/**
 * Selects a named template under the message box template.
 *
 * @param name
 *     The selector.
 */
const messageBoxTemplate = (name) => document.getElementById(MESSAGES_EL)
    .querySelector(`.${MESSAGE_BOX_CLASS}.${TEMPLATE_CLASS}`).content
    .querySelector(name);
