(function () {
  var t = document.querySelector('.menu-toggle'), m = document.getElementById('menu');
  if (!t || !m) return;
  t.addEventListener('click', function () {
    var open = m.classList.toggle('open');
    t.setAttribute('aria-expanded', open);
  });
})();
