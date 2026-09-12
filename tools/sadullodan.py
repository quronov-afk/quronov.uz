"""«Sa'dullo Quronov/maqolalar» papkasidagi ilmiy maqolalarni saytga tayyorlaydi.

Har bir yozuv uchun: qaysi fayl, sarlavha, janr, yil, asl manba hamda matn
qaysi joydan boshlanib qayerda tugashi ko'rsatiladi. Jurnal PDF'laridan faqat
Sa'dullo Quronovning maqolasi qirqib olinadi.

Ishlatish:  python3 tools/sadullodan.py
Natija:     data/sadullo_maqolalar.json
"""

import json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import lotinga, kirillga, slugify, apostrof

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Sa'dullo Quronov" / "maqolalar"

# til: "kir" — kirill matn (lotinga o'giriladi), "lat" — lotin matn (kirillga),
#      "xor" — chet tilidagi matn (o'girilmaydi)
YOZUVLAR = [
    {"fayl": "1. Бадиий тафаккур еволюцияси.pdf", "til": "kir", "janr": "Maqola", "yil": 2022,
     "sarlavha": "Badiiy tafakkur evolyutsiyasi va inson konsepsiyasi",
     "manba": "Ilmiy xabarnoma. Gumanitar tadqiqotlar, 2022, № 7 (67)",
     "boshi": "БАДИИЙ ТАФАККУР ЭВОЛЮЦИЯСИ ВА ИНСОН КОНЦЕПЦИЯСИ",
     "oxiri": "Адабиётлар"},

    {"fayl": "2. Ғўрўғли романи.pdf", "til": "lat", "janr": "Maqola", "yil": 2023,
     "sarlavha": "Badiiy asardagi absurd va inson konsepsiyasi",
     "manba": "Adabiy meros, 2023, 3-4-son",
     "boshi": "BADIIY ASARDAGI ABSURD VA", "oxiri": "Foydalanilgan adabiyotlar ro‘yxati:"},

    {"fayl": "3. Лолазор романи.pdf", "til": "lat", "janr": "Maqola", "yil": 2023,
     "sarlavha": "«Lolazor» romanida inson konsepsiyasi",
     "manba": "Ilmiy xabarnoma. Gumanitar tadqiqotlar, 2023, № 7 (75)",
     "boshi": "ROMANIDA INSON", "oxiri": "Adabiyotlar"},

    {"fayl": "5. Мувозанат романи.pdf", "til": "lat", "janr": "Maqola", "yil": 2023,
     "sarlavha": "Ulugʻbek Hamdamning muvozanat konsepsiyasi",
     "manba": "Ilmiy xabarnoma. Gumanitar tadqiqotlar, 2023, № 3 (71)",
     "boshi": "MUVOZANAT KONS", "oxiri": "Adabiyotlar"},

    {"fayl": "6. Навоий романида.pdf", "til": "kir", "janr": "Maqola", "yil": 2021,
     "sarlavha": "«Alisher Navoiy» romanida tarixiy shaxs konsepsiyasi",
     "manba": "Ilmiy xabarnoma. Gumanitar tadqiqotlar, 2021, № 5 (57)",
     "boshi": "“АЛИШЕР НАВОИЙ” РОМАНИДА ТАРИХИЙ ШАХС КОНЦЕПЦИЯСИ",
     "oxiri": "Адабиётлар"},

    {"fayl": "7. Алишер Навоийнинг тарихий сиймоси.pdf", "til": "kir", "janr": "Maqola",
     "yil": None, "sarlavha": "Navoiy siymosining yangi talqini",
     "manba": "«Sharq yulduzi» jurnali", "boshi": "Роман ёзиш – машаққат"},

    {"fayl": "8. Ўтиш даври романлари.pdf", "til": "kir", "janr": "Maqola", "yil": 2024,
     "sarlavha": "Oʻtish davri romanlari va inson konsepsiyasi",
     "manba": "Filologik tadqiqotlar: til, adabiyot, taʼlim, 2024, № 3",
     "boshi": "Устоз адабиётшунос Озод Шарафиддинов", "oxiri": "Адабиётлар"},

    {"fayl": "9. Хорижий мақола-1.pdf", "til": "xor", "janr": "Maqola (ingliz tilida)",
     "yil": 2023, "sarlavha": "Time of transition in Uzbekistan and the concept of personality",
     "manba": "American Journal of Interdisciplinary Research and Development, 2023, vol. 18",
     "boshi": "Abstract:", "oxiri": "References"},

    {"fayl": "10. Хорижий мақола-2.pdf", "til": "xor", "janr": "Maqola (ingliz tilida)",
     "yil": 2021, "sarlavha": "The concept of a historical man in the novel “Alisher Navoi”",
     "manba": "The American Journal of Social Science and Education Innovations, 2021, 3(10)",
     "boshi": "ABSTRACT", "oxiri": "REFERENCES"},

    {"fayl": "11. Конференция маҳаллий-1.pdf", "til": "lat", "janr": "Tezis", "yil": 2022,
     "sarlavha": "Adabiyotni davrlashtirishda inson konsepsiyasi kategoriyasining ahamiyati",
     "manba": "«Ona tili taʼlimida oʻqitish va baholash muammolari» respublika ilmiy-amaliy "
              "anjumani. Toshkent, 2022",
     "boshi": "ADABIYOTNI DAVRLASHTIRISHDA INSON KONSEPSIYASI", "oxiri": "Foydalanilgan adabiyotlar"},

    {"fayl": "12. Конференция маҳаллий-2.pdf", "til": "lat", "janr": "Tezis", "yil": 2021,
     "sarlavha": "Olam va odam munosabatlarining badiiy talqini",
     "manba": "«Oʻzbek adabiyotshunosligining dolzarb muammolari» respublika anjumani. "
              "Urganch, 2021",
     "boshi": "OLAM VA ODAM MUNOSABATLARINING", "oxiri": "Foydalanilgan adabiyotlar"},

    {"fayl": "13. Халқаро Конференция-1.pdf", "til": "kir", "janr": "Tezis", "yil": 2023,
     "sarlavha": "Oʻtish davri romanlari va shaxs konsepsiyasi",
     "manba": "«Sharq-u Gʻarb: Navoiy va Gyote» xalqaro ilmiy-nazariy konferensiya. "
              "Toshkent, 2023",
     "boshi": "ЎТИШ ДАВРИ РОМАНЛАРИ ВА ШАХС", "oxiri": "Адабиётлар"},

    {"fayl": "14. Халқаро Конференция-2.pdf", "til": "lat", "janr": "Tezis", "yil": 2023,
     "sarlavha": "«Jimjitlik» romanida inson konsepsiyasi",
     "manba": "«Chingiz Aytmatov va jahon adabiyoti» xalqaro ilmiy-amaliy konferensiya. "
              "Fargʻona, 2023",
     "boshi": "“JIMJITLIK” ROMANIDA INSON KONSEPSIYASI", "oxiri": "Foydalanilgan adabiyotlar"},

    {"fayl": "Turkiya.pdf", "til": "xor", "janr": "Maqola (turk tilida)", "yil": 2012,
     "sarlavha": "Şiirin geometrik şekli",
     "manba": "Gazi Türkiyat, Güz 2012/11", "boshi": "Özet:", "oxiri": "KAYNAKLAR",
     "slug": "shiirin-geometrik-shekli"},

    {"fayl": "xabarnoma 2013_№1.pdf", "til": "kir", "janr": "Maqola", "yil": 2013,
     "sarlavha": "Rangtasvirning modern oqimlari va modern sheʼriyat",
     "manba": "Ilmiy xabarnoma (ADU), 2013, № 1",
     "boshi": "РАНГТАСВИРНИНГ МОДЕРН ОҚИМЛАРИ ВА МОДЕРН ШЕЪРИЯТ", "oxiri": "Адабиётлар"},

    {"fayl": "yana/XX аср аввалида Чўлпон.doc", "til": "kir", "janr": "Maqola", "yil": 2015,
     "sarlavha": "Choʻlpon sheʼriyatida badiiy obrazning vizuallashuvi",
     "manba": "Ilmiy xabarnoma (ADU), 2015, № 4",
     "boshi": "ЧЎЛПОН ШЕЪРИЯТИДА БАДИИЙ ОБРАЗНИНГ ВИЗУАЛЛАШУВИ"},

    # skanerdan oʻqilganlar (matn qatlami yoʻq, tesseract bilan tanilgan)
    {"fayl": "4. Минг бир қиёфа романи.pdf", "ocr": True, "bet": 3, "bet_oxiri": 8,
     "til": "kir", "janr": "Maqola", "yil": 2023,
     "sarlavha": "«Ming bir qiyofa» romanida erkin inson gʻoyasi",
     "manba": "«Sharq yulduzi» jurnali, 2023, № 10",
     "boshi": "XIX аср охири ва ХХ аср бошларида"},

    {"fayl": "yana/ОЙБЕК ЛИРИКАСИДА БАДИИЙ СИНТЕЗ.doc", "til": "kir", "janr": "Maqola",
     "yil": 2015, "sarlavha": "Oybek lirikasida badiiy sintez",
     "manba": "«Sharq yulduzi» jurnali, 2015, № 1",
     "boshi": "ОЙБЕК ЛИРИКАСИДА БАДИИЙ СИНТЕЗ"},

    {"fayl": "Тафаккур-Suhbat.pdf", "til": "kir", "janr": "Suhbat", "yil": None,
     "sarlavha": "Takomil mashaqqatlari. Ulugʻbek Hamdam bilan suhbat",
     "manba": "«Tafakkur» jurnali", "boshi": "– Улуғбек ака"},

    {"fayl": "S.Quronov-Ideal-УзАС.doc", "til": "kir", "janr": "Maqola", "yil": None,
     "sarlavha": "Postmodern kayfiyat va ideal ehtiyoji",
     "manba": "«Oʻzbekiston adabiyoti va sanʼati» gazetasi",
     "boshi": "Адабиётшунослигимиз ўтган давр"},

    {"fayl": "Teatr.doc", "til": "kir", "janr": "Maqola", "yil": None,
     "sarlavha": "Bir teatr tarixiga nazar",
     "manba": None, "boshi": "“Халқ уйи”"},

    {"fayl": "Теорема-русча.doc", "til": "xor", "janr": "Maqola (rus tilida)", "yil": None,
     "sarlavha": "Теорема", "slug": "teorema-abduqayum-yoldashev-hikoyasi-haqida",
     "manba": None, "boshi": "В психологии существует термин"},

    {"fayl": "ФУСУЛИ АРБАA 2.rtf", "til": "kir", "janr": "Maqola", "yil": None,
     "sarlavha": "Navoiyning forsiy qasidalarida badiiy sintez muammosi",
     "manba": "«Jahon adabiyoti» jurnali (hammuallif Dilnavoz Yusupova)",
     "boshi": "Мумтоз санъат намуналарини"},

    # «yana» papkasi: muallifning Word nusxalari
    {"fayl": "yana/ЎЗБЕК МОДЕРН ШЕЪРИЯТИДА ФОЛЬКЛОРИЗМ.doc", "til": "kir", "janr": "Tezis",
     "yil": 2015,
     "sarlavha": "Faxriyor sheʼriyatida folklorizm: mifologik obrazlarning vizuallashuvi",
     "manba": "Xalqaro ilmiy konferensiya materiallari. Nukus, 2015",
     "boshi": "ФАХРИЁР ШЕЪРИЯТИДА ФОЛЬКЛОРИЗМ: МИФОЛОГИК ОБРАЗЛАРНИНГ ВИЗУАЛЛАШУВИ"},

    {"fayl": "yana/ШАРҚ-МУМТОЗ-СИНТЕЗ-ОХИРИ.doc", "til": "kir", "janr": "Maqola", "yil": 2017,
     "sarlavha": "Sharq mumtoz adabiyotida badiiy sintezning ahamiyati",
     "manba": "«Filologiya masalalari» jurnali, 2017, № 1",
     "boshi": "ШАРҚ МУМТОЗ АДАБИЁТИДА БАДИИЙ СИНТЕЗНИНГ АҲАМИЯТИ"},

    {"fayl": "yana/Sa_dullo Quronov RTF.rtf", "til": "xor", "janr": "Maqola (ingliz tilida)",
     "yil": None, "slug": "importance-of-literal-synthesis-in-the-oriental-classic-literature",
     "sarlavha": "Importance of literal synthesis in the oriental classic literature",
     "manba": None, "boshi": "Abstract."},

    {"fayl": "yana/Инсон қиёфаси охирги.doc", "til": "kir", "janr": "Maqola", "yil": None,
     "sarlavha": "Sheʼriyat va rangtasvirda inson tasviri", "manba": None,
     "boshi": "ШЕЪРИЯТ ВА РАНГТАСВИРДА ИНСОН ТАСВИРИ"},

    {"fayl": "yana/Мусаввир шоир-С.Қуронов.doc", "til": "kir", "janr": "Maqola", "yil": None,
     "sarlavha": "Musavvir shoir", "manba": None, "boshi": "МУСАВВИР ШОИР"},

    {"fayl": "yana/С.Қуронов-синтез_модерн_мақола.doc", "til": "kir", "janr": "Maqola",
     "yil": None, "manba": None,
     "sarlavha": "Oʻzbek modern sheʼriyatini oʻrganishda badiiy sintezning ahamiyati",
     "boshi": "ЎЗБЕК МОДЕРН ШЕЪРИЯТИНИ ЎРГАНИШДА БАДИИЙ СИНТЕЗНИНГ АҲАМИЯТИ"},

    {"fayl": "yana/ШЕЪРИЯТ ВА РАНГТАСВИР – ЭГИЗ САНЪАТЛАР.doc", "til": "kir", "janr": "Maqola",
     "yil": None, "manba": None, "sarlavha": "Sheʼriyat va rangtasvir – egiz sanʼatlar",
     "boshi": "ШЕЪРИЯТ ВА РАНГТАСВИР – ЭГИЗ САНЪАТЛАР"},

    {"fayl": "yana/ЯНГИ-ЎЗБЕК-ШЕЪРИЯТИДА-БАДИИЙ-СИНТЕЗНИНГ-ЎРНИ1111.doc", "til": "kir",
     "janr": "Maqola", "yil": None, "manba": None,
     "sarlavha": "Yangi oʻzbek sheʼriyatida badiiy sintezning oʻrni (Oybek lirikasi misolida)",
     "boshi": "ЯНГИ ЎЗБЕК ШЕЪРИЯТИДА БАДИИЙ СИНТЕЗНИНГ ЎРНИ"},

    {"fayl": "yana/С.Қуронов-Ёшликка.doc", "til": "kir", "janr": "Taqriz", "yil": None,
     "manba": "«Yoshlik» jurnali",
     "sarlavha": "Maktub. Nargiza Odinayevaning «Toʻrt tomon» toʻplami haqida",
     "slug": "maktub-nargiza-odinayevaning-tort-tomon-toplami-haqida",
     "boshi": "МАКТУБ"},
]

