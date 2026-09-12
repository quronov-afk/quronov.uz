"""«Adabiyotshunoslik lug‘ati.doc» dan lug'at maqolalarini ajratib oladi.

Word fayl HTML'ga o'giriladi (textutil): har bir termin qalin (<b>) shriftda
abzac boshida turadi, keyingi abzaclar, she'riy misralar (<i>) va jadvallar shu
terminning izohiga tegishli bo'ladi.

Ishlatish:  python3 tools/lugatdan.py
Natija:     data/lugat.json
"""

import html, json, re, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitobdan import lotinga, slugify

ROOT = Path(__file__).resolve().parent.parent
MANBA = ROOT / "Adabiyotshunoslik lug‘ati.doc"

KATTA = "А-ЯЎҚҒҲЁЪ"
TERMIN = re.compile(rf"^\s*([{KATTA}][{KATTA}\-‑ʼ’'`]*(?:[ ,]+[{KATTA}][{KATTA}\-‑ʼ’'`]*)*)")


def tozala(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"\s+", " ", s).strip()


def bloklar(h):
    """HTML'ni ketma-ket bloklarga ajratadi: ('p', html) yoki ('table', qatorlar)."""
    tana = h[h.find("<body"):]
    for m in re.finditer(r"<p[^>]*>(.*?)</p>|<table[^>]*>(.*?)</table>", tana, re.S):
        if m.group(1) is not None:
            yield "p", m.group(1)
        else:
            qatorlar = []
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(2), re.S):
                qatorlar.append([tozala(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)])
            yield "table", qatorlar


def main():
    vaqt = Path(tempfile.mkdtemp()) / "lugat.html"
    subprocess.run(["textutil", "-convert", "html", "-output", str(vaqt), str(MANBA)], check=True)
    h = vaqt.read_text(encoding="utf-8", errors="replace")

    maqolalar, joriy = [], None
    for tur, qiymat in bloklar(h):
        if tur == "table":
            if joriy:
                joriy["bloklar"].append({"tur": "jadval", "qatorlar": qiymat})
            continue
        matn = tozala(qiymat)
        if not matn:
            continue
        # yangi termin: abzac qalin bosh harfli soʻz bilan boshlanadi
        qalin = re.match(r"\s*(?:<span[^>]*>\s*</span>)?\s*<b>(.*?)</b>", qiymat, re.S)
        m = TERMIN.match(matn)
        # Word'da ayrim terminlar qalin qilinmagan: «ИҚТИБОС (ар. …) – …» — bosh harfli soʻz,
        # keyin etimologiya qavsi yoki tire kelsa, bu ham yangi termin
        qalinsiz = (m and not qalin and len(re.sub(rf"[^{KATTA}]", "", m.group(1))) >= 4
                    and re.match(r"\s*(\((ар|форс|юн|лот|фр|нем|ингл|итал|рус|туркча|араб)[.\s]|[–—-]\s)",
                                 matn[len(m.group(1)):]))
        if (qalin or qalinsiz) and m and len(re.sub(rf"[^{KATTA}]", "", m.group(1))) >= 3:
            termin = m.group(1).strip(" ,")
            izoh = matn[len(m.group(0)):].strip()
            izoh = re.sub(r"^[–—-]\s*", "", izoh)
            joriy = {"termin_kir": termin, "bloklar": []}
            if izoh:
                joriy["bloklar"].append({"tur": "abzac", "matn": izoh, "bosh": True})
            maqolalar.append(joriy)
            continue
        if not joriy:
            continue                                   # muqaddima
        sheʼr = "<i>" in qiymat and len(matn) < 120 and tozala(re.sub(r"<i>.*?</i>", "", qiymat)).strip(" ,–-") == ""
        joriy["bloklar"].append({"tur": "misra" if sheʼr else "abzac", "matn": matn})

    # lotin yozuvi, slug va havola («қаранг: …»)
    ishlatilgan = set()
    for m in maqolalar:
        m["termin"] = lotinga(m["termin_kir"].capitalize()).replace("ʼ", "ʼ")
        slug = slugify(m["termin"]) or slugify(m["termin_kir"])
        asl, n = slug, 2
        while slug in ishlatilgan:
            slug, n = f"{asl}-{n}", n + 1
        ishlatilgan.add(slug)
        m["slug"] = slug
        for b in m["bloklar"]:
            if b["tur"] in ("abzac", "misra"):
                b["matn_lat"] = lotinga(b["matn"])
            else:
                b["qatorlar_lat"] = [[lotinga(c) for c in q] for q in b["qatorlar"]]
        birinchi = next((b["matn"] for b in m["bloklar"] if b["tur"] == "abzac"), "")
        # «(лот. autor – …) – қаранг: муаллиф» — izoh faqat boshqa terminga havola boʻlsa
        qar = re.search(r"(?:^|[–—-]\s*)қаранг\s*:\s*([^.;]+?)\.?$", birinchi)
        m["qarang"] = qar.group(1).strip() if qar and len(m["bloklar"]) == 1 and len(birinchi) < 160 else None

    (ROOT / "data" / "lugat.json").write_text(json.dumps(maqolalar, ensure_ascii=False, indent=1) + "\n",
                                              encoding="utf-8")
    print(f"{len(maqolalar)} ta termin ajratildi "
          f"({sum(1 for m in maqolalar if m['qarang'])} tasi «qarang» havolasi)")


if __name__ == "__main__":
    main()
