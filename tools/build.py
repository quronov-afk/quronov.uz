"""data/maqolalar.json asosida sayt sahifalarini yasaydi.

Ishlatish:  python3 tools/build.py
Natija:     site/maqola/<slug>.html, site/dilmurod.html ro'yxati, bosh sahifa oqimi
"""

import html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import bibliografiya, asl_manba, kirillga

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MAQOLA_DIR = SITE / "maqola"

TEG_QOIDA = [
    ("Choʻlpon", ["чўлпон"]),
    ("Qodiriy", ["қодирий", "ўтган кунлар"]),
    ("Navoiy", ["навоий"]),
    ("Bobur", ["бобур"]),
    ("Zulfiya", ["зулфия"]),
    ("Sheʼriyat", ["шеър", "лирик", "мисра", "достон"]),
    ("Nasr", ["наср", "ҳикоя", "қисса"]),
    ("Roman", ["роман"]),
    ("Adabiyot nazariyasi", ["назария", "поэтика", "композиц", "жанр", "талқин"]),
    ("Adabiy tanqid", ["танқид", "тақриз", "мунаққид"]),
    ("Jadid adabiyoti", ["жадид"]),
    ("Adabiy taʼlim", ["таълим", "дарслик", "ўқув режа"]),
    ("Tarjima", ["таржима"]),
    ("Til va uslub", ["бадиий нутқ", "услуб", "ритм"]),
]
SHAXS = {"Choʻlpon", "Qodiriy", "Navoiy", "Bobur", "Zulfiya"}


def teglar(m):
    matn = (" ".join(m["matn_kir"]) + " " + m["title_kir"]).lower()
    sarlavha = m["title_kir"].lower()
    ball = []
    for nom, kalitlar in TEG_QOIDA:
        n = sum(matn.count(k) for k in kalitlar) + 8 * sum(sarlavha.count(k) for k in kalitlar)
        chegara = 12 if nom in SHAXS else 8
        if n >= chegara:
            ball.append((n, nom))
    ball.sort(reverse=True)
    return [nom for _, nom in ball[:3]]


TRANSLIT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
            "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "ʼ",
            "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "oʻ", "қ": "q", "ғ": "gʻ",
            "ҳ": "h"}


def manba_lotin(s):
    """Manba yozuvini tozalab, lotin yozuviga o'giradi."""
    if not s:
        return None
    s = re.sub(r"\s+", " ", s.replace("\t", " ")).strip(" .")
    s = re.sub(r"\(\s*[Ҳҳ]аммуаллиф[^)]*\)", "", s)
    s = re.sub(r"\d+,\d+\s*б\.т\.?", "", s)
    s = re.sub(r"\(\s*[А-ЯЁ]\.[^)]*\)", "", s)
    s = re.sub(r"[«»“”\"]", "", s).strip(" .,-–")
    out = []
    for ch in s:
        past = ch.lower()
        rep = TRANSLIT.get(past, ch)
        out.append(rep[0].upper() + rep[1:] if ch.isupper() and rep else rep)
    s = "".join(out)
    s = s.replace("№", "№").replace(" - ", ", ").replace(".- ", ", ")
    return re.sub(r"\s+", " ", s).strip(" .,")


def qisqacha(m, uzunlik=500):
    matn = " ".join(m["matn"])
    if len(matn) <= uzunlik:
        return matn
    kesim = matn[:uzunlik]
    return kesim[:kesim.rfind(" ")] + "…"


def e(s):
    return html.escape(s, quote=True)


SHAPKA = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=PT+Serif:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{yol}style.css">
</head>
<body>

<header class="site-header">
  <div class="masthead">
    <div class="wordmark"><a href="{yol}index.html">Quronov<span>.uz</span></a></div>
    <div class="tagline">Adabiyot va adabiyotshunoslik</div>
  </div>
  <div class="header-inner">
    <nav class="nav">
      <a href="{yol}index.html">Bosh sahifa</a>
      <a href="{yol}dilmurod.html"{dq}>Dilmurod Quronov</a>
      <a href="{yol}sadullo.html"{sq}>Saʼdullo Quronov</a>
      <a href="{yol}kitoblar.html">Kitoblar PDF</a>
      <a href="{yol}galereya.html">Galereya</a>
      <a href="{yol}aloqa.html">Aloqa</a>
    </nav>
  </div>
