"""Maqolalar to'plami (PDF) ichidan alohida maqolalarni ajratib oladi.

Ishlatish:  python3 tools/kitobdan.py
Natija:     data/maqolalar.json  — har bir maqola kirill va lotin yozuvida

Matn tahrir qilinmaydi: faqat PDF'dan o'qishda buzilgan joylar (eski shrift
kodlashi, satr oxiridagi ko'chirish chizig'i) tiklanadi va lotinga o'giriladi.
"""

import difflib, json, re, subprocess, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "D.Quronov kitoblar_PDF"

# eski shrift kodlashini tiklash jadvallari
CP1251_FIX = "cp1251"
ITV_FIX = str.maketrans({"і": "ҳ", "І": "Ҳ", "ї": "қ", "Ї": "Қ",
                         "є": "ў", "Є": "Ў", "ў": "ғ", "Ў": "Ғ"})

KITOBLAR = [
    {"fayl": "Мутолаа ва идрок машқлари.pdf", "nom": "Mutolaa va idrok mashqlari",
     "yil": 2013, "tuzatish": None, "mundarija": 335},
    {"fayl": "Талқин имконлари.pdf", "nom": "Talqin imkonlari",
     "yil": 2015, "tuzatish": None, "mundarija": 87},
    {"fayl": "Назарий кайдлар.pdf", "nom": "Nazariy qaydlar",
     "yil": 2018, "tuzatish": None, "mundarija": 127},
    {"fayl": "Адабий уйлар.pdf", "nom": "Adabiy o'ylar",
     "yil": 2016, "tuzatish": CP1251_FIX, "mundarija": 112},
    {"fayl": "Завкимдан бир шингил.pdf", "nom": "Zavqimdan bir shingil",
     "yil": 2013, "tuzatish": "itv", "mundarija": 64},
    {"fayl": "Adabiyot va b....pdf", "nom": "Adabiyot va b. haqida",
     "yil": 2019, "tuzatish": None, "mundarija": 127, "lotin": True},
]

UNLI = set("аеёиоуўэюяaeiouoʻ")

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ч": "ch", "ш": "sh",
    "щ": "sh", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "oʻ", "қ": "q",
    "ғ": "gʻ", "ҳ": "h",
}


def pdf_pages(path, tuzatish):
    raw = subprocess.run(["pdftotext", "-layout", "-q", str(path), "-"],
                         capture_output=True).stdout.decode("utf-8", "replace")
    pages = raw.split("\f")
    if tuzatish == CP1251_FIX:
        pages = [_cp1251(p) for p in pages]
    elif tuzatish == "itv":
        pages = [p.translate(ITV_FIX) for p in pages]
    return pages


def _cp1251(s):
    out = []
    for c in s:
        if 0x80 <= ord(c) <= 0xFF:
            try:
                out.append(c.encode("latin1").decode("cp1251"))
            except UnicodeError:
                out.append(c)
        else:
            out.append(c)
    return "".join(out)


def norm(s):
    s = re.sub(r"[^\w\s]", " ", s.lower().replace("ʻ", "").replace("'", ""))
    return re.sub(r"\s+", "", s)


def parse_mundarija(page):
    """Mundarija sahifasidan maqola nomlarini oladi (ko'chirilgan satrlarni qo'shib)."""
    nomlar, oldingi = [], ""
    for line in page.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"[\d\s.]+", line):
            continue
        if re.match(r"(МУНДАРИЖА|MUNDARIJA|Мундарижа|Mundarija)", line):
            nomlar, oldingi = [], ""
            continue
        if re.search(r"(нашр|Муҳаррир|Мусаҳҳиҳ|босишга|Нашриёт|ISBN|УДК|КБК)", line, re.I):
            break
        nuqta = re.search(r"\s*\.{3,}", line)
        if nuqta:
            nom = (oldingi + " " + line[:nuqta.start()]).strip()
            oldingi = ""
            nom = re.sub(r"\s+", " ", nom).strip(" .")
            raqam = re.search(r"(\d{1,3})\s*$", line)
            if len(nom) > 4:
                nomlar.append((nom, int(raqam.group(1)) if raqam else None))
        else:
            oldingi = (oldingi + " " + line).strip()
    return nomlar


