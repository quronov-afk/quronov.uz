/* Butun matn boʻyicha qidiruv. Indeks (qidiruv.json) faqat shu sahifada yuklanadi.
   Soʻrov kirill yozuvida kiritilsa, lotinga oʻgirib qidiriladi. */
(function () {
  var SAHIFADA = 10;
  var forma = document.getElementById('qidiruv-forma');
  var kirish = document.getElementById('qidiruv-soz');
  var holat = document.getElementById('qidiruv-holat');
  var joy = document.getElementById('qidiruv-natija');
  var sahifalar = document.getElementById('qidiruv-sahifalar');
  var indeks = null, natijalar = [], sozlar = [], joriy = 1;

  var KIR = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'j','з':'z','и':'i','й':'y',
    'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'x',
    'ц':'s','ч':'ch','ш':'sh','щ':'sh','ъ':"'",'ь':'','ы':'i','э':'e','ю':'yu','я':'ya','ў':"o'",
    'қ':'q','ғ':"g'",'ҳ':'h'};

  function norm(s) {
    return String(s).toLowerCase()
      .replace(/[ʻʼ‘’`´]/g, "'")
      .replace(/[а-яёўқғҳ]/g, function (h) { return KIR[h] || h; });
  }
  function xavfsiz(s) {
    return String(s).replace(/[&<>"]/g, function (h) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[h]; });
  }
  function regexp(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function yukla() {
    if (indeks) return Promise.resolve(indeks);
    holat.textContent = 'Maqolalar yuklanmoqda…';
    return fetch('qidiruv.json').then(function (r) { return r.json(); }).then(function (d) {
      indeks = d.map(function (m) { m._t = norm(m.t); m._m = norm(m.m); return m; });
      return indeks;
    });
  }

  function parcha(m) {
    var matn = m.m, past = m._m, eng = -1, uzun = 0;
    sozlar.forEach(function (w) { var i = past.indexOf(w); if (i > -1 && (eng < 0 || i < eng)) { eng = i; uzun = w.length; } });
    if (eng < 0) return xavfsiz(matn.slice(0, 220)) + '…';
    var bosh = Math.max(0, eng - 90), oxir = Math.min(matn.length, eng + uzun + 130);
    var bolak = (bosh ? '…' : '') + matn.slice(bosh, oxir) + (oxir < matn.length ? '…' : '');
    var html = xavfsiz(bolak);
    sozlar.forEach(function (w) {
      // asl matndagi apostrof shakllari farq qilishi mumkin — har harf orasiga ixtiyoriy belgi
      var naqsh = w.split('').map(function (h) { return h === "'" ? "[ʻʼ‘’'`]" : regexp(h); }).join('');
      html = html.replace(new RegExp('(' + naqsh + ')', 'gi'), '<mark>$1</mark>');
    });
    return html;
  }

  function chiz() {
    joy.innerHTML = '';
    sahifalar.innerHTML = '';
    if (!sozlar.length) { holat.textContent = ''; return; }
    holat.textContent = natijalar.length
      ? natijalar.length + ' ta maqola topildi'
      : 'Hech narsa topilmadi. Soʻzning qisqaroq shaklini kiritib koʻring.';
    var boshi = (joriy - 1) * SAHIFADA;
    natijalar.slice(boshi, boshi + SAHIFADA).forEach(function (m) {
      var el = document.createElement('article');
      el.className = 'natija';
      el.innerHTML = '<div class="entry-meta"><span class="author-tag">' + xavfsiz(m.a) + '</span>' +
        '<span class="entry-date">' + xavfsiz(m.j + (m.y ? ' · ' + m.y : '')) + '</span></div>' +
        '<h3><a href="maqola/' + encodeURIComponent(m.s) + '.html">' + xavfsiz(m.t) + '</a></h3>' +
        '<p>' + parcha(m) + '</p>';
      joy.appendChild(el);
    });
    var jami = Math.ceil(natijalar.length / SAHIFADA);
    if (jami < 2) return;
    for (var i = 1; i <= jami; i++) {
      (function (n) {
        var t = document.createElement('button');
        t.type = 'button'; t.textContent = n;
        if (n === joriy) t.className = 'faol';
        t.addEventListener('click', function () { joriy = n; chiz(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
        sahifalar.appendChild(t);
      })(i);
    }
  }

  function qidir(soz) {
    sozlar = norm(soz).split(/\s+/).filter(function (w) { return w.length > 1; });
    joriy = 1;
    if (!sozlar.length) { natijalar = []; chiz(); return; }
    yukla().then(function (d) {
      natijalar = d.map(function (m) {
        var ball = 0;
        for (var k = 0; k < sozlar.length; k++) {
          var w = sozlar[k], sarlavhada = m._t.indexOf(w) > -1, soni = m._m.split(w).length - 1;
          if (!sarlavhada && !soni) return null;
          ball += (sarlavhada ? 50 : 0) + Math.min(soni, 30);
        }
        return { m: m, ball: ball };
      }).filter(Boolean).sort(function (a, b) { return b.ball - a.ball; }).map(function (x) { return x.m; });
      chiz();
    }).catch(function () { holat.textContent = 'Qidiruv indeksini yuklab boʻlmadi.'; });
  }

  forma.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var soz = kirish.value.trim();
    history.replaceState(null, '', soz ? '?q=' + encodeURIComponent(soz) : location.pathname);
    qidir(soz);
  });

  var boshlangich = new URLSearchParams(location.search).get('q');
  if (boshlangich) { kirish.value = boshlangich; qidir(boshlangich); }
  kirish.focus();
})();
