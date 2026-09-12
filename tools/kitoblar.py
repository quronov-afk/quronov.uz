"""Kitoblar PDF bo'limini yasaydi: PDF fayllar, muqovalar va sahifa.

Ishlatish:  python3 tools/kitoblar.py
Manba:      data/books.json + «D.Quronov kitoblar_PDF» papkasi
Natija:     site/kitoblar/<slug>.pdf, site/img/kitoblar/<slug>.jpg, site/kitoblar.html
"""

import json, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import SHAPKA, PODVAL, e, meta_teglar

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CHIQISH_PDF = SITE / "kitoblar"
CHIQISH_MUQOVA = SITE / "img" / "kitoblar"

# Dissertatsiyalar. «fayl» bo'lsa PDF havolasi qo'yiladi, bo'lmasa faqat yozuv qoladi.
DISSERTATSIYALAR = {
    "Dilmurod Quronov": [
        {"title": "Choʻlponning «Kecha va kunduz» romanida xarakterlar psixologizmi",
         "izoh": "Nomzodlik dissertatsiyasi", "yil": 1992, "joy": "Toshkent",
         "muqova": "dilmurod-nomzodlik-dissertatsiya.jpg"},
        {"title": "Choʻlpon poetikasi (nasriy asarlari asosida)",
         "izoh": "Doktorlik dissertatsiyasi", "yil": 1998, "joy": "Toshkent",
         "muqova": "dilmurod-doktorlik-dissertatsiya.jpg"},
    ],
    "Saʼdullo Quronov": [
        {"title": "Mustaqillik davri oʻzbek romanlarida inson konsepsiyasi",
         "izoh": "Filologiya fanlari doktori (DSc) dissertatsiyasi", "yil": 2024,
         "joy": "Toshkent", "fayl": "sadullo-dsc-dissertatsiya.pdf",
         "avtoreferat": "sadullo-dsc-avtoreferat.pdf"},
        {"title": "Zamonaviy oʻzbek adabiyotida sintez muammosi "
                  "(sheʼriyat va rangtasvir sanʼatlari misolida)",
         "izoh": "Falsafa doktori (PhD) dissertatsiyasi", "yil": 2018,
         "joy": "Fargʻona", "fayl": "sadullo-phd-dissertatsiya.pdf",
         "avtoreferat": "sadullo-phd-avtoreferat.pdf", "kirill": True},
    ],
}


def hajm(nom):
    f = CHIQISH_PDF / nom
    return round(f.stat().st_size / 1048576, 1) if f.exists() else None


def diss_muqova(d):
    """Dissertatsiya muqovasi: PDF bor boʻlsa titul varagʻi, boʻlmasa oldindan chizilgan muqova."""
    if d.get("muqova"):
        return d["muqova"] if (CHIQISH_MUQOVA / d["muqova"]).exists() else None
    if not d.get("fayl"):
        return None
    nom = Path(d["fayl"]).stem + ".jpg"
    chiqish = CHIQISH_MUQOVA / nom
    if not chiqish.exists():
        vaqt = Path(tempfile.mkdtemp())
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "110", "-jpeg",
                        str(CHIQISH_PDF / d["fayl"]), str(vaqt / "titul")], capture_output=True)
        rasmlar = sorted(vaqt.glob("titul*.jpg"))
        if rasmlar:
            subprocess.run(["sips", "-Z", "600", str(rasmlar[0]), "--out", str(chiqish)],
                           capture_output=True)
    return nom if chiqish.exists() else None


