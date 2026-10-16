# MorMavi Danışmanlık Merkezi — www.mormavi.net

WordPress sitesinden taşınmış statik site. Her sayfa WordPress'teki **aynı adreste** durur
(başlık, açıklama, canonical, Open Graph ve Rank Math şema verisi korunmuştur).

## Yapı
- `content/site.json` — WordPress'ten alınan içerik (sayfalar, yazılar, hizmetler, kategoriler)
- `content/tests/` — SCL-90 ve MMPI test araçlarının orijinalleri
- `tools/build.py` — siteyi üretir: `pip install beautifulsoup4 && python3 tools/build.py`
- `wp-content/uploads/` — görseller (WordPress'teki yollarla aynı)
- `assets/` — stil ve menü betiği

## SEO
- `sitemap_index.xml` (+ page / post / hizmetler / category sitemap'leri), `robots.txt`
- Kaldırılmış eski adresler için `_redirects` (Cloudflare'de gerçek 301) ve aynı yerde HTML
  yönlendirme sayfaları (GitHub Pages için). Liste: `tools/build.py` içindeki `REDIRECTS`.
- `google3034ee08a6fa2605.html` — Search Console doğrulama dosyası (silmeyin).

## Yeni yazı eklemek
`content/site.json` içine yeni bir kayıt ekleyip `python3 tools/build.py` çalıştırın.
