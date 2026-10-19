/* Single "Designed & Developed by The Webfix" credit: replaces the theme's version label in the admin footer,
   and sits at the bottom of the login screen. */
(function () {
  /* the brass admin theme is light-only: ignore any dark/auto mode a browser may have stored earlier */
  try { localStorage.removeItem('jazzmin-theme-mode'); } catch (e) {}
  document.documentElement.setAttribute('data-bs-theme', 'light');
  var html = 'Designed &amp; Developed by <a href="https://thewebfix.in" target="_blank" rel="noopener">The Webfix</a>';
  function add() {
    var slot = document.querySelector("footer.app-footer .float-end, footer.main-footer .float-right");
    if (slot) {
      slot.className = "float-end d-none d-sm-inline-block rs-credit";
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
