#!/usr/bin/env python3
"""MorMavi statik site üreticisi.

content/site.json (WordPress'ten alınan içerik) -> repo kökünde statik HTML.
Çalıştırma:  python3 tools/build.py
"""
import html
import json
import math
import os
import re
import shutil
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.mormavi.net"
NAME = "MorMavi Danışmanlık Merkezi"
PHONE = "+90 (507) 563 61 57"
PHONE_TEL = "+905075636157"
WA = "https://wa.me/905075636157"
EMAIL = "info@mormavi.net"
ADDRESS = "Cumhuriyet Mah. Halaskargazi Cd. Koza Apt. No:113 Kat:4 Daire:7, Şişli / İstanbul (Osmanbey Metro Çıkışı)"
MAP_EMBED = "https://maps.google.com/maps?q=41.054423,28.986904&z=16&output=embed"
PER_PAGE = 9
ROBOTS = "follow, index, max-snippet:-1, max-video-preview:-1, max-image-preview:large"

# Canlı sitede artık 404 veren / taşınmış adresler -> en ilgili mevcut sayfa
CIFT = "/hizmetler/cift-ve-aile-danismanligi/"
ONLINE = "/hizmetler/online-danismanlik/"
BIREYSEL = "/hizmetler/bireysel-danismanlik/"
REDIRECTS = {
    "/sisli-bolgesi-psikologlar/": "/sisli-psikolog/",
    "/online-psikolog-ucretleri/": ONLINE,
    "/aile-terapisti-sisli/": CIFT,
    "/cift-terapisi-istanbul/": CIFT,
    "/cift-terapisi-istanbul-avrupa-yakasi/": CIFT,
    "/aile-danismanligi/": CIFT,
    "/bireysel-terapi-fiyatlari-sisli/": BIREYSEL,
    "/psikolojik-aile-danismanligi/": CIFT,
    "/terapi-online/": ONLINE,
    "/duygu-odakli-cift-terapisi-uygulamalari/": CIFT,
    "/online-psikolog-cevrimici-terapi/": ONLINE,
    "/online-psikolog/": ONLINE,
    "/istanbul-en-iyi-cift-terapisi/": CIFT,
    "/online-terapi-ucretleri/": ONLINE,
    "/evlilik-terapisi-nedir/": CIFT,
    "/online-psikolojik-danismanlik-tavsiye/": ONLINE,
    "/en-iyi-online-psikolog/": ONLINE,
    "/aile-danismanligi-merkezi/": CIFT,
    "/aile-terapisti-avrupa-yakasi/": CIFT,
    "/cinsel-terapi-online/": ONLINE,
    "/cift-terapisi/": CIFT,
    "/cevrimici-terapi-hizmeti/": ONLINE,
    "/cift-terapisi-tavsiye/": CIFT,
    "/depresyon-tedavisi/": "/depresyon-belirtileri-ve-destek-yontemleri/",
    "/kalabaliklar-icindeki-yalnizlik-baglanti-caginda-neden-yalniz-hissediyoruz/": "/kalabaliklar-icinde-yalnizlik/",
    "/evlilik-terapisti-faydali-mi/": CIFT,
    "/istanbul-cift-terapisi/": CIFT,
    "/evlilik-terapisti-sisli/": CIFT,
    "/evlilik-terapisi/": CIFT,
    "/online-terapi-oneri/": ONLINE,
    "/psikolog-online/": ONLINE,
    "/cift-terapisi-istanbul-tavsiye/": CIFT,
    "/bosanma-surecinde-danismanlik-istanbul/": CIFT,
    "/online-cinsel-terapi/": ONLINE,
    "/psikolog-ucretleri/": "/hizmetlerimiz/",
    "/online-aile-danismanligi/": ONLINE,
    "/online-terapi-tavsiye/": ONLINE,
    # içerikte geçen eski / hatalı iç bağlantılar
    "/bireysel-danismanlik/": BIREYSEL,
    "/cift-ve-aile-danismanligi/": CIFT,
    "/cocuk-ve-ergen-terapisi/": "/hizmetler/cocuk-ve-ergen-terapisi/",
    "/online-danismanlik/": ONLINE,
    "/psikolog-besiktas/": "/besiktas-psikolog-2/",
    "/besiktas-psikolog/": "/besiktas-psikolog-2/",
    "/scl-90-psikolojik-belirti-tarama-testi/": "/scl-90-testi/",
    "/hizmetler/": "/hizmetlerimiz/",
    "/author/mehmet_durmus/": "/hakkimizda/",
    "/author/bkr/": "/hakkimizda/",
    "/category/genel/page/13/": "/category/genel/",
    "/category/genel/page/12/": "/category/genel/",
    "/category/genel/page/10/": "/category/genel/",
    "/category/genel/page/9/": "/category/genel/",
    "/category/genel/page/8/": "/category/genel/",
    "/category/genel/page/7/": "/category/genel/",
    "/category/genel/page/5/": "/category/genel/",
    "/category/genel/page/4/": "/category/genel/",
    "/blog/page/6/": "/blog/",
    "/blog/page/5/": "/blog/",
}
EXTERNAL_REDIRECTS = {"/whatsapp/": WA}