def diss_html(olim):
    """Dissertatsiyalar kitob kartasi koʻrinishida (muqova, nomi, maʼlumot, PDF havolalari)."""
    kartalar = []
    for d in DISSERTATSIYALAR.get(olim, []):
        muqova_nomi = diss_muqova(d)
        rasm = (f'<img src="img/kitoblar/{e(muqova_nomi)}" alt="" loading="lazy">'
                if muqova_nomi else '<div class="muqova-yoq"></div>')
        havola = f"kitoblar/{e(d['fayl'])}" if d.get("fayl") else None
        muqova_blok = (f'<a class="muqova" href="{havola}">{rasm}</a>' if havola
                       else f'<div class="muqova">{rasm}</div>')
        sarlavha = (f'<a href="{havola}">{e(d["title"])}</a>' if havola else e(d["title"]))
        havolalar = []
        if d.get("fayl"):
            havolalar.append(f'<a class="yuklab" href="kitoblar/{e(d["fayl"])}">'
                             f'Dissertatsiya PDF · {hajm(d["fayl"])} MB</a>')
        if d.get("avtoreferat"):
            havolalar.append(f'<a class="yuklab" href="kitoblar/{e(d["avtoreferat"])}">'
                             f'Avtoreferat PDF · {hajm(d["avtoreferat"])} MB</a>')
        izoh = d["izoh"] + (" · kirill yozuvida" if d.get("kirill") else "")
        pastki = (" ".join(havolalar) if havolalar
                  else '<span class="kutilmoqda-belgi">PDF nusxasi tez orada joylanadi</span>')
        kartalar.append(f"""      <article class="kitob diss">
        {muqova_blok}
        <div class="kitob-matn">
          <h3>{sarlavha}</h3>
          <p class="kitob-meta">{e(izoh)} · {e(d['joy'])}, {d['yil']}</p>
          <p class="diss-havolalar">{pastki}</p>
        </div>
      </article>""")
    return "\n".join(kartalar)


def diss_html_eski(olim):
    qismlar = []
    for d in DISSERTATSIYALAR.get(olim, []):
        havolalar = []
        if d.get("fayl"):
            havolalar.append(f'<a class="yuklab" href="kitoblar/{e(d["fayl"])}">'
                             f'Dissertatsiya PDF · {hajm(d["fayl"])} MB</a>')
        if d.get("avtoreferat"):
            havolalar.append(f'<a class="yuklab" href="kitoblar/{e(d["avtoreferat"])}">'
                             f'Avtoreferat PDF · {hajm(d["avtoreferat"])} MB</a>')
        izoh = d["izoh"] + (" · kirill yozuvida" if d.get("kirill") else "")
        qismlar.append(f"""        <li><span class="diss-nom">{e(d['title'])}</span>
            <span class="diss-meta">{e(izoh)} · {e(d['joy'])}, {d['yil']}</span>
            <span class="diss-havola">{' '.join(havolalar) or 'PDF fayl kutilmoqda'}</span></li>""")
    return "\n".join(qismlar)


def muqova(kitob):
    """Muqova rasmini tayyorlaydi: bor bo'lsa nusxalaydi, yo'q bo'lsa PDF ilk sahifasidan oladi."""
    chiqish = CHIQISH_MUQOVA / f"{kitob['slug']}.jpg"
    if chiqish.exists():
        return chiqish.name
    manba = (ROOT / kitob["muqova_papka"] / kitob["cover"]) if kitob.get("cover") else None

    if manba and manba.exists():
        subprocess.run(["sips", "-Z", "600", "-s", "format", "jpeg",
                        str(manba), "--out", str(chiqish)], capture_output=True)
    else:
        vaqt = Path(tempfile.mkdtemp())
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "80", "-jpeg",
                        str(ROOT / kitob["papka"] / kitob["pdf"]), str(vaqt / "muqova")],
                       capture_output=True)
        rasmlar = sorted(vaqt.glob("muqova*.jpg"))
        if not rasmlar:
            return None
        subprocess.run(["sips", "-Z", "600", str(rasmlar[0]), "--out", str(chiqish)],
                       capture_output=True)
    return chiqish.name if chiqish.exists() else None


def kartalar_html(kitoblar):
    kartalar = []
    for k in kitoblar:
        meta = [k["kind"]]
        if k.get("year"):
            meta.append(str(k["year"]))
        if k.get("publisher"):
            meta.append(k["publisher"])
        meta.append(f"{k['pages']} bet")
        rasm = (f'<img src="img/kitoblar/{e(k["muqova"])}" alt="" loading="lazy">'
                if k.get("muqova") else '<div class="muqova-yoq"></div>')
        kartalar.append(f"""      <article class="kitob">
        <a class="muqova" href="kitoblar/{e(k['fayl'])}">{rasm}</a>
        <div class="kitob-matn">
          <h3><a href="kitoblar/{e(k['fayl'])}">{e(k['title'])}</a></h3>
          <p class="kitob-meta">{e(' · '.join(meta))}</p>
          <p>{e(k['note'])}</p>
          <a class="yuklab" href="kitoblar/{e(k['fayl'])}">PDF yuklab olish · {k['hajm']} MB</a>
        </div>
      </article>""")
    return chr(10).join(kartalar)


