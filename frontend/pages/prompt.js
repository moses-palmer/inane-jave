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
        const [image, download, duplicate, remove, progress] =
            ui.managed(page.doc);
        const iconTemplate = document.getElementById("button-icons");

        const width = page.context.project.imageWidth;
        const height = page.context.project.imageHeight;
        image.style.backgroundImage =
            `url(${api.prompt.iconURL(page.context.prompt.id)})`;
        image.style.height = "auto";
        image.style.aspectRatio = `${width} / ${height}`;
        download.appendChild(
            iconTemplate.content.querySelector("#download").cloneNode(true));
        duplicate.appendChild(
            iconTemplate.content.querySelector("#duplicate").cloneNode(true));
        remove.appendChild(
            iconTemplate.content.querySelector("#remove").cloneNode(true));
        remove.onclick = async () => {
            const response = await ui.message(
                _("Delete prompt"),
                _("Do you want to delete this prompt and all images?"),
                [
                    {name: "no", text: _("No"), classes: ["cancel"]},
                    {name: "yes", text: _("Yes"), classes: ["ok"]},
                ]);
            if (response === "yes") {
                await api.prompt.remove(state, page.context.prompt.id);
                location.href = `#project/${page.context.project.id}`;
            }
        };
        updateProgress(progress, page.context.prompt);
    },

    notificationURL: (page) =>
        `project/${page.context.project.id}/notifications`,

    notify: async (page, state, event) => {
        const [image, download, duplicate, remove, progress] =
            ui.managed(page.doc);
        const prompt = page.context.prompt;
        switch (event.image?.kind) {
            case "idle":
                await api.prompt.generate(state, prompt.id);
                break;
            case "completed":
                if (event.image.data.prompt.id === prompt.id) {
                    updateProgress(progress, prompt);
                    await api.prompt.generate(state, prompt.id);
                }
                break;
        }
    },
};

/**
 * Updates the progress.
 *
 * @param progress
 *     The progress element.
 * @param prompt
 *     The prompt whose progress to show.
 */
const updateProgress = (progress, prompt) => {
    progress.style.width =
        (100 * prompt.progress) + "%";
    progress.parentElement.style.visibility =
        (prompt.progress === undefined || prompt.progress >= 1.0)
            ? "hidden"
            : "visible";
};
