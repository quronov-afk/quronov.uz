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
from kitobdan import lotinga, kirillga, slugify

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
     "boshi": "BADIIY ASARDAGI ABSURD VA", "oxiri": "FANIMIZ FIDOYILARI"},

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

    {"fayl": "xabarnoma 2015_№4-2.pdf", "til": "kir", "janr": "Maqola", "yil": 2015,
     "sarlavha": "Choʻlpon sheʼriyatida badiiy obrazning vizuallashuvi",
     "manba": "Ilmiy xabarnoma (ADU), 2015, № 4",
     "boshi": "ЧЎЛПОН ШЕЪРИЯТИДА БАДИИЙ ОБРАЗНИНГ ВИЗУАЛЛАШУВИ", "oxiri": "Адабиётлар"},

    {"fayl": "Sharq yulduzi # 1-2015.pdf", "til": "kir", "janr": "Maqola", "yil": 2015,
     "sarlavha": "Oybek lirikasida badiiy sintez",
     "manba": "«Sharq yulduzi» jurnali, 2015, № 1",
     "boshi": "Тил универсал фикрлаш ва ифодалаш"},

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

]

AXLAT = re.compile(
    r"^(\d{1,4}|[IVXLC]+)$"                              # sahifa raqami
    r"|^(Илмий хабарнома|Ilmiy xabarnoma|Scientific Bulletin|ADABIY MEROS"
    r"|TANQID VA TAHLIL|LITERARY|ADABIYOTSHUNOSLIK|АДАБИЁТШУНОСЛИК|ТАРИХ|TARIX"
    r"|ISSN|ISNN|УДК|UDK|UO‘K|DOI|www\.|E-mail|Тел|Volume|Web)", re.I)

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


def xom_matn(fayl):
    if fayl.suffix.lower() == ".pdf":
        r = subprocess.run(["pdftotext", str(fayl), "-"], capture_output=True)
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
    return {q for q, n in sanoq.items() if n >= 3}


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
        if len(p) < 40 and not p.endswith((".", "!", "?", ":")):
            continue                       # sarlavha bo'laklari, imzo qoldiqlari
        tozalangan.append(p)
    return tozalangan


def bosh_tozalash(p):
    """Birinchi abzacdagi sarlavha–muallif qoldiqlarini kesadi."""
    sozlar = p.split()
    while sozlar and (sozlar[0].isupper() and len(sozlar[0]) > 1
                      or sozlar[0] in {"S.D.", "С.Д.", "Annotatsiya:", "Аннотация:"}):
        sozlar.pop(0)
    if sozlar[:1] in (["Quronov"], ["Қуронов"], ["Quronov,"]):
        sozlar.pop(0)
    return " ".join(sozlar)


def main():
    chiqish = []
    for y in YOZUVLAR:
        fayl = SRC / y["fayl"]
        if not fayl.exists():
            print("  yo'q:", y["fayl"])
            continue
        matn = xom_matn(fayl)
        if y.get("shrift"):
            matn = eski_shrift(matn, y["shrift"])
        matn = kesish(matn, y["boshi"], y.get("oxiri"))
        paragraflar = abzaclar(matn, satr_abzac=fayl.suffix.lower() != ".pdf")
        if not paragraflar:
            print("  bo'sh:", y["fayl"])
            continue
        paragraflar[0] = bosh_tozalash(paragraflar[0])
        if y["til"] == "kir":
            lat = [lotinga(p) for p in paragraflar]
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