</header>
"""

PODVAL = """
<footer class="site-footer">
  <div class="footer-inner">
    <span>© 2026 Quronov.uz</span>
    <span><a href="mailto:squronov@gmail.com">squronov@gmail.com</a></span>
  </div>
</footer>

</body>
</html>
"""


def meta_qatori(m):
    meta = [m["janr"]]
    if m.get("yil"):
        meta.append(str(m["yil"]))
    manba = manba_lotin(m.get("asl_manba"))
    if manba:
        meta.append(manba)
    if m.get("kitob"):
        meta.append(f"«{m['kitob']}» toʻplamidan")
    return meta


# Filtr ruknlari faqat janr asosida: mavzu teglari panelga chiqmaydi
JANR_GURUH = {
    "Maqola": "Maqolalar", "Tezis": "Maqolalar", "Maqola (ingliz tilida)": "Maqolalar",
    "Maqola (turk tilida)": "Maqolalar", "Maqola (rus tilida)": "Maqolalar",
    "Nutq": "Maʼruzalar", "Maʼruza": "Maʼruzalar",
    "Taqriz": "Taqrizlar", "So'z boshi": "Taqrizlar",
    "Suhbat": "Suhbatlar",
    "Asar": "Badiiy asarlar",
    "Olim haqida": "Olim haqida", "Biografiya": "Olim haqida", "Yangilik": "Olim haqida",
}

RUKNLAR = ["Maqolalar", "Maʼruzalar", "Taqrizlar", "Suhbatlar",
           "Badiiy asarlar", "Olim haqida"]

JANR_YORLIQ = {
    "Maqola": "Maqolalar", "Suhbat": "Suhbatlar", "Taqriz": "Taqrizlar",
    "Nutq": "Nutqlar", "So'z boshi": "Soʻz boshilar", "Asar": "Badiiy asarlar",
    "Tezis": "Tezislar", "Biografiya": "Biografiya", "Olim haqida": "Olim haqida",
    "Maqola (ingliz tilida)": "Ingliz tilida",
    "Maqola (turk tilida)": "Turk tilida", "Maqola (rus tilida)": "Rus tilida",
}

MUALLIF_NOM = {
    "Dilmurod Quronov": ("Dilmurod Quronov", "Дилмурод Қуронов"),
    "Sa'dullo Quronov": ("Saʼdullo Quronov", "Саъдулло Қуронов"),
}


def muallif_ismi(m):
    """Yozuv ostida turadigan ism. «Olim haqida» bo'lsa — maqolani yozgan kishi."""
    if m.get("yozgan"):
        return m["yozgan"], kirillga(m["yozgan"])
    return MUALLIF_NOM[m.get("muallif", "Dilmurod Quronov")]


MUALLIFLAR = {
    "Dilmurod Quronov": ("dilmurod.html", "dq"),
    "Sa'dullo Quronov": ("sadullo.html", "sq"),
}


