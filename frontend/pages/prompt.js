import api from "../api.js";
import { translate as _ } from "../translation.js";
import * as ui from "../ui.js";


export default {
    initialize: async (state, id) => {
        const prompt = await api.prompt.get(state, id);
        const project = await api.project.get(state, prompt.project);
        return { prompt, project };
    },

    show: async (page, state) => {
        const [image, download, progress] = ui.managed(page.doc);
        const iconTemplate = document.getElementById("button-icons");

        const width = page.context.project.image_width;
        const height = page.context.project.image_height;
        image.style.backgroundImage =
            `url(${api.prompt.iconURL(page.context.prompt.id)})`;
        image.style.height = "auto";
        image.style.aspectRatio = `${width} / ${height}`;
        download.appendChild(
            iconTemplate.content.querySelector("#download").cloneNode(true));
    },

    notificationURL: (page) =>
        `project/${page.context.project.id}/notifications`,

    notify: async (page, state, event) => {
        const [image, download, progress] = ui.managed(page.doc);
        const prompt = page.context.prompt;
        switch (event.image?.kind) {
            case "idle":
                await api.prompt.generate(state, prompt.id);
                break;
            case "completed":
                if (event.image.data.prompt.id === prompt.id) {
                    progress.style.width =
                        (100 * event.image.data.progress) + "%";
                    progress.parentElement.style.visibility =
                        event.image.data.progress >= 1.0
                            ? "hidden"
                            : "visible";
                    await api.prompt.generate(state, prompt.id);
                }
                break;
        }
    },
};
