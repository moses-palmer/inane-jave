import api from "../api.js";
import { translate as _ } from "../translation.js";
import * as ui from "../ui.js";


export default {
    initialize: async (state, projectID) => ({
        projectID,
    }),

    show: async (page, state) => {
        const [form] = ui.managed(page.doc);
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const data = new FormData(form);

            // Create the prompt
            const prompt = await api.prompt.create(
                state,
                page.context.projectID,
                data.get("text"),
                parseInt(data.get("steps") || 50),
                65536 * Math.random(),
                parseFloat(data.get("strength") || 10.0));
            location.href = `#prompt/${prompt.id}`;
        });
    },
};
