"""Saytning inglizcha versiyasi: site/en/ sahifalari va barcha sahifalardagi til tugmasi.

Ishlatish:  build.py ichidan chaqiriladi (yasash(), til_belgilari()).
Maʼlumot:   data/en/interfeys.json — interfeys matnlari.
"""

import json, os, re
from pathlib import Path

from build import SITE, SAYT, PODVAL, e, meta_teglar

ROOT = Path(__file__).resolve().parent.parent
EN = SITE / "en"
UI = json.loads((ROOT / "data" / "en" / "interfeys.json").read_text(encoding="utf-8"))


def shapka(sarlavha, meta, yol, faol=""):
    """Inglizcha sahifa boshi. Menyuda faqat inglizchasi bor sahifalar koʻrinadi."""
    bandlar = []
    for b in UI["menyu"]:
        if b["sahifa"] != "index.html" and not (EN / b["sahifa"]).exists():
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


def bosh_sahifa():
    b = UI["bosh_sahifa"]
    meta = meta_teglar(b["sarlavha"], b["tavsif"], "en/")
    return shapka(e(b["sarlavha"]), meta, "", "index.html") + f"""
<div class="wrap">
  <section class="intro">
    <h1>{e(b["h1"])}</h1>
    <p>{e(b["kirish"])}</p>
  </section>
  <section class="en-tayyorlanmoqda">
    <p>{e(b["tayyorlanmoqda"])}</p>
    <p><a href="../index.html" hreflang="uz" lang="uz">{e(b["ozbekcha_havola"])}</a></p>
  </section>
</div>
""" + podval()


def yasash():
    """site/en/ sahifalarini yasaydi; yasalgan sahifalar sonini qaytaradi."""
    EN.mkdir(exist_ok=True)
    (EN / "index.html").write_text(bosh_sahifa(), encoding="utf-8")
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
