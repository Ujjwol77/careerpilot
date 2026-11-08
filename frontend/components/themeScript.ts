export const THEME_KEY = "careerpilot-theme";

/** Runs before the page paints, so a saved theme never flashes the wrong colours. */
export const themeInitScript = `(function(){try{var t=localStorage.getItem("${THEME_KEY}");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}catch(e){}})();`;