AXLAT = re.compile(
    r"^\d{1,4}$"                                                         # sahifa raqami
    # boʻlim kolontitullari faqat butun satr boʻlsa («Тарихнинг…» kabi matn satrlari emas!)
    r"|^(ТАРИХ|TARIX|LITERARY( STUDIES)?|ADABIYOTSHUNOSLIK|АДАБИЁТШУНОСЛИК|TANQID VA TAHLIL"
    r"|ADABIY MEROS|FANIMIZ FIDOYILARI)(\s+(TANQID VA TAHLIL|ADABIY MEROS))*$"
    r"|^(Илмий хабарнома\.|Ilmiy xabarnoma\.|Scientific Bulletin\.|ISSN\b|ISNN\b|УДК\b|UDK\b"
    r"|UO‘K\b|DOI\b|www\.|E-mail\b|Тел\.?:|Volume\s+\d|Website:)", re.I)

# izoh (snoska) satrlari: «Шу асар. Б. 79.», «Ўша манба. Б. 12.»
SNOSKA = re.compile(r"^(Шу асар|Ўша асар|Ўша манба|Shu asar|O‘sha asar)\b")


# eski oʻzbek shriftlari: pdftotext bergan belgilarni kirillga qaytarish jadvali
SHRIFTLAR = {
    "sharq2010": {"і": "ҳ", "І": "Ҳ", "ї": "қ", "Ї": "Қ",
                  "є": "ў", "Є": "Ў", "ў": "ғ", "Ў": "Ғ"},
    "jahon": {"µ": "ҳ", "Μ": "Ҳ", "і": "қ", "І": "ғ", "ґ": "ў", "Ґ": "Ў"},
}


