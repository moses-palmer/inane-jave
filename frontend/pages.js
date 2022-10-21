import overview from "./pages/overview.js";
import project from "./pages/project.js";
import project_create from "./pages/project-create.js";
import prompt from "./pages/prompt.js";

/**
 * The pages of the application.
 *
 * The names correspond to classes added to the body for simplicity.
 */
const module = {
    "overview": overview,
    "project": project,
    "project:create": project_create,
    "prompt": prompt,

    /**
     * Attempts to calculate the next view given an application state.
     *
     * @param state
     *     The current application state.
     */
    calculate: async (state) => {
        // Default to the overview
        return "overview";
    },
};

export default module;