def sarlavha_joyi(pages, nom, boshlanish, oxiri=None):
    """Maqola sarlavhasi turgan sahifa va satrni topadi (eng birinchi mosini)."""
    kalit = norm(nom)
    eng_yaxshi = None
    for p in range(boshlanish, min(oxiri or len(pages), len(pages))):
        lines = [l.strip() for l in pages[p].splitlines()]
        for i, line in enumerate(lines):
            if not line or len(line) < 4:
                continue
            # sarlavha 1-3 qatorga bo'lingan bo'lishi mumkin: eng mos variant olinadi
            birikma, nomzod = line, None
            for j in range(1, 4):
                n = norm(birikma)
                if not n:
                    break
                nisbat = difflib.SequenceMatcher(None, n, kalit).ratio()
                if nomzod is None or nisbat > nomzod[2] + 0.02:
                    nomzod = (p, i + j - 1, nisbat, i)
                if i + j < len(lines):
                    birikma = birikma + " " + lines[i + j].strip()
                else:
                    break
            if nomzod and nomzod[2] > 0.9:
                return nomzod[0], nomzod[1], nomzod[3]
            if nomzod and nomzod[2] > 0.8 and (eng_yaxshi is None or nomzod[2] > eng_yaxshi[2]):
                eng_yaxshi = nomzod
    # (sahifa, sarlavhaning oxirgi qatori, sarlavhaning birinchi qatori)
    return (eng_yaxshi[0], eng_yaxshi[1], eng_yaxshi[3]) if eng_yaxshi else None


def joylarni_topish(pages, nomlar, mundarija_sahifa):
    """Mundarijadagi sahifa raqamlaridan foydalanib har bir maqolaning o'rnini topadi."""
    surish = None
    for nom, raqam in nomlar:  # bosma sahifa raqami bilan PDF sahifasi orasidagi farq
        if raqam is None:
            continue
        joy = sarlavha_joyi(pages, nom, 0, mundarija_sahifa)
        if joy:
            surish = joy[0] - (raqam - 1)
            break

    joylar, qidiruv = [], 0
    for nom, raqam in nomlar:
        joy = None
        if raqam is not None and surish is not None:
            taxmin = raqam - 1 + surish
            joy = sarlavha_joyi(pages, nom, max(0, taxmin - 3),
                                min(taxmin + 5, mundarija_sahifa))
        if joy is None:
            joy = sarlavha_joyi(pages, nom, qidiruv, mundarija_sahifa)
        if joy:
            joylar.append((nom, joy))
            qidiruv = joy[0]
        else:
            print(f"   topilmadi: {nom[:55]}")
    return joylar


def defisli_sozlar(pages):
    """Satr ichida (ko'chirilmagan holda) uchraydigan chiziqchali so'zlar to'plami."""
    topilgan = set()
    for page in pages:
        for line in page.splitlines():
            for m in re.finditer(r"(\w+)-(\w+)", line):
                if m.end() < len(line.rstrip()):  # satr oxiri emas
                    topilgan.add(m.group(0).lower())
    return topilgan


def defis_tiklash(matn, defisli):
    """Satr oxirida ko'chirilgan so'zlarni birlashtiradi.

    Chiziqcha faqat o'sha birikma kitobning boshqa joyida ham chiziqcha bilan
    yozilgan bo'lsa saqlanadi (masalan «ijtimoiy-tarixiy»), aks holda so'z
    ko'chirilgan deb hisoblanib qo'shib yoziladi («o'zi-\\nning» → «o'zining»).
    """
    def almash(m):
        chap, ong = m.group(1), m.group(2)
        if f"{chap}-{ong}".lower() in defisli:
            return f"{chap}-{ong}"
        return chap + ong
    matn = re.sub(r"(\w+)-\s*\n\s*(\w+)", almash, matn)
    # tirnoqdan keyingi qo'shimcha: «...»- ni → «...»-ni
    return re.sub(r"([»”\"'\)])-\s*\n\s*(\w+)", r"\1-\2", matn)