def eski_shrift(matn, nom):
    """cp1251 baytlari latin-1 sifatida oʻqilgan matnni tiklaydi."""
    tiklangan = matn.encode("latin-1", "replace").decode("cp1251", "replace")
    return tiklangan.translate(str.maketrans(SHRIFTLAR[nom]))


OCR_KESH = ROOT / "Sa'dullo Quronov" / "ocr"


def ocr_matn(fayl, boshi=1, oxiri=None):
    """Skaner qilingan PDF: sahifalarni rasmga oʻgirib, tesseract bilan oʻqiydi.

    Sahifa chetidagi qora hoshiya tesseractni adashtirgani uchun kesib tashlanadi.
    """
    from PIL import Image
    kesh = OCR_KESH / fayl.stem
    kesh.mkdir(parents=True, exist_ok=True)
    natija = kesh / "matn.txt"
    if natija.exists():
        return natija.read_text(encoding="utf-8")
    bet = [str(boshi)] + (["-l", str(oxiri)] if oxiri else [])
    subprocess.run(["pdftoppm", "-r", "300", "-gray", "-jpeg", "-f", str(boshi)]
                   + (["-l", str(oxiri)] if oxiri else [])
                   + [str(fayl), str(kesh / "s")], capture_output=True)
    bolaklar = []
    for rasm in sorted(kesh.glob("s-*.jpg")):
        im = Image.open(rasm)
        w, h = im.size
        im.crop((int(w * .03), int(h * .02), int(w * .97), int(h * .98))).save(rasm, quality=92)
        r = subprocess.run(["tesseract", str(rasm), "stdout", "-l", "uzb_cyrl"],
                           capture_output=True)
        bolaklar.append(r.stdout.decode("utf-8", "replace"))
    matn = "\n".join(bolaklar)
    natija.write_text(matn, encoding="utf-8")
    return matn


