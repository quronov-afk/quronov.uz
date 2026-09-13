"""Saytning inglizcha versiyasi: site/en/ sahifalari va barcha sahifalardagi til tugmasi.

Ishlatish:  build.py ichidan chaqiriladi (yasash(), til_belgilari()).
Maʼlumot:   data/en/interfeys.json — interfeys matnlari, data/en/atamalar.json — atamalar,
            data/en/kitoblar.json, data/en/galereya.json — kitob va galereya tarjimalari.
"""

import json, os, re
from collections import defaultdict
from pathlib import Path

from build import (SITE, SAYT, PODVAL, MUALLIFLAR, e, meta_teglar, muallif_ismi, manba_lotin,
                   qisqacha, guruhlar, matbuot_ruknlari, mavzu_slug, RUKNLAR)

ROOT = Path(__file__).resolve().parent.parent
EN = SITE / "en"
DATA_EN = ROOT / "data" / "en"


def _json(nom):
    return json.loads((DATA_EN / nom).read_text(encoding="utf-8"))


UI = _json("interfeys.json")
AT = _json("atamalar.json")

# yasaladigan inglizcha sahifalar (menyu shu roʻyxatga qarab tuziladi)
SAHIFALAR = {"index.html", "dilmurod.html", "sadullo.html", "kitoblar.html", "galereya.html",
             "aloqa.html", "qidiruv.html"}

ASL_TIL = {"Maqola (ingliz tilida)": "en", "Maqola (turk tilida)": "tr", "Maqola (rus tilida)": "ru"}

# tarjimasi topilmagan matnlar — yigʻish oxirida koʻrsatiladi
TARJIMASIZ = []

# maqola tarjimalari: data/en/maqolalar/<slug>.json
TR = {f.stem: json.loads(f.read_text(encoding="utf-8"))
      for f in sorted((DATA_EN / "maqolalar").glob("*.json"))}


def asl_xesh(m):
    """Oʻzbekcha asl matn izi: oʻzgarsa, tarjima eskirgan deb ogohlantiriladi."""
    import hashlib
    return hashlib.sha1("\n".join(m["matn"]).encode("utf-8")).hexdigest()[:12]

QIDIRUV_IKONA = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                 '<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>')


def tarjima(lugat, kalit, zaxira=None):
    if kalit in lugat:
        return lugat[kalit]
    TARJIMASIZ.append(kalit)
    return kalit if zaxira is None else zaxira


def en_ism(s):
    """Oʻzbekcha ismning inglizcha yozilishi: Saʼdullo → Sadullo, Choʻlpon → Cholpon."""
    return s.replace("Sa'dullo", "Sadullo").replace("ʻ", "").replace("ʼ", "").replace("'", "")


def uz_imlo(s):
    """Maʼlumotdagi oddiy apostrofni oʻzbek lotin belgisiga almashtiradi: O'qituvchi → Oʻqituvchi."""
    return re.sub(r"(?<=[OoGg])'", "ʻ", s or "").replace("'", "ʼ")


def shapka(sarlavha, meta, yol, faol=""):
    """Inglizcha sahifa boshi. `yol` — en/ ildiziga nisbiy yoʻl ("" yoki "../")."""
    bandlar = []
    for b in UI["menyu"]:
        if b["sahifa"] not in SAHIFALAR:
            continue
        cls = ' class="active"' if b["sahifa"] == faol else ""
        bandlar.append(f'      <a href="{yol}{b["sahifa"]}"{cls}>{e(b["nom"])}</a>')
    meta = meta.replace('content="uz_UZ"', 'content="en_US"')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{sarlavha}</title>
{meta}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=PT+Serif:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{yol}../style.css">
</head>
<body>

<header class="site-header">
  <div class="masthead">
    <div class="wordmark"><a href="{yol}index.html">Quronov<span>.uz</span></a></div>
    <div class="tagline">{e(UI["tagline"])}</div>
  </div>
  <div class="header-inner">
    <nav class="nav">
{chr(10).join(bandlar)}
    </nav>
  </div>
