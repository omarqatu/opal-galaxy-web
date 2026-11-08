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
    Array.prototype.forEach.call(unit.options, function (o) {
      o.hidden = !!(b && b !== 'other' && o.dataset.brands !== undefined && o.dataset.brands.split(' ').indexOf(b) === -1);
    });
  }
  if (unit) { unit.addEventListener('change', filterBrands); filterBrands(); }
  if (brand) { brand.addEventListener('change', filterUnits); filterUnits(); }

  // Remove ?sent= from the address bar once the notice is shown.
  if (/[?&]sent=/.test(location.search) && history.replaceState) {
    history.replaceState(null, '', location.pathname + location.hash);
  }
})();