def pdf_ustunli_matn(fayl):
    """PDF matnini ustunlarni hisobga olib chiqaradi (poppler -bbox-layout).

    Har sahifada matn bloklari koordinatasi bilan olinadi. Tor bloklar sahifaning
    chap yoki oʻng yarmida boʻlsa, ikki ustunli qism deb hisoblanadi: avval chap
    ustun yuqoridan pastga, keyin oʻng ustun oʻqiladi. Keng bloklar (sarlavha,
    annotatsiya) boʻlim chegarasi vazifasini bajaradi.
    """
    import html as _html
    r = subprocess.run(["pdftotext", "-bbox-layout", str(fayl), "-"], capture_output=True)
    xml = r.stdout.decode("utf-8", "replace")
    chiqish = []
    for sahifa in re.finditer(r'<page width="([\d.]+)" height="[\d.]+">(.*?)</page>', xml, re.S):
        kenglik = float(sahifa.group(1))
        orta = kenglik / 2
        bloklar = []
        for b in re.finditer(r'<block xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</block>',
                             sahifa.group(2), re.S):
            x0, y0, x1, y1 = map(float, b.groups()[:4])
            satrlar = []
            for satr in re.finditer(r"<line[^>]*>(.*?)</line>", b.group(5), re.S):
                sozlar = re.findall(r"<word[^>]*>(.*?)</word>", satr.group(1), re.S)
                if sozlar:
                    satrlar.append(_html.unescape(" ".join(sozlar)))
            if satrlar:
                bloklar.append((x0, y0, x1, y1, satrlar))
        if not bloklar:
            continue
        tor = [b for b in bloklar if (b[2] - b[0]) < kenglik * 0.55]
        ikki_ustun = (len(tor) >= 0.4 * len(bloklar)
                      and any(b[2] <= orta + 15 for b in tor) and any(b[0] >= orta - 15 for b in tor))
        if not ikki_ustun:
            tartib = sorted(bloklar, key=lambda b: (round(b[1]), b[0]))
        else:
            tartib, bolim = [], []
            def bolimni_yoz():
                chap = sorted([b for b in bolim if b[0] < orta - 15], key=lambda b: b[1])
                ong = sorted([b for b in bolim if b[0] >= orta - 15], key=lambda b: b[1])
                tartib.extend(chap + ong)
                bolim.clear()
            for b in sorted(bloklar, key=lambda b: b[1]):
                if (b[2] - b[0]) >= kenglik * 0.55:
                    bolimni_yoz()
                    tartib.append(b)
                else:
                    bolim.append(b)
            bolimni_yoz()
        for b in tartib:
            chiqish.append("\n".join(b[4]))
            chiqish.append("")
    matn = "\n".join(chiqish)
    # satr oxiridagi boʻgʻin koʻchirishlarini tiklash: «konsep-\nsiya» → «konsepsiya»
    return re.sub(r"(\w)[-­]\n(\w)", r"\1\2", matn)


def xom_matn(fayl):
    if fayl.suffix.lower() == ".pdf":
        return pdf_ustunli_matn(fayl)
    else:
        r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(fayl)],
                           capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def kesish(matn, boshi, oxiri):
    """Maqolaning o'zini jurnal sahifalaridan ajratib oladi."""
    i = matn.find(boshi)
    if i < 0:
        raise SystemExit(f"boshlanish topilmadi: {boshi!r}")
    matn = matn[i:]
    if boshi.isupper():           # sarlavha satri matn tarkibiga kirmasin
        matn = matn[len(boshi):]
    if oxiri:
        j = matn.find(oxiri, 200)
        if j > 0:
            matn = matn[:j]
    return matn


