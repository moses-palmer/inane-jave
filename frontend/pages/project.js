import api from "../api.js";
import { translate as _ } from "../translation.js";
import * as ui from "../ui.js";


export default {
    initialize: async (state, id) => {
        const [project, prompts] = await Promise.all([
            api.project.get(state, id),
            api.project.prompts(state, id),
        ]);
        return { project };
    },

    show: async (page, state) => {
        const [target, add, remover, remove] = ui.managed(page.doc);
        const buttonTemplate = document.getElementById("button-large");
        const iconTemplate = document.getElementById("button-icons");
        page.context.project.prompts.forEach((prompt) => {
            const button = buttonTemplate.content.cloneNode(true);
            const [link, icon, name, description] = ui.managed(button);

            button.firstElementChild.classList.add(
                ui.PROMPT_CLASS,
                ui.className(prompt.id));
            link.href = `#prompt/${prompt.id}`;
            icon.style.backgroundImage =
                `url(${api.prompt.iconURL(prompt.id)})`;
            name.innerText = prompt.text;

            target.appendChild(button);
        });
        add.appendChild(
            iconTemplate.content.querySelector("#add").cloneNode(true));
        remove.appendChild(
            iconTemplate.content.querySelector("#remove").cloneNode(true));
        remover.onclick = async() => {
            const response = await ui.message(
                _("Delete project"),
                _("Do you want to delete this project and all prompts?"),
                [
                    {name: "no", text: _("No"), classes: ["cancel"]},
                    {name: "yes", text: _("Yes"), classes: ["ok"]},
                ]);
            if (response === "yes") {
                await api.project.remove(state, page.context.project.id);
                location.href = `#overview`;
            }
        };
    },

    notificationURL: (page) =>
        `project/${page.context.project.id}/notifications`,

    notify: async (page, state, event) => {
        page.context.project.prompts.forEach(async (prompt) => {
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