RAQAM_QATOR = re.compile(r"\s*\d{1,3}\s*")
USTKI = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
IZOH_BELGI = re.compile(r"⁅\d+\.\d+⁆")


def izohlarni_ajrat(page, sahifa):
    """Sahifa pastidagi izohlarni (snoskalarni) asosiy matndan ajratadi.

    PDF'da izoh bloki: yolgʻiz raqamli qator («18»), undan keyin izoh matni; eng oxirida
    sahifa raqami. Matndagi havola raqami («…gan19») ⁅sahifa.raqam⁆ belgisiga almashtiriladi.
    Sahifa raqami ham olib tashlanadi — aks holda boʻlingan soʻzga yopishadi («maса-/4/ласига»).
    Qaytaradi: (izohsiz sahifa matni, {belgi: (izoh matni, havolasi topildimi)}).
    """
    lines = page.split("\n")
    oxirgi = len(lines)
    while oxirgi and not lines[oxirgi - 1].strip():
        oxirgi -= 1
    pastki = oxirgi - 1 if oxirgi and RAQAM_QATOR.fullmatch(lines[oxirgi - 1]) else oxirgi
    izohsiz = "\n".join(lines[:pastki])

    raqamli = [j for j in range(pastki) if RAQAM_QATOR.fullmatch(lines[j])]
    boshi = None
    for j in raqamli:
        keyingi = next((l for l in lines[j + 1:pastki] if l.strip()), None)
        if keyingi is None or RAQAM_QATOR.fullmatch(keyingi):
            continue
        qolgan = [int(lines[k]) for k in raqamli if k >= j]
        if qolgan == list(range(qolgan[0], qolgan[0] + len(qolgan))):
            boshi = j
            break
    if boshi is None:
        return izohsiz, {}

    izohlar, joriy = {}, None
    for l in lines[boshi:pastki]:
        if RAQAM_QATOR.fullmatch(l):
            joriy = int(l)
            izohlar[joriy] = []
        elif l.strip():
            izohlar[joriy].append(l.strip())

    tana = "\n".join(lines[:boshi]).rstrip()
    natija, joy = {}, 0
    for n in sorted(izohlar):
        matn = re.sub(r"(\w)-\n(\w)", r"\1\2", "\n".join(izohlar[n])).replace("\n", " ")
        belgi = f"⁅{sahifa}.{n}⁆"
        # raqam soʻz yoki tinish belgisiga yopishgan boʻladi: «…di»gan19», «davri46deb»
        havola = re.compile(rf"(?<=[^\s\d№/(\[–-]){n}(?!\d)").search(tana, joy)
        if not havola and not natija:
            # birinchi raqamning havolasi yoʻq — bu izoh emas (masalan, sheʼrdagi misra raqamlari)
            return izohsiz, {}
        if havola:
            tana = tana[:havola.start()] + belgi + tana[havola.end():]
            joy = havola.start() + len(belgi)
        natija[belgi] = (re.sub(r"\s+", " ", matn).strip(), bool(havola))
    return tana, natija


def izohlarni_joyla(lat, kir, baza, lotin):
    """⁅sahifa.raqam⁆ belgilarini maqola ichida 1 dan raqamlangan ustki raqamlarga aylantiradi."""
    tartib = {}
    for p in lat:
        for belgi in IZOH_BELGI.findall(p):
            tartib.setdefault(belgi, len(tartib) + 1)

    def almash(p):
        return IZOH_BELGI.sub(lambda t: str(tartib.get(t.group(0), "")).translate(USTKI), p)

    izoh_lat, izoh_kir = [], []
    for belgi in tartib:
        matn = baza[belgi][0]
        if lotin:
            l = imlo_tuzat(apostrof(matn))
            k = kirillga(l)
        else:
            k, l = matn, imlo_tuzat(lotinga(matn))
        izoh_lat.append(l)
        izoh_kir.append(k)
    return [almash(p) for p in lat], [almash(p) for p in kir], izoh_lat, izoh_kir


