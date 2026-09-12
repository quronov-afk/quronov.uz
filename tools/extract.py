"""Manba hujjatlardan matn va metama'lumot ajratib, data/ ichiga yozadi.

Ishlatish:  python3 tools/extract.py
Manba:      "quronov.uz materiallar" papkasi (.doc/.docx/.rtf)
Natija:     data/matn/<slug>.txt  va  data/articles.json
"""

import json, re, subprocess, unicodedata, difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "quronov.uz materiallar"
OUT_TXT = ROOT / "data" / "matn"
BIB_FILE = SRC / "ПРОФЕССОРИ ДИЛМУРОД ҚУРОНОВНИНГ ЭЪЛОН ҚИЛИНГАН ИЛМИЙ ИШЛАРИ РЎЙХАТИ.docx"

JANR = {
    "макола": "Maqola",
    "макола/01": "Maqola",
    "нутк": "Nutq",
    "сухбат": "Suhbat",
    "такриз": "Taqriz",
    "сщз боши": "So'z boshi",
}

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'", "ы": "o'", "ь": "", "э": "e", "ю": "yu",
    "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}


def translit(s):
    out = []
    for ch in s:
        low = ch.lower()
        rep = TRANSLIT.get(low)
        if rep is None:
            out.append(ch)
        elif ch.isupper():
            out.append(rep[0].upper() + rep[1:] if rep else "")
        else:
            out.append(rep)
    return "".join(out)


ATOQLI = ["Чўлпон", "Қодирий", "Навоий", "Бобур", "Зулфия", "Ойбек", "Андижон",
          "Тошкент", "Ўзбекистон", "Айтматов", "Чингиз", "Мопассан", "Ҳамид",
          "Олимжон", "Орипов", "Усмон", "Азим", "Тоғай", "Мурод", "Ғафур", "Ғулом"]


def smart_case(s):
    """Bosh harflar bilan yozilgan sarlavhani odatiy ko'rinishga keltiradi."""
    harflar = [c for c in s if c.isalpha()]
    if not harflar or sum(c.isupper() for c in harflar) / len(harflar) < 0.6:
        return s
    s = s.lower()
    for i, c in enumerate(s):
        if c.isalpha():
            s = s[:i] + c.upper() + s[i + 1:]
            break
    for atoq in ATOQLI:
        s = re.sub(rf"\b{atoq.lower()}", atoq, s)
    return s


def slugify(s):
    s = translit(s).lower()
    s = s.replace("'", "").replace("ʻ", "")
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)[:60]