</header>
"""


def podval():
    return PODVAL.replace("© 2026 Quronov.uz", e(UI["podval"]))


def oddiy_sahifa(nom, sarlavha, tavsif, ichki, oxiri="", rasm="img/ulashish.jpg"):
    """en/<nom> sahifasi: shapka + ichki qism + podval."""
    meta = meta_teglar(f"{sarlavha} — Quronov.uz", tavsif, f"en/{nom}", rasm)
    return shapka(f"{e(sarlavha)} — Quronov.uz", meta, "", nom) + ichki + oxiri + podval()


# ---------------------------------------------------------------- roʻyxatlar

def meta_qatori(m):
    meta = [AT["janr"].get(m["janr"], m["janr"])]
    if m.get("yil"):
        meta.append(str(m["yil"]))
    manba = manba_lotin(m.get("asl_manba"))
    if manba:
        meta.append(manba)
    if m.get("kitob"):
        meta.append(UI["royxat"]["toplamdan"].format(kitob=uz_imlo(m["kitob"])))
    return meta


def yozuv_html(m, yol=""):
    """Roʻyxatdagi bitta yozuv: asl sarlavha, asl til belgisi, matn asl sahifada ochiladi."""
    rang = MUALLIFLAR[m.get("muallif", "Dilmurod Quronov")][1]
    t = TR.get(m["slug"])
    if t:
        til, belgi, sarlavha = "en", UI["tillar"]["tarjima"], t["title"]
        havola = f"{yol}maqola/{m['slug']}.html"
        parcha = f"\n        <p>{e(qisqacha({'matn': t['paragraphs']}))}</p>"
    else:
        til = ASL_TIL.get(m["janr"], "uz")
        belgi, sarlavha = UI["tillar"][til], m["title"]
        havola = f"{yol}../maqola/{m['slug']}.html"
        parcha = f"\n        <p>{e(qisqacha(m))}</p>" if til == "en" else ""
    return f"""      <article class="entry {rang}" data-teg="{e(' '.join(guruhlar(m)))}">
        <div class="entry-meta">
          <span class="author-tag">{e(en_ism(muallif_ismi(m)[0]))}</span>
          <span class="entry-date">{e(' · '.join(meta_qatori(m)))}</span>
          <span class="til-belgi">{e(belgi)}</span>
          <span class="oqildi" data-kalit="{e(m['slug'])}"></span>
        </div>
        <h3><a href="{havola}" lang="{til}">{e(sarlavha)}</a></h3>{parcha}
      </article>"""


def matbuot_html(muallif):
    fayl = ROOT / "data" / "matbuot.json"
    if not fayl.exists():
        return ""
    yozuvlar = [m for m in json.loads(fayl.read_text(encoding="utf-8")) if m["muallif"] == muallif]
    if not yozuvlar:
        return ""
    yozuvlar.sort(key=lambda m: m["sana"], reverse=True)
    qismlar = [f'      <p class="section-label">{e(UI["royxat"]["matbuotda"])}</p>']
    for m in yozuvlar:
        sana = ""
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", m["sana"] or ""):
            y, o, k = m["sana"].split("-")
            sana = f"{int(k)} {UI['oylar'][int(o) - 1]} {y}"
        qismlar.append(f"""      <article class="matbuot-entry" data-teg="{e(m.get('rukn', 'Maqolalar'))}">
        <div class="entry-meta">
          <span class="nashr">{e(m['nashr'])}</span>
          <span class="entry-date">{e(sana)}</span>
          <span class="til-belgi">{e(UI["tillar"]["uz"])}</span>
        </div>
        <h3><a href="{e(m['url'])}" target="_blank" rel="noopener" lang="uz">{e(m['sarlavha'])}</a></h3>
        <p lang="uz">{e(m['parcha'])}</p>
      </article>""")
    return "\n".join(qismlar)


def yon_ustun(yol="", qoshimcha=""):
    y = UI["yon_ustun"]
    return f"""    <aside class="sidebar">
      <section>
        <a class="lugat-tugma" href="{yol}../lugat/index.html" hreflang="uz">
          <span class="lugat-tugma-belgi">Aa</span>
          <span><strong>{e(y["lugat"])}</strong><small>{e(y["lugat_izoh"])}</small></span>
        </a>
      </section>

      <section>
        <form action="{yol}qidiruv.html" role="search" class="qidiruv-qutisi">
          <input type="search" name="q" class="search" placeholder="{e(y["qidiruv"])}" aria-label="{e(UI["qidiruv"]["sarlavha"])}">
          <button type="submit" class="qidiruv-ikona" aria-label="{e(UI["qidiruv"]["tugma"])}">{QIDIRUV_IKONA}</button>
        </form>
      </section>

      <section>
        <h4>{e(y["mualliflar"])}</h4>
        <a class="author-link" href="{yol}dilmurod.html"><span class="dot dq"></span>Dilmurod Quronov</a>
        <a class="author-link" href="{yol}sadullo.html"><span class="dot sq"></span>{e(UI["olimlar"]["Sa'dullo Quronov"]["ism"])}</a>
      </section>
{qoshimcha}    </aside>"""


# ---------------------------------------------------------------- sahifalar

def bosh_sahifa(songgilar, mavzular):
    b = UI["bosh_sahifa"]
    meta = meta_teglar(b["sarlavha"], b["tavsif"], "en/")
    tugmalar = "\n".join(
        f'          <a class="tag" href="mavzu/{slug}.html">'
        f'{e(tarjima(AT["mavzu"], nom))}<span class="soni">{soni}</span></a>'
        for nom, soni, slug in mavzular[:18])
    mavzu_blok = f"""
      <section>
        <h4>{e(UI["yon_ustun"]["mavzular"])}</h4>
        <div class="tags">
{tugmalar}
        </div>
      </section>