OLIMLAR = (("Dilmurod Quronov", "Dilmurod Quronov", "dq"),
           ("Sa'dullo Quronov", "Saʼdullo Quronov", "sq"))


def sahifa(kitoblar):
    tugmalar, bolimlar = [], []
    for i, (olim, yorliq, belgi) in enumerate(OLIMLAR):
        faol = " tanlangan" if i == 0 else ""
        tugmalar.append(f'    <button type="button" class="kitob-tugma{faol}" '
                        f'data-bolim="{belgi}">{e(yorliq)} kitoblari (PDF)</button>')

        uniki = [k for k in kitoblar if k["muallif"] == olim]
        qism = []
        if uniki:
            qism.append(f'    <div class="kitoblar">\n{kartalar_html(uniki)}\n    </div>')
        else:
            qism.append('    <p class="kutilmoqda">Kitoblar tayyorlanmoqda.</p>')
        diss = diss_html(yorliq)
        if diss:
            qism.append('    <h3 class="kitob-bolim kichik">Dissertatsiyalar</h3>')
            qism.append(f'    <div class="kitoblar">\n{diss}\n    </div>')
        yashirin = "" if i == 0 else " hidden"
        bolimlar.append(f'  <section id="bolim-{belgi}" class="kitob-bolimi"{yashirin}>\n'
                        + chr(10).join(qism) + "\n  </section>")

    tugmalar = chr(10).join(tugmalar)
    bolimlar = (chr(10) * 2).join(bolimlar)

    meta_html = meta_teglar("Kitoblar PDF — Quronov.uz",
                            "Dilmurod Quronov va Saʼdullo Quronov kitoblarini PDF shaklida oʻqish "
                            "va yuklab olish.", "kitoblar.html")
    return SHAPKA.format(title="Kitoblar PDF — Quronov.uz", yol="", dq="", sq="",
                         meta=meta_html) + f"""
<div class="wrap">
  <section class="intro">
    <h1>Kitoblar PDF</h1>
    <p>Kitoblar toʻliq holda, PDF koʻrinishida yuklab olish uchun qoʻyilgan.</p>
  </section>

  <div class="kitob-tanlov" role="tablist">
{tugmalar}
  </div>

{bolimlar}
</div>

<script>
(function () {{
  var tugma = document.querySelectorAll('.kitob-tugma');
  tugma.forEach(function (t) {{
    t.addEventListener('click', function () {{
      tugma.forEach(function (x) {{
        x.classList.toggle('tanlangan', x === t);
        document.getElementById('bolim-' + x.dataset.bolim).hidden = (x !== t);
      }});
    }});
  }});
}})();
</script>
""" + PODVAL


def main():
    CHIQISH_PDF.mkdir(parents=True, exist_ok=True)
    CHIQISH_MUQOVA.mkdir(parents=True, exist_ok=True)
    kitoblar = json.loads((ROOT / "data" / "books.json").read_text(encoding="utf-8"))

    tayyor = []
    for k in kitoblar:
        manba = ROOT / k["papka"] / k["pdf"]
        if not manba.exists():
            print(f"  PDF yo'q: {k['pdf']}")
            continue
        nishon = CHIQISH_PDF / f"{k['slug']}.pdf"
        if not nishon.exists():
            shutil.copy2(manba, nishon)
        k["fayl"] = nishon.name
        k["hajm"] = round(nishon.stat().st_size / 1048576, 1)
        k["muqova"] = muqova(k)
        tayyor.append(k)
        print(f"  + {k['year'] or '????'}  {k['hajm']:>5} MB  "
              f"{'muqova' if k['muqova'] else 'muqovasiz'}  {k['title'][:44]}")

    tayyor.sort(key=lambda k: -(k["year"] or 0))
    (SITE / "kitoblar.html").write_text(sahifa(tayyor), encoding="utf-8")
    print(f"\n{len(tayyor)} ta kitob joylandi")


if __name__ == "__main__":
    main()
