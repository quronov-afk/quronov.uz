"""Skanerlangan (matn qatlami yo'q) PDF maqolalarni matnga o'giradi.

Sahifalar rasmga aylantirilib, Gemini modeliga berib o'qitiladi. Matn tahrir
qilinmaydi — model faqat ko'rgan matnini aynan ko'chirib yozadi. Natija
«tekshirilsin» belgisi bilan saqlanadi: skanerdan o'qilgan matnni keyin asl
nusxa bilan solishtirish kerak.

Ishlatish:  GEMINI_API_KEY=... python3 tools/skanerdan.py
"""

import base64, json, os, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import lotinga, slugify

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "quronov.uz materiallar" / "pdf"
MODEL = "gemini-3.1-pro-preview"

# Skanerda sarlavha aniq ko'rinmagan hollar uchun qo'lda kiritilgan ma'lumot
QOLDA = {
    "Yoshlik 1991 6-son": {
        "title_kir": "Икки роман – икки талқин",
        "janr": "Maqola", "yil": 1991,
        "asl_manba": "«Ёшлик», 1991, № 6, Б.28-32",
    },
    "Д.Қуронов 1988-6_": {
        "title_kir": "Кечмиш",
        "janr": "Asar", "yil": 1988,
        "asl_manba": "1988, № 6",
    },
}

KORSATMA = """Bu — o'zbek adabiy jurnalining skanerlangan sahifasi (kirill yozuvida).
Sahifadagi maqola matnini AYNAN ko'chirib yoz. Qoidalar:
- Hech narsani tahrir qilma, qisqartirma, tuzatma, izoh qo'shma.
- Faqat maqola matnini yoz: sarlavha, muallif ismi va abzaclar.
- Jurnal nomi, sahifa raqami, reklama, boshqa maqolalar matnini yozma.
- Har bir abzacni alohida qatorda ber.
- Agar biror so'z o'qilmasa, uning o'rniga [?] qo'y.
Javobda faqat matnning o'zi bo'lsin."""


def sahifa_rasmlari(pdf):
    papka = Path(tempfile.mkdtemp())
    subprocess.run(["pdftoppm", "-r", "200", "-png", str(pdf), str(papka / "p")],
                   check=True, capture_output=True)
    return sorted(papka.glob("p-*.png"))


def oqit(rasm, kalit):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={kalit}")
    body = {"contents": [{"parts": [
        {"text": KORSATMA},
        {"inline_data": {"mime_type": "image/png",
                         "data": base64.b64encode(rasm.read_bytes()).decode()}},
    ]}]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        javob = json.load(r)
    qismlar = javob["candidates"][0]["content"]["parts"]
    return "\n".join(q["text"] for q in qismlar if "text" in q)


def main():
    kalit = os.environ["GEMINI_API_KEY"]
    natija = []
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        rasmlar = sahifa_rasmlari(pdf)
        print(f"{pdf.name}: {len(rasmlar)} sahifa o'qilmoqda...")
        sahifalar = [oqit(r, kalit) for r in rasmlar]
        matn = "\n".join(sahifalar)

        qatorlar = [re.sub(r"\s+", " ", q).strip() for q in matn.splitlines() if q.strip()]
        qatorlar = [q for q in qatorlar if not re.fullmatch(r"[\d\W]+", q)]
        if not qatorlar:
            print("   matn topilmadi")
            continue
        sarlavha_kir = qatorlar[0].strip("«»\"'. ")
        tana_kir = [q for q in qatorlar[1:] if len(q) > 40]

        qolda = QOLDA.get(pdf.stem, {})
        if qolda.get("title_kir"):
            if sarlavha_kir not in qolda["title_kir"]:
                tana_kir.insert(0, sarlavha_kir) if len(sarlavha_kir) > 40 else None
            sarlavha_kir = qolda["title_kir"]
        natija.append({
            "slug": slugify(lotinga(sarlavha_kir)),
            "title": lotinga(sarlavha_kir),
            "title_kir": sarlavha_kir,
            "muallif": "Dilmurod Quronov",
            "janr": qolda.get("janr", "Maqola"),
            "yil": qolda.get("yil"),
            "asl_manba": qolda.get("asl_manba"),
            "manba_sayt": "jurnal skaneridan oʻqildi",
            "tekshirilsin": True,
            "matn": [lotinga(p) for p in tana_kir],
            "matn_kir": tana_kir,
            "belgi": len("".join(tana_kir)),
        })
        print(f"   {sarlavha_kir[:60]} — {len(''.join(tana_kir))} belgi")

    (ROOT / "data" / "skaner_maqolalar.json").write_text(
        json.dumps(natija, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(natija)} ta maqola yozildi")


if __name__ == "__main__":
    main()
