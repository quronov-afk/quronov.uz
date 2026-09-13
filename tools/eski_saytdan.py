"""Eski quronov.narod.ru saytidan materiallarni ajratib oladi.

Eski quronov.uz serveri o'chgan, ammo undan oldingi narod.ru sayti saqlanib
qolgan. Bu skript o'sha sahifalardan matnlarni olib, data/eski_sayt.json ga
yozadi va qaysilari maqolalar to'plamlarida yo'qligini ko'rsatadi.

Ishlatish:  python3 tools/eski_saytdan.py <yuklangan_papka>
"""

import difflib, html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import lotinga as imloli_lotin

ROOT = Path(__file__).resolve().parent.parent
NAV = ["Quronov", "Home", "Yangiliklar", "Photos", "Kutubxona", "Biz haqimizda",
       "Mehmon", "Bog'lanish", "Dilmurod Quronov", "Sa'dullo Quronov",
       "Copyright", "Sayt yangilandi"]

BOLIM = {"dmaq": ("Dilmurod Quronov", "Maqola"), "dmaqk": ("Dilmurod Quronov", "Maqola"),
         "dsuh": ("Dilmurod Quronov", "Suhbat"), "dsoz": ("Dilmurod Quronov", "So'z boshi"),
         "dkit": ("Dilmurod Quronov", "Kitob"), "dkitk": ("Dilmurod Quronov", "Kitob"),
         "smaq": ("Sa'dullo Quronov", "Maqola"), "smaqk": ("Sa'dullo Quronov", "Maqola"),
         "ssuh": ("Sa'dullo Quronov", "Suhbat"), "skid": ("Sa'dullo Quronov", "Kitob"),
         "mod": ("—", "Maqola"), "pos": ("—", "Maqola")}


def oqi(fayl):
    """Sahifa UTF-8 yoki cp1251 kodlashda bo'lishi mumkin."""
    raw = fayl.read_bytes()
    try:
        s = raw.decode("utf-8")
        if "�" not in s:
            return s
    except UnicodeDecodeError:
        pass
    return raw.decode("cp1251", errors="replace")


def apostrof(s):
    s = re.sub(r"([oOgG])[‘’'`]", lambda m: m.group(1) + "ʻ", s)
    return s.replace("’", "ʼ").replace("‘", "ʻ")


def matnlar(fayl):
    s = oqi(fayl)
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", body))
    qatorlar = [q.strip() for q in t.splitlines() if q.strip()]
    # navigatsiyadan keyingi qism
    boshi = 0
    for i, q in enumerate(qatorlar):
        if q.startswith("Bog'lanish") or q.startswith("Bogʻlanish"):
            boshi = i + 1
            break
    qolgan = [q for q in qatorlar[boshi:]
              if not any(q.startswith(n) for n in NAV) and "Copyright" not in q]
    if not qolgan:
        return None, []
    sarlavha = qolgan[0]
    tana = yon_havolasiz([apostrof(q) for q in qolgan[1:] if len(q) > 40])
    # sarlavhadan keyingi bibliografik qator matn emas, manba ma'lumoti
    manba = None
    if tana and "//" in tana[0] and len(tana[0]) < 260:
        manba = re.sub(r"\s+", " ", tana.pop(0)).strip(" .")
    return sarlavha_tozala(apostrof(sarlavha)), tana, manba


ATOQLI = ["Choʻlpon", "Qodiriy", "Navoiy", "Bobur", "Oripov", "Hamza", "Oybek"]


def sarlavha_tozala(s):
    """«E H T I R O M» → «Ehtirom», ortiqcha bo'shliqlarni olib tashlaydi."""
    s = re.sub(r"\s+", " ", s).strip(" .,-–—")
    tokenlar = s.split()
    if len(tokenlar) > 2 and sum(len(t) == 1 for t in tokenlar) / len(tokenlar) > 0.7:
        s = "".join(tokenlar)
    harflar = [c for c in s if c.isalpha()]
    if harflar and sum(c.isupper() for c in harflar) / len(harflar) > 0.6:
        s = s.lower()
        for i, c in enumerate(s):
            if c.isalpha():
                s = s[:i] + c.upper() + s[i + 1:]
                break
        for atoq in ATOQLI:
            s = re.sub(rf"\b{atoq.lower()}", atoq, s)
    return s


def norm(s):
    s = re.sub(r"[^\w\s]", " ", s.lower().replace("ʻ", "").replace("ʼ", ""))
    return re.sub(r"\s+", "", s)


# eski sayt yon ustunidagi havolalar va rukn menyusi maqola oxiriga yopishib qolgan
YON_HAVOLALAR = {norm(s) for s in (
    "Suhbatlar, nutqlar, soʻz boshilar, taqrizlar",
    "Ilk avval koʻzimni ishq bilan ochdim...",
    "A.Oripovning 60-yillar sheʼriyatida tarix konsepsiyasi",
    "А.Ориповнинг 60-йиллар шеъриятида тарих консепсияси",
    "Hozirgi sheʼriyatning tasviriy imkoniyatlari haqida",
    "«Fusuli arbaa» qasidalar majmuasida badiiy sintez masalasi",
)}


def yon_havolasiz(tana):
    tana = list(tana)
    while tana and norm(tana[-1]) in YON_HAVOLALAR:
        tana.pop()
    return tana


