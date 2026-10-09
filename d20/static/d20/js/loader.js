// Shows the dice roll while the next page is loading.
//
// Pages are rendered on the server, so "loading" is the wait between a
// click on a link or a form submit and the next page. Fast responses never
// show the loader: it appears only after SHOW_DELAY.
(function () {
  "use strict";

  var SHOW_DELAY = 250;
  var GIVE_UP_AFTER = 20000;

  var loader = document.getElementById("page-loader");
  if (!loader) {
    return;
  }
  var video = loader.querySelector("video");
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var showTimer = null;
  var giveUpTimer = null;

  function showStill() {
    loader.classList.add("is-still");
  }

  function play() {
    var playing = video.play();
    if (playing && playing.catch) {
      playing.catch(function (error) {
        // Hiding the loader interrupts play(); that is not a failure.
        if (error.name === "NotSupportedError") {
          showStill();
        }
      });
    }
  }

  function show() {
    loader.hidden = false;
    if (reducedMotion.matches) {
      showStill();
      return;
    }
    video.currentTime = 0;
    play();
  }

  function hide() {
    clearTimeout(showTimer);
    clearTimeout(giveUpTimer);
    loader.hidden = true;
    video.pause();
  }

  function schedule() {
    clearTimeout(showTimer);
    clearTimeout(giveUpTimer);
    showTimer = setTimeout(show, SHOW_DELAY);
    // The browser may never leave the page (a download, a stopped request).
    giveUpTimer = setTimeout(hide, GIVE_UP_AFTER);
  }

  function leavesPage(link, event) {
    if (event.button !== 0) {
      return false;
    }
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return false;
    }
    if (link.target && link.target !== "_self") {
      return false;
    }
    if (link.hasAttribute("download") || link.origin !== location.origin) {
      return false;
    }
    var samePage =
      link.pathname === location.pathname && link.search === location.search;
    return !(samePage && link.hash);
  }

  // Sources are tried in order: an error on the last one means that the
  // browser cannot play the clip at all.
  var sources = video.querySelectorAll("source");
  sources[sources.length - 1].addEventListener("error", showStill);

  document.addEventListener("click", function (event) {
    var link = event.target.closest ? event.target.closest("a[href]") : null;
    if (link && !event.defaultPrevented && leavesPage(link, event)) {
      schedule();
    }
  });

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!event.defaultPrevented && (!form.target || form.target === "_self")) {
      schedule();
    }
  });

  // A click on the overlay or Escape closes it if the page did not change.
  loader.addEventListener("click", hide);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      hide();
    }
  });

  // Browsers pause a muted clip in a background tab; resume it on return.
  document.addEventListener("visibilitychange", function () {
    var waiting = !loader.hidden && !loader.classList.contains("is-still");
    if (!document.hidden && waiting && video.paused) {
      play();
    }
  });

  // The page can come back from the back/forward cache with the loader on.
  window.addEventListener("pageshow", hide);
})();
