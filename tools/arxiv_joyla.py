"""Arxivdan tiklangan sahifalarni saytga tayyor ko'rinishga keltiradi.

Har bir sahifa qaysi olimga va qaysi janrga tegishli ekani qo'lda belgilangan:
avtomatik aniqlash ishonchsiz, chunki «ular haqida» bo'limidagi matnlar ham
olimlarning o'z maqolalariga o'xshab ketadi.

Ishlatish:  python3 tools/arxiv_joyla.py
Natija:     data/arxiv_maqolalar.json
"""

import difflib, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import lotinga, norm, slugify, kirillga
from eski_saytdan import sarlavha_tozala

ROOT = Path(__file__).resolve().parent.parent
D, S = "Dilmurod Quronov", "Sa'dullo Quronov"

# fayl nomi → (kim haqida / kimning asari, janr, yozgan kishi, yil)
TASNIF = {
    # olimlar haqida yozilganlar
    "баҳодир-раҳмонов-тонг-юлдузидан-бо.html": (D, "Olim haqida", "Bahodir Rahmonov", None),
    "қозоқбой-йўлдош-уйғунлик.html": (D, "Olim haqida", "Qozoqboy Yoʻldosh", None),
    "галактикада-бир-кун-фантастик-аса.html": (S, "Olim haqida", None, None),
    "baxtiyor-sheraliyev-galaktikada-bir-kunni-bir-kechada-oqidim.html":
        (S, "Olim haqida", "Baxtiyor Sheraliyev", 2024),
    "qozoqboy-yoʻldoshev-galaktikada-bir-kun-haqida.html":
        (S, "Olim haqida", "Qozoqboy Yoʻldoshev", 2024),
    # tarjimai hollar
    "дилмурод-қуронов-ҳақида.html": (D, "Biografiya", None, None),
    "саъдулло-қуронов-ҳақида.html": (S, "Biografiya", None, None),
    # Sa'dullo Quronovning o'z maqolalari
    "постмодерн-оламда-манзил-излаб.html": (S, "Maqola", None, None),
    "замонавий-ўзбек-насри-ва-постмодерни.html": (S, "Maqola", None, None),
    "замонавий-ўзбек-шеъриятда-бадиий-син.html": (S, "Maqola", None, None),
    "43-yilga-kechikkan-adabiyot.html": (S, "Maqola", None, None),
    "avvalo-maqsadni-toʻgʻrilaylik.html": (S, "Maqola", None, None),
    "голливуд-сценаристлари-ҳам-доғда-қол.html": (S, "Taqriz", None, None),
    # sayt yangiliklari
    "дилмурод-куронов-ўзбекистон-республ.html": (D, "Yangilik", None, 2021),
    # Dilmurod Quronov maqolasining ingliz tilidagi nashri
    "the-friend-who-had-introduced-a-foe.html": (D, "Maqola (ingliz tilida)", None, None),
}


def mavjud_kalitlar():
    kalitlar = []
    for nom in ("maqolalar.json", "eski_maqolalar.json", "qolgan_materiallar.json",
                "skaner_maqolalar.json"):
        fayl = ROOT / "data" / nom
        if not fayl.exists():
            continue
        for m in json.loads(fayl.read_text(encoding="utf-8")):
            if m.get("matn"):
                kalitlar.append((norm(m["title"]), norm(" ".join(m["matn"])[:400])))
    return kalitlar


def kirill_kop(p):
    return len(re.findall(r"[а-яёўқғҳ]", p, re.I)) > len(p) * 0.3


def main():
    xom = {n["fayl"]: n for n in
           json.loads((ROOT / "data" / "arxiv_xom.json").read_text(encoding="utf-8"))}
    kalitlar = mavjud_kalitlar()
    natija = []

    for fayl, (olim, janr, yozgan, yil) in TASNIF.items():
        n = xom.get(fayl)
        if not n or n["belgi"] < 700:
            print(f"  topilmadi yoki qisqa: {fayl}")
            continue

        kirill = bool(re.search(r"[а-яёқғҳў]", n["sarlavha"], re.I))
        if kirill:
            sarlavha_kir = sarlavha_tozala(n["sarlavha"])
            sarlavha = sarlavha_tozala(lotinga(sarlavha_kir))
            matn_kir = n["matn"]
            matn = [lotinga(p) for p in matn_kir]
        else:
            sarlavha = sarlavha_tozala(n["sarlavha"])
            sarlavha_kir = kirillga(sarlavha)
            # lotin matn ichida kirillda qolgan xatboshilar ham lotinga oʻgiriladi
            matn = [lotinga(p) if kirill_kop(p) else p for p in n["matn"]]
            matn_kir = [p if kirill_kop(p) else kirillga(p) for p in n["matn"]]

        nisbat = max((max(difflib.SequenceMatcher(None, norm(sarlavha), a).ratio(),
                          difflib.SequenceMatcher(None, norm(" ".join(matn)[:400]), b).ratio())
                      for a, b in kalitlar), default=0)
        if nisbat > 0.6:
            print(f"  saytda bor: {sarlavha[:50]}")
            continue

        natija.append({
            "slug": slugify(sarlavha),
            "title": sarlavha,
            "title_kir": sarlavha_kir,
            "muallif": olim,
            "janr": janr,
            "yil": yil,
            "yozgan": yozgan,
            "manba_sayt": "quronov.uz arxivi",
            "matn": matn,
            "matn_kir": matn_kir,
            "belgi": n["belgi"],
        })
        print(f"  + {olim[:8]:<8} {janr:<20} {sarlavha[:46]}")

    (ROOT / "data" / "arxiv_maqolalar.json").write_text(
        json.dumps(natija, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(natija)} ta material tayyorlandi")


if __name__ == "__main__":
    main()