def abzaclar(matn):
    """Chekinish bo'yicha abzaclarga ajratadi."""
    band, natija = [], []
    for line in matn.splitlines():
        if not line.strip():
            continue
        if re.fullmatch(r"[\s\d]+", line):  # sahifa raqami
            continue
        if re.match(r"^\s{2,}\S", line) and band:
            natija.append(" ".join(band))
            band = []
        band.append(line.strip())
    if band:
        natija.append(" ".join(band))
    return [re.sub(r"\s+", " ", p).strip() for p in natija if len(p.strip()) > 1]


def lotinga(s):
    """Kirill matnini o'zbek lotin yozuviga o'giradi."""
    natija = []
    for soz in re.split(r"(\W+)", s):
        if not soz or not re.search(r"[а-яёқғҳўА-ЯЁҚҒҲЎ]", soz):
            natija.append(soz)
            continue
        katta = soz.isupper() and len(soz) > 1
        harflar = []
        for i, ch in enumerate(soz):
            past = ch.lower()
            oldingi = soz[i - 1].lower() if i else ""
            if past == "е":
                rep = "ye" if (i == 0 or oldingi in UNLI or oldingi in "ъь") else "e"
            elif past == "ц":
                # imlo qoidasi: unlidan keyin «ts», aks holda «s» (konsepsiya, retseptiv)
                rep = "ts" if oldingi in UNLI else "s"
            elif past == "ъ":
                rep = "" if i + 1 < len(soz) and soz[i + 1].lower() in "еёюя" else "ʼ"
            else:
                rep = TRANSLIT.get(past, ch)
            if ch.isupper() and rep:
                rep = rep.upper() if katta else rep[0].upper() + rep[1:]
            harflar.append(rep)
        natija.append("".join(harflar))
    return "".join(natija)


# kirillchaga oʻgirilmaydigan xalqaro qisqartmalar
LOTINCHA_QOLADI = ("PhD", "DSc", "ISBN", "UDK", "PDF")

# oʻgirishdan keyingi imlo tuzatishlari
KIRILL_TUZAT = {"консепси": "концепци", "консепц": "концепц"}


def kirillga(s):
    """Lotin yozuvidagi kitob uchun: teskari o'girish (taxminiy)."""
    # uch harfli birikmalar oldin tekshiriladi: «yoʻl» → «йўл» («ёʻл» emas)
    uchliklar = [("yoʻ", "йў"), ("yo‘", "йў"), ("ygʻ", "йғ"), ("yg‘", "йғ"),
                 ("tsh", "тш")]  # «adabiyotshunos» → «ц» boʻlib ketmasligi uchun
    juftlar = [("oʻ", "ў"), ("o‘", "ў"), ("gʻ", "ғ"), ("g‘", "ғ"), ("ch", "ч"),
               ("sh", "ш"), ("ts", "ц"), ("ya", "я"), ("yo", "ё"), ("yu", "ю"),
               ("ye", "е")]
    bitta = {"a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
             "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
             "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
             "x": "х", "y": "й", "z": "з", "ʼ": "ъ", "’": "ъ"}
    out, i = [], 0
    while i < len(s):
        saqlangan = next((t for t in LOTINCHA_QOLADI if s.startswith(t, i)), None)
        if saqlangan:
            out.append(saqlangan)
            i += len(saqlangan)
            continue
        uchta = s[i:i + 3]
        mos3 = next((c for lat, c in uchliklar if uchta.lower() == lat), None)
        if mos3:
            out.append(mos3[0].upper() + mos3[1:] if s[i].isupper() else mos3)
            i += 3
            continue
        uch = s[i:i + 2]
        mos = next((c for lat, c in juftlar if uch.lower() == lat), None)
        if mos:
            out.append(mos.upper() if s[i].isupper() else mos)
            i += 2
            continue
        ch = s[i]
        rep = bitta.get(ch.lower())
        if ch.lower() == "e":  # so'z boshida «э», so'z ichida «е»
            rep = "э" if (i == 0 or not s[i - 1].isalpha()) else "е"
        if rep:
            out.append(rep.upper() if ch.isupper() else rep)
        else:
            out.append(ch)
        i += 1
    natija = "".join(out)
    for xato, togri in KIRILL_TUZAT.items():
        natija = natija.replace(xato, togri)
    return natija


