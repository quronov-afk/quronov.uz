"""Skanerlangan PDF kitoblarning hajmini kichraytiradi.

Faqat matn qatlami yo'q (skaner) PDF'lar qayta ishlanadi. Sahifalar asl
zichlikda (150 dpi) rasmga o'giriladi va ikki rangli (1-bit, CCITT G4)
ko'rinishda qayta joylanadi — bu matn skaneri uchun odatiy usul: harflar
o'z tiniqligini saqlaydi, hajm esa 5 barobar kichrayadi. Chegara har bir
sahifa uchun Otsu usulida hisoblanadi.

Matn qatlami bor PDF'lar o'zgarmaydi (ularni rasmga aylantirish matn
sifatini buzadi). Rasmli sahifalar (masalan rangli muqova) ikki rangga
o'tkazilmaydi — ular JPEG ko'rinishida saqlanadi.

Ishlatish:  python3 tools/pdf_siqish.py <pdf...>
"""

import re, shutil, subprocess, sys, tempfile
from pathlib import Path

from PIL import Image

ZICHLIK = 150           # asl skaner zichligi
RASM_CHEGARA = 0.35     # yarim ton ulushi shundan yuqori bo'lsa sahifada rasm bor deb olinadi


def matn_borligi(pdf):
    matn = subprocess.run(["pdftotext", "-q", str(pdf), "-"],
                          capture_output=True).stdout
    betlar = betlar_soni(pdf)
    return len(matn) > betlar * 200


def betlar_soni(pdf):
    chiqish = subprocess.run(["pdfinfo", str(pdf)], capture_output=True).stdout.decode()
    m = re.search(r"^Pages:\s+(\d+)", chiqish, re.M)
    return int(m.group(1)) if m else 0


def otsu(gist):
    """Qora va oq o'rtasidagi eng maqbul chegarani hisoblaydi."""
    jami = sum(gist)
    eng_yaxshi, chegara = -1.0, 128
    orqa_n = orqa_s = 0
    umumiy_s = sum(i * n for i, n in enumerate(gist))
    for t in range(1, 255):
        orqa_n += gist[t - 1]
        orqa_s += (t - 1) * gist[t - 1]
        old_n = jami - orqa_n
        if orqa_n == 0 or old_n == 0:
            continue
        farq = (orqa_s / orqa_n - (umumiy_s - orqa_s) / old_n) ** 2 * orqa_n * old_n
        if farq > eng_yaxshi:
            eng_yaxshi, chegara = farq, t
    return chegara


def rasmli_sahifa(im):
    gist = im.histogram()
    orta = sum(gist[60:200]) / max(1, sum(gist))
    return orta > RASM_CHEGARA


def siqish(pdf):
    pdf = Path(pdf)
    if matn_borligi(pdf):
        print(f"  o'tkazildi (matn qatlami bor): {pdf.name}")
        return None

    vaqt = Path(tempfile.mkdtemp())
    subprocess.run(["pdftoppm", "-r", str(ZICHLIK), "-png", str(pdf), str(vaqt / "b")],
                   check=True, capture_output=True)
    betlar = sorted(vaqt.glob("b-*.png"))
    if not betlar:
        print(f"  rasmga o'girilmadi: {pdf.name}")
        return None

    rasmlar, rasmli = [], 0
    for b in betlar:
        asl = Image.open(b)
        kul = asl.convert("L")
        if rasmli_sahifa(kul):     # rangli muqova yoki surat — JPEG holida qoladi
            rasmlar.append(asl.convert("RGB"))
            rasmli += 1
        else:
            chegara = otsu(kul.histogram())
            rasmlar.append(kul.point(lambda x, t=chegara: 255 if x > t else 0, mode="1"))

    natija = vaqt / "siqilgan.pdf"
    # «quality» barcha sahifalarga tegishli bo'lgani uchun berilmaydi: ikki rangli
    # sahifalar CCITT bilan, rasmli sahifalar esa JPEG (sukut sifati) bilan yoziladi
    rasmlar[0].save(natija, "PDF", save_all=True, append_images=rasmlar[1:],
                    resolution=ZICHLIK)

    oldin = pdf.stat().st_size
    keyin = natija.stat().st_size
    if keyin >= oldin:
        print(f"  kichraymadi, qoldirildi: {pdf.name}")
        return None
    if betlar_soni(natija) != betlar_soni(pdf):
        print(f"  bet soni mos emas, qoldirildi: {pdf.name}")
        return None

    shutil.copy2(natija, pdf)
    print(f"  {pdf.name[:44]:<46} {oldin/1048576:6.1f} → {keyin/1048576:5.1f} MB  "
          f"({len(betlar)} bet; {len(betlar) - rasmli} ta ikki rangli, "
          f"{rasmli} ta rasmli sahifa JPEG)")
    return keyin


if __name__ == "__main__":
    for yol in sys.argv[1:]:
        siqish(yol)
