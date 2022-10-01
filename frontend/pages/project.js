import api from "../api.js";
import { translate as _ } from "../translation.js";
import * as ui from "../ui.js";


export default {
    initialize: async (state, id) => {
        const [project, prompts] = await Promise.all([
            api.project.get(state, id),
            api.project.prompts(state, id),
        ]);
        return { project, prompts };
    },

    show: async (page, state) => {
        const [target] = ui.managed(page.doc);
        const buttonTemplate = document.getElementById("button-large");
        page.context.prompts.forEach((prompt) => {
            const button = buttonTemplate.content.cloneNode(true);
            const [link, icon, name, description] = ui.managed(button);

            button.firstElementChild.classList.add(
                ui.PROMPT_CLASS,
                ui.className(prompt.id));
            icon.style.backgroundImage =
                `url(${api.prompt.iconURL(prompt.id)})`;
            name.innerText = prompt.text;

            target.appendChild(button);
        });
    },

    notificationURL: (page) =>
        `project/${page.context.project.id}/notifications`,

    notify: async (page, state, event) => {
        page.context.prompts.forEach(async (prompt) => {
            switch (event.image?.kind) {
                case "idle":
                    await api.prompt.generate(state, prompt.id);
                    break;
                case "completed":
                    if (event.image.data.prompt.id === prompt.id) {
                        await api.prompt.generate(state, prompt.id);
                    }
                    break;
            }
        });
    },
};