ATOQLI = ["Andijon", "Bobur", "Choʻlpon", "Qodiriy", "Navoiy", "Zulfiya", "Hamza",
          "Oybek", "Toshkent", "Fransiya", "Gʻafur", "Gʻulom"]

# manbadagi terish xatolari (mazmun emas, imlo tuzatiladi)
IMLO = {"adibiyot": "adabiyot", "Adibiyot": "Adabiyot", "kompozision": "kompozitsion",
        "reseptiv": "retseptiv", "Reseptiv": "Retseptiv"}


def apostrof(s):
    """Turli tirnoq belgilarini yagona imlo belgilariga keltiradi."""
    s = re.sub(r"[оo]['‘’`ʼ]", "oʻ", s)
    s = re.sub(r"[ОO]['‘’`ʼ]", "Oʻ", s)
    s = re.sub(r"g['‘’`ʼ]", "gʻ", s)
    s = re.sub(r"G['‘’`ʼ]", "Gʻ", s)
    return s.replace("’", "ʼ").replace("‘", "ʻ")


def imlo_tuzat(s):
    for xato, togri in IMLO.items():
        s = s.replace(xato, togri)
    return s


def sarlavha_tozalash(s):
    s = imlo_tuzat(apostrof(s)).strip(" .,-–—")
    for atoq in ATOQLI:
        s = re.sub(rf"\b{atoq.lower()}\b", atoq, s)
    return s


def slugify(s):
    s = s.lower().replace("ʻ", "").replace("’", "").replace("ʼ", "")
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")[:60]


BIBL = ROOT / "quronov.uz materiallar" / \
    "ПРОФЕССОРИ ДИЛМУРОД ҚУРОНОВНИНГ ЭЪЛОН ҚИЛИНГАН ИЛМИЙ ИШЛАРИ РЎЙХАТИ.docx"


def bibliografiya():
    """Olimning e'lon qilingan ishlari ro'yxatidan (sarlavha, manba, yil) oladi."""
    matn = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(BIBL)],
                          capture_output=True).stdout.decode("utf-8", "replace")
    yozuvlar = []
    for line in matn.splitlines():
        m = re.match(r"^\d+\.\s+(.*)$", line.strip())
        if not m:
            continue
        tana = m.group(1).strip()
        yillar = re.findall(r"\b(19\d{2}|20\d{2})\b", tana)
        bolak = re.split(r"(?<=[а-яёқғҳўa-z…\"”»?])\.\s+", tana, maxsplit=1)
        yozuvlar.append({
            "nom": bolak[0].strip(" ."),
            "manba": bolak[1].strip() if len(bolak) > 1 else "",
            "yil": int(yillar[0]) if yillar else None,
        })
    return yozuvlar


def asl_manba(nom_kir, yozuvlar):
    """Maqolaning dastlab qayerda chiqqanini ro'yxatdan topadi."""
    kalit = norm(nom_kir)
    eng = (0, None)
    for y in yozuvlar:
        ynom = norm(y["nom"])
        n = max(difflib.SequenceMatcher(None, kalit, ynom).ratio(),
                difflib.SequenceMatcher(None, kalit, ynom[:len(kalit) + 4]).ratio())
        if n > eng[0]:
            eng = (n, y)
    return eng[1] if eng[0] > 0.82 else None