def main():
    papka = Path(sys.argv[1])
    bor = json.loads((ROOT / "data" / "maqolalar.json").read_text(encoding="utf-8"))
    bor_kalit = [(norm(m["title"]), norm(" ".join(m["matn"])[:400])) for m in bor]

    topilgan = []
    for fayl in sorted(papka.glob("*.html")):
        m = re.fullmatch(r"([a-z]+?)(k?)(\d+)\.html", fayl.name)
        if not m:
            continue
        bolim = BOLIM.get(m.group(1) + m.group(2))
        if not bolim:
            continue
        sarlavha, tana, manba_qatori = matnlar(fayl)
        if not sarlavha or len("".join(tana)) < 700:
            continue
        muallif, janr = bolim
        kirill = bool(re.search(r"[а-яёқғҳў]", sarlavha, re.I))

        solish_s = lotinga(sarlavha) if kirill else sarlavha
        solish_m = lotinga(" ".join(tana)[:400]) if kirill else " ".join(tana)[:400]
        # takrorlik faqat o'sha muallifning saytdagi materiallari bilan solishtiriladi
        eng = 0 if muallif != "Dilmurod Quronov" else max(
            (max(difflib.SequenceMatcher(None, norm(solish_s), a).ratio(),
                 difflib.SequenceMatcher(None, norm(solish_m), b).ratio())
             for a, b in bor_kalit), default=0)

        topilgan.append({
            "fayl": fayl.name,
            "sarlavha": sarlavha,
            "muallif": muallif,
            "janr": janr,
            "yozuv": "kirill" if kirill else "lotin",
            "belgi": len("".join(tana)),
            "bor_ekan": round(eng, 2),
            "manba_qatori": manba_qatori,
            "matn": tana,
        })

    (ROOT / "data" / "eski_sayt.json").write_text(
        json.dumps(topilgan, ensure_ascii=False, indent=1), encoding="utf-8")

    juftlar = juftlash(topilgan)
    yangi = [j for j in juftlar if j["bor_ekan"] < 0.6]
    print(f"eski saytdan {len(topilgan)} ta sahifa olindi → {len(juftlar)} ta material, "
          f"shundan {len(yangi)} tasi bizda yo'q\n")
    for j in sorted(juftlar, key=lambda x: (x["muallif"], x["janr"], x["sarlavha"])):
        belgi = "YANGI" if j["bor_ekan"] < 0.6 else "bor  "
        yozuv = "lot+kir" if j.get("matn_kir") and j.get("matn") else \
                ("kir" if j.get("matn_kir") else "lot")
        print(f"  {belgi} {j['muallif'][:8]:<8} {j['janr']:<10} {yozuv:<8} "
              f"{j['belgi']:>6}  {j['sarlavha'][:52]}")

    chiqar(yangi)


def juftlash(topilgan):
    """Bir maqolaning lotin va kirill sahifalarini birlashtiradi."""
    lotin = [t for t in topilgan if t["yozuv"] == "lotin"]
    kirill = [t for t in topilgan if t["yozuv"] == "kirill"]
    ishlatilgan, natija = set(), []

    for t in lotin:
        kalit = norm(lotinga(t and " ".join([])) or "")  # joy egallaydi
        eng, eng_n = None, 0
        for k in kirill:
            if k["fayl"] in ishlatilgan:
                continue
            n = difflib.SequenceMatcher(
                None, norm(lotinga(k["sarlavha"])), norm(t["sarlavha"])).ratio()
            if n > eng_n:
                eng, eng_n = k, n
        if eng and eng_n > 0.72:
            ishlatilgan.add(eng["fayl"])
            natija.append({**t, "matn_kir": eng["matn"], "sarlavha_kir": eng["sarlavha"],
                           "belgi": max(t["belgi"], eng["belgi"])})
        else:
            natija.append({**t, "matn_kir": None, "sarlavha_kir": None})

    for k in kirill:
        if k["fayl"] not in ishlatilgan:
            natija.append({**k, "matn_kir": k["matn"], "sarlavha_kir": k["sarlavha"],
                           "matn": None})
    return natija


KIR_LOT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
           "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
           "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
           "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
           "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "қ": "q", "ғ": "g",
           "ҳ": "h"}


def lotinga(s):
    return "".join(KIR_LOT.get(c.lower(), c.lower()) for c in s)


def chiqar(yangi):
    """Bizda yo'q materiallarni sayt uchun tayyor ko'rinishda yozadi."""
    yozuvlar = []
    for j in yangi:
        if j["janr"] == "Kitob":  # kitoblar alohida bo'lim, hozircha olinmaydi
            continue
        kir = j.get("matn_kir")
        lat = j.get("matn") or ([imloli_lotin(p) for p in kir] if kir else None)
        # eski sayt kodlashi buzilgan lotin matn («soСz», «OТzMU») — toza kirillchadan olinadi
        if lat and kir and len(re.findall(r"[a-zA-Z][СТУФЦ][a-zA-Z]|[СТ][a-z]|[УФ]", " ".join(lat))) > 10:
            lat = [imloli_lotin(p) for p in kir]
        sarlavha = j["sarlavha"] if j.get("matn") else imloli_lotin(j["sarlavha"])
        yozuvlar.append({
            "slug": re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-",
                           lotinga(sarlavha).lower().replace("ʻ", "").replace("ʼ", ""))).strip("-")[:60],
            "title": sarlavha,
            "title_kir": j.get("sarlavha_kir") or (j["sarlavha"] if not lat else None),
            "muallif": j["muallif"],
            "janr": j["janr"],
            "manba_sayt": "quronov.narod.ru arxivi",
            "manba_qatori": j.get("manba_qatori"),
            "matn": lat,
            "matn_kir": kir,
            "belgi": j["belgi"],
        })
    (ROOT / "data" / "eski_maqolalar.json").write_text(
        json.dumps(yozuvlar, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\ndata/eski_maqolalar.json: {len(yozuvlar)} ta material")


if __name__ == "__main__":
    main()
