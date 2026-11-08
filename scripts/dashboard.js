// The dashboard's one script (scripts/dashboard.py copies it into the site as site.js): the charts' tooltips. Every
// mark carries its numbers in data-tip (and the same text in aria-label); this shows them on hover, on keyboard
// focus and on a tap, so no number needs a mouse. A tap elsewhere, Escape or a resize hides them. No library.
(function () {
  var tip = document.createElement("div");
  tip.className = "tip";
  tip.setAttribute("role", "tooltip");
  tip.hidden = true;
  document.body.appendChild(tip);
  var pinned = null;

  function mark(node) {
    return node && node.closest ? node.closest("[data-tip]") : null;
  }

  function show(el) {
    tip.textContent = el.getAttribute("data-tip");
    tip.hidden = false;
    var r = el.getBoundingClientRect();
    var t = tip.getBoundingClientRect();
    var width = document.documentElement.clientWidth;
    var x = Math.max(8, Math.min(r.left + r.width / 2 - t.width / 2, width - t.width - 8));
    var y = r.top - t.height - 8;
    if (y < 8) y = r.bottom + 8;
    tip.style.left = x + window.scrollX + "px";
    tip.style.top = y + window.scrollY + "px";
  }

  function pin(el) {
    if (pinned) pinned.classList.remove("on");
    pinned = el;
    if (el) el.classList.add("on");
  }

  function hide() {
    tip.hidden = true;
    pin(null);
  }

  document.addEventListener("mouseover", function (e) {
    var m = mark(e.target);
    if (m) show(m);
    else if (pinned) show(pinned);
    else tip.hidden = true;
  });
  document.addEventListener("focusin", function (e) {
    var m = mark(e.target);
    if (m) {
      pin(m);
      show(m);
    }
  });
  document.addEventListener("focusout", function (e) {
    if (!mark(e.relatedTarget)) hide();
  });
  document.addEventListener("click", function (e) {
    var m = mark(e.target);
    if (m) {
      e.preventDefault();
      pin(m);
      show(m);
    } else {
      hide();
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hide();
  });
  window.addEventListener("resize", hide);
})();
