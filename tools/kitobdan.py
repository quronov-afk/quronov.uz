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
                    nomzod = (p, i + j - 1, nisbat)
                if i + j < len(lines):
                    birikma = birikma + " " + lines[i + j].strip()
                else:
                    break
            if nomzod and nomzod[2] > 0.9:
                return nomzod[:2]
            if nomzod and nomzod[2] > 0.8 and (eng_yaxshi is None or nomzod[2] > eng_yaxshi[2]):
                eng_yaxshi = nomzod
    return eng_yaxshi[:2] if eng_yaxshi else None


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


def kirillga(s):
    """Lotin yozuvidagi kitob uchun: teskari o'girish (taxminiy)."""
    juftlar = [("oʻ", "ў"), ("o‘", "ў"), ("gʻ", "ғ"), ("g‘", "ғ"), ("ch", "ч"),
               ("sh", "ш"), ("ts", "ц"), ("ya", "я"), ("yo", "ё"), ("yu", "ю"),
               ("ye", "е")]
    bitta = {"a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
             "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
             "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
             "x": "х", "y": "й", "z": "з", "ʼ": "ъ", "’": "ъ"}
    out, i = [], 0
    while i < len(s):
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
    return "".join(out)


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
        mund = pages[kitob["mundarija"] - 1]
        nomlar = parse_mundarija(mund)
        print(f"\n{kitob['nom']}: mundarijada {len(nomlar)} ta nom")

        defisli = defisli_sozlar(pages)

        joylar = joylarni_topish(pages, nomlar, kitob["mundarija"] - 1)

        for idx, (nom, (p, satr)) in enumerate(joylar):
            oxiri = joylar[idx + 1][1] if idx + 1 < len(joylar) else (kitob["mundarija"] - 1, 0)
            bolaklar = ["\n".join(pages[p].splitlines()[satr + 1:])]
            for q in range(p + 1, oxiri[0]):
                bolaklar.append(pages[q])
            if oxiri[0] > p:
                bolaklar.append("\n".join(pages[oxiri[0]].splitlines()[:oxiri[1]]))
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
