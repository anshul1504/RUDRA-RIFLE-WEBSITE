/* Rudra Sports site scripts. Everything degrades gracefully without JavaScript. */
(function () {
  "use strict";

  /* Close the mobile menu after choosing a link */
  document.querySelectorAll("#mainNav .nav-link").forEach(function (link) {
    link.addEventListener("click", function () {
      var panel = document.getElementById("mainNav");
      if (panel && panel.classList.contains("show") && window.bootstrap) {
        window.bootstrap.Collapse.getOrCreateInstance(panel).hide();
      }
    });
  });

  /* Homepage carousel: autoplay unless reduced motion is preferred; pauses on hover, focus and via the button */
  var hero = document.getElementById("heroCarousel");
  if (hero && window.bootstrap) {
    var interval = parseInt(hero.getAttribute("data-interval"), 10) || 6500;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var carousel = window.bootstrap.Carousel.getOrCreateInstance(hero, { interval: interval, ride: false, pause: false, touch: true, wrap: true });
    var toggle = document.getElementById("heroToggle");
    var current = document.getElementById("heroCurrent");
    var userPaused = reduce, hoverPaused = false;
    hero.style.setProperty("--hero-interval", interval / 1000 + "s");
    var apply = function () {
      var paused = userPaused || hoverPaused;
      hero.classList.toggle("is-paused", paused);
      hero.classList.toggle("no-autoplay", userPaused);
      if (paused) { carousel.pause(); } else { carousel.cycle(); }
      if (toggle) {
        toggle.setAttribute("aria-label", userPaused ? "Play slideshow" : "Pause slideshow");
        toggle.innerHTML = '<i class="bi bi-' + (userPaused ? "play" : "pause") + '-fill" aria-hidden="true"></i>';
      }
    };
    apply();
    if (toggle) { toggle.addEventListener("click", function () { userPaused = !userPaused; apply(); }); }
    hero.addEventListener("mouseenter", function () { hoverPaused = true; apply(); });
    hero.addEventListener("mouseleave", function () { hoverPaused = false; apply(); });
    hero.addEventListener("focusin", function () { hoverPaused = true; apply(); });
    hero.addEventListener("focusout", function () { hoverPaused = false; apply(); });
    hero.addEventListener("slid.bs.carousel", function (e) {
      if (current) { current.textContent = String(e.to + 1).padStart(2, "0"); }
      hero.querySelectorAll(".hero-indicators button").forEach(function (b, i) {
        if (i === e.to) { b.setAttribute("aria-current", "true"); } else { b.removeAttribute("aria-current"); }
      });
    });
  }

  /* Contact page: quick topic chips fill the subject field */
  var topics = document.querySelectorAll(".cx-topics button");
  var subject = document.getElementById("id_subject");
  if (topics.length && subject) {
    topics.forEach(function (btn) {
      btn.addEventListener("click", function () {
        subject.value = btn.getAttribute("data-topic");
        topics.forEach(function (b) { b.classList.toggle("is-on", b === btn); b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
        subject.focus();
      });
    });
  }

  /* Admission form: highlight the guardian section when the date of birth makes the applicant under 18 */
  var enquiry = document.getElementById("enquiryForm");
  var dobInput = document.getElementById("id_date_of_birth");
  if (enquiry && dobInput) {
    var hint = document.getElementById("guardianHint");
    var check = function () {
      var v = dobInput.value, minor = false;
      if (v) {
        var d = new Date(v), now = new Date();
        if (!isNaN(d)) {
          var age = now.getFullYear() - d.getFullYear();
          if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) { age--; }
          minor = age < 18;
        }
      }
      enquiry.classList.toggle("is-minor", minor);
      if (hint) { hint.textContent = minor ? "Required: the applicant is under 18, so please add a parent or guardian." : "Required if the applicant is under 18. Adults can leave this blank."; }
    };
    dobInput.addEventListener("change", check);
    dobInput.addEventListener("input", check);
    check();
  }

  /* Prevent double submission of forms */
  document.querySelectorAll("form[data-once]").forEach(function (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector('[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.setAttribute("aria-busy", "true");
        btn.dataset.label = btn.textContent;
        btn.textContent = "Sending...";
      }
    });
  });
  /* Re-enable if the user navigates back (bfcache) */
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    document.querySelectorAll("form[data-once] [type=submit]").forEach(function (btn) {
      btn.disabled = false;
      if (btn.dataset.label) btn.textContent = btn.dataset.label;
    });
  });

  /* Scroll reveal: sections animate in once, with a small stagger between siblings. */
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealSelector = ".section-head, .card-rudra, .tile, .feature, .why-item, .event-row, .contact-card, .gallery-item, " +
    ".frame, .reel, .form-card, .cta-band .row, .safety .col-lg-8, .empty-state, .detail-list, .prose, .hero-title";
  if (!reduceMotion && "IntersectionObserver" in window) {
    var targets = Array.prototype.slice.call(document.querySelectorAll("main " + revealSelector))
      .filter(function (el) { return !el.closest(".hero-carousel") && !el.closest(".page-hero") && !el.closest("dialog"); });
    var seen = new Map();
    targets.forEach(function (el) {
      var idx = seen.get(el.parentElement) || 0;
      seen.set(el.parentElement, idx + 1);
      el.style.setProperty("--d", Math.min(idx, 5) * 0.09 + "s");
      el.classList.add("reveal");
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        el.classList.add("is-visible");
        el.addEventListener("animationend", function () {
          el.classList.remove("reveal", "is-visible");
          el.style.removeProperty("--d");
        }, { once: true });
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    targets.forEach(function (el) { io.observe(el); });
  }

  /* Announcement bar: dismissible per browser session */
  var announce = document.getElementById("announce");
  if (announce) {
    var key = "announce-" + announce.getAttribute("data-id");
    try { if (window.sessionStorage.getItem(key)) { announce.classList.add("is-hidden"); } } catch (e) { /* storage unavailable */ }
    announce.querySelector(".announce__close").addEventListener("click", function () {
      announce.classList.add("is-hidden");
      try { window.sessionStorage.setItem(key, "1"); } catch (e) { /* ignore */ }
    });
  }

  /* One passive, rAF-throttled scroll handler for header shadow, progress bar and back-to-top.
     It only reads scrollY once per frame and writes with cheap class / transform changes (no layout reads in the loop). */
  var header = document.getElementById("site-header");
  var bar = document.getElementById("scrollProgress");
  var toTop = document.getElementById("toTop");
  if (header || bar || toTop) {
    var ticking = false, docMax = 0, lastShadow = null, lastShown = null;
    var measure = function () { var h = document.documentElement; docMax = Math.max(h.scrollHeight - h.clientHeight, 0); };
    var update = function () {
      var y = window.scrollY;
      if (header) {
        var shadow = y > 8;
        if (shadow !== lastShadow) { header.classList.toggle("is-scrolled", shadow); lastShadow = shadow; }
      }
      if (bar) { bar.style.transform = "scaleX(" + (docMax > 0 ? Math.min(y / docMax, 1) : 0) + ")"; }
      if (toTop) {
        var shown = y > 700;
        if (shown !== lastShown) { toTop.classList.toggle("is-shown", shown); lastShown = shown; }
      }
      ticking = false;
    };
    measure();
    update();
    window.addEventListener("scroll", function () { if (!ticking) { ticking = true; window.requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener("resize", function () { measure(); }, { passive: true });
    window.addEventListener("load", measure);
    if (toTop) {
      toTop.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" }); });
    }
  }

  /* Decode images off the main thread so image-heavy sections do not stall scrolling. */
  document.querySelectorAll("img:not([decoding])").forEach(function (img) { img.decoding = "async"; });

  /* ---------------- Gallery: filters + lightbox ---------------- */
  var grid = document.getElementById("gallery-grid");
  if (!grid) return;

  var items = Array.prototype.slice.call(grid.querySelectorAll(".gallery-item"));
  var filterBar = document.getElementById("gallery-filters");
  var status = document.getElementById("gallery-status");

  function visibleItems() { return items.filter(function (i) { return !i.hidden; }); }

  if (filterBar) {
    filterBar.hidden = false;
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      var cat = btn.getAttribute("data-filter");
      filterBar.querySelectorAll("[data-filter]").forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      items.forEach(function (item) {
        item.hidden = !(cat === "all" || item.getAttribute("data-category") === cat);
      });
      if (status) {
        var n = visibleItems().length;
        status.textContent = "Showing " + n + (n === 1 ? " photo" : " photos") + (cat === "all" ? "" : " in " + btn.textContent.trim());
      }
    });
  }

  var dialog = document.getElementById("lightbox");
  if (!dialog || typeof dialog.showModal !== "function") return; /* links open the full image instead */

  var imgEl = dialog.querySelector(".lightbox__img");
  var capEl = dialog.querySelector(".lightbox__caption");
  var current = 0, list = [], opener = null;

  function show(i) {
    current = (i + list.length) % list.length;
    var a = list[current].querySelector("a.gallery-thumb");
    var thumb = a.querySelector("img");
    imgEl.src = a.getAttribute("href");
    imgEl.alt = thumb.getAttribute("alt") || "";
    var cap = list[current].querySelector("figcaption");
    capEl.textContent = (cap ? cap.textContent.trim() : "") + (list.length > 1 ? "  (" + (current + 1) + " / " + list.length + ")" : "");
  }

  grid.addEventListener("click", function (e) {
    var a = e.target.closest("a.gallery-thumb");
    if (!a) return;
    e.preventDefault();
    opener = a;
    list = visibleItems();
    var idx = list.indexOf(a.closest(".gallery-item"));
    show(idx < 0 ? 0 : idx);
    dialog.showModal();
    dialog.querySelector(".lightbox__close").focus();
  });

  dialog.querySelector(".lightbox__prev").addEventListener("click", function () { show(current - 1); });
  dialog.querySelector(".lightbox__next").addEventListener("click", function () { show(current + 1); });
  dialog.querySelector(".lightbox__close").addEventListener("click", function () { dialog.close(); });
  dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });
  dialog.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") { show(current - 1); }
    else if (e.key === "ArrowRight") { show(current + 1); }
  });
  dialog.addEventListener("close", function () { imgEl.removeAttribute("src"); if (opener) opener.focus(); });
})();