"""
    return shapka(e(b["sarlavha"]), meta, "", "index.html") + f"""
<div class="wrap">

  <section class="intro">
    <h1>{e(b["h1"])}</h1>
    <p>{e(b["kirish"])}</p>
    <p class="en-izoh">{e(b["izoh"])}</p>
  </section>

  <div class="layout">

    <main>
      <p class="section-label">{e(b["songgi"])}</p>
{chr(10).join(yozuv_html(m) for m in songgilar)}
    </main>

{yon_ustun("", mavzu_blok)}

  </div>
</div>

<script src="../oqilgan.js" defer></script>
""" + podval()


def olim_sahifasi(muallif, maqolalar):
    sahifa, rang = MUALLIFLAR[muallif]
    o = UI["olimlar"][muallif]
    uniki = [m for m in maqolalar if m.get("muallif", "Dilmurod Quronov") == muallif]
    bor = {g for m in uniki for g in guruhlar(m)} | matbuot_ruknlari(muallif)
    panel = [f'      <a class="tag active" href="#" data-suzgi="">{e(AT["rukn"]["Barchasi"])}</a>']
    panel += [f'      <a class="tag" href="#" data-suzgi="{e(g)}">{e(tarjima(AT["rukn"], g))}</a>'
              for g in RUKNLAR if g in bor]
    if o["biografiya"] in TR:
        bio_havola = f'<a href="maqola/{o["biografiya"]}.html">{e(UI["olim_sahifasi"]["biografiya_en"])}</a>'
    else:
        bio_havola = (f'<a href="../maqola/{o["biografiya"]}.html" hreflang="uz">'
                      f'{e(UI["olim_sahifasi"]["biografiya"])}</a>')
    ichki = f"""
<div class="wrap">

  <div class="author-head">
    <img class="avatar" src="../{o["rasm"]}" alt="{e(o["ism"])}" width="84" height="84">
    <div>
      <h1>{e(o["ism"])}</h1>
      <p class="role">{e(o["rol"])}</p>
      <p class="biografiya-havola">{bio_havola}</p>
    </div>
  </div>

  <div class="filter-bar">
{chr(10).join(panel)}
  </div>

  <div class="layout">
    <main>
      <p class="en-izoh">{e(UI["olim_sahifasi"]["izoh"])}</p>
      <div id="royxat">
{chr(10).join(yozuv_html(m) for m in uniki)}
      </div>
      <nav class="sahifalar" id="sahifalar" aria-label="{e(UI["royxat"]["sahifalar"])}"></nav>
      <section class="matbuot">
{matbuot_html(muallif)}
      </section>
    </main>

