"""«quronov.uz materiallar» papkasidagi nutq, suhbat, so'z boshi va taqrizlarni oladi.

Maqolalar to'plam-kitoblardan olingani uchun bu yerda faqat qolgan janrlar
yig'iladi. Saytda allaqachon bor materiallar o'tkazib yuboriladi.

Ishlatish:  python3 tools/materiallardan.py
Natija:     data/qolgan_materiallar.json
"""

import difflib, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import lotinga, norm, slugify, bibliografiya, asl_manba, sarlavha_tozalash
from eski_saytdan import sarlavha_tozala

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "quronov.uz materiallar"

PAPKALAR = {"нутк": "Nutq", "сухбат": "Suhbat", "сщз боши": "So'z boshi",
            "такриз": "Taqriz"}

MUALLIF_RE = re.compile(r"(Қуронов|Каримов|Ҳамроқулов|Нурмонов|Полвонова|Мамажонов)")
OTKAZ_RE = re.compile(r"^(\*+|УДК|UDK|Таянч сўзлар)", re.I)


def matn(fayl):
    r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(fayl)],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def sarlavha_va_tana(text):
    qatorlar = [q.strip() for q in text.splitlines() if q.strip()]
    sarlavha, boshi = None, 0
    for i, q in enumerate(qatorlar):
        if OTKAZ_RE.match(q) or (MUALLIF_RE.search(q) and len(q) < 70):
            continue
        if len(q) < 3:
            continue
        sarlavha, boshi = q, i + 1
        break
    tana = [re.sub(r"\s+", " ", q).strip() for q in qatorlar[boshi:] if len(q.strip()) > 40]
    return sarlavha, tana


def bor_ekan(sarlavha, tana, mavjud):
    kalit_s, kalit_m = norm(sarlavha), norm(" ".join(tana)[:400])
    return max((max(difflib.SequenceMatcher(None, kalit_s, a).ratio(),
                    difflib.SequenceMatcher(None, kalit_m, b).ratio())
                for a, b in mavjud), default=0)


def main():
    mavjud = []
    for nom in ("maqolalar.json", "eski_maqolalar.json"):
        fayl = ROOT / "data" / nom
        if fayl.exists():
            for m in json.loads(fayl.read_text(encoding="utf-8")):
                if m.get("muallif") and m["muallif"] != "Dilmurod Quronov":
                    continue
                mavjud.append((norm(m["title"]), norm(" ".join(m["matn"])[:400])))

    yozuvlar = bibliografiya()
    natija = []
    for papka, janr in PAPKALAR.items():
        d = SRC / papka
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in (".doc", ".docx", ".rtf"):
                continue
            text = matn(f)
            sarlavha_kir, tana_kir = sarlavha_va_tana(text)
            if not sarlavha_kir or len("".join(tana_kir)) < 900:
                continue

            sarlavha = sarlavha_tozala(sarlavha_tozalash(lotinga(sarlavha_kir)))
            sarlavha_kir = sarlavha_tozala(sarlavha_kir)
            tana = [lotinga(p) for p in tana_kir]
            nisbat = bor_ekan(sarlavha, tana, mavjud)
            asl = asl_manba(sarlavha_kir, yozuvlar)

            natija.append({
                "slug": slugify(sarlavha),
                "title": sarlavha,
                "title_kir": sarlavha_kir,
                "muallif": "Dilmurod Quronov",
                "janr": janr,
                "yil": asl["yil"] if asl else None,
                "asl_manba": asl["manba"] if asl else None,
                "manba_sayt": "shaxsiy arxiv",
                "matn": tana,
                "matn_kir": tana_kir,
                "belgi": len("".join(tana_kir)),
                "bor_ekan": round(nisbat, 2),
            })

    yangi = [n for n in natija if n["bor_ekan"] < 0.6]
    (ROOT / "data" / "qolgan_materiallar.json").write_text(
        json.dumps(yangi, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(natija)} ta fayl ko'rildi, {len(yangi)} tasi yangi\n")
    for n in natija:
        belgi = "YANGI" if n["bor_ekan"] < 0.6 else "bor  "
        yil = n["yil"] or "????"
        print(f"  {belgi} {n['janr']:<10} {yil}  {n['belgi']:>6}  {n['title'][:50]}")


if __name__ == "__main__":
    main()
