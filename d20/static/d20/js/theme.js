// Day and night themes.
//
// The choice is kept in the browser; without one the theme follows the
// system setting. The script is loaded in <head> without "defer", so the
// page is painted in the right theme from the start.
(function () {
  "use strict";

  var KEY = "d20-theme";
  var root = document.documentElement;
  var system = window.matchMedia("(prefers-color-scheme: dark)");
  var button = null;
  // Used when the browser does not let the page store anything.
  var chosen = null;

  function stored() {
    try {
      return window.localStorage.getItem(KEY);
    } catch (error) {
      return null;
    }
  }

  function theme() {
    var value = chosen || stored();
    if (value === "dark" || value === "light") {
      return value;
    }
    return system.matches ? "dark" : "light";
  }

  function apply() {
    var current = theme();
    root.dataset.theme = current;
    if (button) {
      var label =
        current === "dark"
          ? "Switch to the day theme"
          : "Switch to the night theme";
      button.setAttribute("aria-label", label);
      button.title = label;
    }
  }

  function toggle() {
    chosen = theme() === "dark" ? "light" : "dark";
    try {
      window.localStorage.setItem(KEY, chosen);
    } catch (error) {
      // The choice lasts until the page is closed.
    }
    apply();
  }

  apply();
  // Without a stored choice the page follows the system as it changes.
  if (system.addEventListener) {
    system.addEventListener("change", apply);
  }

  document.addEventListener("DOMContentLoaded", function () {
    button = document.querySelector("[data-theme-toggle]");
    if (!button) {
      return;
    }
    button.hidden = false;
    button.addEventListener("click", toggle);
    apply();
  });
})();