{yon_ustun()}
  </div>
</div>
"""
    oxiri = '\n<script src="../sayt.js"></script>\n<script src="../oqilgan.js" defer></script>\n'
    return oddiy_sahifa(sahifa, o["ism"], o["tavsif"], ichki, oxiri, o["rasm"])


def mavzu_sahifalari(maqolalar):
    """en/mavzu/<slug>.html — mavzu boʻyicha yozuvlar roʻyxati."""
    guruh = defaultdict(list)
    for m in maqolalar:
        for t in m.get("teglar", []):
            guruh[t].append(m)
    papka = EN / "mavzu"
    papka.mkdir(parents=True, exist_ok=True)
    for eski in papka.glob("*.html"):
        eski.unlink()
    u = UI["mavzu"]
    for nom, uniki in guruh.items():
        slug = mavzu_slug(nom)
        nom_en = tarjima(AT["mavzu"], nom)
        soni = u["soni_1"] if len(uniki) == 1 else u["soni"].format(n=len(uniki))
        meta = meta_teglar(f"{nom_en} — Quronov.uz", u["tavsif"].format(n=len(uniki), nom=nom_en),
                           f"en/mavzu/{slug}.html")
        sahifa = shapka(f"{e(nom_en)} — Quronov.uz", meta, "../") + f"""
<div class="wrap">
  <section class="intro">
    <p class="section-label">{e(u["yorliq"])}</p>
    <h1>{e(nom_en)}</h1>
    <p>{e(soni)}</p>
  </section>
  <main>
    <div id="royxat">
{chr(10).join(yozuv_html(m, "../") for m in uniki)}
    </div>
    <nav class="sahifalar" id="sahifalar" aria-label="{e(UI["royxat"]["sahifalar"])}"></nav>
  </main>