def maqola_sahifasi(m):
    meta = meta_qatori(m)
    muallif = m.get("muallif", "Dilmurod Quronov")
    sahifa, rang = MUALLIFLAR[muallif]
    ism_lat, ism_kir = muallif_ismi(m)
    dq = ' class="active"' if muallif == "Dilmurod Quronov" else ""
    sq = ' class="active"' if muallif != "Dilmurod Quronov" else ""
    lat = "\n".join(f"<p>{e(p)}</p>" for p in m["matn"])
    kir = "\n".join(f"<p>{e(p)}</p>" for p in m["matn_kir"])

    return SHAPKA.format(title=e(m["title"]) + " — Quronov.uz", yol="../", dq=dq, sq=sq) + f"""
<div class="wrap maqola {rang}">
  <div class="maqola-top">
    <a class="ortga" href="../{sahifa}">← {e(m.get("muallif", "Dilmurod Quronov")).replace("Sa'dullo", "Saʼdullo")}</a>
    <div class="yozuv-tanlov" role="group" aria-label="Yozuv turi">
      <button type="button" data-yozuv="lat" class="tanlangan">Lotin</button>
      <span>|</span>
      <button type="button" data-yozuv="kir">Kirill</button>
    </div>
  </div>

  <h1 data-lat="{e(m['title'])}" data-kir="{e(m['title_kir'])}">{e(m['title'])}</h1>
  <p class="byline {rang}" data-lat="{e(ism_lat)}" data-kir="{e(ism_kir)}">{e(ism_lat)}</p>
  <p class="maqola-meta">{e(' · '.join(meta))}</p>

  <div class="matn" id="matn-lat">
{lat}
  </div>
  <div class="matn" id="matn-kir" hidden>
{kir}
  </div>

  <p class="imzo" data-lat="{e(ism_lat)}" data-kir="{e(ism_kir)}">{e(ism_lat)}</p>
</div>

<script>
(function () {{
  var tugma = document.querySelectorAll('.yozuv-tanlov button');
  var ikkiyozuv = document.querySelectorAll('[data-lat]');
  function qoy(y) {{
    document.getElementById('matn-lat').hidden = (y === 'kir');
    document.getElementById('matn-kir').hidden = (y !== 'kir');
    ikkiyozuv.forEach(function (el) {{
      var qiymat = el.getAttribute(y === 'kir' ? 'data-kir' : 'data-lat');
      if (qiymat) el.textContent = qiymat;
    }});
    tugma.forEach(function (t) {{
      t.classList.toggle('tanlangan', t.dataset.yozuv === y);
    }});
    try {{ localStorage.setItem('yozuv', y); }} catch (x) {{}}
  }}
  tugma.forEach(function (t) {{
    t.addEventListener('click', function () {{ qoy(t.dataset.yozuv); }});
  }});
  try {{ if (localStorage.getItem('yozuv') === 'kir') qoy('kir'); }} catch (x) {{}}
}})();
</script>
""" + PODVAL


def guruhlar(m):
    """Yozuv tegishli boʻlgan rukn (janr asosida)."""
    return [JANR_GURUH.get(m["janr"], m["janr"])]


def royxat_html(maqolalar, havola_oldi=""):
    qismlar = []
    for m in maqolalar:
        meta = meta_qatori(m)
        teg_attr = " ".join(guruhlar(m))
        rang = MUALLIFLAR[m.get("muallif", "Dilmurod Quronov")][1]
        ism = muallif_ismi(m)[0]
        qismlar.append(f"""      <article class="entry {rang}" data-teg="{e(teg_attr)}">
        <div class="entry-meta">
          <span class="author-tag">{e(ism)}</span>
          <span class="entry-date">{e(' · '.join(meta))}</span>
        </div>
        <h3><a href="{havola_oldi}maqola/{m['slug']}.html">{e(m['title'])}</a></h3>
        <p>{e(qisqacha(m))}</p>
      </article>""")
    return "\n".join(qismlar)


def matbuot_ruknlari(muallif):
    """Matbuot yozuvlari qaysi ruknlarga tegishli ekani."""
    fayl = ROOT / "data" / "matbuot.json"
    if not fayl.exists():
        return set()
    return {m.get("rukn", "Maqolalar")
            for m in json.loads(fayl.read_text(encoding="utf-8"))
            if m["muallif"] == muallif}


def matbuot_html(muallif):
    """Boshqa nashrlarda chiqqan materiallar: sarlavha, manba va havola."""
    fayl = ROOT / "data" / "matbuot.json"
    if not fayl.exists():
        return ""
    yozuvlar = [m for m in json.loads(fayl.read_text(encoding="utf-8"))
                if m["muallif"] == muallif]
    if not yozuvlar:
        return ""
    yozuvlar.sort(key=lambda m: m["sana"], reverse=True)
    qismlar = ['      <p class="section-label">Internet nashrlarida</p>']
    oylar = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul",
             "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
    for m in yozuvlar:
        sana = ""
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", m["sana"] or ""):
            y, o, k = m["sana"].split("-")
            sana = f"{y}, {int(k)}-{oylar[int(o) - 1]}"
        qismlar.append(f"""      <article class="matbuot-entry" data-teg="{e(m.get('rukn', 'Maqolalar'))}">
        <div class="entry-meta">
          <span class="nashr">{e(m['nashr'])}</span>
          <span class="entry-date">{e(sana)}</span>
        </div>
        <h3><a href="{e(m['url'])}" target="_blank" rel="noopener">{e(m['sarlavha'])}</a></h3>
        <p>{e(m['parcha'])}</p>
      </article>""")
    return "\n".join(qismlar)


