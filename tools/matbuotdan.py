"""Matbuot saytlaridagi maqola va suhbatlarni yig'adi.

Bu materiallar boshqa nashrlarda chiqqani uchun to'liq matn ko'chirilmaydi:
sarlavha, sana, manba, havola va qisqa parcha olinadi. To'liq matn faqat
tahririyat ruxsati bo'lsa qo'yiladi.

Ishlatish:  python3 tools/matbuotdan.py
Natija:     data/matbuot.json
"""

import html, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HAVOLALAR = [
    ("Sa'dullo Quronov", "https://kun.uz/74171664"),
    ("Sa'dullo Quronov", "https://kun.uz/05514287"),
    ("Sa'dullo Quronov", "https://kun.uz/28239006"),
    ("Sa'dullo Quronov", "https://www.gazeta.uz/oz/2023/03/31/bolalar-adabiyoti/"),
    ("Sa'dullo Quronov", "https://daryo.uz/2022/02/19/30-milliondan-ortiq-xalq-uchun-bir-ikki-bolalar-yozuvchisi-borligi-fojia-yozuvchi-sadullo-quronov-bilan-suhbat/"),
    ("Sa'dullo Quronov", "https://daryo.uz/2021/07/29/galati-paradoks-bor-yozuvchilik-ham-kasb-ammo-maosh-tolanmaydigan-kasb-yozuvchi-sadulla-quronov-bilan-bolalar-nasridagi-muammolar-haqida-suhbat"),
    ("Dilmurod Quronov", "https://oyina.uz/uz/article/2713"),
]

NASHR = {"kun.uz": "Kun.uz", "gazeta.uz": "Gazeta.uz", "daryo.uz": "Daryo.uz",
         "oyina.uz": "Oyina.uz"}


def yukla(url):
    r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 Chrome/120 Safari/537.36", url],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def meta(s, nom):
    m = re.search(rf'<meta[^>]+(?:property|name)="{nom}"[^>]+content="([^"]*)"', s)
    if not m:
        m = re.search(rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{nom}"', s)
    return html.unescape(m.group(1)).strip() if m else None


def sahifa_matni(s):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [re.sub(r"\s+", " ", q).strip() for q in t.splitlines() if len(q.strip()) > 80]


def qatorlar_oldindan(s):
    q = [x for x in sahifa_matni(s) if len(x) > 30]
    return q


def main():
    natija = []
    for muallif, url in HAVOLALAR:
        s = yukla(url)
        nashr = next((v for k, v in NASHR.items() if k in url), url.split("/")[2])
        sarlavha = meta(s, "og:title") or (re.findall(r"<title>(.*?)</title>", s, re.S) or [""])[0]
        sarlavha = re.sub(r"\s+", " ", html.unescape(sarlavha)).strip()
        sarlavha = re.sub(r"\s*[—|–-]\s*(Kun\.uz|Daryo|Gazeta\.uz|Oyina).*$", "", sarlavha)
        if len(sarlavha) < 12 and qatorlar_oldindan(s):  # og:title bo'sh bo'lsa sahifadan olinadi
            sarlavha = qatorlar_oldindan(s)[0][:200]
        tavsif = meta(s, "og:description")
        sana = (meta(s, "article:published_time") or meta(s, "publish-date") or "")[:10]

        qatorlar = sahifa_matni(s)
        if len(sarlavha) < 12 and qatorlar:
            sarlavha = qatorlar[0][:200]
        parcha = tavsif
        if not parcha and qatorlar:
            nomzod = [q for q in qatorlar if "Quronov" in q or len(q) > 200]
            parcha = nomzod[0] if nomzod else qatorlar[0]

        natija.append({
            "muallif": muallif,
            "nashr": nashr,
            "url": url,
            "sarlavha": sarlavha,
            "sana": sana,
            "parcha": (parcha or "")[:600],
            "sahifa_belgi": sum(len(q) for q in qatorlar),
        })
        print(f"  {nashr:<10} {sana or '??????????'}  {len(natija[-1]['parcha']):>3} belgi parcha  "
              f"{sarlavha[:60]}")

    (ROOT / "data" / "matbuot.json").write_text(
        json.dumps(natija, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(natija)} ta material yozildi")


if __name__ == "__main__":
    main()