def kolontitullar(matn):
    """Har sahifada takrorlanadigan qisqa satrlar — jurnal kolontituli."""
    sanoq = {}
    for q in matn.splitlines():
        q = q.strip()
        if q and len(q) < 90:
            sanoq[q] = sanoq.get(q, 0) + 1
    jurnal = re.compile(r"xabarnoma|хабарнома|bulletin|meros|мерос|journal|журнал|tadqiqot|тадқиқот|"
                        r"yulduzi|юлдузи|adabiyot|адабиёт|ISSN|№|\|", re.I)
    return {q for q, n in sanoq.items()
            if n >= 3 and (re.search(r"\d", q) or q.isupper() or jurnal.search(q) or len(q) >= 30)}


def abzaclar(matn, satr_abzac=False):
    """Satrlarni abzaclarga yig'adi, kolontitul va sahifa raqamlarini tashlaydi.

    satr_abzac — matbuot fayllarida (.doc, .rtf) har bir satr alohida abzac.
    """
    matn = matn.replace("\u00ad", "")
    takror = kolontitullar(matn)
    uzunliklar = [len(q.strip()) for q in matn.splitlines() if len(q.strip()) > 20]
    en_uzun = max(uzunliklar) if uzunliklar else 80
    if satr_abzac:
        natija = [q.strip() for q in matn.splitlines() if q.strip()]
    else:
        natija, joriy = [], []
        for qator in matn.splitlines():
            q = qator.strip()
            if not q or AXLAT.match(q) or SNOSKA.match(q) or q in takror:
                if joriy:
                    natija.append(" ".join(joriy))
                    joriy = []
                continue
            joriy.append(q)
            # qatori kalta va nuqta bilan tugasa — abzac shu yerda tugaydi
            if q[-1] in ".!?:»”" and len(q) < 0.72 * en_uzun:
                natija.append(" ".join(joriy))
                joriy = []
        if joriy:
            natija.append(" ".join(joriy))
    tozalangan = []
    for p in natija:
        for t in takror:
            if len(t) > 25:
                p = p.replace(t, " ")
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) < 40 and not p.endswith((".", "!", "?", ":")) and (p.isupper() or not re.search(r"[a-zа-яўқғҳ]{3}", p)):
            continue                       # sarlavha bo'laklari, imzo qoldiqlari
        tozalangan.append(p)
    return tozalangan


def bosh_tozalash(p):
    """Birinchi abzacdagi sarlavha–muallif qoldiqlarini kesadi."""
    sozlar = p.split()
    rim = re.compile(r"^[IVXLC]+$")              # «XIX аср» dagi rim raqami matnga tegishli
    while sozlar and (sozlar[0].isupper() and len(sozlar[0]) > 1 and not rim.match(sozlar[0])
                      or sozlar[0] in {"S.D.", "С.Д.", "Annotatsiya:", "Аннотация:"}):
        sozlar.pop(0)
    if sozlar[:1] in (["Quronov"], ["Қуронов"], ["Quronov,"]):
        sozlar.pop(0)
    matn = " ".join(sozlar)
    return matn[:1].upper() + matn[1:]           # «мазкур мақолада…» → «Мазкур…»


# ---------- matnni tozalash (PDF, eski shrift va OCR qoldiqlari) ----------
RUSCHA_ANNOT = re.compile(r"\b(статье|статья|Ключевые слова|Аннотация:?\s+В)\b|"
                          r"^(Аннотация|Annotatsiya)\s*:?\s*(В|V)\s", re.I)
RUSCHA_HARF = re.compile(r"[ыщЫЩ]")
INGLIZCHA_ANNOT = re.compile(r"^(Abstract|Annotation|Resume|Key ?words)\b[.:]?", re.I)
SNOSKA_RAQAM = re.compile(r"(?:(?<=[a-zʻʼа-яўқғҳ”»!?])|(?<=[a-zʻʼа-яўқғҳ”»]\.))\d{1,2}(?=[\s.,;:)]|$)")
BIBLIO_SNOSKA = re.compile(r"(–|-)\s*(B|S|С|Б|C|P|Pp|T|Т)\.\s?\d+[\d–\-,\s]*\.?\s*$|"
                           r"(Toshkent|Тошкент|Москва|Moskva|Moscow|Ленинград|T\.|Т\.)\s*:\s*.{0,60}\b(19|20)\d\d\b|"
                           r"\s//\s*.{2,60}\b(19|20)\d\d\b|"
                           r"\b(19|20)\d\d\b.{0,20}\b(С|S|B|Б|P|Р)\.\s?\d+[\d–\-]*\.?\s*$|"
                           r"\b(Под (общ\. )?ред|Учебник|Издательство|Изд-во)\b|^https?://\S+$")
SAHIFA_KOLONTITUL = re.compile(r"\b\d{1,3}\s*\|\s*P a g e\b|(?:\b\S \S \S \S (?:\S ){2,}\S\b)|\|\s*\d{1,3}\b")
WORD_HAVOLA = re.compile(r'HYPERLINK\s+"[^"]*"|\\o\s+"[^"]*"|\S*[?&](ei|usg|sa|ved)=\S*')