def belgilar_orasiga(fayl, nishon, yangi):
    matn = fayl.read_text(encoding="utf-8")
    naqsh = re.compile(rf"(<!-- {nishon}:boshi -->).*?(<!-- {nishon}:oxiri -->)", re.S)
    if not naqsh.search(matn):
        raise SystemExit(f"{fayl.name} ichida '{nishon}' belgilari topilmadi")
    fayl.write_text(naqsh.sub(lambda m: f"{m.group(1)}\n{yangi}\n{m.group(2)}", matn),
                    encoding="utf-8")


def eski_saytdan_qoshish(maqolalar, fayl_nomi="eski_maqolalar.json"):
    """Arxiv va shaxsiy papkadan tiklangan, to'plamlarda yo'q materiallar."""
    fayl = ROOT / "data" / fayl_nomi
    if not fayl.exists():
        return maqolalar
    yozuvlar = bibliografiya()
    bor_slug = {m["slug"] for m in maqolalar}
    for m in json.loads(fayl.read_text(encoding="utf-8")):
        if m["slug"] in bor_slug:
            continue
        kir = m.get("matn_kir") or [kirillga(p) for p in m["matn"]]
        nom_kir = m.get("title_kir") or kirillga(m["title"])
        asl = asl_manba(nom_kir, yozuvlar)
        if not asl and m.get("manba_qatori"):
            qator = m["manba_qatori"].split("//", 1)[-1]
            yil_m = re.search(r"\b(19\d{2}|20\d{2})\b", qator)
            asl = {"manba": qator.strip(" ."), "yil": int(yil_m.group(1)) if yil_m else None}
        maqolalar.append({
            "slug": m["slug"], "title": m["title"], "title_kir": nom_kir,
            "janr": m["janr"], "yil": m.get("yil") or (asl["yil"] if asl else None),
            "asl_manba": m.get("asl_manba") or (asl["manba"] if asl else None),
            "manba_sayt": m["manba_sayt"], "kitob": None, "yozgan": m.get("yozgan"),
            "muallif": m.get("muallif", "Dilmurod Quronov"),
            "matn": m["matn"], "matn_kir": kir, "belgi": m["belgi"],
        })
    return maqolalar


def galereya_sahifasi():
    """Video va foto galereya: yuqorida ikkita boʻlim tugmasi."""
    fayl = ROOT / "data" / "videolar.json"
    if not fayl.exists():
        return None
    videolar = json.loads(fayl.read_text(encoding="utf-8"))
    kartalar = []
    for v in videolar:
        kartalar.append(f"""      <figure class="video">
        <div class="video-ramka">
          <iframe src="https://www.youtube-nocookie.com/embed/{e(v['id'])}" title="{e(v['nom'])}"
                  loading="lazy" allowfullscreen></iframe>
        </div>
        <figcaption>{e(v['nom'])}<span>{e(v['manba'])}</span></figcaption>
      </figure>""")
    video_ichki = "\n".join(kartalar)

    rasm_fayl = ROOT / "data" / "rasmlar.json"
    rasmlar = json.loads(rasm_fayl.read_text(encoding="utf-8")) if rasm_fayl.exists() else []
    if rasmlar:
        def foto_karta(r):
            izoh = ""
            if r.get("nom") or r.get("manba"):
                manba = f"<span>{e(r['manba'])}</span>" if r.get("manba") else ""
                izoh = f"\n        <figcaption>{e(r.get('nom', ''))}{manba}</figcaption>"
            return (f"""      <figure class="foto">
        <a href="{e(r['fayl'])}" target="_blank" rel="noopener">
          <img src="{e(r['fayl'])}" alt="{e(r.get('nom', 'Quronovlar arxividan surat'))}"
               loading="lazy">
        </a>{izoh}
      </figure>""")

        foto_ichki = "\n".join(foto_karta(r) for r in rasmlar)
        foto_blok = f'  <div class="galereya foto-tur" id="foto" style="display:none">\n{foto_ichki}\n  </div>'
    else:
        foto_blok = '  <div id="foto" style="display:none"></div>'

    return SHAPKA.format(title="Galereya — Quronov.uz", yol="", dq="", sq="") + f"""
<div class="wrap">
  <section class="intro">
    <h1>Galereya</h1>
  </section>

  <div class="filter-bar galereya-menyu">
    <a class="tag active" href="#" data-bolim="video">Video galereya</a>
    <a class="tag" href="#" data-bolim="foto">Foto galereya</a>
  </div>

  <div class="galereya" id="video">
{video_ichki}
  </div>
{foto_blok}
</div>

<script>
(function () {{
  var tugma = document.querySelectorAll('.galereya-menyu .tag');
  tugma.forEach(function (t) {{
    t.addEventListener('click', function (ev) {{
      ev.preventDefault();
      tugma.forEach(function (x) {{ x.classList.toggle('active', x === t); }});
      ['video', 'foto'].forEach(function (nom) {{
        var el = document.getElementById(nom);
        el.style.display = t.dataset.bolim === nom ? '' : 'none';
      }});
    }});
  }});
}})();
</script>
""" + PODVAL