TESTS = {
    "/scl-90-testi/": ("/test.html", "SCL-90 Psikolojik Belirti Tarama Testi"),
    "/mmpi-testi/": ("/mmpi.html", "MMPI Çok Yönlü Kişilik Envanteri"),
}

MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
          "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

NAV = [
    ("/", "Ana Sayfa"),
    ("/hakkimizda/", "Hakkımızda"),
    ("/hizmetlerimiz/", "Hizmetler", [
        (BIREYSEL, "Bireysel Danışmanlık"),
        (CIFT, "Çift ve Aile Danışmanlığı"),
        ("/hizmetler/cocuk-ve-ergen-terapisi/", "Çocuk ve Ergen Terapisi"),
        (ONLINE, "Online Danışmanlık"),
        ("/hizmetler/grup-danismanligi/", "Grup Danışmanlığı"),
        ("/hizmetler/is-yeri-psikologu-ve-danismanlik/", "İş Yeri Psikoloğu"),
    ]),
    ("/scl-90-testi/", "Testler", [
        ("/scl-90-testi/", "SCL-90 Belirti Tarama Testi"),
        ("/mmpi-testi/", "MMPI Kişilik Envanteri"),
    ]),
    ("/blog/", "Blog"),
    ("/iletisim/", "İletişim"),
]
LOCATIONS = [("/nisantasi-psikolog/", "Nişantaşı Psikolog"), ("/sisli-psikolog/", "Şişli Psikolog"),
             ("/besiktas-psikolog-2/", "Beşiktaş Psikolog")]

esc = html.escape


def fmt_date(iso):
    d = datetime.fromisoformat(iso[:19])
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def strip_brand(t):
    t = html.unescape(t or "")
    return re.sub(r"\s*[|\-–]\s*(MorMavi|Mor Mavi)[^|]*$", "", t).strip()


def norm_path(href):
    """mormavi.net bağlantısını kök-göreli yola çevirir; dış bağlantıları aynen bırakır."""
    if href.startswith(("mailto:", "tel:", "#")):
        return href
    u = urlparse(href)
    if u.netloc and u.netloc not in ("www.mormavi.net", "mormavi.net"):
        return href
    if not u.netloc and not href.startswith("/"):
        return href
    path = u.path or "/"
    if "/wp-content/" not in path and not os.path.splitext(path)[1] and not path.endswith("/"):
        path += "/"
    return path + (("#" + u.fragment) if u.fragment else "")


