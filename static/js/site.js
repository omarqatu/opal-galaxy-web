/* Opal Galaxy — small progressive enhancements. The site works without JS. */
(function () {
  'use strict';
  var burger = document.getElementById('burger'), menu = document.getElementById('menu');
  if (burger && menu) {
    burger.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', open);
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') { menu.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  // Hide the mobile action bar while the quote form is on screen.
  var mbar = document.getElementById('mbar'), contact = document.getElementById('contact');
  if (mbar && contact && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (es) { mbar.classList.toggle('hide', es[0].isIntersecting); },
      { threshold: 0.15 }).observe(contact);
  }

  // Only offer brands that actually supply the chosen product.
  var unit = document.getElementById('f-unit'), brand = document.getElementById('f-brand');
  function filterBrands() {
    if (!unit || !brand) return;
    var opt = unit.selectedOptions[0], ids = opt && opt.dataset.brands ? opt.dataset.brands.split(' ') : null;
    Array.prototype.forEach.call(brand.options, function (o) {
      o.hidden = !!(ids && o.value && o.value !== 'other' && ids.indexOf(o.value) === -1);
    });
    if (brand.selectedOptions[0] && brand.selectedOptions[0].hidden) brand.value = '';
  }
  function filterUnits() {
    if (!unit || !brand || unit.value) return;
    var b = brand.value;
    var supplies = function (o) { return o.dataset.brands !== undefined && o.dataset.brands.split(' ').indexOf(b) !== -1; };
    // A brand with no catalogue rows yet must not empty the product list.
    var known = Array.prototype.some.call(unit.options, supplies);
    Array.prototype.forEach.call(unit.options, function (o) {
      o.hidden = !!(known && b && b !== 'other' && o.dataset.brands !== undefined && !supplies(o));
    });
  }
  if (unit) { unit.addEventListener('change', filterBrands); filterBrands(); }
  if (brand) { brand.addEventListener('change', filterUnits); filterUnits(); }

  // Header: a quiet shadow once the page has scrolled.
  var header = document.getElementById('site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  // Scroll reveal. Content is visible by default; CSS hides [data-reveal] only when the
  // "js" class is set and the visitor has not asked for reduced motion.
  var targets = document.querySelectorAll('[data-reveal]');
  if (targets.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      Array.prototype.forEach.call(targets, function (t) { io.observe(t); });
    } else {
      Array.prototype.forEach.call(targets, function (t) { t.classList.add('is-in'); });
    }
  }

  // Gallery viewer. Without JavaScript each photo is a plain link to the larger image.
  var box = document.getElementById('lightbox'), links = document.querySelectorAll('[data-lightbox]');
  if (box && links.length && typeof box.showModal === 'function') {
    var img = box.querySelector('img'), cap = box.querySelector('figcaption'), at = 0, opener = null;
    var show = function (i) {
      at = (i + links.length) % links.length;
      var a = links[at], thumb = a.querySelector('img');
      img.src = a.href; img.alt = thumb ? thumb.alt : ''; cap.textContent = a.dataset.caption || '';
    };
    Array.prototype.forEach.call(links, function (a, i) {
      a.addEventListener('click', function (e) { e.preventDefault(); opener = a; show(i); box.showModal(); });
    });
    box.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (b && b.dataset.step) show(at + Number(b.dataset.step));
      else if (b || e.target === box) box.close();
    });
    box.addEventListener('keydown', function (e) {
      var rtl = document.documentElement.dir === 'rtl';
      if (e.key === 'ArrowRight') show(at + (rtl ? -1 : 1));
      if (e.key === 'ArrowLeft') show(at + (rtl ? 1 : -1));
    });
    box.addEventListener('close', function () { img.removeAttribute('src'); if (opener) opener.focus(); });
  }

  // Remove ?sent= from the address bar once the notice is shown.
  if (/[?&]sent=/.test(location.search) && history.replaceState) {
    history.replaceState(null, '', location.pathname + location.hash);
  }
})();
