"""Saytning inglizcha versiyasi: site/en/ sahifalari va barcha sahifalardagi til tugmasi.

Ishlatish:  build.py ichidan chaqiriladi (yasash(), til_belgilari()).
Maʼlumot:   data/en/interfeys.json — interfeys matnlari, data/en/atamalar.json — atamalar.
"""

import json, os, re
from pathlib import Path

from build import (SITE, SAYT, PODVAL, MUALLIFLAR, e, meta_teglar, muallif_ismi, manba_lotin,
                   qisqacha, guruhlar, matbuot_ruknlari, RUKNLAR)

ROOT = Path(__file__).resolve().parent.parent
EN = SITE / "en"
UI = json.loads((ROOT / "data" / "en" / "interfeys.json").read_text(encoding="utf-8"))
AT = json.loads((ROOT / "data" / "en" / "atamalar.json").read_text(encoding="utf-8"))

# yasaladigan inglizcha sahifalar (menyu shu roʻyxatga qarab tuziladi)
SAHIFALAR = {"index.html", "dilmurod.html", "sadullo.html"}

ASL_TIL = {"Maqola (ingliz tilida)": "en", "Maqola (turk tilida)": "tr", "Maqola (rus tilida)": "ru"}


def en_ism(s):
    """Oʻzbekcha ismning inglizcha yozilishi: Saʼdullo → Sadullo, Choʻlpon → Cholpon."""
    return s.replace("Sa'dullo", "Sadullo").replace("ʻ", "").replace("ʼ", "").replace("'", "")


def shapka(sarlavha, meta, yol, faol=""):
    """Inglizcha sahifa boshi. Menyuda faqat inglizchasi bor sahifalar koʻrinadi."""
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


def meta_qatori(m):
    meta = [AT["janr"].get(m["janr"], m["janr"])]
    if m.get("yil"):
        meta.append(str(m["yil"]))
    manba = manba_lotin(m.get("asl_manba"))
    if manba:
        meta.append(manba)
    if m.get("kitob"):
        meta.append(UI["royxat"]["toplamdan"].format(kitob=m["kitob"].replace("'", "ʻ")))
    return meta


def yozuv_html(m):
    """Roʻyxatdagi bitta yozuv: asl sarlavha, asl til belgisi, matn asl sahifada ochiladi."""
    rang = MUALLIFLAR[m.get("muallif", "Dilmurod Quronov")][1]
    til = ASL_TIL.get(m["janr"], "uz")
    parcha = f"\n        <p>{e(qisqacha(m))}</p>" if til == "en" else ""
    return f"""      <article class="entry {rang}" data-teg="{e(' '.join(guruhlar(m)))}">
        <div class="entry-meta">
          <span class="author-tag">{e(en_ism(muallif_ismi(m)[0]))}</span>
          <span class="entry-date">{e(' · '.join(meta_qatori(m)))}</span>
          <span class="til-belgi">{e(UI["tillar"][til])}</span>
          <span class="oqildi" data-kalit="{e(m['slug'])}"></span>
        </div>
        <h3><a href="../maqola/{m['slug']}.html" lang="{til}">{e(m['title'])}</a></h3>{parcha}
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


def yon_ustun(qoshimcha=""):
    y = UI["yon_ustun"]
    return f"""    <aside class="sidebar">
      <section>
        <a class="lugat-tugma" href="../lugat/index.html" hreflang="uz">
          <span class="lugat-tugma-belgi">Aa</span>
          <span><strong>{e(y["lugat"])}</strong><small>{e(y["lugat_izoh"])}</small></span>
        </a>
      </section>

      <section>
        <h4>{e(y["mualliflar"])}</h4>
        <a class="author-link" href="dilmurod.html"><span class="dot dq"></span>Dilmurod Quronov</a>
        <a class="author-link" href="sadullo.html"><span class="dot sq"></span>{e(UI["olimlar"]["Sa'dullo Quronov"]["ism"])}</a>
      </section>
{qoshimcha}    </aside>"""


def bosh_sahifa(songgilar, mavzular):
    b = UI["bosh_sahifa"]
    meta = meta_teglar(b["sarlavha"], b["tavsif"], "en/")
    tugmalar = "\n".join(
        f'          <a class="tag" href="../mavzu/{slug}.html" hreflang="uz">'
        f'{e(AT["mavzu"].get(nom, nom))}<span class="soni">{soni}</span></a>'
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

{yon_ustun(mavzu_blok)}

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
    panel += [f'      <a class="tag" href="#" data-suzgi="{e(g)}">{e(AT["rukn"].get(g, g))}</a>'
              for g in RUKNLAR if g in bor]
    meta = meta_teglar(f'{o["ism"]} — Quronov.uz', o["tavsif"], f"en/{sahifa}", o["rasm"])
    return shapka(f'{e(o["ism"])} — Quronov.uz', meta, "", sahifa) + f"""
<div class="wrap">

  <div class="author-head">
    <img class="avatar" src="../{o["rasm"]}" alt="{e(o["ism"])}" width="84" height="84">
    <div>
      <h1>{e(o["ism"])}</h1>
      <p class="role">{e(o["rol"])}</p>
      <p class="biografiya-havola"><a href="../maqola/{o["biografiya"]}.html" hreflang="uz">{e(UI["olim_sahifasi"]["biografiya"])}</a></p>
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

<script src="../sayt.js"></script>
<script src="../oqilgan.js" defer></script>
""" + podval()


def yasash(maqolalar, songgilar, mavzular):
    """site/en/ sahifalarini yasaydi; yasalgan sahifalar sonini qaytaradi."""
    EN.mkdir(exist_ok=True)
    (EN / "index.html").write_text(bosh_sahifa(songgilar, mavzular), encoding="utf-8")
    for muallif, (sahifa, _) in MUALLIFLAR.items():
        (EN / sahifa).write_text(olim_sahifasi(muallif, maqolalar), encoding="utf-8")
    return len(list(EN.rglob("*.html")))


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
