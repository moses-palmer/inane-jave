import api from "../api.js";
import { translate as _ } from "../translation.js";
import * as ui from "../ui.js";


export default {
    initialize: async (state) => {
        return await api.project.all(state);
    },

    show: async (page, state) => {
        const [target] = ui.managed(page.doc);
        const buttonTemplate = document.getElementById("button-large");
        page.context.forEach((project) => {
            const button = buttonTemplate.content.cloneNode(true);
            const [link, icon, name, description] = ui.managed(button);

            button.firstElementChild.classList.add(
                ui.PROJECT_CLASS,
                ui.className(project.id));
            icon.style.backgroundImage =
                `url(${api.project.iconURL(project.id)})`;
            name.innerText = project.name;
            description.innerText = project.description;

            target.appendChild(button);
        });
    },
};
