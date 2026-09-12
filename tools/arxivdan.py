"""O'chib ketgan eski quronov.uz saytini Internet Archive'dan tiklaydi.

Ishlatish:  python3 tools/arxivdan.py [yuklash|ajratish]
  yuklash  — arxivdagi barcha sahifalarni <scratch>/arxiv papkasiga tushiradi
  ajratish — tushirilgan sahifalardan matnlarni ajratib, data/ ga yozadi
"""

import html, json, re, subprocess, sys, time, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPKA = ROOT / "data" / "arxiv_sahifalar"
CDX = ("https://web.archive.org/cdx/search/cdx?url=quronov.uz&matchType=domain"
       "&fl=original,timestamp&filter=statuscode:200&collapse=urlkey&limit=2000")

TASHLAB = re.compile(r"\.(css|js|png|jpe?g|gif|svg|ico|woff2?|ttf|xml|json|txt|pdf)($|\?)", re.I)


def royxat():
    matn = subprocess.run(["curl", "-s", "--max-time", "60", CDX],
                          capture_output=True).stdout.decode()
    sahifalar = {}
    for qator in matn.splitlines():
        bolak = qator.split()
        if len(bolak) < 2:
            continue
        url, ts = bolak[0], bolak[1]
        if TASHLAB.search(url) or "/wp-" in url or "/.well-known" in url or "?" in url:
            continue
        yol = urllib.parse.unquote(url.split("quronov.uz", 1)[1]) or "/"
        # har bir sahifaning eng so'nggi nusxasi olinadi
        if yol not in sahifalar or ts > sahifalar[yol][1]:
            sahifalar[yol] = (url, ts)
    return sahifalar


def yukla(url, ts, fayl, urinish=3):
    """Arxiv so'rovlarni cheklaydi, shuning uchun bir necha bor urinib ko'riladi."""
    manzil = f"https://web.archive.org/web/{ts}id_/{url}"
    for n in range(urinish):
        r = subprocess.run(["curl", "-sL", "--max-time", "90", manzil], capture_output=True)
        if len(r.stdout) > 500:
            fayl.write_bytes(r.stdout)
            return True
        time.sleep(8 * (n + 1))
    return False


def yuklash():
    PAPKA.mkdir(parents=True, exist_ok=True)
    sahifalar = royxat()
    print(f"arxivda {len(sahifalar)} ta sahifa topildi")
    for yol, (url, ts) in sorted(sahifalar.items()):
        nom = re.sub(r"[^\w.-]+", "_", yol.strip("/")) or "index"
        fayl = PAPKA / f"{nom}.html"
        if fayl.exists():
            continue
        ok = yukla(url, ts, fayl)
        print(f"  {'+' if ok else '-'} {ts[:4]}  {yol[:70]}")
        time.sleep(2)


NAV_SOZ = ("Bosh sahifa", "Sayt haqida", "Aloqa", "Videogalereya", "Fotogalereya",
           "Copyright", "Powered by", "Search", "Qidirish")


def sahifa_matni(fayl):
    raw = fayl.read_bytes()
    try:
        s = raw.decode("utf-8")
        if "�" in s:
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "")
    except UnicodeDecodeError:
        s = raw.decode("cp1251", errors="replace")

    sarlavha = None
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', s)
    if m:
        sarlavha = html.unescape(m.group(1)).strip()
    if not sarlavha:
        m = re.search(r"<title>(.*?)</title>", s, re.S)
        sarlavha = html.unescape(m.group(1)).strip() if m else fayl.stem
    sarlavha = re.sub(r"\s*[–|-]\s*quronov\.uz.*$", "", sarlavha, flags=re.I).strip()

    # WordPress maqola tanasi
    tana = re.search(r'<div[^>]+class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>\s*<(?:/|footer|div[^>]+class="[^"]*(?:entry-footer|nav))', s, re.S)
    bolak = tana.group(1) if tana else s
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", bolak, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    qatorlar = [re.sub(r"\s+", " ", q).strip() for q in t.splitlines()]
    qatorlar = [q for q in qatorlar if len(q) > 60 and not any(n in q for n in NAV_SOZ)]
    return sarlavha, qatorlar, bool(tana)


def ajratish():
    natija = []
    for fayl in sorted(PAPKA.glob("*.html")):
        if fayl.stem.startswith(("category", "author", "page", "index")):
            continue
        sarlavha, qatorlar, topildi = sahifa_matni(fayl)
        natija.append({
            "fayl": fayl.name,
            "sarlavha": sarlavha,
            "belgi": sum(len(q) for q in qatorlar),
            "tana_topildi": topildi,
            "matn": qatorlar,
        })
    (ROOT / "data" / "arxiv_xom.json").write_text(
        json.dumps(natija, ensure_ascii=False, indent=1), encoding="utf-8")
    for n in sorted(natija, key=lambda x: -x["belgi"]):
        print(f"  {n['belgi']:>7}  {'tana' if n['tana_topildi'] else '????'}  {n['sarlavha'][:66]}")
    print(f"\n{len(natija)} ta sahifa ajratildi")


if __name__ == "__main__":
    buyruq = sys.argv[1] if len(sys.argv) > 1 else "yuklash"
    (yuklash if buyruq == "yuklash" else ajratish)()
