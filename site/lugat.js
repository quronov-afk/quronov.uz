/* Adabiyotshunoslik lugʻati: alifbo boʻyicha tanlash, qidiruv va sahifalash (cheksiz aylantirish emas).
   Terminlar roʻyxati sahifaga HTML sifatida yozilgan; skript faqat koʻrinishni boshqaradi. */
(function () {
  var SAHIFADA = 60;                                   // 4 ustunda 15 qatordan
  var elementlar = Array.prototype.slice.call(document.querySelectorAll('#terminlar li'));
  var tugmalar = Array.prototype.slice.call(document.querySelectorAll('.alifbo button'));
  var qidiruv = document.getElementById('lugat-qidiruv');
  var holat = document.getElementById('lugat-holat');
  var sahifalar = document.getElementById('lugat-sahifalar');
  var harf = '', joriy = 1;

  function norm(s) { return String(s).toLowerCase().replace(/[ʻʼ‘’'`]/g, ''); }

  // boʻsh harflarni oʻchirib qoʻyish
  tugmalar.forEach(function (t) {
    if (t.dataset.harf && !elementlar.some(function (li) { return li.dataset.harf === t.dataset.harf; })) {
      t.disabled = true;
    }
  });

  function mos() {
    var soz = qidiruv ? norm(qidiruv.value.trim()) : '';
    return elementlar.filter(function (li) {
      return (!harf || li.dataset.harf === harf) && (!soz || norm(li.textContent).indexOf(soz) > -1);
    });
  }

  function chiz() {
    var royxat = mos();
    var jami = Math.max(1, Math.ceil(royxat.length / SAHIFADA));
    if (joriy > jami) joriy = jami;
    var boshi = (joriy - 1) * SAHIFADA;
    elementlar.forEach(function (li) { li.hidden = true; });
    royxat.slice(boshi, boshi + SAHIFADA).forEach(function (li) { li.hidden = false; });
    holat.textContent = royxat.length + ' ta termin' + (jami > 1 ? ' · ' + joriy + '/' + jami + '-sahifa' : '');

    sahifalar.innerHTML = '';
    if (jami < 2) return;
    function tugma(belgi, n, oʻchiq, faol) {
      var b = document.createElement('button');
      b.type = 'button'; b.textContent = belgi;
      if (faol) b.className = 'faol';
      if (oʻchiq) b.disabled = true;
      else b.addEventListener('click', function () {
        joriy = n; chiz();
        document.querySelector('.alifbo').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      sahifalar.appendChild(b);
    }
    tugma('←', joriy - 1, joriy === 1);
    for (var i = 1; i <= jami; i++) tugma(String(i), i, false, i === joriy);
    tugma('→', joriy + 1, joriy === jami);
  }

  tugmalar.forEach(function (t) {
    t.addEventListener('click', function () {
      harf = t.dataset.harf || '';
      joriy = 1;
      tugmalar.forEach(function (x) { x.classList.toggle('faol', x === t); });
      try { history.replaceState(null, '', harf ? '#' + encodeURIComponent(harf) : location.pathname); } catch (x) {}
      chiz();
    });
  });
  if (qidiruv) qidiruv.addEventListener('input', function () { joriy = 1; chiz(); });

  var boshlangich = decodeURIComponent(location.hash.slice(1));
  var tanlangan = tugmalar.filter(function (t) { return t.dataset.harf === boshlangich; })[0];
  if (tanlangan && !tanlangan.disabled) tanlangan.click(); else chiz();
})();
