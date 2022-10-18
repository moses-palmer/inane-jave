import api from "../api.js";
import { translate as _ } from "../translation.js";
import * as ui from "../ui.js";


export default {
    initialize: async (state) => { },

    show: async (page, state) => {
        const [form] = ui.managed(page.doc);
        form.addEventListener("submit",  async (e) => {
            e.preventDefault();
            const data = new FormData(form);

            // Warn about similar names
            const normalized = normalize(data.get("name"));
            const matches = (await api.project.all(state))
                    .filter(project => normalize(project.name) === normalized);
            if (matches.length > 0) {
                switch (await ui.message(
                    _("Project already exists"),
                    _("A project named {} already exists. Do you still want "
                        + "to create {}?").format(
                            matches[0].name,
                            data.get("name")),
                    [
                        { name: "yes", text: _("Yes"), classes: ["ok"] },
                        { name: "no", text: _("No"), classes: ["cancel"] },
                    ])) {
                    case "yes":
                        break;
                    default:
                        return;
                }
            }

            // Create the project
            const project = await api.project.create(
                state,
                state.project().empty()
                    .withName(data.get("name"))
                    .withDescription(data.get("description"))
                    .withImageWidth(parseInt(data.get("width")) || 512)
                    .withImageHeight(parseInt(data.get("height")) || 512));
            location.href = `#project/${project.id}`;
        });
    },
};


/**
 * Normalises a string by lower casing and replacing all whitespace by a single
 * space.
 *
 * @param s
 *     The string to normalise.
 * @return a new string
 */
const normalize = (s) => s.toLowerCase()
    .split(/\s+/)
    .filter(p => !!p).join(" ");