QOLDA_TUZATISH = {
    "«Ming bir qiyofa» romanida erkin inson gʻoyasi": [
        # sahifa kolontituli va sahifa osti snoskalari (skanerdan)
        ("\"Минг бир қиёфа\" романида эркин инсон ғояси ", ""),
        # OCR va terish xatolari — asl skaner bilan solishtirildi
        ("Узбек адабиётида", "Ўзбек адабиётида"), ("Уртага ташланган", "Ўртага ташланган"),
        ("Утмиш ҳақида", "Ўтмиш ҳақида"), ("Бунгасабаб", "Бунга сабаб"), ("позтика", "поэтика"),
        ("борликдаги", "борлиқдаги"), ("максад", "мақсад"), ("ҳодислар", "ҳодисалар"),
        ("собик", "собиқ"), ("чукур", "чуқур"), ("каҳрамонини", "қаҳрамонини"),
        ("Бирок", "Бироқ"), ("тасвирларган", "тасвирланган"), ("Минг бир киёфа", "Минг бир қиёфа"),
        ("мустақиллика", "мустақилликка"), ("Раҳим П,", "Раҳим II,"), ("Бурхон", "Бурҳон"),
        ("фаслафасига", "фалсафасига"), ("кадимий", "қадимий"), ("колган эски", "қолган эски"),
        ("ишончсизикни", "ишончсизликни"), ("фолъклор", "фольклор"), ("серкирра", "серқирра"),
        ("кулъминацияси", "кульминацияси"), ("базан", "баъзан"), ("чирмовукдай", "чирмовиқдай"),
        ("кон тўкмай", "қон тўкмай"), ("аср олиш", "асир олиш"), ("хукумати", "ҳукумати"),
        ("ҳар кандай вокеага", "ҳар қандай воқеага"), ("хам уради", "ҳам уради"),
        ("нимага ўхшаш", "нимага ўхшаш"),
        ("қаламга олди Ёзувчида", "қаламга олди? Ёзувчида"),
        ("нега пайдо бўлди\" Нима учун бевосита ўз замонига юзланмади", "нега пайдо бўлди? Нима учун бевосита ўз замонига юзланмади?"),
        ("ўйламасдинг Сен", "ўйламасдинг. Сен"),
        ("деб ўйлайман\"\" деб ёзади", "деб ўйлайман\" деб ёзади"),
        ("гуноҳи эди. Бироқ, шоир бўлганидан, бу гуноҳ, афтидан, унга юкланган эди\"\"", "гуноҳи эди. Бироқ, шоир бўлганидан, бу гуноҳ, афтидан, унга юкланган эди\""),
        ("шахси\"\" намоён", "шахси\" намоён"), ("юз тутади\"\",", "юз тутади\"."),
        ("вужудга келди\", Ўзбек", "вужудга келди\". Ўзбек"), ("тайёрлади\", Ўзбек", "тайёрлади\". Ўзбек"),
        ("таассурот қолдиради\",", "таассурот қолдиради\"."),
        ("мурожаат этадилар\", Дарҳақиқат", "мурожаат этадилар\". Дарҳақиқат"),
        # Kabirov iqtibosi (129-bet)
        ("“...MEHTA шаҳардаги мана шу бутун масжид-мадрасалар бузилгани ёқади, деб уйлайсизми\") «...» Илож йўқ, билдийизми\"7;",
         "“...менга шаҳардаги мана шу бутун масжид-мадрасалар бузилгани ёқади, деб ўйлайсизми?! «...» Илож йўқ, билдингизми?!"),
        ("шундай қилишади\"\" Кўринадики", "шундай қилишади!” Кўринадики"),
        # Rahim II iqtiboslari (129-bet)
        ("керак\", Подшоҳнинг", "керак\". Подшоҳнинг"),
        ("сўйиб ташлаймиз) Бундан буёғи", "сўйиб ташлаймиз! Бундан буёғи"),
        ("мен ўзим ўйлайман\"\" деб", "мен ўзим ўйлайман!\" деб"),
        ("кўрган\", Бу шундай", "кўрган\". Бу шундай"), ("эди\", Кейинчалик", "эди\". Кейинчалик"),
        # muallif nutqi — asarning kulminatsiyasi (130-bet)
        ("шумиди, халк Кимлар, бошман, деб сенинг бошингга чиқмади) Жиловни",
         "шумиди, халқ?! Кимлар, бошман, деб сенинг бошингга чиқмади! Жиловни"),
        ("пайига тушади: Зиндонга ташлайди Бу етмаса", "пайига тушади! Зиндонга ташлайди! Бу етмаса"),
        ("оч қолдиради Йўлларда", "оч қолдиради! Йўлларда"), ("мажбур қилади.. Хукмдордан", "мажбур қилади!.. Ҳукмдордан"),
        ("уради, тунайди).. Хаммаси сендан қўркиш", "уради, тунайди!.. Ҳаммаси сендан қўрқиш"),
        ("қул булиб яшашни талаб килади", "қул бўлиб яшашни талаб қилади!"),
        ("бечора халк{ Эртанги кунга умидланасан Одил", "бечора халқ! Эртанги кунга умидланасан! Одил"),
        ("бордир-ку, дейсанГ\"", "бордир-ку, дейсан!\""),
    ],
    "Badiiy asardagi absurd va inson konsepsiyasi": [
        # sahifada «XIX» alohida blok boʻlib turgan, annotatsiya olib tashlangach ajralib qoldi
        ("asr oxiri va XX asr boshlarida F.Nitshe", "XIX asr oxiri va XX asr boshlarida F.Nitshe"),
    ],
    "Şiirin geometrik şekli": [
        ("http//www. ashtray.ru.", ""),
    ],
}

