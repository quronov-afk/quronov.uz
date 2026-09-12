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
    ("Inson konsepsiyasi", ["инсон концепция", "шахс концепция"]),
    ("Modernizm", ["модерн"]),
    ("Postmodernizm", ["постмодерн"]),
    ("Badiiy sintez", ["синтез"]),
    ("Tasviriy sanʼat", ["рангтасвир", "мусаввир", "миниатюра", "расс"]),
    ("Mumtoz adabiyot", ["мумтоз"]),
    ("Folklor va mif", ["фольклор", "фолклор", "миф", "афсона"]),
    ("Dramaturgiya", ["драма", "театр", "саҳна"]),
    ("Bolalar adabiyoti", ["болалар адабиёт", "болалар учун", "болалар ёзувчи", "фантастик"]),
    ("Oybek", ["ойбек"]),
]
SHAXS = {"Choʻlpon", "Qodiriy", "Navoiy", "Bobur", "Zulfiya", "Oybek"}
# kam uchraydigan, lekin sayt uchun muhim mavzular uchun pastroq chegara
CHEGARA = {"Bolalar adabiyoti": 4, "Postmodernizm": 5, "Badiiy sintez": 5}


def teglar(m):
    matn = (" ".join(m["matn_kir"]) + " " + m["title_kir"]).lower()
    sarlavha = m["title_kir"].lower()
    ball = []
    for nom, kalitlar in TEG_QOIDA:
        n = sum(matn.count(k) for k in kalitlar) + 8 * sum(sarlavha.count(k) for k in kalitlar)
        chegara = CHEGARA.get(nom, 12 if nom in SHAXS else 8)
        if n >= chegara:
            ball.append((n, nom))
    ball.sort(reverse=True)
    return [nom for _, nom in ball[:4]]


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
{meta}<link rel="preconnect" href="https://fonts.googleapis.com">
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

SAYT = "https://quronov.uz"


def meta_teglar(sarlavha, tavsif, yol, rasm="img/ulashish.jpg", tur="website"):
    """Google tavsifi, kanonik havola va Telegram/Facebook uchun Open Graph kartasi."""
    tavsif = re.sub(r"\s+", " ", tavsif).strip()
    if len(tavsif) > 180:
        tavsif = tavsif[:177].rsplit(" ", 1)[0] + "…"
    url = f"{SAYT}/{yol}"
    return (f'<meta name="description" content="{e(tavsif)}">\n'
            f'<link rel="canonical" href="{e(url)}">\n'
            f'<meta property="og:site_name" content="Quronov.uz">\n'
            f'<meta property="og:type" content="{tur}">\n'
            f'<meta property="og:title" content="{e(sarlavha)}">\n'
            f'<meta property="og:description" content="{e(tavsif)}">\n'
            f'<meta property="og:url" content="{e(url)}">\n'
            f'<meta property="og:image" content="{SAYT}/{rasm}">\n'
            f'<meta property="og:locale" content="uz_UZ">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n')


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


def tagsarlavha_html(m):
    """Sarlavha ostidagi izohli tag sarlavha (bo'lsa)."""
    t = m.get("tagsarlavha")
    if not t:
        return ""
    return (f'\n  <p class="tagsarlavha" data-lat="{e(t)}" data-kir="{e(kirillga(t))}">'
            f"{e(t)}</p>")


def qisqa_ism(toliq):
    """«Saʼdullo Quronov» → «Quronov S.» (bibliografik shakl)."""
    qism = toliq.replace("Sa'dullo", "Saʼdullo").split()
    if len(qism) < 2:
        return toliq
    return f"{qism[-1]} {qism[0][0]}."


def iqtibos_matni(m, ism_lat):
    from datetime import date
    bolaklar = [f"{qisqa_ism(ism_lat)} {m['title']}"]
    manba = manba_lotin(m.get("asl_manba"))
    if manba:
        bolaklar.append(f" // {manba}")
    elif m.get("kitob"):
        bolaklar.append(f" // {m['kitob']}")
    if m.get("yil") and str(m["yil"]) not in (manba or ""):
        bolaklar.append(f". – {m['yil']}")
    url = f"{SAYT}/maqola/{m['slug']}.html"
    return "".join(bolaklar) + f". – URL: {url} (murojaat sanasi: {date.today():%d.%m.%Y})"


def iqtibos_html(m, ism_lat):
    """Maqola oxiridagi «Iqtibos keltirish uchun» bloki (nusxa olish tugmasi bilan)."""
    return f"""  <aside class="iqtibos">
    <p class="iqtibos-sarlavha">Iqtibos keltirish uchun</p>
    <p class="iqtibos-matn" id="iqtibos-matn">{e(iqtibos_matni(m, ism_lat))}</p>
    <button type="button" class="iqtibos-tugma" id="iqtibos-tugma">Nusxa olish</button>
  </aside>"""


