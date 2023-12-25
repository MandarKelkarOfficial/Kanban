
"use strict";
galPicker();
var originalPosition = null;
var dragEl, nextEl;
var args = [].slice.call(document.getElementsByClassName("dragBox"));
console.log(typeof args);
[].slice
  .call(document.getElementsByClassName("dragBox"))
  .forEach(function (itemEl) {
    console.log(itemEl);
    itemEl.ondrop = function () {
      drop(this, event);
    };
    itemEl.ondragover = function () {
      allowDrop(this, event);
    };
    [].slice.call(itemEl.children).forEach(function (taskEl) {
      taskEl.draggable = true;

      taskEl.ondragstart = function () {
        drag(this, event);
      };
    });
  });
function insertAfter(elem, refElem) {
  return refElem.parentNode.insertBefore(elem, refElem.nextSibling);
}
function swipeInfo(event) {
  var x = event.clientX,
    y = event.clientY,
    dx,
    dy;

  dx = x > originalPosition.x ? "right" : "left";
  dy = y > originalPosition.y ? "down" : "up";
  originalPosition = {
    x: event.clientX,
    y: event.clientY,
  };
  return {
    direction: {
      x: dx,
      y: dy,
    },
    offset: {
      x: x - originalPosition.x,
      y: originalPosition.y - y,
    },
  };
}

function allowDrop(thisTarget, ev) {
  ev.preventDefault();
  ev.dataTransfer.dropEffect = 'move';
  var target = ev.target;
  var info = swipeInfo(ev);
  var superTarget = (target.parentNode).parentNode;

  if (target && superTarget !== dragEl && superTarget.className == 'task') {
      // Check if the drop target is a different column
      if (superTarget.parentNode.id !== dragEl.parentNode.id) {
          var taskId = superTarget.querySelector('.content').getAttribute('data-id');
          var targetStatus = superTarget.parentNode.id.split('-')[1]; // Assuming your column IDs are like "drag1", "drag2", ...

          // Update the task status in the database
          updateTaskStatus(taskId, targetStatus);
      }

      // Continue with your existing code for sorting
      if (info.direction.y === "down") {
          insertAfter(dragEl, superTarget);
      }
      if (info.direction.y === "up") {
          thisTarget.insertBefore(dragEl, superTarget);
      }
  }
}

function drag(target, event) {
  dragEl = event.target;
  originalPosition = {
    // И его первоночальную позицию
    x: event.clientX,
    y: event.clientY,
  };
  nextEl = dragEl.nextSibling;
  event.dataTransfer.setData("text", target.id);
}

function drop(target, event) {
  var data = event.dataTransfer.getData("text");
  if (event.target !== dragEl && event.target.className == "dragBox") {
    target.appendChild(document.getElementById(data));
  }
  event.preventDefault();
}

var thisTask;
function expandCard(thisCard) {
  thisTask = thisCard;
  document.querySelector(".modal-overlay").classList.add("active");
  var cardMini = thisCard.querySelector(".cardMini");
  var cardFull = thisCard.querySelector(".cardFull");
  if (thisCard.className !== "active") {
    thisCard.classList.add("active");
    cardLoc = cardMini.getBoundingClientRect();
    // cardFull.log(cardLoc.left);
    cardFull.style.left = cardLoc.left + "px";
    cardFull.style.top = cardLoc.top + "px";
    cardFull.style.width = cardLoc.width + "px";
    cardFull.style.height = cardLoc.height + "px";
    //     cardFull.style.backgroundColor = '#cccccc';

    //thisCard.classList.add("active");
    setTimeout(function () {
      var w =
        window.innerWidth ||
        document.documentElement.clientWidth ||
        document.body.clientWidth;

      var h =
        window.innerHeight ||
        document.documentElement.clientHeight ||
        document.body.clientHeight;

      //  console.log(h + ' ' + w);
      cardFull.style.width = w * 0.6 + "px";
      cardFull.style.height = h * 0.6 + "px";
      cardFull.style.left = w * 0.2 + "px";
      cardFull.style.top = h * 0.2 + "px";
    }, 25);
  }
}
var cardLoc;
window.addEventListener("click", function (event) {
  var cardDetail = document.querySelector(".task.active .cardFull");
  var modal = document.querySelector(".modal-overlay");
  //  console.log(cardDetail);

  //   console.log(cardDetail);
  if (event.target == modal) {
    //  var cardLoc = cardDetail.getBoundingClientRect();

    //                // cardDetail.removeAttribute("st/yle");
    cardDetail.style.left = cardLoc.left + "px";
    cardDetail.style.top = cardLoc.top + "px";
    cardDetail.style.width = cardLoc.width + "px";
    cardDetail.style.height = cardLoc.height + "px";

    setTimeout(function () {
      //
      document.querySelector(".modal-overlay").classList.remove("active");
      document.querySelector(".task.active").classList.remove("active");
      cardDetail.removeAttribute("style");
      //                    cardDetail.classList.remove("cardDetail");
    }, 300);
  }
});

