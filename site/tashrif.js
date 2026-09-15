/* Sayt kirishlari hisobi (abacus.jasoncameron.dev): jami va kunlik (Toshkent vaqti).
   Bir brauzer sessiyasida bir marta hisoblanadi; podvalda kechagi va jami kirishlar koʻrsatiladi. */
(function () {
  var joy = document.querySelector('.tashrif');
  if (!joy || !window.fetch) return;
  var API = 'https://abacus.jasoncameron.dev';
  var NOM = 'quronov-uz';

  function son(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function sorov(yol) {
    return fetch(API + yol, { mode: 'cors' })
      .then(function (r) { return r.ok ? r.json() : { value: 0 }; })
      .then(function (d) { return d && d.value ? d.value : 0; })
      .catch(function () { return null; });
  }
  function kun(siljish) {
    return new Date(Date.now() + 5 * 3600e3 - siljish * 864e5).toISOString().slice(0, 10);
  }
  function yozuv() {
    try { return localStorage.getItem('yozuv') === 'kir' ? 'kir' : 'lat'; } catch (x) { return 'lat'; }
  }

  var hisoblangan = false;
  try { hisoblangan = sessionStorage.getItem('tashrif') === '1'; } catch (x) {}
  var amal = hisoblangan ? '/get/' : '/hit/';
  if (!hisoblangan) {
    try { sessionStorage.setItem('tashrif', '1'); } catch (x) {}
    sorov('/hit/' + NOM + '/kun-' + kun(0));
  }

  Promise.all([sorov(amal + NOM + '/jami-tashrif'), sorov('/get/' + NOM + '/kun-' + kun(1))])
    .then(function (javob) {
      var jami = javob[0], kecha = javob[1];
      if (!jami) return;
      kecha = son(kecha || 0);
      jami = son(jami);
      if (document.documentElement.lang === 'en') {
        joy.textContent = 'Yesterday: ' + kecha + ' · Total: ' + jami;
      } else {
        var lat = 'Kechagi kirishlar: ' + kecha + ' · Jami: ' + jami;
        var kir = 'Кечаги киришлар: ' + kecha + ' · Жами: ' + jami;
        joy.setAttribute('data-lat', lat);
        joy.setAttribute('data-kir', kir);
        joy.textContent = yozuv() === 'kir' ? kir : lat;
      }
      joy.hidden = false;
    });
})();