def mavzudosh_html(m):
    royxat = m.get("mavzudosh") or []
    if not royxat:
        return ""
    qatorlar = "\n".join(
        f'      <li><a href="{x["slug"]}.html">{e(x["title"])}</a>'
        f'<span>{e(x["ism"])}{" · " + str(x["yil"]) if x.get("yil") else ""}</span></li>'
        for x in royxat)
    return f"""  <nav class="mavzudosh" aria-label="Mavzudosh maqolalar">
    <p class="mavzudosh-sarlavha">Mavzudosh maqolalar</p>
    <ul>
{qatorlar}
    </ul>
  </nav>"""


def mavzudoshlarni_topish(maqolalar, soni=3):
    """Matn soʻzlari boʻyicha (TF-IDF, kosinus) eng yaqin maqolalarni topadi."""
    import math
    from collections import Counter
    def tokenlar(m):
        matn = (m["title"] + " ") * 3 + " ".join(m["matn"])
        sozlar = re.findall(r"[a-zʻʼ]{5,}", matn.lower().replace("ʻ", "").replace("ʼ", ""))
        return Counter(w[:6] for w in sozlar)
    hujjatlar = [tokenlar(m) for m in maqolalar]
    df = Counter(w for h in hujjatlar for w in h)
    n = len(maqolalar)
    vektorlar = []
    for h in hujjatlar:
        v = {w: (1 + math.log(c)) * math.log(n / df[w]) for w, c in h.items()
             if 1 < df[w] < n * 0.4}
        norma = math.sqrt(sum(x * x for x in v.values())) or 1
        vektorlar.append({w: x / norma for w, x in v.items()})
    for i, m in enumerate(maqolalar):
        if m["janr"] == "Biografiya":
            m["mavzudosh"] = []
            continue
        ballar = []
        for j, boshqa in enumerate(maqolalar):
            if i == j or boshqa["janr"] == "Biografiya":
                continue
            a, b2 = vektorlar[i], vektorlar[j]
            if len(a) > len(b2):
                a, b2 = b2, a
            ball = sum(x * b2.get(w, 0) for w, x in a.items())
            if ball > 0.9:            # deyarli bir xil matn — tavsiya qilinmaydi
                continue
            if boshqa.get("muallif") == m.get("muallif"):
                ball *= 1.15
            ballar.append((ball, j))
        ballar.sort(reverse=True)
        m["mavzudosh"] = [{"slug": maqolalar[j]["slug"], "title": maqolalar[j]["title"],
                           "ism": muallif_ismi(maqolalar[j])[0], "yil": maqolalar[j].get("yil")}
                          for ball, j in ballar[:soni] if ball > 0.05]