# tozalashdan oldin qoʻllanadigan tuzatishlar (snoska raqami hali olib tashlanmagan matnga)
QOLDA_OLDIN = {
    "Oʻtish davri romanlari va inson konsepsiyasi": [
        ("XX аср ўзбек адабиёти масалалари. Тўплам. – Т:. FAN, 2012. B.40.", ""),
    ],
}


OCR_SNOSKA = re.compile(r"^(\"|\d)\s*[А-ЯЎҚҒҲ][а-яўқғҳ]+\s+[А-ЯЎҚҒҲ3]\.|^Саъдулло ҚУРОНОВ –")


def qolda_tuzat(paragraflar, sarlavha, lugat):
    tuzatishlar = lugat.get(sarlavha, [])
    if not tuzatishlar:
        return paragraflar
    natija = []
    for p in paragraflar:
        if OCR_SNOSKA.match(p):
            continue
        for eski, yangi in tuzatishlar:
            p = p.replace(eski, yangi)
        if p.strip():
            natija.append(p)
    return natija


SARLAVHA_QOLDIQ = ("Саъдулло ҚУРОНОВ", "Saʼdullo QURONOV", "Takomil mashaqqatlari",
                   "Навоий сиймосининг янги талқини", "Navoiy siymosining yangi talqini")


def tozalash(paragraflar, til):
    """Chiqarib olingan abzaclarni tozalaydi: annotatsiya tarjimalari, snoska raqamlari,
    kolontitullar, soʻz ichidagi boshqa alifbo harflari va notoʻgʻri boʻlingan abzaclar."""
    # oldindan: sahifa sarlavhasi/osti bloklari va OCR snoskalari (birlashtirishdan OLDIN)
    from collections import Counter
    kalta = Counter(p.strip() for p in paragraflar if len(p.strip()) < 70)
    SAHIFA_OSTI = re.compile(r"^\(?\d[\d ]{1,3}\s*\)?\s*(Sharq yulduzi|Шарқ юлдузи)$|"
                             r"^(№|N\S{0,3})\s*\d{0,2}\s*20\d\d\s*\(?\d{2,3}\)?$|"
                             r"^\d{2,3}\)\s*\S+(\s\S+)?$|^UrDU Filologiya fakulteti$|^\d{1,3}$")
    OSTI_BOSHI = re.compile(r"^(№|N\S{0,3})\s*\d{0,2}\s*20\d\d\s*\(?\d{2,3}\)?\s+")
    AFFIL = re.compile(r"doktoranti|falsafa doktori|докторанти|фалсафа доктори|universiteti|университети|"
                       r"professori|профессори|dotsent|доцент|e-mail|quronov@", re.I)
    oldindan = []
    for k, p in enumerate(paragraflar):
        q = OSTI_BOSHI.sub("", p.strip())
        p = q
        if not q:
            continue
        if k < 4 and len(q) < 220 and AFFIL.search(q) and not re.search(r"[.!?]\s+[A-ZА-ЯЎҚҒҲ][a-zа-яўқғҳ]+\s+[a-zа-яўқғҳ]", q):
            continue                                   # muallif va ish joyi haqidagi blok
        # (c) bosh harf alohida blok boʻlib qolgan (drop cap): «Y» + «angi oʻzbek…»
        if oldindan and len(oldindan[-1].strip()) == 1 and oldindan[-1].strip().isupper() and q[:1].islower():
            oldindan[-1] = oldindan[-1].strip() + q
            continue
        if oldindan and re.fullmatch(r"[IVXL]{2,5}", oldindan[-1].strip()) and q[:1].islower():
            oldindan[-1] = oldindan[-1].strip() + " " + q
            continue
        if re.fullmatch(r"https?://\S+", q):
            continue                                   # snoskadagi yakka havola
        if len(q) < 70 and kalta[q] >= 2 and not q.endswith((".", "!", "?", ":", ";", "…")):
            continue                                   # takrorlangan sahifa sarlavhasi
        if SAHIFA_OSTI.match(q) or OCR_SNOSKA.match(q):
            continue
        oldindan.append(p)
    paragraflar = oldindan

    natija = []
    oxirgi_qism = int(len(paragraflar) * 0.85)
    for i, p in enumerate(paragraflar):
        p = WORD_HAVOLA.sub("", p)
        for sarl in SARLAVHA_QOLDIQ:
            if p.startswith(sarl + " ") and p[len(sarl) + 1:len(sarl) + 2].islower():
                p = p[len(sarl) + 1:]
        if til == "xor":
            p = SAHIFA_KOLONTITUL.sub(" ", p)
            p = re.sub(r"(?:^|\s)\d{2,3}\s*\|\s*", " ", p)
            p = re.sub(r"(?<=[.”»])\s\d{1,2}(?=\s[A-ZÇĞİÖŞÜ])", "", p)
            p = re.sub(r"(?<=[.”»])\s\d{1,2}$", "", p)
            p = SNOSKA_RAQAM.sub("", p)
        if til != "xor":
            # oʻzbekcha maqoladagi ruscha va inglizcha annotatsiyalar saytda kerak emas
            if RUSCHA_ANNOT.search(p) or INGLIZCHA_ANNOT.match(p):
                continue
            if i < oxirgi_qism and len(RUSCHA_HARF.findall(p)) >= 2 and len(p) < 400:
                continue
            # matn ichiga tushib qolgan sahifa osti snoskalari (roʻyxat oxiridagilar qoladi)
            if i < oxirgi_qism and len(p) < 220 and BIBLIO_SNOSKA.search(p):
                continue
            p = SNOSKA_RAQAM.sub("", p)
            # ustunli oʻqishda snoska raqami soʻzdan ajralib qoladi: «“fojia” 1 deya», «koʻzlaydi 1. Biroq»
            p = re.sub(r"(?<=[”»]) \d{1,2}(?=[\s.,;:])", "", p)
            p = re.sub(r"(?<=[a-zʻʼа-яўқғҳ]) \d(?=[.,;:]\s)", "", p)
        # soʻz ichidagi boshqa alifbo harflari (PDF shriftidagi «е», «М» va h.k.)
        if til == "lat":
            p = re.sub(r"(?<=[A-Za-zʻʼ])е|е(?=[A-Za-zʻʼ])", "e", p)
            p = p.replace("М", "M") if re.search(r"[A-Za-z]М|М[a-z]", p) else p
            p = re.sub(r"\bË", "Yo", p).replace("ë", "yo")
            p = apostrof(p)                       # o‘ / o' / o’ → oʻ, g‘ → gʻ, ’ → ʼ
        if til == "kir":
            p = re.sub(r"(?<=[а-яўқғҳ])a|a(?=[а-яўқғҳ])", "а", p)
            p = re.sub(r"(?<=[а-яўқғҳ])u(?=[а-яўқғҳ])", "и", p)
            p = re.sub(r"\bM(?=[а-яўқғҳ])", "М", p)
        p = re.sub(r"\s+", " ", p)
        p = re.sub(r"\s+([,.;:!?])", r"\1", p).replace(",,", ",").strip()
        if not p:
            continue
        # abzac sahifa oxirida uzilib qolgan boʻlsa, oldingisiga qoʻshiladi
        if natija and p[:1].islower():
            oldingi = natija[-1]
            # sheʼr: kamida uch qator ketma-ket kalta boʻlsa (misralar alohida qoladi)
            sheʼr = (len(p) < 70 and len(oldingi) < 70
                     and (len(natija) < 2 or len(natija[-2]) < 70))
            # oraga tushib qolgan snoska: undan oldingi abzac davom etadi
            if (til != "xor" and len(natija) > 1 and len(oldingi) < 220
                    and BIBLIO_SNOSKA.search(oldingi)):
                natija.pop()
                oldingi = natija[-1]
            if oldingi.endswith("-"):
                natija[-1] = oldingi[:-1] + p
                continue
            ochiq = (not oldingi.endswith((".", "!", "?", ":", ";", "…", ")"))
                     or bool(re.search(r"(^|\s)[A-ZА-ЯЎҚҒҲ]\.$", oldingi)))
            qoshtirnoq = oldingi.endswith(("”", "»")) and len(oldingi) > 25
            if oldingi.endswith(("“...", "“…", "\"...", "«...")):
                qoshtirnoq = True
            if not sheʼr and (ochiq or qoshtirnoq):
                natija[-1] = oldingi + " " + p
                continue
        if (natija and len(natija[-1]) > 150 and len(p) > 80
                and not natija[-1].endswith((".", "!", "?", ":", ";", "…", ")", "»", "”", "]"))
                and not BIBLIO_SNOSKA.search(natija[-1])):
            natija[-1] = natija[-1] + " " + p            # satr koʻchishi abzac deb oʻqilgan
            continue
        natija.append(p)
    return natija


