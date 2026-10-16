/* Single "Designed & Developed by The Webfix" credit: replaces the theme's version label in the admin footer,
   and sits at the bottom of the login screen. */
(function () {
  var html = 'Designed &amp; Developed by <a href="https://thewebfix.in" target="_blank" rel="noopener">The Webfix</a>';
  function add() {
    var slot = document.querySelector("footer.main-footer .float-right");
    if (slot) {
      slot.className = "float-right d-none d-sm-inline-block rs-credit";
      slot.innerHTML = html;
      return;
    }
    if (document.querySelector(".rs-credit")) { return; }
    var box = document.createElement("div");
    box.className = "rs-credit rs-credit--floating";
    box.innerHTML = html;
    document.body.appendChild(box);
  }
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", add); } else { add(); }
})();