def maqola_sahifasi(m):
    meta = meta_qatori(m)
    muallif = m.get("muallif", "Dilmurod Quronov")
    sahifa, rang = MUALLIFLAR[muallif]
    ism_lat, ism_kir = muallif_ismi(m)
    dq = ' class="active"' if muallif == "Dilmurod Quronov" else ""
    sq = ' class="active"' if muallif != "Dilmurod Quronov" else ""
    lat = "\n".join(f"<p>{e(p)}</p>" for p in m["matn"])
    kir = "\n".join(f"<p>{e(p)}</p>" for p in m["matn_kir"])

    rasm = "img/dilmurod.jpg" if muallif == "Dilmurod Quronov" else "img/sadullo.jpg"
    meta_html = meta_teglar(m["title"], f"{ism_lat}. " + qisqacha(m, 200),
                            f"maqola/{m['slug']}.html", rasm, "article")
    return SHAPKA.format(title=e(m["title"]) + " — Quronov.uz", yol="../", dq=dq, sq=sq,
                         meta=meta_html) + f"""
<div class="wrap maqola {rang}">
  <div class="maqola-top">
    <a class="ortga" href="../{sahifa}">← {e(m.get("muallif", "Dilmurod Quronov")).replace("Sa'dullo", "Saʼdullo")}</a>
    <div class="yozuv-tanlov" role="group" aria-label="Yozuv turi">
      <button type="button" data-yozuv="lat" class="tanlangan">Lotin</button>
      <span>|</span>
      <button type="button" data-yozuv="kir">Kirill</button>
    </div>
  </div>

  <h1 data-lat="{e(m['title'])}" data-kir="{e(m['title_kir'])}">{e(m['title'])}</h1>{tagsarlavha_html(m)}
  <p class="byline {rang}" data-lat="{e(ism_lat)}" data-kir="{e(ism_kir)}">{e(ism_lat)}</p>
  <p class="maqola-meta">{e(' · '.join(meta))}</p>

  <div class="matn" id="matn-lat">
{lat}
  </div>
  <div class="matn" id="matn-kir" hidden>
{kir}
  </div>

  <p class="imzo" data-lat="{e(ism_lat)}" data-kir="{e(ism_kir)}">{e(ism_lat)}</p>
  <p class="oqilgan" data-kalit="{e(m['slug'])}" hidden></p>
{iqtibos_html(m, ism_lat)}
{mavzudosh_html(m)}
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
  var tugma2 = document.getElementById('iqtibos-tugma');
  var iqtibos = document.getElementById('iqtibos-matn');
  if (tugma2 && iqtibos) {{
    var bugun = new Date();
    var sana = ('0' + bugun.getDate()).slice(-2) + '.' + ('0' + (bugun.getMonth() + 1)).slice(-2) + '.' + bugun.getFullYear();
    iqtibos.textContent = iqtibos.textContent.replace(/murojaat sanasi: [0-9.]+/, 'murojaat sanasi: ' + sana);
    tugma2.addEventListener('click', function () {{
      var tayyor = function () {{ tugma2.textContent = 'Nusxa olindi'; setTimeout(function () {{ tugma2.textContent = 'Nusxa olish'; }}, 2000); }};
      if (navigator.clipboard) navigator.clipboard.writeText(iqtibos.textContent).then(tayyor);
      else {{ var r = document.createRange(); r.selectNodeContents(iqtibos); var t = window.getSelection(); t.removeAllRanges(); t.addRange(r); document.execCommand('copy'); tayyor(); }}
    }});
  }}
}})();
</script>
<script src="../oqilgan.js" defer></script>
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
          <span class="oqildi" data-kalit="{e(m['slug'])}"></span>
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
            "tagsarlavha": m.get("tagsarlavha"),
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

    meta_html = meta_teglar("Galereya — Quronov.uz",
                            "Dilmurod Quronov va Saʼdullo Quronov ishtirokidagi videolar va suratlar.",
                            "galereya.html")
    return SHAPKA.format(title="Galereya — Quronov.uz", yol="", dq="", sq="",
                         meta=meta_html) + f"""
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


def qidiruv_yasash(maqolalar):
    """Butun matn boʻyicha qidiruv: site/qidiruv.json indeksi va site/qidiruv.html sahifasi."""
    indeks = [{"s": m["slug"], "t": m["title"], "a": muallif_ismi(m)[0], "y": m.get("yil") or "",
               "j": m["janr"], "m": re.sub(r"\s+", " ", " ".join(m["matn"]))}
              for m in maqolalar]
    (SITE / "qidiruv.json").write_text(json.dumps(indeks, ensure_ascii=False, separators=(",", ":")),
                                       encoding="utf-8")
    meta_html = meta_teglar("Qidiruv — Quronov.uz",
                            "Dilmurod Quronov va Saʼdullo Quronov maqolalari matni boʻyicha qidiruv.",
                            "qidiruv.html")
    sahifa = SHAPKA.format(title="Qidiruv — Quronov.uz", yol="", dq="", sq="", meta=meta_html) + """
<div class="wrap">
  <section class="intro">
    <h1>Qidiruv</h1>
  </section>
  <form class="qidiruv-forma" id="qidiruv-forma" role="search">
    <input type="search" id="qidiruv-soz" class="search" placeholder="Maqolalar matni boʻyicha qidirish"
           autocomplete="off" aria-label="Qidiruv soʻzi">
    <button type="submit">Qidirish</button>
  </form>
  <p class="qidiruv-holat" id="qidiruv-holat"></p>
  <div id="qidiruv-natija"></div>
  <nav class="sahifalar" id="qidiruv-sahifalar" aria-label="Sahifalar"></nav>
</div>
<script src="qidiruv.js" defer></script>
""" + PODVAL
    (SITE / "qidiruv.html").write_text(sahifa, encoding="utf-8")
    return len(json.dumps(indeks, ensure_ascii=False)) // 1024


def sitemap_yasash():
    """Google uchun sahifalar xaritasi va robots.txt."""
    from datetime import date
    bugun = date.today().isoformat()
    sahifalar = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("*.html"))
    ustuvor = {"index.html": "1.0", "dilmurod.html": "0.9", "sadullo.html": "0.9"}
    qatorlar = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for yol in sahifalar:
        url = f"{SAYT}/" if yol == "index.html" else f"{SAYT}/{yol}"
        qatorlar.append(f"  <url><loc>{e(url)}</loc><lastmod>{bugun}</lastmod>"
                        f"<priority>{ustuvor.get(yol, '0.6')}</priority></url>")
    qatorlar.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(qatorlar) + "\n", encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SAYT}/sitemap.xml\n",
                                     encoding="utf-8")
    return len(sahifalar)


