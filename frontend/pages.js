import overview from "./pages/overview.js";

/**
 * The pages of the application.
 *
 * The names correspond to classes added to the body for simplicity.
 */
const module = {
    "overview": overview,

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
