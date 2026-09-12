(function () {
  var SAHIFADA = 10;
  var teglar = document.querySelectorAll('.filter-bar .tag');
  var yozuvlar = Array.prototype.slice.call(document.querySelectorAll('#royxat .entry'));
  var qidiruv = document.getElementById('qidiruv');
  var sahifalar = document.getElementById('sahifalar');
  var faolTeg = '';
  var joriy = 1;

  function mos() {
    var matn = qidiruv ? qidiruv.value.trim().toLowerCase() : '';
    return yozuvlar.filter(function (y) {
      var tegMos = !faolTeg || (' ' + y.dataset.teg + ' ').indexOf(' ' + faolTeg + ' ') > -1;
      var matnMos = !matn || y.textContent.toLowerCase().indexOf(matn) > -1;
      return tegMos && matnMos;
    });
  }

  function chizish() {
    var royxat = mos();
    var jami = Math.max(1, Math.ceil(royxat.length / SAHIFADA));
    if (joriy > jami) joriy = jami;
    var boshi = (joriy - 1) * SAHIFADA;

    yozuvlar.forEach(function (y) { y.hidden = true; });
    royxat.slice(boshi, boshi + SAHIFADA).forEach(function (y) { y.hidden = false; });

    if (!sahifalar) return;
    sahifalar.innerHTML = '';
    if (royxat.length <= SAHIFADA) return;

    var tugma = function (belgi, raqam, holat) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = belgi;
      if (holat === 'faol') b.className = 'faol';
      if (holat === 'oʻchiq') b.disabled = true;
      else b.addEventListener('click', function () {
        joriy = raqam;
        chizish();
        document.querySelector('.filter-bar').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      sahifalar.appendChild(b);
    };

    tugma('←', joriy - 1, joriy === 1 ? 'oʻchiq' : '');
    for (var i = 1; i <= jami; i++) {
      if (jami > 9 && i > 2 && i < jami - 1 && Math.abs(i - joriy) > 1) {
        if (sahifalar.lastChild && sahifalar.lastChild.textContent !== '…') {
          var uch = document.createElement('span');
          uch.textContent = '…';
          sahifalar.appendChild(uch);
        }
        continue;
      }
      tugma(String(i), i, i === joriy ? 'faol' : '');
    }
    tugma('→', joriy + 1, joriy === jami ? 'oʻchiq' : '');
  }

  teglar.forEach(function (t) {
    t.addEventListener('click', function (ev) {
      ev.preventDefault();
      faolTeg = t.dataset.suzgi || '';
      joriy = 1;
      teglar.forEach(function (x) { x.classList.toggle('active', x === t); });
      chizish();
    });
  });

  if (qidiruv) {
    qidiruv.addEventListener('input', function () { joriy = 1; chizish(); });
  }

  chizish();
})();
