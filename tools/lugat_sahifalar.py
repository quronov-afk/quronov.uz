"""Adabiyotshunoslik lug'ati sahifalarini yasaydi.

Manba:   data/lugat.json (tools/lugatdan.py natijasi)
Natija:  site/lugat/index.html — alifbo bo'yicha, 4 ustunli, sahifalangan ro'yxat
         site/lugat/<slug>.html — har bir termin alohida sahifa
build.py ichidan chaqiriladi, alohida ham ishlaydi: python3 tools/lugat_sahifalar.py
"""

import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import SHAPKA, PODVAL, e, meta_teglar

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PAPKA = SITE / "lugat"

KITOB_LAT = ("Dilmurod Quronov, Zokirjon Mamajonov, Mashhura Sheraliyeva. Adabiyotshunoslik lugʻati / "
             "f.f.d. D. Quronovning umumiy tahriri ostida. – Toshkent: Akademnashr, 2010. – 400 b.")
KITOB_KIR = ("Дилмурод Қуронов, Зокиржон Мамажонов, Машҳура Шералиева. Адабиётшунослик луғати / "
             "ф.ф.д. Д.Қуроновнинг умумий таҳрири остида. – Тошкент: Akademnashr, 2010. – 400 б.")
KITOB_PDF = "kitoblar/adabiyotshunoslik-lugati-2010.pdf"

# oʻzbek lotin alifbosi tartibi
ALIFBO = ["A", "B", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
          "S", "T", "U", "V", "X", "Y", "Z", "Oʻ", "Gʻ", "Sh", "Ch"]
IKKI = ("Oʻ", "Gʻ", "Sh", "Ch")


def harf(soz):
    return soz[:2] if soz[:2] in IKKI else soz[:1].upper()


def saralash_kaliti(soz):
    kalit, i = [], 0
    while i < len(soz):
        bolak = soz[i:i + 2]
        if bolak.capitalize() in IKKI:
            kalit.append(ALIFBO.index(bolak.capitalize()) + 1); i += 2
            continue
        ch = soz[i].upper()
        kalit.append(ALIFBO.index(ch) + 1 if ch in ALIFBO else 0 if not ch.isalpha() else 99)
        i += 1
    return kalit


def qarang_slug(nom, slugs):
    """«адабий анъаналар» → «адабий анъана»: aniq, keyin oʻzak boʻyicha moslik."""
    nom = nom.lower().strip()
    if nom in slugs:
        return slugs[nom]
    for uzunlik in range(len(nom), 3, -1):
        oʻzak = nom[:uzunlik]
        mos = [k for k in slugs if k.startswith(oʻzak) or oʻzak.startswith(k)]
        if mos:
            return slugs[min(mos, key=len)]
    return None


def birinchi_abzac(termin, matn):
    """Lugʻat uslubida: «<b>Termin</b> (etimologiya) – izoh»."""
    if matn.startswith(("(", ",")):
        birikish = "" if matn.startswith(",") else " "
        return f"<strong>{e(termin)}</strong>{birikish}{e(matn)}"
    return f"<strong>{e(termin)}</strong> – {e(matn)}"


def bloklar_html(m, yozuv, slugs):
    termin = m["termin"] if yozuv == "lat" else m["termin_kir"].capitalize()
    qismlar = []
    for b in m["bloklar"]:
        if b["tur"] == "jadval":
            qatorlar = b["qatorlar_lat"] if yozuv == "lat" else b["qatorlar"]
            tr = "\n".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in q) + "</tr>" for q in qatorlar)
            qismlar.append(f'<div class="termin-jadval"><table>\n{tr}\n</table></div>')
            continue
        matn = b["matn_lat"] if yozuv == "lat" else b["matn"]
        if b.get("bosh"):
            html_matn = birinchi_abzac(termin, matn)
        else:
            html_matn = e(matn)
        if m.get("qarang") and b.get("bosh"):
            maqsad = qarang_slug(m["qarang"], slugs)
            if maqsad:
                qarang_matn = re.search(r"(qarang|қаранг)\s*:\s*(.+?)\.?$", html_matn)
                if qarang_matn:
                    html_matn = (html_matn[:qarang_matn.start(2)]
                                 + f'<a href="{maqsad}.html">{qarang_matn.group(2)}</a>'
                                 + html_matn[qarang_matn.end(2):])
        sinf = ' class="misra"' if b["tur"] == "misra" else ""
        qismlar.append(f"<p{sinf}>{html_matn}</p>")
    return "\n".join(qismlar)