</div>
<script src="../../sayt.js"></script>
<script src="../../oqilgan.js" defer></script>
""" + podval()
        (papka / f"{slug}.html").write_text(sahifa, encoding="utf-8")
    return len(guruh)


def kitoblar_sahifasi():
    import kitoblar as K
    T = _json("kitoblar.json")
    k_ui = UI["kitoblar"]

    kitoblar = []
    for k in json.loads((ROOT / "data" / "books.json").read_text(encoding="utf-8")):
        if not (SITE / "kitoblar" / f"{k['slug']}.pdf").exists():
            continue
        k["fayl"] = f"{k['slug']}.pdf"
        k["muqova"] = f"{k['slug']}.jpg" if (SITE / "img" / "kitoblar" / f"{k['slug']}.jpg").exists() else None
        kitoblar.append(k)
    kitoblar.sort(key=lambda k: -(k["year"] or 0))

    def karta(k):
        t = tarjima(T["kitoblar"], k["slug"], {"title": k["title"], "note": k["note"]})
        meta = [tarjima(T["turlar"], k["kind"].replace("ʻ", "'"))]
        if k.get("year"):
            meta.append(str(k["year"]))
        if k.get("publisher"):
            meta.append(uz_imlo(k["publisher"]))
        meta.append(k_ui["bet"].format(n=k["pages"]))
        havola = f"../kitoblar/{e(k['fayl'])}"
        rasm = (f'<img src="../img/kitoblar/{e(k["muqova"])}" alt="" loading="lazy">'
                if k["muqova"] else '<div class="muqova-yoq"></div>')
        return f"""      <article class="kitob">
        <a class="muqova" href="{havola}">{rasm}</a>
        <div class="kitob-matn">
          <h3><a href="{havola}">{e(t["title"])}</a></h3>
          <p class="kitob-asl" lang="uz">{e(uz_imlo(k["title"]))}</p>
          <p class="kitob-meta">{e(' · '.join(meta))}</p>
          <p>{e(t["note"])}</p>
          <a class="yuklab" href="{havola}">{e(k_ui["yuklab"].format(hajm=K.hajm(k["fayl"])))}</a>
        </div>
      </article>"""

    def diss_karta(d):
        t = tarjima(T["dissertatsiyalar"], d["title"], {"title": d["title"], "izoh": d["izoh"]})
        muqova_nomi = K.diss_muqova(d)
        rasm = (f'<img src="../img/kitoblar/{e(muqova_nomi)}" alt="" loading="lazy">'
                if muqova_nomi else '<div class="muqova-yoq"></div>')
        havola = f"../kitoblar/{e(d['fayl'])}" if d.get("fayl") else None
        muqova_blok = (f'<a class="muqova" href="{havola}">{rasm}</a>' if havola
                       else f'<div class="muqova">{rasm}</div>')
        sarlavha = f'<a href="{havola}">{e(t["title"])}</a>' if havola else e(t["title"])
        havolalar = []
        if d.get("fayl"):
            havolalar.append(f'<a class="yuklab" href="../kitoblar/{e(d["fayl"])}">'
                             f'{e(k_ui["diss_pdf"].format(hajm=K.hajm(d["fayl"])))}</a>')
        if d.get("avtoreferat"):
            havolalar.append(f'<a class="yuklab" href="../kitoblar/{e(d["avtoreferat"])}">'
                             f'{e(k_ui["avtoreferat"].format(hajm=K.hajm(d["avtoreferat"])))}</a>')
        izoh = t["izoh"] + (f' · {k_ui["kirill"]}' if d.get("kirill") else "")
        pastki = (" ".join(havolalar) if havolalar
                  else f'<span class="kutilmoqda-belgi">{e(k_ui["tez_orada"])}</span>')
        joy = tarjima(T["joylar"], d["joy"])
        return f"""      <article class="kitob diss">
        {muqova_blok}
        <div class="kitob-matn">
          <h3>{sarlavha}</h3>
          <p class="kitob-asl" lang="uz">{e(d["title"])}</p>
          <p class="kitob-meta">{e(izoh)} · {e(joy)}, {d['yil']}</p>
          <p class="diss-havolalar">{pastki}</p>
        </div>
      </article>"""

    tugmalar, bolimlar = [], []
    olimlar = (("Dilmurod Quronov", "Dilmurod Quronov", "dq"), ("Sa'dullo Quronov", "Saʼdullo Quronov", "sq"))
    for i, (olim, diss_kalit, belgi) in enumerate(olimlar):
        faol = " tanlangan" if i == 0 else ""
        ism = UI["olimlar"][olim]["ism"]
        tugmalar.append(f'    <button type="button" class="kitob-tugma{faol}" '
                        f'data-bolim="{belgi}">{e(k_ui["tugma"].format(ism=ism))}</button>')
        uniki = [k for k in kitoblar if k["muallif"] == olim]
        qism = [f'    <div class="kitoblar">\n{chr(10).join(karta(k) for k in uniki)}\n    </div>' if uniki
                else f'    <p class="kutilmoqda">{e(k_ui["kutilmoqda"])}</p>']
        diss = K.DISSERTATSIYALAR.get(diss_kalit, [])
        if diss:
            qism.append(f'    <h3 class="kitob-bolim kichik">{e(k_ui["dissertatsiyalar"])}</h3>')
            qism.append(f'    <div class="kitoblar">\n{chr(10).join(diss_karta(d) for d in diss)}\n    </div>')
        yashirin = "" if i == 0 else " hidden"
        bolimlar.append(f'  <section id="bolim-{belgi}" class="kitob-bolimi"{yashirin}>\n'
                        + "\n".join(qism) + "\n  </section>")

    ichki = f"""
<div class="wrap">
  <section class="intro">
    <h1>{e(k_ui["sarlavha"])}</h1>
    <p>{e(k_ui["kirish"])}</p>
  </section>

  <div class="kitob-tanlov" role="tablist">
{chr(10).join(tugmalar)}
  </div>