def to_text(path):
    r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def norm(s):
    s = re.sub(r"[“”\"«»‘’'`.,:;!?()\[\]—–-]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def parse_bibliography():
    """Ro'yxatdagi har bir yozuvni (sarlavha, manba, yil) ko'rinishida qaytaradi."""
    items = []
    for line in to_text(BIB_FILE).splitlines():
        line = line.strip()
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if not m:
            continue
        body = m.group(2).strip()
        years = re.findall(r"\b(19\d{2}|20\d{2})\b", body)
        parts = re.split(r"(?<=[а-яёқғҳўa-z…\"”»?])\.\s+", body, maxsplit=1)
        title = parts[0].strip(" .")
        source = parts[1].strip() if len(parts) > 1 else ""
        items.append({
            "title": title,
            "source": source,
            "year": int(years[0]) if years else None,
            "raw": body,
        })
    return items


def first_lines(text, n=6):
    return [l.strip() for l in text.splitlines() if l.strip()][:n]


AUTHOR_RE = re.compile(r"(Қуронов|Каримов|Ҳамроқулов|Нурмонов|Полвонова|Мамажонов)")
SKIP_RE = re.compile(r"^(\*+|УДК|UDK|УДK|Таянч сўзлар|Ключевые|Key words)", re.I)
CITATION_RE = re.compile(r"(-\s*Т\.:|нашриёти,\s*\d{4}|\bБ\.\d)")

# Sarlavhasi hujjat ichida yo'q yoki noto'g'ri o'qilgan fayllar uchun qo'lda kiritilgan ma'lumot
QOLDA = {
    "макола/01/Провинция.docx": {"title": "Провинция", "manba": "Тафаккур"},
    "макола/01/Тафаккур-Провинция.docx": {"title": "Провинция", "manba": "Тафаккур"},
    "макола/01/Китоб дунёсига — копия.docx": {"title": "Китоб дунёсига", "tekshirilsin": True},
    "макола/01/Собиржон.docx": {"title": "Таълим ва ўқитувчи мавқеи ҳақида", "tekshirilsin": True},
    "макола/мутолаа.doc": {"title": "“Ўтган кунлар” мутолаасидан қайдлар", "tekshirilsin": True},
    "макола/А.Орипов.rtf": {"title": "А.Ориповнинг 60-йиллар шеъриятида тарих концепцияси"},
    "макола/ideal.doc": {"title": "Идеал ва бадиий яхлитлик"},
    "макола/тогай.rtf": {"title": "Қалбларни ларзага солган ҳиргойи"},
    "макола/хамидолимжон.rtf": {"title": "Тарих сабоқлари", "tekshirilsin": True},
    "макола/01/Қурдош ака.docx": {"title": "Оптималлаштиришда ҳам мантиқ зарур"},
    "макола/01/Наср ритмиклиги-Бух.docx": {"title": "Насрий нутқнинг ритмиклиги"},
    "макола/01/Достон 113.doc": {"tekshirilsin": True},
    "макола/01/А.Қод-конф.doc": {
        "title": "“Ўтган кунлар”: мифопоэтик таҳлил тажрибаси",
        "janr": "Tezis",
        "yil": 2015,
        "manba": "Адабиётшуносликнинг долзарб муаммолари. – Фарғона, 2015",
    },
}

# Saytga chiqmaydigan hujjatlar: xizmat yozuvlari, kitob qo'lyozmasi va takroriy nusxalar
CHIQMAYDI = {
    "макола/01/Хостинг-домен.docx",
    "макола/01/ЖАЖ-жавоб.docx",
    "макола/01/Тўплам333.doc",
    "макола/01/Драматик компя-Фар.doc",
    "макола/01/Лирик асар комп. Узб тили ва ад.docx",
    "макола/01/Тафаккур-Провинция.docx",
    "макола/01/Қалбларни ларзага111.rtf",
    "макола/01/Чўлпоннинг туғилган-туз.rtf",
}


def pick_title(lines):
    """Sarlavhani topadi: muallif, UDK, iqtibos qatorlarini o'tkazib yuboradi."""
    picked = []
    for line in lines:
        if SKIP_RE.match(line) or CITATION_RE.search(line):
            continue
        if AUTHOR_RE.search(line) and len(line) < 70:
            continue
        if len(line) < 3:
            continue
        picked.append(line.strip(" ."))
        # Sarlavha ikki qatorga bo'lingan bo'lsa, davomini qo'shadi
        if len(picked) == 1 and len(picked[0]) < 45 and not picked[0].endswith(("?", "!", "...", "»", "”")):
            continue
        break
    if len(picked) == 2 and picked[1][:1].islower() or (len(picked) == 2 and picked[1].isupper()):
        return " ".join(picked)
    return picked[0] if picked else (lines[0] if lines else "")


def split_inline_manba(title):
    """«Sarlavha / Manba.- 2018.- 24 январь» ko'rinishini ajratadi."""
    if "/" not in title:
        return title, None, None
    left, right = title.split("/", 1)
    yil = re.search(r"\b(19\d{2}|20\d{2})\b", right)
    manba = re.sub(r"\s*\.-\s*", ", ", right).strip(" .,")
    return left.strip(" ."), manba, int(yil.group(1)) if yil else None


def pick_authors(lines):
    for line in lines[:2]:
        if AUTHOR_RE.search(line) and len(line) < 70 and "," in line:
            return line.strip()
    return None


SHAXS_TEGLAR = {"Cho'lpon", "Qodiriy", "Navoiy", "Bobur", "Zulfiya", "Oybek"}

TAG_RULES = [
    ("Cho'lpon", ["чўлпон", "чулпон"]),
    ("Qodiriy", ["қодирий", "ўтган кунлар"]),
    ("Navoiy", ["навоий"]),
    ("Bobur", ["бобур"]),
    ("Zulfiya", ["зулфия"]),
    ("Oybek", ["ойбек"]),
    ("She'riyat", ["шеър", "лирик", "поэзия", "достон", "мисра"]),
    ("Nasr", ["наср", "ҳикоя", "қисса"]),
    ("Roman", ["роман"]),
    ("Adabiyot nazariyasi", ["назария", "поэтика", "композиц", "жанр", "талқин"]),
    ("Adabiy tanqid", ["танқид", "тақриз", "мунаққид"]),
    ("Jadid adabiyoti", ["жадид"]),
    ("Adabiy ta'lim", ["таълим", "дарслик", "ўқув режа", "методик"]),
    ("Tarjima", ["таржима", "таржимон"]),
    ("Til va uslub", ["бадиий нутқ", "услуб", "ритм"]),
    ("Adabiy jarayon", ["адабий жараён", "даврлаштириш", "адабий муҳит"]),
]


def pick_tags(title, body):
    hay = norm(title + " " + body)
    scored = []
    for name, keys in TAG_RULES:
        n = sum(hay.count(k) for k in keys)
        n += 5 * sum(norm(title).count(k) for k in keys)
        chegara = 3 if name in SHAXS_TEGLAR else 2
        if n >= chegara:
            scored.append((n, name))
    scored.sort(reverse=True)
    return [name for _, name in scored[:3]]


def main():
    OUT_TXT.mkdir(parents=True, exist_ok=True)
    bib = parse_bibliography()
    bib_norm = [norm(b["title"]) for b in bib]

    records = []
    seen_slug, seen_body = set(), {}
    for folder, janr in JANR.items():
        d = SRC / folder
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            rel = str(f.relative_to(SRC))
            if f.is_dir() or f.name.startswith(".") or rel in CHIQMAYDI:
                continue
            if f.suffix.lower() not in (".doc", ".docx", ".rtf"):
                continue
            text = to_text(f)
            if len(text.strip()) < 400:
                continue

            qolda = QOLDA.get(rel, {})
            lines = first_lines(text)
            title = qolda.get("title") or pick_title(lines)
            title, inline_manba, inline_yil = split_inline_manba(title)
            title = smart_case(title)

            # Bir xil maqolaning ikki nusxasi bo'lsa, uzunrog'i qoladi
            kalit = norm(text)[:300]
            if kalit in seen_body:
                oldingi = seen_body[kalit]
                if len(text) <= oldingi["belgi"]:
                    continue
                records.remove(oldingi)

            match = difflib.get_close_matches(norm(title), bib_norm, n=1, cutoff=0.62)
            b = bib[bib_norm.index(match[0])] if match else None

            oxirgi = [l.strip() for l in text.splitlines() if l.strip()][-3:]
            oxirgi_yil = next((int(m.group(1)) for l in oxirgi
                               if (m := re.fullmatch(r"(19\d{2}|20\d{2})(\s*йил)?", l))), None)

            slug = slugify(title) or slugify(f.stem)
            if slug in seen_slug:
                slug = f"{slug}-{len(seen_slug)}"
            seen_slug.add(slug)

            (OUT_TXT / f"{slug}.txt").write_text(text, encoding="utf-8")
            rec = {
                "slug": slug,
                "title_uz": translit(title),
                "title": title,
                "janr": qolda.get("janr", janr),
                "yil": qolda.get("yil") or (b["year"] if b else None) or inline_yil or oxirgi_yil,
                "manba": qolda.get("manba") or (b["source"] if b else None) or inline_manba,
                "hammuallif": pick_authors(lines),
                "teglar": pick_tags(title, text),
                "manba_fayl": rel,
                "belgi": len(text),
            }
            if qolda.get("tekshirilsin"):
                rec["tekshirilsin"] = True
            records.append(rec)
            seen_body[kalit] = rec

    records.sort(key=lambda r: (-(r["yil"] or 0), r["title"]))
    (ROOT / "data" / "articles.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(records)} ta material yozildi")
    for r in records:
        print(f"{r['yil'] or '????'}  {r['janr']:<10} {r['title'][:52]:<54} {', '.join(r['teglar'])}")


if __name__ == "__main__":
    main()