function galPicker() {
  //  "use strict";
  let el;
  let inputEl;
  let colors = [
    "#f44336",
    "#e91e63",
    "#9c27b0",
    "#673ab7",
    "#3f51b5",
    "#2196f3",
    "#03a9f4",
    "#00bcd4",
    "#009688",
    "#4caf50",
    "#8bc34a",
    "#cddc39",
    "#ffeb3b",
    "#ffc107",
    "#ff9800",
    "#ff5722",
    "#795548",
    "#607d8b",
    "#00c097",
    "#FF5E8F",
  ];
  document.getElementsByTagName("body")[0].innerHTML +=
    '<div class="color-picker" id="gal-picker"></div>';
  let picker = document.getElementById("gal-picker");
  let i = 0;
  let text = "";

  /**
   * Usage for Example  <input type="hidden" class="gal-color" value="#9c27b0">
   *
   */
  function glaColorInit() {
    let init = document.querySelectorAll(".gal-color");
    let i = 0;

    while (init[i]) {
      let initColor = init[i].getAttribute("value");
      el = document.createElement("div");
      insertAfter(init[i], el);
      el.classList.add("color-input");
      el.setAttribute("style", "background-color: " + initColor + ";");
      i++;
    }
  }

  function insertAfter(referenceNode, newNode) {
    referenceNode.parentNode.insertBefore(
      newNode,
      referenceNode.nextSibling
    );
  }

  glaColorInit();

  while (colors[i]) {
    text +=
      '<div   class="color item" style="background-color:' +
      colors[i] +
      ';"></div>';
    i++;
  }

  document.getElementById("gal-picker").innerHTML = text;

  document.addEventListener("click", pickerOpen, false);

  function pickerOpen(event) {
    let theTarget = event.target || event.srcElement;
    pickerClose(theTarget);

    if (theTarget.className === "color-input") {
      inputEl = theTarget;
      let callElement = theTarget.getBoundingClientRect();
      picker.classList.add("active");
      let b = callElement.bottom;
      let l = callElement.left;
      picker.style.top = b + 10 + "px";
      picker.style.left = l + "px";
    }
    //console.log(inputEl);
    if (inputEl) {
      pickerOnClick(event, inputEl);
    }
  }

  function pickerOnClick(event, theTarget) {
    let target = event.target;
    if (target.className === "color item") {
      console.log(theTarget);
      theTarget.style.backgroundColor = target.style.backgroundColor;
      theTarget.previousElementSibling.value =
        target.style.backgroundColor;
      console.log(theTarget.style.backgroundColor);
      console.log(theTarget.closest(".cardFull").firstElementChild.style);
      theTarget.closest(
        ".cardFull"
      ).firstElementChild.style.backgroundColor =
        target.style.backgroundColor;
      console.log(thisTask);
      thisTask.querySelector(
        ".cardMini"
      ).firstElementChild.style.backgroundColor =
        target.style.backgroundColor;
      return;
    }
  }

  function pickerClose(theTarget) {
    if (
      theTarget.className !== "color-picker active" &&
      theTarget.className !== "color-input"
    ) {
      picker.classList.remove("active");
      // if use drug and drop need to delete position inside the window in view
      picker.removeAttribute("style");
    }
  }
}

//galPicker();