{(chr(10) * 2).join(bolimlar)}
</div>
"""
    oxiri = """
<script>
(function () {
  var tugma = document.querySelectorAll('.kitob-tugma');
  tugma.forEach(function (t) {
    t.addEventListener('click', function () {
      tugma.forEach(function (x) {
        x.classList.toggle('tanlangan', x === t);
        document.getElementById('bolim-' + x.dataset.bolim).hidden = (x !== t);
      });
    });
  });
})();
</script>
"""
    return oddiy_sahifa("kitoblar.html", k_ui["sarlavha"], k_ui["tavsif"], ichki, oxiri)


def galereya_sahifasi():
    T = _json("galereya.json")
    g = UI["galereya"]
    videolar = json.loads((ROOT / "data" / "videolar.json").read_text(encoding="utf-8"))
    rasmlar = json.loads((ROOT / "data" / "rasmlar.json").read_text(encoding="utf-8"))

    kartalar = []
    for v in videolar:
        t = tarjima(T["videolar"], v["id"], {"nom": v["nom"], "manba": v["manba"]})
        kartalar.append(f"""      <figure class="video">
        <div class="video-ramka">
          <iframe src="https://www.youtube-nocookie.com/embed/{e(v['id'])}" title="{e(t['nom'])}"
                  loading="lazy" allowfullscreen></iframe>
        </div>
        <figcaption>{e(t['nom'])}<span>{e(t['manba'])}</span></figcaption>
      </figure>""")

    fotolar = []
    for r in rasmlar:
        nom = tarjima(T["izohlar"], r["nom"]) if r.get("nom") else ""
        izoh = f"\n        <figcaption>{e(nom)}</figcaption>" if nom else ""
        fotolar.append(f"""      <figure class="foto">
        <a href="../{e(r['fayl'])}" target="_blank" rel="noopener">
          <img src="../{e(r['fayl'])}" alt="{e(nom or g['alt'])}"
               loading="lazy">
        </a>{izoh}
      </figure>""")

    ichki = f"""
<div class="wrap">
  <section class="intro">
    <h1>{e(g["sarlavha"])}</h1>
    <p class="en-izoh">{e(g["kirish"])}</p>
  </section>

  <div class="filter-bar galereya-menyu">
    <a class="tag active" href="#" data-bolim="video">{e(g["video"])}</a>
    <a class="tag" href="#" data-bolim="foto">{e(g["foto"])}</a>
  </div>

  <div class="galereya" id="video">
{chr(10).join(kartalar)}
  </div>
  <div class="galereya foto-tur" id="foto" style="display:none">
{chr(10).join(fotolar)}
  </div>
</div>
"""
    oxiri = """
<script>
(function () {
  var tugma = document.querySelectorAll('.galereya-menyu .tag');
  tugma.forEach(function (t) {
    t.addEventListener('click', function (ev) {
      ev.preventDefault();
      tugma.forEach(function (x) { x.classList.toggle('active', x === t); });
      ['video', 'foto'].forEach(function (nom) {
        document.getElementById(nom).style.display = t.dataset.bolim === nom ? '' : 'none';
      });
    });
  });
})();
</script>
"""
    return oddiy_sahifa("galereya.html", g["sarlavha"], g["tavsif"], ichki, oxiri)


def aloqa_sahifasi():
    a = UI["aloqa"]
    qatorlar = [("Dilmurod Quronov", "dilmurod271060@gmail.com"),
                (UI["olimlar"]["Sa'dullo Quronov"]["ism"], "squronov@gmail.com")]
    ichki = f"""
<div class="wrap">
  <section class="intro">
    <h1>{e(a["sarlavha"])}</h1>
  </section>

  <div class="aloqa">
""" + "\n".join(f"""    <p class="aloqa-qator">
      <span class="aloqa-yorliq">{e(ism)}</span>
      <a href="mailto:{pochta}">{pochta}</a>
    </p>""" for ism, pochta in qatorlar) + """
  </div>
</div>
"""
    return oddiy_sahifa("aloqa.html", a["sarlavha"], a["tavsif"], ichki)


def qidiruv_sahifasi():
    q = UI["qidiruv"]
    ichki = f"""
