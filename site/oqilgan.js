/* Maqolalarning oʻqilganlik hisoblagichi (abacus.jasoncameron.dev, bepul, roʻyxatdan oʻtishsiz).
   Maqola sahifasi ochilganda hisob bittaga oshadi; roʻyxatlarda faqat oʻqiladi. */
(function () {
  var API = 'https://abacus.jasoncameron.dev';
  var NOM = 'quronov-uz';

  function kalit(slug) { return encodeURIComponent(String(slug).slice(0, 64)); }
  function son(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function sorov(yol) {
    return fetch(API + yol, { mode: 'cors' })
      .then(function (r) { return r.ok ? r.json() : { value: 0 }; })
      .then(function (d) { return d && d.value ? d.value : 0; })
      .catch(function () { return null; });
  }
  function yozuv() {
    try { return localStorage.getItem('yozuv') === 'kir' ? 'kir' : 'lat'; } catch (x) { return 'lat'; }
  }

  // maqola sahifasi: ochilganda +1 va oxirida koʻrsatish
  var pastki = document.querySelector('.oqilgan[data-kalit]');
  if (pastki) {
    sorov('/hit/' + NOM + '/' + kalit(pastki.dataset.kalit)).then(function (n) {
      if (!n) return;
      var lat = 'Bu maqola ' + son(n) + ' marta oʻqildi';
      var kir = 'Бу мақола ' + son(n) + ' марта ўқилди';
      pastki.setAttribute('data-lat', lat);
      pastki.setAttribute('data-kir', kir);
      pastki.textContent = yozuv() === 'kir' ? kir : lat;
      pastki.hidden = false;
    });
  }

  // roʻyxatlar: yozuv koʻrinishga kirgandagina soʻraladi
  var belgilar = document.querySelectorAll('.oqildi[data-kalit]');
  if (!belgilar.length) return;
  function toldir(el) {
    if (el.dataset.olingan) return;
    el.dataset.olingan = '1';
    sorov('/get/' + NOM + '/' + kalit(el.dataset.kalit)).then(function (n) {
      if (n) el.textContent = son(n) + (document.documentElement.lang === 'en' ? ' views' : ' marta oʻqilgan');
    });
  }
  if ('IntersectionObserver' in window) {
    // boʻsh belgi yashirin (display:none) boʻlgani uchun uning oʻzini emas, yozuv blokini kuzatamiz
    var kuzatuvchi = new IntersectionObserver(function (yozuvlar) {
      yozuvlar.forEach(function (y) {
        if (!y.isIntersecting) return;
        toldir(y.target.querySelector('.oqildi[data-kalit]'));
        kuzatuvchi.unobserve(y.target);
      });
    }, { rootMargin: '200px' });
    belgilar.forEach(function (el) { kuzatuvchi.observe(el.closest('article') || el.parentElement); });
  } else {
    belgilar.forEach(toldir);
  }
})();
