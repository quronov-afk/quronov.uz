# Quronov.uz — inglizcha versiya rejasi

Maqsad: saytning inglizcha versiyasi. Yuqori oʻng burchakda til tanlash tugmasi, **asosiy til — oʻzbekcha**.
Maqolalar professional tarjimon darajasida, bosqichma-bosqich, sekin-asta tarjima qilinadi.

Holat: **0-bosqich bajarildi** (2026-09-13); navbatda — 1-bosqich.

---

## Umumiy qoidalar

- **Manzillar:** oʻzbekcha sahifalar joyida qoladi, inglizchasi `site/en/` ostida (`/en/index.html`,
  `/en/articles/<slug>.html` …). Har juft sahifada `hreflang` havolalari.
- **Til tugmasi:** sarlavha satrining oʻng burchagida `UZ | EN`. Tarjimasi yoʻq sahifada EN bosilsa,
  inglizcha bosh sahifaga olib boradi (yoki «This article is available in Uzbek» belgisi).
- **Tarjima maʼlumoti:** `data/en/` — har maqola alohida JSON (`<slug>.json`): `title`, `subtitle`,
  `paragraphs`, `holat` (`qoralama` / `koʻrib chiqilgan`), `tarjima_sanasi`.
  Oʻzbekcha asl matn oʻzgarsa, tarjima eskirgan deb belgilanadi.
- **Izchil atamalar:** `data/en/atamalar.json` — asosiy terminlar lugʻati (masalan: inson konsepsiyasi →
  *concept of the human*, badiiy sintez → *artistic synthesis*, badiiy tafakkur → *artistic thinking*,
  romaniy tafakkur → *novelistic thinking*, mumtoz adabiyot → *classical literature*). Har yangi atama
  birinchi uchraganda shu yerga qoʻshiladi.
- **Nomlar va asarlar:** shaxs ismlari ISO-yaqin inglizcha transliteratsiyada (Choʻlpon → *Cholpon*,
  Abdulla Qodiriy → *Abdulla Qodiriy*); asar nomi kursiv, birinchi marta qavs ichida tarjimasi bilan:
  *Kecha va kunduz* (Night and Day).
- **Iqtiboslar:** nasriy iqtibos — tarjima; sheʼriy parcha — asl misra (lotin) + ostida soʻzma-soʻz
  inglizcha tarjima.
- **Bibliografiya va manba qatori** tarjima qilinmaydi (asl holida), faqat yorliqlar inglizcha.
- **Sifat nazorati:** har partiyadan keyin 1–2 maqolani muallif (yoki ingliz tilini biluvchi) koʻrib chiqadi;
  izohlar `atamalar.json` va uslub qoidalariga qoʻshiladi.

---

## Texnik tuzilma (0-bosqichda yaratilgan)

- `tools/en.py` — `yasash()` inglizcha sahifalarni `site/en/` ga yozadi; `til_belgilari()` har sahifaga
  `<!-- til -->` (UZ | EN tugmasi) va `<!-- hreflang -->` bloklarini qoʻyadi. `build.py` oxirida chaqiriladi.
- Menyuda faqat `site/en/` da mavjud sahifalar koʻrinadi; tarjimasi yoʻq sahifada EN → `/en/`.
- Interfeys matnlari: `data/en/interfeys.json`. Yangi sahifa qoʻshish — `en.py` ga funksiya + `yasash()` ga qator.

## Bosqichlar

### 0-bosqich — infratuzilma (tarjimasiz)
- `build.py` ga til parametri: bitta shablon, ikki til (`uz`, `en`); interfeys matnlari `data/en/interfeys.json`.
- Til tugmasi, `hreflang`, inglizcha `sitemap` yozuvlari, `og:locale=en_US`.
- Tarjimasi yoʻq sahifalar uchun zaxira xatti-harakat.
- **Natija:** `/en/` ochiladi, lekin ichida faqat interfeys; hech narsa buzilmaydi.

### 1-bosqich — asosiy sahifalar
- Bosh sahifa, Dilmurod Quronov va Saʼdullo Quronov sahifalari (roʻyxatda faqat tarjima qilinganlar),
  Kitoblar (kitob nomlari + qisqa izoh), Galereya (izohlar), Aloqa, Qidiruv.
- Mavzu nomlari (24 ta) va ruknlar.

### 2-bosqich — biografiyalar va «Olim haqida»
- Ikkala olim biografiyasi (kitoblar roʻyxati bilan), «Olim haqida» maqolalari.

### 3-bosqich va keyingilari — maqolalar partiyalarda (har partiya 10–12 ta)
Tartib (ahamiyati va oʻqilishi boʻyicha):
1. Saʼdullo Quronovning inson konsepsiyasi va roman nazariyasiga oid maqolalari
   («Roman janri evolyutsiyasi haqida», «Badiiy tafakkur evolyutsiyasi…», «Oʻtish davri romanlari…» …).
   Ingliz tilida allaqachon bor 3 ta maqola shu partiyada tekshirib qoʻshiladi.
2. Saʼdullo Quronovning badiiy sintez mavzusidagi maqolalari.
3. Dilmurod Quronovning Choʻlpon va Qodiriyga oid maqolalari.
4. Dilmurod Quronovning adabiyot nazariyasiga oid maqolalari.
5. Qolgan maqolalar, taqrizlar, suhbatlar (mavzu va oʻqilganlik soniga qarab).

Har partiyadan keyin: sayt yigʻiladi, tekshiriladi, push qilinadi, bu faylda holat yangilanadi.

### Oxirgi (ixtiyoriy) bosqich — Adabiyotshunoslik lugʻati
- 549 termin: termin nomi + qisqa inglizcha izoh (toʻliq tarjima emas), asl manba koʻrsatiladi.

---

## Holat jadvali

| Bosqich | Mazmuni | Holat |
|---|---|---|
| 0 | Infratuzilma, til tugmasi | bajarildi (2026-09-13) |
| 1 | Asosiy sahifalar | kutilmoqda |
| 2 | Biografiyalar | kutilmoqda |
| 3.1 | S. Quronov: inson konsepsiyasi, roman (≈12) | kutilmoqda |
| 3.2 | S. Quronov: badiiy sintez (≈12) | kutilmoqda |
| 3.3 | D. Quronov: Choʻlpon, Qodiriy (≈12) | kutilmoqda |
| 3.4+ | Qolgan maqolalar (10–12 tadan) | kutilmoqda |
| L | Lugʻat (ixtiyoriy) | kutilmoqda |

Hozir saytda 138 ta maqola sahifasi + matbuotdagi materiallar bor (jami ≈170 yozuv).