<div class="wrap">
  <section class="intro">
    <h1>{e(q["sarlavha"])}</h1>
    <p class="en-izoh">{e(q["izoh"])}</p>
  </section>
  <form class="qidiruv-forma" id="qidiruv-forma" role="search">
    <input type="search" id="qidiruv-soz" class="search" placeholder="{e(q["placeholder"])}"
           autocomplete="off" aria-label="{e(q["sarlavha"])}">
    <button type="submit">{e(q["tugma"])}</button>
  </form>
  <p class="qidiruv-holat" id="qidiruv-holat"></p>
  <div id="qidiruv-natija"></div>
  <nav class="sahifalar" id="qidiruv-sahifalar" aria-label="{e(UI["royxat"]["sahifalar"])}"></nav>
</div>
"""
    janrlar = json.dumps(AT["janr"], ensure_ascii=False)
    oxiri = f'<script>window.JANR_EN = {janrlar};</script>\n<script src="../qidiruv.js" defer></script>\n'
    return oddiy_sahifa("qidiruv.html", q["sarlavha"], q["tavsif"], ichki, oxiri)


def maqola_sahifasi(m, t):
    """en/maqola/<slug>.html — tarjima qilingan maqola; asl sahifaga havola bilan."""
    muallif = m.get("muallif", "Dilmurod Quronov")
    sahifa, rang = MUALLIFLAR[muallif]
    olim = UI["olimlar"][muallif]
    ism = en_ism(muallif_ismi(m)[0])
    meta = [AT["janr"].get(m["janr"], m["janr"])]
    if m.get("yil"):
        meta.append(str(m["yil"]))
    tavsif = f"{ism}. " + qisqacha({"matn": t["paragraphs"]}, 200)
    meta_html = meta_teglar(t["title"], tavsif, f"en/maqola/{m['slug']}.html", olim["rasm"], "article")
    tagsarlavha = f'\n  <p class="tagsarlavha">{e(t["subtitle"])}</p>' if t.get("subtitle") else ""
    matn = "\n".join(f"<p>{e(p)}</p>" for p in t["paragraphs"])
    return shapka(f"{e(t['title'])} — Quronov.uz", meta_html, "../", sahifa) + f"""
<div class="wrap maqola {rang}">
  <div class="maqola-top">
    <a class="ortga" href="../{sahifa}">← {e(olim["ism"])}</a>
  </div>

  <h1>{e(t["title"])}</h1>{tagsarlavha}
  <p class="byline {rang}">{e(ism)}</p>
  <p class="maqola-meta">{e(' · '.join(meta))}</p>
  <p class="en-izoh">{e(UI["maqola"]["tarjima_izoh"])} <a href="../../maqola/{m['slug']}.html" hreflang="uz" lang="uz">{e(m["title"])}</a></p>

  <div class="matn">
{matn}
  </div>

  <p class="imzo">{e(ism)}</p>
  <p class="oqilgan" data-kalit="{e(m['slug'])}" hidden></p>
</div>