def havolalarni_tekshirish():
    """Sayt ichidagi havolalarni tekshiradi: yo'q fayl yoki bo'sh menyu havolasi."""
    xatolar = []
    for fayl in sorted(SITE.rglob("*.html")):
        matn = fayl.read_text(encoding="utf-8")
        for menyu in re.findall(r'<nav class="nav">(.*?)</nav>', matn, re.S):
            for nom in re.findall(r'<a href="#"[^>]*>([^<]+)</a>', menyu):
                xatolar.append(f"{fayl.relative_to(SITE)}: menyuda bo'sh havola — {nom}")
        for havola in re.findall(r'(?:href|src)="([^"#:]+)"', matn):
            if havola.startswith(("http", "//", "mailto")):
                continue
            if not (fayl.parent / havola).exists():
                xatolar.append(f"{fayl.relative_to(SITE)}: yo'q fayl — {havola}")
    return xatolar


def main():
    maqolalar = json.loads((ROOT / "data" / "maqolalar.json").read_text(encoding="utf-8"))
    maqolalar = eski_saytdan_qoshish(maqolalar)
    maqolalar = eski_saytdan_qoshish(maqolalar, "qolgan_materiallar.json")
    maqolalar = eski_saytdan_qoshish(maqolalar, "skaner_maqolalar.json")
    maqolalar = eski_saytdan_qoshish(maqolalar, "arxiv_maqolalar.json")
    maqolalar = eski_saytdan_qoshish(maqolalar, "sadullo_maqolalar.json")
    maqolalar = eski_saytdan_qoshish(maqolalar, "monografiyadan.json")
    for m in maqolalar:
        m["teglar"] = teglar(m)
    maqolalar.sort(key=lambda m: (-(m["yil"] or 0), m["title"]))

    MAQOLA_DIR.mkdir(parents=True, exist_ok=True)
    for eski in MAQOLA_DIR.glob("*.html"):
        eski.unlink()
    for m in maqolalar:
        (MAQOLA_DIR / f"{m['slug']}.html").write_text(maqola_sahifasi(m), encoding="utf-8")

    # har bir muallif sahifasidagi ro'yxat va teglar paneli
    for muallif, (sahifa, _) in MUALLIFLAR.items():
        uniki = [m for m in maqolalar if m.get("muallif", "Dilmurod Quronov") == muallif]
        if not uniki:
            continue
        bor = {g for m in uniki for g in guruhlar(m)} | matbuot_ruknlari(muallif)
        tanlangan = [g for g in RUKNLAR if g in bor]
        panel = ['      <a class="tag active" href="#" data-suzgi="">Barchasi</a>']
        panel += [f'      <a class="tag" href="#" data-suzgi="{e(g)}">{e(g)}</a>' for g in tanlangan]
        belgilar_orasiga(SITE / sahifa, "teglar", "\n".join(panel))
        belgilar_orasiga(SITE / sahifa, "royxat", royxat_html(uniki))
        belgilar_orasiga(SITE / sahifa, "matbuot", matbuot_html(muallif))

    # bosh sahifadagi so'nggi yozuvlar
    belgilar_orasiga(SITE / "index.html", "oqim", royxat_html(maqolalar[:5], ""))

    sahifa = galereya_sahifasi()
    if sahifa:
        (SITE / "galereya.html").write_text(sahifa, encoding="utf-8")

    print(f"{len(maqolalar)} ta maqola sahifasi yasaldi")

    xatolar = havolalarni_tekshirish()
    if xatolar:
        print(f"\nDIQQAT: {len(xatolar)} ta havola muammosi:")
        for x in sorted(set(xatolar))[:12]:
            print("  -", x)


if __name__ == "__main__":
    main()