class Site:
    def __init__(self):
        data = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))
        self.cats = {c["id"]: c for c in data["cats"]}
        self.pages = data["pages"]
        self.by_path = {p["path"]: p for p in self.pages}
        self.live = set(self.by_path)
        self.posts = sorted([p for p in self.pages if p["type"] == "post"], key=lambda p: p["date"], reverse=True)
        self.generated = []   # (path, lastmod, kind, image)
        self.missing_links = set()

    # ---------- içerik temizliği ----------
    def fix_link(self, href):
        if not href:
            return None
        if "google.com/url" in href:
            q = parse_qs(urlparse(href).query).get("q") or parse_qs(urlparse(href).query).get("url")
            return q[0] if q else None
        if re.search(r"wa\.me/5\d{9}\b", href):
            href = re.sub(r"wa\.me/(5\d{9})", r"wa.me/90\1", href)
        p = norm_path(href)
        if p.startswith("/") and "/wp-content/" not in p:
            base = p.split("#")[0]
            if re.match(r"^/\d{4}/\d{2}/\d{2}/$", base):
                return None  # tarih arşivi: bağlantıyı kaldır
            if base in REDIRECTS:
                return REDIRECTS[base]
            if base not in self.live and base not in ("/blog/",) and not base.startswith("/category/") \
                    and base not in TESTS and not base.endswith(".html"):
                self.missing_links.add(base)
        return p

    def clean(self, page):
        raw = page["html"].split("<!--[googlesitekit-end-of-content]-->")[0]  # sonrası yazar kutusu
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
        soup = BeautifulSoup(raw, "html.parser")
        author = None
        # yazı meta listesi (yazar / tarih)
        for ul in soup.find_all("ul"):
            a = ul.find("a", href=re.compile(r"/author/"))
            if a:
                author = " ".join(a.get_text().split())
                ul.decompose()
        # emoji görselleri
        for img in soup.find_all("img", src=re.compile(r"s\.w\.org/images/core/emoji")):
            img.replace_with(img.get("alt", ""))
        # bağlantılar
        for a in soup.find_all("a"):
            new = self.fix_link(a.get("href", "").strip())
            if not new:
                a.unwrap()
                continue
            a["href"] = new
            if new.startswith("http") and "mormavi.net" not in new:
                a["rel"] = "noopener"
                a["target"] = "_blank"
            if a.parent and a.parent.name in ("article", "[document]"):
                a["class"] = "btn-inline"
                a.string = " ".join(a.get_text().split())
        # görseller
        first = True
        for img in soup.find_all("img"):
            img["src"] = norm_path(img.get("src", ""))
            if not first:
                img["loading"] = "lazy"
            img["decoding"] = "async"
            first = False
        # tek H1 kuralı
        h1s = soup.find_all("h1")
        for extra in h1s[1:]:
            extra.name = "p"
            extra["class"] = "lead"
        # boş paragraflar
        for p in soup.find_all("p"):
            if not p.get_text(strip=True) and not p.find("img"):
                p.decompose()
        for hr in soup.find_all("hr"):
            prev = hr.find_previous_sibling()
            if prev is None:
                hr.decompose()
        art = soup.find("article")
        if art:
            art.unwrap()
        out = str(soup).strip()
        out = re.sub(r"(&nbsp;| |‎|‏)+", lambda m: " " if "nbsp" in m.group(0) or " " in m.group(0) else "", out)
        return out, author, bool(h1s)

    # ---------- şablon ----------
    def nav_html(self, current):
        items = []
        for item in NAV:
            href, label = item[0], item[1]
            active = ' aria-current="page"' if href == current else ""
            if len(item) == 3:
                sub = "".join(f'<li><a href="{h}">{esc(l)}</a></li>' for h, l in item[2])
                items.append(f'<li class="has-sub"><a href="{href}"{active}>{esc(label)}</a>'
                             f'<ul class="sub">{sub}</ul></li>')
            else:
                items.append(f'<li><a href="{href}"{active}>{esc(label)}</a></li>')
        return "".join(items)

    def layout(self, *, path, title, description, body, og_type="website", image="", image_alt="",
               ldjson=(), robots=ROBOTS, published="", modified="", extra_head="", breadcrumbs=None):
        canonical = SITE + path
        img_abs = (SITE + image) if image.startswith("/") else image
        meta = [
            f'<title>{esc(title)}</title>',
            f'<meta name="description" content="{esc(description)}">',
            f'<meta name="robots" content="{robots}">',
            f'<link rel="canonical" href="{canonical}">',
            '<meta property="og:locale" content="tr_TR">',
            f'<meta property="og:type" content="{og_type}">',
            f'<meta property="og:title" content="{esc(title)}">',
            f'<meta property="og:description" content="{esc(description)}">',
            f'<meta property="og:url" content="{canonical}">',
            f'<meta property="og:site_name" content="{NAME}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{esc(title)}">',
            f'<meta name="twitter:description" content="{esc(description)}">',
        ]
        if img_abs:
            meta += [f'<meta property="og:image" content="{img_abs}">',
                     f'<meta property="og:image:alt" content="{esc(image_alt or title)}">',
                     f'<meta name="twitter:image" content="{img_abs}">']
        if published:
            meta.append(f'<meta property="article:published_time" content="{published}+03:00">')
        if modified:
            meta += [f'<meta property="article:modified_time" content="{modified}+03:00">',
                     f'<meta property="og:updated_time" content="{modified}+03:00">']
        for j in ldjson:
            meta.append(f'<script type="application/ld+json">{j}</script>')
        crumbs = ""
        if breadcrumbs:
            parts = ['<a href="/">Ana Sayfa</a>'] + [
                (f'<a href="{h}">{esc(l)}</a>' if h else f'<span aria-current="page">{esc(l)}</span>')
                for h, l in breadcrumbs]
            crumbs = f'<nav class="crumbs wrap" aria-label="Sayfa yolu">{" <span>/</span> ".join(parts)}</nav>'
        year = datetime.now().year
        loc = " · ".join(f'<a href="{h}">{esc(l)}</a>' for h, l in LOCATIONS)
        return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{chr(10).join(meta)}