<script src="../../oqilgan.js" defer></script>
""" + podval()


def tarjima_sahifalari(maqolalar):
    papka = EN / "maqola"
    papka.mkdir(parents=True, exist_ok=True)
    for eski in papka.glob("*.html"):
        eski.unlink()
    bor = {m["slug"]: m for m in maqolalar}
    for slug, t in TR.items():
        m = bor.get(slug)
        if not m:
            print(f"DIQQAT: tarjimasi bor, lekin saytda yoʻq maqola: {slug}")
            continue
        if t.get("asl_xesh") != asl_xesh(m):
            print(f"DIQQAT: {slug} — oʻzbekcha asl matn tarjimadan keyin oʻzgargan "
                  f"(yangi iz: {asl_xesh(m)}), tarjimani tekshiring")
        (papka / f"{slug}.html").write_text(maqola_sahifasi(m, t), encoding="utf-8")


def yasash(maqolalar, songgilar, mavzular):
    """site/en/ sahifalarini yasaydi; yasalgan sahifalar sonini qaytaradi."""
    EN.mkdir(exist_ok=True)
    TARJIMASIZ.clear()
    tarjima_sahifalari(maqolalar)
    sahifalar = {
        "index.html": bosh_sahifa(songgilar, mavzular),
        "kitoblar.html": kitoblar_sahifasi(),
        "galereya.html": galereya_sahifasi(),
        "aloqa.html": aloqa_sahifasi(),
        "qidiruv.html": qidiruv_sahifasi(),
    }
    for muallif, (sahifa, _) in MUALLIFLAR.items():
        sahifalar[sahifa] = olim_sahifasi(muallif, maqolalar)
    for nom, matn in sahifalar.items():
        (EN / nom).write_text(matn, encoding="utf-8")
    mavzu_sahifalari(maqolalar)
    if TARJIMASIZ:
        print(f"DIQQAT: {len(set(TARJIMASIZ))} ta matnning inglizcha tarjimasi yoʻq:")
        for x in sorted(set(TARJIMASIZ))[:12]:
            print("  -", x)
    return len(list(EN.rglob("*.html")))


# ---------------------------------------------------------------- til tugmasi

def _url(rel):
    if rel == "index.html":
        return f"{SAYT}/"
    if rel.endswith("/index.html"):
        return f"{SAYT}/{rel[:-len('index.html')]}"
    return f"{SAYT}/{rel}"


def _belgi_qoy(matn, nishon, yangi, oldidan):
    """<!-- nishon:boshi -->…<!-- nishon:oxiri --> blokini almashtiradi, yoʻq boʻlsa `oldidan` dan keyin qoʻyadi."""
    blok = f"<!-- {nishon}:boshi -->{yangi}<!-- {nishon}:oxiri -->"
    naqsh = re.compile(rf"<!-- {nishon}:boshi -->.*?<!-- {nishon}:oxiri -->", re.S)
    if naqsh.search(matn):
        return naqsh.sub(lambda _: blok, matn, count=1)
    return matn.replace(oldidan, oldidan + blok, 1)


def til_belgilari():
    """Har sahifaga UZ | EN tugmasi va (juftligi bor sahifalarga) hreflang havolalari."""
    juftlar = 0
    for fayl in sorted(SITE.rglob("*.html")):
        rel = fayl.relative_to(SITE).as_posix()
        if rel.startswith("en/"):
            til, uz_rel, en_rel = "en", rel[3:], rel
        else:
            til, uz_rel, en_rel = "uz", rel, "en/" + rel
        uz_bor = (SITE / uz_rel).exists()
        en_bor = (SITE / en_rel).exists()
        uz_yol = os.path.relpath(SITE / (uz_rel if uz_bor else "index.html"), fayl.parent)
        en_yol = os.path.relpath(SITE / (en_rel if en_bor else "en/index.html"), fayl.parent)

        def band(kod, yol):
            if kod == til:
                return f'<span class="faol" lang="{kod}">{kod.upper()}</span>'
            return f'<a href="{yol}" hreflang="{kod}" lang="{kod}">{kod.upper()}</a>'

        tugma = (f'\n  <div class="til-tanlov" aria-label="{"Language" if til == "en" else "Til"}">'
                 f'{band("uz", uz_yol)}<span class="ajratgich">|</span>{band("en", en_yol)}</div>\n  ')
        hreflang = ""
        if uz_bor and en_bor:
            juftlar += 1
            hreflang = (f'\n<link rel="alternate" hreflang="uz" href="{_url(uz_rel)}">'
                        f'\n<link rel="alternate" hreflang="en" href="{_url(en_rel)}">'
                        f'\n<link rel="alternate" hreflang="x-default" href="{_url(uz_rel)}">\n')

        matn = fayl.read_text(encoding="utf-8")
        yangi = _belgi_qoy(matn, "til", tugma, '<header class="site-header">')
        yangi = _belgi_qoy(yangi, "hreflang", hreflang, "</title>")
        if yangi != matn:
            fayl.write_text(yangi, encoding="utf-8")
    return juftlar
