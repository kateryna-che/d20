// Helpers of the character sheet and of its form.
//
// The form shows the modifier next to every ability score and a token in
// the colour of the chosen class. The sheet gets a button that prints it.
(function () {
  "use strict";

  // The modifier that an ability score adds to a roll: 10 gives 0, 12 gives +1.
  function modifierText(score) {
    var modifier = Math.floor((score - 10) / 2);
    return (modifier < 0 ? "−" : "+") + Math.abs(modifier);
  }

  function watchScore(input) {
    var label = document.querySelector('label[for="' + input.id + '"]');
    if (!label) {
      return;
    }
    var badge = document.createElement("span");
    badge.className = "ability-modifier";
    label.appendChild(badge);

    function update() {
      var score = parseInt(input.value, 10);
      badge.textContent = isNaN(score) ? "" : modifierText(score);
    }

    input.addEventListener("input", update);
    update();
  }

  var scores = document.querySelectorAll("[data-ability-scores] input");
  for (var index = 0; index < scores.length; index += 1) {
    watchScore(scores[index]);
  }

  var token = document.querySelector("[data-token-preview]");
  var nameField = document.getElementById("id_name");
  var classField = document.getElementById("id_character_class");
  if (token && nameField && classField) {
    var drawToken = function () {
      token.className = "token token-large token-" + classField.value;
      token.textContent = (nameField.value.trim().charAt(0) || "?").toUpperCase();
    };
    nameField.addEventListener("input", drawToken);
    classField.addEventListener("change", drawToken);
    drawToken();
    token.hidden = false;
  }

  var printButton = document.querySelector("[data-print]");
  if (printButton) {
    printButton.addEventListener("click", function () {
      window.print();
    });
    printButton.hidden = false;
  }
})();