<meta name="theme-color" content="#3b3570">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{extra_head}
</head>
<body>
<a class="skip" href="#icerik">İçeriğe geç</a>
<header class="site-header">
  <div class="wrap nav">
    <a href="/" class="brand" aria-label="{NAME} ana sayfa"><span class="brand-mark" aria-hidden="true"><i></i><i></i></span><span>MorMavi</span></a>
    <button class="menu-toggle" aria-expanded="false" aria-controls="menu">Menü</button>
    <nav id="menu" class="menu" aria-label="Ana menü">
      <ul>{self.nav_html(path)}</ul>
      <a href="{WA}" class="btn btn-small" rel="noopener" target="_blank">WhatsApp ile Randevu</a>
    </nav>
  </div>
</header>
{crumbs}
<main id="icerik">
{body}
</main>
<aside class="crisis wrap" role="note"><strong>Acil bir durumdaysanız</strong> ya da kendinize zarar verme düşünceleriniz varsa lütfen beklemeyin: <a href="tel:112">112 Acil Çağrı Merkezi</a>'ni arayın veya en yakın acil servise başvurun.</aside>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <a href="/" class="brand"><span class="brand-mark" aria-hidden="true"><i></i><i></i></span><span>MorMavi</span></a>
      <p>Şişli &amp; Nişantaşı'nda yüz yüze, dünyanın her yerinde online psikolojik danışmanlık.</p>
    </div>
    <div>
      <h2>İletişim</h2>
      <p>{esc(ADDRESS)}</p>
      <p><a href="tel:{PHONE_TEL}">{PHONE}</a><br><a href="mailto:{EMAIL}">{EMAIL}</a></p>
      <p>Pazartesi – Cumartesi: 10:00 – 22:00</p>
    </div>
    <div>
      <h2>Hizmetler</h2>
      <ul>{"".join(f'<li><a href="{h}">{esc(l)}</a></li>' for h, l in NAV[2][2])}</ul>
    </div>
    <div>
      <h2>Bağlantılar</h2>
      <ul>
        <li><a href="/blog/">Blog</a></li>
        <li><a href="/scl-90-testi/">SCL-90 Testi</a></li>
        <li><a href="/mmpi-testi/">MMPI Testi</a></li>
        <li><a href="/gizlilik-ilkesi/">Gizlilik Politikası</a></li>
      </ul>
      <p class="locs">{loc}</p>
    </div>
  </div>
  <div class="wrap footer-bottom">© {year} {NAME}. Tüm hakları saklıdır.</div>