def main():
    yozuvlar = bibliografiya()
    hammasi = []
    for kitob in KITOBLAR:
        pages = pdf_pages(PDF_DIR / kitob["fayl"], kitob["tuzatish"])
        izoh_bazasi = {}
        for i in range(kitob["mundarija"] - 1):
            pages[i], izohlar = izohlarni_ajrat(pages[i], i + 1)
            izoh_bazasi.update(izohlar)
        yetim = [b for b, (_, topildi) in izoh_bazasi.items() if not topildi]
        print(f"   izohlar: {len(izoh_bazasi)}, havolasi topilmagan: {len(yetim)} {yetim[:6]}")
        mund = pages[kitob["mundarija"] - 1]
        nomlar = parse_mundarija(mund)
        print(f"\n{kitob['nom']}: mundarijada {len(nomlar)} ta nom")

        defisli = defisli_sozlar(pages)

        joylar = joylarni_topish(pages, nomlar, kitob["mundarija"] - 1)

        for idx, (nom, (p, satr, bosh)) in enumerate(joylar):
            # havolasi sarlavhaning oʻzida turgan izoh (masalan, hammualliflik haqida)
            sarlavha_qatorlari = "\n".join(pages[p].splitlines()[bosh:satr + 1])
            sarlavha_izohi = [izoh_bazasi[b][0] for b in IZOH_BELGI.findall(sarlavha_qatorlari)]
            # keyingi maqola sarlavhasining birinchi qatorigacha olinadi
            oxiri = joylar[idx + 1][1] if idx + 1 < len(joylar) else (kitob["mundarija"] - 1, 0, 0)
            if oxiri[0] == p:
                bolaklar = ["\n".join(pages[p].splitlines()[satr + 1:oxiri[2]])]
            else:
                bolaklar = ["\n".join(pages[p].splitlines()[satr + 1:])]
            for q in range(p + 1, oxiri[0]):
                bolaklar.append(pages[q])
            if oxiri[0] > p:
                bolaklar.append("\n".join(pages[oxiri[0]].splitlines()[:oxiri[2]]))
            matn = defis_tiklash("\n".join(bolaklar), defisli)
            banda = abzaclar(matn)
            if len("".join(banda)) < 900:
                print(f"   qisqa, o'tkazildi: {nom[:50]}")
                continue

            if kitob.get("lotin"):
                banda = [imlo_tuzat(apostrof(b)) for b in banda]
                lat_nom = sarlavha_tozalash(nom)
                kir_nom = kirillga(lat_nom)
                lat, kir = banda, [kirillga(b) for b in banda]
            else:
                lat_nom, kir_nom = sarlavha_tozalash(lotinga(nom)), nom
                lat, kir = [imlo_tuzat(lotinga(b)) for b in banda], banda
            lat, kir, izoh_lat, izoh_kir = izohlarni_joyla(lat, kir, izoh_bazasi, kitob.get("lotin"))
            tagsarlavha = None
            if sarlavha_izohi:
                matn = " ".join(sarlavha_izohi)
                tagsarlavha = imlo_tuzat(apostrof(matn) if kitob.get("lotin") else lotinga(matn))
                print(f"   sarlavha izohi: {lat_nom[:40]} — {tagsarlavha}")

            asl = asl_manba(kir_nom, yozuvlar)
            janr = "Suhbat" if re.search(r"суҳбат|suhbat", nom, re.I) else "Maqola"
            hammasi.append({
                "slug": slugify(lat_nom),
                "title": lat_nom,
                "title_kir": kir_nom,
                "janr": janr,
                "kitob": kitob["nom"],
                "yil": asl["yil"] if asl and asl["yil"] else kitob["yil"],
                "kitob_yili": kitob["yil"],
                "asl_manba": asl["manba"] if asl else None,
                "sahifa": p + 1,
                "belgi": len("".join(banda)),
                "matn": lat,
                "matn_kir": kir,
                "izohlar": izoh_lat,
                "izohlar_kir": izoh_kir,
                "tagsarlavha": tagsarlavha,
            })

    korilgan = set()
    yakuniy = []
    for m in sorted(hammasi, key=lambda x: -x["belgi"]):
        kalit = norm(m["title"])[:40]
        if kalit in korilgan:
            continue
        korilgan.add(kalit)
        yakuniy.append(m)
    yakuniy.sort(key=lambda m: (m["kitob"], m["sahifa"]))

    (ROOT / "data" / "maqolalar.json").write_text(
        json.dumps(yakuniy, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nJami {len(yakuniy)} ta maqola yozildi")
    for m in yakuniy:
        print(f"  {m['yil']}  {m['belgi']:>6}  {m['title'][:58]}")


if __name__ == "__main__":
    main()