def main():
    chiqish = []
    for y in YOZUVLAR:
        fayl = SRC / y["fayl"]
        if not fayl.exists():
            print("  yo'q:", y["fayl"])
            continue
        matn = ocr_matn(fayl, y.get("bet", 1), y.get("bet_oxiri")) if y.get("ocr") \
            else xom_matn(fayl)
        if y.get("shrift"):
            matn = eski_shrift(matn, y["shrift"])
        matn = kesish(matn, y["boshi"], y.get("oxiri"))
        paragraflar = abzaclar(matn, satr_abzac=fayl.suffix.lower() != ".pdf")
        if not paragraflar:
            print("  bo'sh:", y["fayl"])
            continue
        paragraflar[0] = bosh_tozalash(paragraflar[0])
        paragraflar = qolda_tuzat(paragraflar, y["sarlavha"], QOLDA_OLDIN)
        paragraflar = tozalash(paragraflar, y["til"])
        paragraflar = qolda_tuzat(paragraflar, y["sarlavha"], QOLDA_TUZATISH)
        if y["til"] == "kir":
            lat = [p if RUSCHA_HARF.search(p) else lotinga(p) for p in paragraflar]
            kir = paragraflar
        elif y["til"] == "lat":
            lat = paragraflar
            kir = [kirillga(p) for p in paragraflar]
        else:
            lat = kir = paragraflar
        chiqish.append({
            "slug": y.get("slug") or slugify(y["sarlavha"]), "title": y["sarlavha"],
            "title_kir": kirillga(y["sarlavha"]) if y["til"] != "xor" else y["sarlavha"],
            "janr": y["janr"], "yil": y["yil"], "asl_manba": y["manba"],
            "manba_sayt": "shaxsiy arxiv", "muallif": "Sa'dullo Quronov",
            "matn": lat, "matn_kir": kir,
            "belgi": sum(len(p) for p in paragraflar),
        })
        print(f"  {len(paragraflar):3d} abzac  {y['sarlavha'][:58]}")

    (ROOT / "data" / "sadullo_maqolalar.json").write_text(
        json.dumps(chiqish, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chiqish)} ta maqola yig'ildi")


if __name__ == "__main__":
    main()