</footer>
<a class="wa-float" href="{WA}" rel="noopener" target="_blank" aria-label="WhatsApp ile yazın"><svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3zm0 23.7a10.7 10.7 0 0 1-5.5-1.5l-.4-.2-3.9 1 1-3.8-.2-.4A10.7 10.7 0 1 1 16 26.7zm5.9-8c-.3-.2-1.9-1-2.2-1s-.5-.2-.7.2-.8 1-1 1.2-.4.2-.7 0a8.8 8.8 0 0 1-4.4-3.8c-.3-.6.3-.5 1-1.6.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6a1.2 1.2 0 0 0-.9.4 3.7 3.7 0 0 0-1.1 2.7 6.5 6.5 0 0 0 1.4 3.4 14.8 14.8 0 0 0 5.6 5c2.1.9 2.9 1 4 .8a3.4 3.4 0 0 0 2.2-1.6 2.8 2.8 0 0 0 .2-1.6c0-.2-.3-.3-.6-.4z"/></svg></a>
<script src="/assets/site.js" defer></script>
</body>
</html>
"""

    def write(self, path, content, lastmod=None, kind=None, image=None):
        out = os.path.join(ROOT, path.lstrip("/"), "index.html") if path.endswith("/") else os.path.join(ROOT, path.lstrip("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        if kind:
            self.generated.append((path, lastmod, kind, image))

    # ---------- yardımcılar ----------
    def description(self, page, text_html):
        desc = html.unescape(page.get("description") or "").strip()
        if len(desc) >= 60:
            return desc
        txt = " ".join(BeautifulSoup(text_html, "html.parser").find_all(string=True)).strip()
        txt = re.sub(r"\s+", " ", txt)
        # başlığı atla
        h1 = page.get("h1") or ""
        if h1 and txt.startswith(h1):
            txt = txt[len(h1):].strip()
        if len(txt) > 155:
            txt = txt[:155].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
        return txt

    def first_image(self, page, body):
        m = re.search(r'<img[^>]+src="(/wp-content/[^"]+)"[^>]*alt="([^"]*)"', body)
        og = page.get("ogImage") or ""
        if og:
            return norm_path(og), page.get("ogImageAlt") or ""
        return (m.group(1), m.group(2)) if m else ("", "")

    def card(self, p):
        img = re.search(r'<img[^>]+src="([^"]+)"', p["_body"])
        img_html = f'<img src="{img.group(1)}" alt="" loading="lazy" decoding="async">' if img else ""
        cat = self.cats.get((p["categories"] or [1])[0], {}).get("name", "")
        excerpt = p["_desc"]
        return (f'<article class="post-card"><a href="{p["path"]}" class="post-card-img">{img_html}</a>'
                f'<div class="post-card-body"><p class="meta">{esc(cat)} · <time datetime="{p["date"][:10]}">{fmt_date(p["date"])}</time></p>'
                f'<h3><a href="{p["path"]}">{esc(p["_title"])}</a></h3><p>{esc(excerpt)}</p></div></article>')

    # ---------- sayfalar ----------
    def build_content_pages(self):
        for p in self.pages:
            body, author, has_h1 = self.clean(p)
            p["_body"], p["_author"] = body, author
            p["_title"] = html.unescape(p["h1"]) if p.get("h1") else strip_brand(p.get("ogTitle") or p["title"])
            p["_desc"] = self.description(p, body)
        for p in self.pages:
            path = p["path"]
            if path == "/blog/":
                continue
            body = p["_body"]
            image, image_alt = self.first_image(p, body)
            has_h1 = "<h1" in body
            kind = p["type"]
            heading = "" if has_h1 else f'<h1>{esc(p["_title"])}</h1>'
            crumbs = None
            if kind == "post":
                cat = self.cats.get((p["categories"] or [1])[0])
                crumbs = [(f'/category/{cat["slug"]}/', cat["name"]), (None, p["_title"])] if cat else [(None, p["_title"])]
                tags = " ".join(f'<a class="chip" href="/category/{self.cats[c]["slug"]}/">{esc(self.cats[c]["name"])}</a>'
                                for c in p["categories"] if c in self.cats)
                related = [q for q in self.posts if q is not p and set(q["categories"]) & set(p["categories"])][:3]
                if len(related) < 3:
                    related += [q for q in self.posts if q is not p and q not in related][:3 - len(related)]
                meta_line = (f'<p class="post-meta">{esc(p["_author"] or "MorMavi")} · '
                             f'<time datetime="{p["date"]}">{fmt_date(p["date"])}</time></p>')
                # meta satırını H1'in hemen arkasına koy
                if has_h1:
                    body = re.sub(r"(</h1>)", r"\1" + meta_line, body, count=1)
                else:
                    heading += meta_line
                main = f"""<article class="wrap narrow prose post">
{heading}{body}
<div class="post-tags">{tags}</div>
<div class="cta-box"><h2>Bu konuda destek almak ister misiniz?</h2><p>Şişli &amp; Nişantaşı merkezimizde yüz yüze ya da online seans için bize ulaşın.</p><p><a class="btn" href="{WA}" rel="noopener" target="_blank">WhatsApp ile Randevu</a> <a class="btn btn-ghost" href="tel:{PHONE_TEL}">{PHONE}</a></p></div>
</article>
<section class="wrap related"><h2>Bunları da okuyabilirsiniz</h2><div class="post-grid">{"".join(self.card(q) for q in related)}</div></section>"""
                og_type = "article"
            else:
                if path in TESTS:
                    src, label = TESTS[path]
                    frame = (f'<div class="test-frame"><iframe src="{src}" title="{esc(label)}" loading="lazy"></iframe></div>'
                             f'<p class="fine">Test yüklenmiyorsa <a href="{src}">buradan tam ekran açabilirsiniz</a>.</p>')
                    body = frame + body
                if path == "/iletisim/":
                    body += (f'<div class="map"><iframe src="{MAP_EMBED}" title="MorMavi Danışmanlık Merkezi konumu" '
                             'loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>')
                cls = "home" if path == "/" else "page"
                crumbs = None if path == "/" else [(None, p["_title"])]
                if kind == "hizmetler":
                    crumbs = [("/hizmetlerimiz/", "Hizmetler"), (None, p["_title"])]
                cta = "" if path == "/" else (f'<div class="cta-box"><h2>Randevu ve bilgi için</h2><p>Şişli &amp; Nişantaşı merkezimizde yüz yüze ya da online seans planlamak için bize ulaşın.</p>'
                                               f'<p><a class="btn" href="{WA}" rel="noopener" target="_blank">WhatsApp ile Randevu</a> <a class="btn btn-ghost" href="tel:{PHONE_TEL}">{PHONE}</a></p></div>')
                extra = ""
                if path == "/":
                    extra = (f'<section class="home-latest"><h2>Blogdan son yazılar</h2><div class="post-grid">'
                             f'{"".join(self.card(q) for q in self.posts[:3])}</div><p><a class="link-arrow" href="/blog/">Tüm yazılar →</a></p></section>')
                main = f'<article class="wrap prose {cls}">\n{heading}{body}\n{cta}{extra}</article>'
                og_type = "website" if path == "/" else "article"
            title = html.unescape(p["title"])
            out = self.layout(path=path, title=title, description=p["_desc"], body=main, og_type=og_type,
                              image=image, image_alt=image_alt, ldjson=p.get("ldjson") or [],
                              robots=p.get("robots") or ROBOTS,
                              published=p["date"] if kind == "post" else "", modified=p.get("modified") or "",
                              breadcrumbs=crumbs)
            sitemap_kind = {"post": "post", "hizmetler": "hizmetler"}.get(kind, "page")
            self.write(path, out, (p.get("modified") or p.get("date") or "")[:10] or None, sitemap_kind, image)

    def build_listing(self, base, title, heading, intro, posts, desc, crumbs):
        pages = max(1, math.ceil(len(posts) / PER_PAGE))
        for n in range(1, pages + 1):
            chunk = posts[(n - 1) * PER_PAGE:n * PER_PAGE]
            path = base if n == 1 else f"{base}page/{n}/"
            links = []
            if n > 1:
                links.append(f'<a rel="prev" href="{base if n == 2 else f"{base}page/{n-1}/"}">← Önceki</a>')
            links.append(f"<span>Sayfa {n} / {pages}</span>")
            if n < pages:
                links.append(f'<a rel="next" href="{base}page/{n+1}/">Sonraki →</a>')
            body = (f'<section class="wrap listing"><h1>{esc(heading)}</h1><p class="lead">{esc(intro)}</p>'
                    f'<div class="post-grid">{"".join(self.card(p) for p in chunk)}</div>'
                    f'<nav class="pager" aria-label="Sayfalar">{" ".join(links)}</nav></section>')
            t = title if n == 1 else f"{title} - Sayfa {n}"
            ld = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage", "name": t,
                             "url": SITE + path, "isPartOf": {"@id": SITE + "/#website"}}, ensure_ascii=False)
            out = self.layout(path=path, title=t, description=desc, body=body, ldjson=[ld],
                              breadcrumbs=crumbs if n == 1 else crumbs[:-1] + [(base, crumbs[-1][1]), (None, f"Sayfa {n}")])
            lastmod = max(p["modified"] for p in chunk)[:10] if chunk else None
            self.write(path, out, lastmod, "category" if n == 1 and base.startswith("/category/") else ("page" if n == 1 else None))

    def build_listings(self):
        blog = self.by_path.get("/blog/")
        self.build_listing("/blog/", "Blog - MorMavi Danışmanlık Merkezi", "Blog",
                           "Kaygı, ilişkiler, öz şefkat, stres ve daha fazlası üzerine uzman psikologlarımızın yazıları.",
                           self.posts, "MorMavi Danışmanlık Merkezi uzman psikologlarından kaygı, ilişkiler, stres yönetimi ve ruh sağlığı üzerine güncel yazılar.",
                           [(None, "Blog")])
        for c in self.cats.values():
            posts = [p for p in self.posts if c["id"] in p["categories"]]
            if not posts:
                continue
            self.build_listing(f'/category/{c["slug"]}/', f'{c["name"]} - MorMavi Danışmanlık Merkezi', c["name"],
                               f'“{c["name"]}” kategorisindeki yazılarımız.', posts,
                               f'{c["name"]} kategorisinde MorMavi Danışmanlık Merkezi uzman psikologlarının yazıları.',
                               [("/blog/", "Blog"), (None, c["name"])])

    def redirect_page(self, target):
        url = target if target.startswith("http") else SITE + target
        return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<title>Yönlendiriliyor…</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(target)} + location.hash);</script>
</head><body><p>Bu sayfa taşındı: <a href="{target}">{url}</a></p></body></html>
"""

    def build_redirects(self):
        lines = ["# Kalıcı yönlendirmeler (Cloudflare Pages/Workers _redirects biçimi)",
                 "# GitHub Pages bu dosyayı okumaz; aynı adreslerdeki HTML yönlendirme sayfaları devreye girer."]
        for src, dst in {**REDIRECTS, **EXTERNAL_REDIRECTS}.items():
            if src in self.live:
                continue
            code = 302 if dst.startswith("http") else 301
            lines.append(f"{src} {dst} {code}")
            lines.append(f"{src.rstrip('/')} {dst} {code}")
            self.write(src, self.redirect_page(dst))
        with open(os.path.join(ROOT, "_redirects"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def build_404(self):
        body = ('<section class="wrap narrow prose page notfound"><h1>Aradığınız sayfa bulunamadı</h1>'
                '<p>Sayfa taşınmış ya da kaldırılmış olabilir. Aşağıdaki bağlantılardan devam edebilirsiniz.</p>'
                '<p><a class="btn" href="/">Ana sayfaya dön</a> <a class="btn btn-ghost" href="/blog/">Blog</a></p></section>')
        out = self.layout(path="/404.html", title="Sayfa bulunamadı - MorMavi", description="Aradığınız sayfa bulunamadı.",
                          body=body, robots="noindex, follow")
        self.write("/404.html", out)

    def build_sitemaps(self):
        groups = {}
        for path, lastmod, kind, image in self.generated:
            groups.setdefault(kind, []).append((path, lastmod, image))
        names = {"page": "page-sitemap.xml", "post": "post-sitemap.xml",
                 "hizmetler": "hizmetler-sitemap.xml", "category": "category-sitemap.xml"}
        index = []
        all_urls = []
        for kind, fname in names.items():
            urls = sorted(groups.get(kind, []), key=lambda u: (u[0] != "/", u[0]))
            rows = []
            for path, lastmod, image in urls:
                img = f"<image:image><image:loc>{SITE + image}</image:loc></image:image>" if image and image.startswith("/") else ""
                lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
                rows.append(f"<url><loc>{SITE + path}</loc>{lm}{img}</url>")
                all_urls.append(rows[-1])
            xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                   'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "\n".join(rows) + "\n</urlset>\n")
            open(os.path.join(ROOT, fname), "w", encoding="utf-8").write(xml)
            newest = max((u[1] for u in urls if u[1]), default=None)
            index.append(f"<sitemap><loc>{SITE}/{fname}</loc>" + (f"<lastmod>{newest}</lastmod>" if newest else "") + "</sitemap>")
        idx = ('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "\n".join(index) + "\n</sitemapindex>\n")
        open(os.path.join(ROOT, "sitemap_index.xml"), "w", encoding="utf-8").write(idx)
        open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(idx)
        robots = (f"User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /content/\n\n"
                  f"Sitemap: {SITE}/sitemap_index.xml\n")
        open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(robots)
        return len(all_urls)

    def verify(self):
        """Üretilen her sayfadaki yerel görsel ve iç bağlantıların var olduğunu kontrol eder."""
        bad = set()
        for dirpath, _, files in os.walk(ROOT):
            if any(x in dirpath for x in ("/.git", "/tools", "/content", "/wp-content")):
                continue
            for fn in files:
                if not fn.endswith(".html"):
                    continue
                txt = open(os.path.join(dirpath, fn), encoding="utf-8").read()
                for ref in re.findall(r'(?:src|href)="(/[^"#?]*)', txt):
                    target = os.path.join(ROOT, ref.lstrip("/"))
                    if ref.endswith("/"):
                        target = os.path.join(target, "index.html")
                    if not os.path.exists(target):
                        bad.add(ref)
        if bad:
            print("UYARI - eksik dosya/bağlantı:", sorted(bad))

    def build_tests(self):
        """Gömülü test araçlarını kopyalar; ayrı sayfa olarak dizine girmemeleri için noindex ekler."""
        for src, (parent) in (("test.html", "/scl-90-testi/"), ("mmpi.html", "/mmpi-testi/")):
            fp = os.path.join(ROOT, "content", "tests", src)
            if not os.path.exists(fp):
                continue
            txt = open(fp, encoding="utf-8").read()
            tag = f'<meta name="robots" content="noindex, follow"><link rel="canonical" href="{SITE}{parent}">'
            txt = re.sub(r"(<head[^>]*>)", r"\1" + tag, txt, count=1, flags=re.I)
            open(os.path.join(ROOT, src), "w", encoding="utf-8").write(txt)

    def run(self):
        # önceki çıktıyı temizle (yalnızca üretilen klasörler)
        for p in list(self.live) + list(REDIRECTS) + list(EXTERNAL_REDIRECTS) + ["/blog/", "/category/"]:
            if p != "/":
                d = os.path.join(ROOT, p.strip("/").split("/")[0])
                if os.path.isdir(d) and not d.endswith("wp-content"):
                    shutil.rmtree(d)
        self.build_content_pages()
        self.build_listings()
        self.build_redirects()
        self.build_404()
        self.build_tests()
        n = self.build_sitemaps()
        self.verify()
        print(f"{len(self.generated)} sayfa, {n} sitemap adresi, {len(REDIRECTS) + len(EXTERNAL_REDIRECTS)} yönlendirme")
        if self.missing_links:
            print("UYARI - hedefi olmayan iç bağlantılar:", sorted(self.missing_links))


if __name__ == "__main__":
    Site().run()