def qoshilgan_vaqtlari():
    """Har bir maqola sahifasi repozitoriyaga birinchi marta qoʻshilgan vaqt (git).
    Hali commit qilinmagan yangi maqola «hozir» qoʻshilgan hisoblanadi."""
    import subprocess, time
    vaqt = {}
    try:
        r = subprocess.run(["git", "log", "--diff-filter=A", "--name-only", "--format=@%ct",
                            "--", "site/maqola"], cwd=ROOT, capture_output=True, text=True)
        joriy = None
        for q in r.stdout.splitlines():
            if q.startswith("@"):
                joriy = int(q[1:])
            elif q.startswith("site/maqola/") and q.endswith(".html") and joriy:
                slug = q[len("site/maqola/"):-5]
                vaqt[slug] = min(vaqt.get(slug, joriy), joriy)
    except OSError:
        pass
    return vaqt, int(time.time())


def mavzu_slug(nom):
    from kitobdan import slugify
    return slugify(nom)


def mavzu_sahifalari(maqolalar):
    """site/mavzu/<slug>.html — mavzu boʻyicha maqolalar roʻyxati; bosh sahifa uchun (nom, soni, slug)."""
    from collections import defaultdict
    guruh = defaultdict(list)
    for m in maqolalar:
        for t in m.get("teglar", []):
            guruh[t].append(m)
    papka = SITE / "mavzu"
    papka.mkdir(exist_ok=True)
    for eski in papka.glob("*.html"):
        eski.unlink()
    royxat = []
    for nom, uniki in sorted(guruh.items(), key=lambda x: (-len(x[1]), x[0])):
        slug = mavzu_slug(nom)
        meta_html = meta_teglar(f"{nom} — Quronov.uz",
                                f"«{nom}» mavzusidagi {len(uniki)} ta maqola: Dilmurod Quronov va "
                                "Saʼdullo Quronov ilmiy-ijodiy merosidan.", f"mavzu/{slug}.html")
        sahifa = SHAPKA.format(title=f"{e(nom)} — Quronov.uz", yol="../", dq="", sq="",
                               meta=meta_html) + f"""
<div class="wrap">
  <section class="intro">
    <p class="section-label">Mavzu</p>
    <h1>{e(nom)}</h1>
    <p>{len(uniki)} ta maqola</p>
  </section>
  <main>
    <div id="royxat">
{royxat_html(uniki, "../")}
    </div>
    <nav class="sahifalar" id="sahifalar" aria-label="Sahifalar"></nav>
  </main>
</div>
<script src="../sayt.js"></script>
<script src="../oqilgan.js" defer></script>
""" + PODVAL
        (papka / f"{slug}.html").write_text(sahifa, encoding="utf-8")
        royxat.append((nom, len(uniki), slug))
    return royxat


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

    mavzudoshlarni_topish(maqolalar)
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

    # bosh sahifadagi soʻnggi yozuvlar: saytga soʻnggi qoʻshilganlar birinchi
    vaqtlar, hozir = qoshilgan_vaqtlari()
    songgilar = sorted(maqolalar, key=lambda m: (-vaqtlar.get(m["slug"], hozir),
                                                 -(m["yil"] or 0), m["title"]))
    belgilar_orasiga(SITE / "index.html", "oqim", royxat_html(songgilar[:5], ""))

    # bosh sahifadagi mavzular: eng koʻp maqolali mavzular oldinda
    mavzular = mavzu_sahifalari(maqolalar)
    tugmalar = "\n".join(
        f'          <a class="tag" href="mavzu/{slug}.html">{e(nom)}<span class="soni">{soni}</span></a>'
        for nom, soni, slug in mavzular[:18])
    belgilar_orasiga(SITE / "index.html", "mavzular", tugmalar)

    sahifa = galereya_sahifasi()
    if sahifa:
        (SITE / "galereya.html").write_text(sahifa, encoding="utf-8")

    print(f"{len(maqolalar)} ta maqola sahifasi yasaldi")
    print(f"qidiruv.json: {qidiruv_yasash(maqolalar)} KB")
    print(f"sitemap.xml: {sitemap_yasash()} ta sahifa")

    xatolar = havolalarni_tekshirish()
    if xatolar:
        print(f"\nDIQQAT: {len(xatolar)} ta havola muammosi:")
        for x in sorted(set(xatolar))[:12]:
            print("  -", x)


if __name__ == "__main__":
    main()
