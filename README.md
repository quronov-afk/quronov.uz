# quronov.uz

Adabiyotshunos olimlar **Dilmurod Quronov** va **Saʼdullo Quronov**ning ilmiy-ijodiy
faoliyatiga bagʻishlangan sayt: maqolalar, suhbatlar, taqrizlar, kitoblar va
dissertatsiyalar bir joyda.

Sayt statik: hech qanday server, maʼlumotlar bazasi yoki ramka ishlatilmaydi —
faqat HTML, CSS va bir nechta qator JavaScript.

## Tuzilma

| Papka | Nima uchun |
|---|---|
| `site/` | Saytning oʻzi. GitHub Pages shu papkani chiqaradi. |
| `data/` | Materiallar maʼlumot bazasi (JSON) — sahifalar shundan yasaladi. |
| `tools/` | Materiallarni manbalardan ajratib olib, sahifalarni yasaydigan skriptlar. |

Manba fayllar (asl kitob PDF'lari, skanerlar, hujjatlar) `.gitignore` orqali
chetlatilgan: ular faqat mahalliy kompyuterda saqlanadi.

## Matnlar qanday yigʻilgan

Materiallar toʻrt xil manbadan tiklangan:

1. **Maqolalar toʻplami kitoblari** — `tools/kitobdan.py` PDF mundarijasi boʻyicha
   har bir maqolani ajratib oladi, eski shrift kodlashini tiklaydi va lotin
   yozuviga oʻgiradi.
2. **quronov.narod.ru arxivi** — `tools/eski_saytdan.py`. Eski saytda matnlar
   lotin va kirill yozuvida saqlangan.
3. **Internet Archive'dagi quronov.uz** — `tools/arxivdan.py` va
   `tools/arxiv_joyla.py`. Oʻchib ketgan sayt shu yerdan tiklandi.
4. **Shaxsiy arxiv** — `tools/materiallardan.py` (nutq, suhbat, taqriz) va
   `tools/skanerdan.py` (matn qatlami yoʻq jurnal skanerlari).

Matn mazmuni tahrir qilinmaydi: faqat PDF'dan oʻqishda buzilgan joylar
(eski shrift kodlashi, satr oxiridagi koʻchirish chizigʻi) tiklanadi va
imlo xatolari toʻgʻrilanadi.

## Sahifalarni qayta yasash

```bash
python3 tools/build.py       # maqola sahifalari, muallif roʻyxatlari, galereya
python3 tools/kitoblar.py    # Kitoblar PDF boʻlimi
```

Skanerlangan kitob hajmini kichraytirish (matn qatlami bor PDF'larga tegmaydi):

```bash
python3 tools/pdf_siqish.py site/kitoblar/<fayl>.pdf
```

## Mahalliy koʻrish

```bash
cd site && python3 -m http.server 4321
```

Soʻng brauzerda `http://localhost:4321` manzilini ochish kifoya.

## Talablar

- Python 3.9+ va Pillow (`pip3 install Pillow`)
- `poppler` (`pdftotext`, `pdftoppm`, `pdfinfo`) — `brew install poppler`
- macOS `textutil` (.doc/.rtf hujjatlarini oʻqish uchun)
