// Messages of the site float in a corner and leave by themselves: that is
// done in CSS. This script only adds the button that closes one earlier.
(function () {
  "use strict";

  var notices = document.querySelectorAll(".messages .message");

  function close(event) {
    var notice = event.currentTarget.parentNode;
    notice.parentNode.removeChild(notice);
  }

  for (var index = 0; index < notices.length; index += 1) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "message-close";
    button.setAttribute("aria-label", "Close the message");
    button.textContent = "×";
    button.addEventListener("click", close);
    notices[index].appendChild(button);
  }
})();
