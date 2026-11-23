/* Opal Galaxy — small progressive enhancements. The site works without JS. */
(function () {
  'use strict';
  var burger = document.getElementById('burger'), menu = document.getElementById('menu');
  var drops = document.querySelectorAll('.nav-drop');
  var closeDrops = function (except) {
    Array.prototype.forEach.call(drops, function (d) { if (d !== except) d.removeAttribute('open'); });
  };
  var setMenu = function (open) {
    menu.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.documentElement.classList.toggle('menu-open', open);
    if (!open) closeDrops();
  };
  if (burger && menu) {
    burger.addEventListener('click', function () { setMenu(!menu.classList.contains('open')); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
  }

  // Dropdown menus are native <details>: they open with click, touch, Enter and Space, and work
  // without JavaScript. Here: one open at a time, Escape and outside clicks close, and on a device
  // with a mouse they also open on hover.
  var desktop = window.matchMedia('(min-width: 1181px)');
  var canHover = window.matchMedia('(hover: hover) and (pointer: fine)');
  Array.prototype.forEach.call(drops, function (d) {
    d.addEventListener('toggle', function () { if (d.open && desktop.matches) closeDrops(d); });
    var hovering = false;
    d.parentNode.addEventListener('mouseenter', function () {
      if (desktop.matches && canHover.matches) { hovering = true; closeDrops(d); d.setAttribute('open', ''); }
    });
    d.parentNode.addEventListener('mouseleave', function () {
      if (hovering) { hovering = false; d.removeAttribute('open'); }
    });
    // A mouse click on a menu that hover has already opened keeps it open instead of closing it.
    d.querySelector('summary').addEventListener('click', function (e) {
      if (hovering && d.open && e.detail > 0) e.preventDefault();
    });
  });
  document.addEventListener('click', function (e) {
    if (desktop.matches && !e.target.closest('.nav-drop')) closeDrops();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var openDrop = document.querySelector('.nav-drop[open]');
    if (openDrop && desktop.matches) { openDrop.removeAttribute('open'); openDrop.querySelector('summary').focus(); return; }
    if (menu && menu.classList.contains('open')) { setMenu(false); burger.focus(); }
  });

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
    var count = box.querySelector('.lightbox__count');
    var show = function (i) {
      at = (i + links.length) % links.length;
      var a = links[at], thumb = a.querySelector('img');
      img.src = a.href; img.alt = thumb ? thumb.alt : ''; cap.textContent = a.dataset.caption || '';
      if (count) count.textContent = (at + 1) + ' / ' + links.length;
      new Image().src = links[(at + 1) % links.length].href;   // warm the next photo
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
