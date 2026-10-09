// Rolls a d20: plays the clip of the rolling die, then shows the face.
//
// Any element with a data-roll attribute starts a roll. With
// data-roll-label and data-roll-modifier it is an ability check: the
// modifier is added to the number on the die. A roll with advantage or
// disadvantage throws two dice side by side; then the higher or the lower
// one comes to the front and the other one steps back.
(function () {
  "use strict";

  var SIDES = 20;
  // The face is shown when the clip ends; this is for a clip that never does.
  var ROLL_TIME_LIMIT = 2000;
  // Two dice lie side by side for a moment before one of them is chosen.
  var CHOICE_DELAY = 700;
  var HISTORY_LENGTH = 5;
  var MODES = { advantage: "Advantage", disadvantage: "Disadvantage" };

  var dialog = document.getElementById("dice-dialog");
  if (!dialog || !dialog.showModal || !window.crypto) {
    return;
  }
  // Two dice; the second one is on the table only when two are thrown.
  var stages = dialog.querySelectorAll(".dice-stage");
  var videos = dialog.querySelectorAll("video");
  var faces = dialog.querySelectorAll(".dice-face");
  var title = document.getElementById("dice-title");
  var result = dialog.querySelector(".dice-result");
  var detail = dialog.querySelector(".dice-detail");
  var earlierRolls = dialog.querySelector(".dice-history");
  var defaultTitle = title.textContent;
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var modifier = null;
  // The roll that waits for the clip to end.
  var pending = null;
  // The roll on the screen: it moves to the history with the next one.
  var shown = null;
  var clipIsBroken = false;
  // Waits for the end of the clip, then for the choice between two dice.
  var timer = null;

  // Every face is equally likely: numbers above the last full set of
  // twenty are thrown away.
  function randomFace() {
    var limit = Math.floor(0x100000000 / SIDES) * SIDES;
    var buffer = new Uint32Array(1);
    do {
      window.crypto.getRandomValues(buffer);
    } while (buffer[0] >= limit);
    return (buffer[0] % SIDES) + 1;
  }

  // One die, or two dice of which the mode keeps one.
  function throwDice(mode) {
    var dice = [randomFace()];
    if (MODES[mode]) {
      dice.push(randomFace());
    }
    var pick = mode === "disadvantage" ? Math.min : Math.max;
    var kept = pick.apply(null, dice);
    return {
      mode: mode,
      dice: dice,
      kept: kept,
      keptIndex: dice.indexOf(kept),
    };
  }

  function remember(entry) {
    var item = document.createElement("li");
    var label = document.createElement("span");
    var total = document.createElement("b");
    label.textContent = entry.label;
    total.textContent = entry.total;
    item.appendChild(label);
    item.appendChild(total);
    earlierRolls.insertBefore(item, earlierRolls.firstChild);
    while (earlierRolls.children.length > HISTORY_LENGTH) {
      earlierRolls.removeChild(earlierRolls.lastChild);
    }
    earlierRolls.hidden = false;
  }

  // Puts the dice of the last choice back side by side at once: the motion
  // belongs to the choice, not to the start of the next roll.
  function resetStages() {
    var index;
    for (index = 0; index < stages.length; index += 1) {
      stages[index].style.transition = "none";
      stages[index].classList.remove("is-kept", "is-dropped");
    }
    // Reading the size makes the browser apply the styles right now.
    void dialog.offsetWidth;
    for (index = 0; index < stages.length; index += 1) {
      stages[index].style.transition = "";
    }
  }

  // Stops the clips and whatever the roll was waiting for.
  function stop() {
    clearTimeout(timer);
    pending = null;
    for (var index = 0; index < videos.length; index += 1) {
      videos[index].pause();
    }
  }

  // Shows the faces. Two dice wait a moment before one of them is chosen.
  function reveal(thrown) {
    stop();
    dialog.classList.remove("is-rolling");
    if (thrown.dice.length === 1 || reducedMotion.matches) {
      announce(thrown);
    } else {
      timer = setTimeout(function () {
        announce(thrown);
      }, CHOICE_DELAY);
    }
  }

  // Brings the die that counts to the front and writes the result.
  function announce(thrown) {
    var value = thrown.kept;
    if (thrown.dice.length === 2) {
      for (var index = 0; index < stages.length; index += 1) {
        stages[index].classList.add(
          index === thrown.keptIndex ? "is-kept" : "is-dropped"
        );
      }
    }

    var outcome = "";
    var parts = [];
    var total = value;
    if (modifier !== null) {
      total = value + modifier;
      parts.push(
        value + (modifier < 0 ? " − " : " + ") + Math.abs(modifier)
      );
    }
    if (MODES[thrown.mode]) {
      parts.push(MODES[thrown.mode] + ": " + thrown.dice.join(" and "));
    }
    if (value === SIDES) {
      outcome = "critical";
      parts.push("Critical success");
    } else if (value === 1) {
      outcome = "fumble";
      parts.push("Critical failure");
    }
    dialog.dataset.outcome = outcome;
    result.textContent = total;
    detail.textContent = parts.join(" · ");
    shown = { label: title.textContent, total: total };
  }

  function playClip(video) {
    video.currentTime = 0;
    var playing = video.play();
    if (playing && playing.catch) {
      playing.catch(function (error) {
        // reveal() pauses the clip; that interruption is not a failure.
        if (error.name === "NotSupportedError") {
          clipIsBroken = true;
          finish();
        }
      });
    }
  }

  function roll(mode) {
    var thrown = throwDice(mode);
    var index;
    clearTimeout(timer);
    if (shown) {
      remember(shown);
      shown = null;
    }
    dialog.dataset.outcome = "";
    result.textContent = "";
    detail.textContent = "";
    resetStages();
    dialog.classList.toggle("is-pair", thrown.dice.length === 2);
    for (index = 0; index < stages.length; index += 1) {
      var value = thrown.dice[index];
      stages[index].hidden = value === undefined;
      if (value !== undefined) {
        // The face loads while the clip is playing.
        faces[index].src = dialog.dataset.faceSrc.replace(
          /\d+(?=\.\w+$)/,
          value
        );
        faces[index].alt = "The die shows " + value;
      }
    }

    if (reducedMotion.matches || clipIsBroken) {
      reveal(thrown);
      return;
    }
    dialog.classList.add("is-rolling");
    pending = thrown;
    for (index = 0; index < thrown.dice.length; index += 1) {
      playClip(videos[index]);
    }
    timer = setTimeout(finish, ROLL_TIME_LIMIT);
  }

  function finish() {
    if (pending !== null) {
      reveal(pending);
    }
  }

  function open(trigger) {
    var label = trigger.dataset.rollLabel;
    var bonus = parseInt(trigger.dataset.rollModifier, 10);
    // A roll that is still on the screen keeps its own title in the history:
    // announce() has already stored it.
    title.textContent = label || defaultTitle;
    modifier = isNaN(bonus) ? null : bonus;
    if (!dialog.open) {
      dialog.showModal();
    }
    roll();
  }

  // Sources are tried in order: an error on the last one means that the
  // browser cannot play the clip at all.
  var sources = videos[0].querySelectorAll("source");
  sources[sources.length - 1].addEventListener("error", function () {
    clipIsBroken = true;
  });
  // Both clips are the same, so the first one tells when the dice stop.
  videos[0].addEventListener("ended", finish);

  document.addEventListener("click", function (event) {
    var trigger = event.target.closest
      ? event.target.closest("[data-roll]")
      : null;
    if (trigger) {
      open(trigger);
    }
  });

  dialog.addEventListener("click", function (event) {
    var again = event.target.closest("[data-dice-again]");
    if (again) {
      // An empty value is one die; "advantage" and "disadvantage" are two.
      roll(again.dataset.diceAgain);
      return;
    }
    // A click on the backdrop closes the dialog as the button does. The
    // backdrop belongs to the dialog element, so the click is told apart
    // by its position.
    var box = dialog.getBoundingClientRect();
    var inside =
      event.clientX >= box.left &&
      event.clientX <= box.right &&
      event.clientY >= box.top &&
      event.clientY <= box.bottom;
    var onBackdrop = event.target === dialog && !inside;
    if (onBackdrop || event.target.closest("[data-dice-close]")) {
      stop();
      dialog.close();
    }
  });
  // Escape closes the dialog without a click.
  dialog.addEventListener("close", function () {
    // The event comes late: the dialog may be rolling again by now.
    if (!dialog.open) {
      stop();
    }
  });

  // Roll buttons are useless without this script, so they start hidden.
  var hiddenTriggers = document.querySelectorAll("[data-roll][hidden]");
  for (var index = 0; index < hiddenTriggers.length; index += 1) {
    hiddenTriggers[index].hidden = false;
  }
})();