def termin_sahifasi(m, oldingi, keyingi, slugs):
    tavsif = next((b["matn_lat"] for b in m["bloklar"] if b["tur"] == "abzac"), "")
    meta_html = meta_teglar(f"{m['termin']} — Adabiyotshunoslik lugʻati",
                            f"{m['termin']}: {tavsif}", f"lugat/{m['slug']}.html", tur="article")
    nav = []
    if oldingi:
        nav.append(f'<a href="{oldingi["slug"]}.html">← {e(oldingi["termin"])}</a>')
    else:
        nav.append("<span></span>")
    if keyingi:
        nav.append(f'<a href="{keyingi["slug"]}.html">{e(keyingi["termin"])} →</a>')
    return SHAPKA.format(title=f"{e(m['termin'])} — Adabiyotshunoslik lugʻati", yol="../", dq="", sq="",
                         meta=meta_html) + f"""
<div class="wrap maqola termin-sahifa">
  <div class="maqola-top">
    <a class="ortga" href="index.html#{e(harf(m['termin']))}">← Adabiyotshunoslik lugʻati</a>
    <div class="yozuv-tanlov" role="group" aria-label="Yozuv turi">
      <button type="button" data-yozuv="lat" class="tanlangan">Lotin</button>
      <span>|</span>
      <button type="button" data-yozuv="kir">Kirill</button>
    </div>
  </div>

  <h1 data-lat="{e(m['termin'])}" data-kir="{e(m['termin_kir'].capitalize())}">{e(m['termin'])}</h1>

  <div class="matn" id="matn-lat">
{bloklar_html(m, "lat", slugs)}
  </div>
  <div class="matn" id="matn-kir" hidden>
{bloklar_html(m, "kir", slugs)}
  </div>

  <p class="termin-manba" data-lat="{e(KITOB_LAT)}" data-kir="{e(KITOB_KIR)}"><strong>Manba:</strong> {e(KITOB_LAT)}</p>
  <p class="termin-manba-havola"><a class="yuklab" href="../{KITOB_PDF}">Lugʻatni PDF shaklida oʻqish</a></p>

  <nav class="termin-nav" aria-label="Qoʻshni terminlar">{"".join(nav)}</nav>
</div>

<script>
(function () {{
  var tugma = document.querySelectorAll('.yozuv-tanlov button');
  var manba = document.querySelector('.termin-manba');
  function qoy(y) {{
    document.getElementById('matn-lat').hidden = (y === 'kir');
    document.getElementById('matn-kir').hidden = (y !== 'kir');
    var h1 = document.querySelector('h1');
    h1.textContent = h1.getAttribute(y === 'kir' ? 'data-kir' : 'data-lat');
    manba.innerHTML = '<strong>' + (y === 'kir' ? 'Манба:' : 'Manba:') + '</strong> ' +
      manba.getAttribute(y === 'kir' ? 'data-kir' : 'data-lat');
    tugma.forEach(function (t) {{ t.classList.toggle('tanlangan', t.dataset.yozuv === y); }});
    try {{ localStorage.setItem('yozuv', y); }} catch (x) {{}}
  }}
  tugma.forEach(function (t) {{ t.addEventListener('click', function () {{ qoy(t.dataset.yozuv); }}); }});
  try {{ if (localStorage.getItem('yozuv') === 'kir') qoy('kir'); }} catch (x) {{}}
}})();
</script>
""" + PODVAL


def royxat_sahifasi(terminlar):
    bor_harflar = {harf(m["termin"]) for m in terminlar}
    tugmalar = ['    <button type="button" class="faol" data-harf="">Barchasi</button>']
    tugmalar += [f'    <button type="button" data-harf="{e(h)}">{e(h)}</button>' for h in ALIFBO if h in bor_harflar]
    elementlar = []
    for m in terminlar:
        belgi = (f' <span class="qarang-belgi">→ {e(m["qarang_lat"])}</span>' if m.get("qarang_lat") else "")
        elementlar.append(f'      <li data-harf="{e(harf(m["termin"]))}"><a href="{m["slug"]}.html">{e(m["termin"])}</a>{belgi}</li>')
    meta_html = meta_teglar("Adabiyotshunoslik lugʻati — Quronov.uz",
                            f"Adabiyotshunoslikka oid {len(terminlar)} ta termin izohi: D. Quronov, Z. Mamajonov, "
                            "M. Sheraliyeva. Adabiyotshunoslik lugʻati (Akademnashr, 2010).", "lugat/index.html")
    return SHAPKA.format(title="Adabiyotshunoslik lugʻati — Quronov.uz", yol="../", dq="", sq="",
                         meta=meta_html) + f"""
<div class="wrap">
  <section class="intro">
    <h1>Adabiyotshunoslik lugʻati</h1>
    <p>Adabiyotshunoslikka oid {len(terminlar)} ta termin izohi. {e(KITOB_LAT)}</p>
  </section>

  <div class="alifbo" role="toolbar" aria-label="Alifbo">
{chr(10).join(tugmalar)}
  </div>
  <input type="search" id="lugat-qidiruv" class="search lugat-qidiruv" placeholder="Terminni qidirish" aria-label="Terminni qidirish">
  <p class="lugat-holat" id="lugat-holat"></p>
  <ul class="terminlar" id="terminlar">
{chr(10).join(elementlar)}
  </ul>
  <nav class="sahifalar" id="lugat-sahifalar" aria-label="Sahifalar"></nav>
</div>
<script src="../lugat.js"></script>
""" + PODVAL


def yasash():
    fayl = ROOT / "data" / "lugat.json"
    if not fayl.exists():
        return 0
    from kitobdan import lotinga
    terminlar = json.loads(fayl.read_text(encoding="utf-8"))
    terminlar.sort(key=lambda m: saralash_kaliti(m["termin"]))
    slugs = {m["termin_kir"].lower(): m["slug"] for m in terminlar}
    for m in terminlar:
        if m.get("qarang"):
            m["qarang_lat"] = lotinga(m["qarang"])
    PAPKA.mkdir(exist_ok=True)
    for eski in PAPKA.glob("*.html"):
        eski.unlink()
    for i, m in enumerate(terminlar):
        oldingi = terminlar[i - 1] if i else None
        keyingi = terminlar[i + 1] if i + 1 < len(terminlar) else None
        (PAPKA / f"{m['slug']}.html").write_text(termin_sahifasi(m, oldingi, keyingi, slugs), encoding="utf-8")
    (PAPKA / "index.html").write_text(royxat_sahifasi(terminlar), encoding="utf-8")
    return len(terminlar)


if __name__ == "__main__":
    print(f"lugʻat: {yasash()} ta termin sahifasi")
