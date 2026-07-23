#!/usr/bin/env python3
"""
generate.py — Générateur de site maçon
Usage: python3 generate.py [chemin/vers/config.json]
       python3 generate.py  (utilise config-exemple.json par défaut)
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
TEMPLATES = BASE / "templates"

# ── Chargement config ─────────────────────────────────────────────────────────
config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "config-exemple.json"
with open(config_path, encoding="utf-8") as f:
    config = json.load(f)

SLUG = config["SLUG"]
OUTPUT = BASE / "output" / SLUG
IMAGES_SRC = BASE / "images"

# ── Nettoyage + création dossier output (préserve .git) ──────────────────────
if OUTPUT.exists():
    for item in OUTPUT.iterdir():
        if item.name == ".git":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
else:
    OUTPUT.mkdir(parents=True)

# Copie du dossier images source s'il existe
if IMAGES_SRC.exists():
    shutil.copytree(IMAGES_SRC, OUTPUT / "images")

print(f"✓ Dossier output : {OUTPUT}")

# ── Lecture index.html source ─────────────────────────────────────────────────
index_src = (BASE / "index.html").read_text(encoding="utf-8")

# ── Extraction CSS partagé ────────────────────────────────────────────────────
css_match = re.search(r'<style>([\s\S]*?)</style>', index_src)
shared_css = f"<style>{css_match.group(1)}</style>" if css_match else ""

# Le dark mode + .card sont désormais dans le CSS partagé de index.html (pas de doublon ici)
shared_css += """
<style>
.card{background:var(--card,var(--bg))}
</style>"""

# ── Extraction HEADER ─────────────────────────────────────────────────────────
header_match = re.search(r'(<header[\s\S]*?</header>)', index_src)
shared_header = header_match.group(1) if header_match else ""

# Drawer mobile (juste après </header>)
drawer_match = re.search(r'(<nav class="mob-drawer"[\s\S]*?</nav>)', index_src)
if drawer_match:
    shared_header += "\n" + drawer_match.group(1)

# ── Extraction FOOTER ─────────────────────────────────────────────────────────
footer_match = re.search(r'(<footer[\s\S]*?</footer>)', index_src)
shared_footer = footer_match.group(1) if footer_match else ""

# ── Extraction JS partagé ─────────────────────────────────────────────────────
# Prendre tout ce qui est entre </footer> et </body>
script_match = re.search(r'</footer>([\s\S]*?)</body>', index_src)
shared_script = script_match.group(1).strip() if script_match else ""

print("✓ Composants partagés extraits (CSS, header, footer, JS)")

# ── Génération ZONE_CHIPS et FOOTER_ZONE_LINKS (avant pré-résolution) ────────
zones = config.get("ZONES", [])

zone_chips_html = ""
for z in zones:
    zone_chips_html += (
        f'<a href="/macon-{z["SLUG"]}/" class="zone-chip">'
        f'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'
        f'{z["VILLE"]}</a>\n'
    )

footer_zone_links_html = ""
for z in zones:
    footer_zone_links_html += (
        f'<li><a href="/macon-{z["SLUG"]}/">Maçon à {z["VILLE"]}</a></li>\n'
    )

# ── Cloudflare Web Analytics ─────────────────────────────────────────────────
def _cf_analytics_script():
    token = config.get("CF_ANALYTICS_TOKEN", "")
    if not token:
        return ""
    return f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token": "{token}"}}\' crossorigin="anonymous"></script>'

# ── Variables de base — mapping simple pour pré-résolution ───────────────────
_base_simple = {
    "ENTREPRISE":     config["ENTREPRISE"],
    "VILLE":          config["VILLE"],
    "DEPARTEMENT":    config["DEPARTEMENT"],
    "CODE_POSTAL":    config["CODE_POSTAL"],
    "TEL_DISPLAY":    config["TEL_DISPLAY"],
    "TEL_RAW":        config["TEL_RAW"],
    "EMAIL":          config["EMAIL"],
    "PRENOM":         config["PRENOM"],
    "EXPERIENCE":     config["EXPERIENCE"],
    "NB_CHANTIERS":   config["NB_CHANTIERS"],
    "NOTE":           config["NOTE"],
    "NB_AVIS":        config["NB_AVIS"],
    "SIRET":          config["SIRET"],
    "RAYON":          config["RAYON"],
    "DOMAIN":         config["DOMAIN"],
    "FORM_ACTION":    config["FORM_ACTION"],
    "WEB3FORMS_KEY":        config.get("WEB3FORMS_KEY", ""),
    "CF_ANALYTICS_SCRIPT":  _cf_analytics_script(),
    "ANNEE":                config.get("ANNEE", "2025"),
    "ANNEE_CREATION":       config.get("ANNEE_CREATION", "2010"),
    "LAT":                  config.get("LAT", ""),
    "LNG":                  config.get("LNG", ""),
    "ZONE_CHIPS":           zone_chips_html,
    "FOOTER_ZONE_LINKS":    footer_zone_links_html,
}

def _apply_simple(text):
    for k, v in _base_simple.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text

# Pré-résolution des variables dans les composants partagés
shared_header = _apply_simple(shared_header)
shared_footer = _apply_simple(shared_footer)
shared_script = _apply_simple(shared_script)

# ── Variables de base (depuis config) ─────────────────────────────────────────
def build_vars(extra=None):
    v = {
        "ENTREPRISE":     config["ENTREPRISE"],
        "VILLE":          config["VILLE"],
        "DEPARTEMENT":    config["DEPARTEMENT"],
        "REGION":         config.get("REGION", ""),
        "CODE_POSTAL":    config["CODE_POSTAL"],
        "TEL_DISPLAY":    config["TEL_DISPLAY"],
        "TEL_RAW":        config["TEL_RAW"],
        "EMAIL":          config["EMAIL"],
        "PRENOM":         config["PRENOM"],
        "EXPERIENCE":     config["EXPERIENCE"],
        "NB_CHANTIERS":   config["NB_CHANTIERS"],
        "NOTE":           config["NOTE"],
        "NB_AVIS":        config["NB_AVIS"],
        "SIRET":          config["SIRET"],
        "RAYON":          config["RAYON"],
        "DOMAIN":         config["DOMAIN"],
        "FORM_ACTION":    config["FORM_ACTION"],
        "WEB3FORMS_KEY":  config.get("WEB3FORMS_KEY", ""),
        "ANNEE":          config.get("ANNEE", "2025"),
        "ANNEE_CREATION": config.get("ANNEE_CREATION", "2010"),
        "LAT":            config.get("LAT", ""),
        "LNG":            config.get("LNG", ""),
        "SHARED_STYLE":   shared_css,
        "HEADER":         shared_header,
        "FOOTER":         shared_footer,
        "SHARED_SCRIPT":  shared_script,
        "CF_ANALYTICS_SCRIPT": _cf_analytics_script(),
    }
    # Mentions légales
    mentions = config.get("MENTIONS", {})
    v["MENTIONS_FORME_JURIDIQUE"] = mentions.get("FORME_JURIDIQUE", "SARL")
    v["MENTIONS_CAPITAL"]         = mentions.get("CAPITAL", "")
    v["MENTIONS_RCS"]             = mentions.get("RCS", config["VILLE"])
    v["MENTIONS_TVA_INTRA"]       = mentions.get("TVA_INTRA", "")
    v["MENTIONS_HEBERGEUR"]       = mentions.get("HEBERGEUR", "Cloudflare Pages")
    v["MENTIONS_HEBERGEUR_ADRESSE"] = mentions.get("HEBERGEUR_ADRESSE", "")
    v["GOOGLE_MAPS_KEY"] = config.get("GOOGLE_MAPS_KEY", "")
    v["GOOGLE_PLACE_ID"] = config.get("GOOGLE_PLACE_ID", "")
    v["GOOGLE_GMB_URL"]  = config.get("GOOGLE_GMB_URL", "")

    if extra:
        v.update(extra)
    return v


def apply_vars(template_str, variables):
    """Remplace tous les {{VAR}} par leur valeur."""
    result = template_str
    for key, val in variables.items():
        result = result.replace("{{" + key + "}}", str(val))
    return result


def write_page(folder, html_content):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(html_content, encoding="utf-8")


# ── Génération AVIS HTML ──────────────────────────────────────────────────────
avis_list = config.get("AVIS", [{}, {}, {}])
avis_vars = {}
for i, avis in enumerate(avis_list[:3], 1):
    avis_vars[f"AVIS_{i}_NOM"]       = avis.get("NOM", "")
    avis_vars[f"AVIS_{i}_INITIALES"] = avis.get("INITIALES", "")
    avis_vars[f"AVIS_{i}_TEXTE"]     = avis.get("TEXTE", "")
    avis_vars[f"AVIS_{i}_PROJET"]    = avis.get("PROJET", "")

# ── Photos ────────────────────────────────────────────────────────────────────
photos = config.get("PHOTOS", {})
hero_photo = photos.get("HERO", "")
real_photos = photos.get("REALISATIONS", ["", "", "", "", ""])

def photo_tag(src, alt="Réalisation maçonnerie"):
    if src:
        return f'<img class="real-ph" src="{src}" alt="{alt}" loading="lazy" decoding="async" width="800" height="600">'
    return '<div class="real-ph">Photo à venir</div>'

# ── PAGE : index.html ─────────────────────────────────────────────────────────
photo_real_vars = {f"PHOTO_REAL_{i}": photo_tag(src, f"Réalisation maçonnerie {i}") for i, src in enumerate(real_photos[:5], 1)}

base_vars = build_vars({
    "ZONE_CHIPS": zone_chips_html,
    "FOOTER_ZONE_LINKS": footer_zone_links_html,
    **avis_vars,
    **photo_real_vars,
})

# index.html se suffit à lui-même (pas de {{SHARED_STYLE}} etc.)
# On applique les variables directement sur index.html complet
index_html = apply_vars(index_src, base_vars)
# Résoudre les variables dans les SERVICES/ZONES qui pourraient être dans index
write_page(OUTPUT, index_html)
print("✓ index.html")

# ── PAGE : devis ──────────────────────────────────────────────────────────────
devis_tpl = (TEMPLATES / "devis.html").read_text(encoding="utf-8")
devis_html = apply_vars(devis_tpl, build_vars())
write_page(OUTPUT / "devis", devis_html)
print("✓ devis/index.html")

# ── PAGE : merci ──────────────────────────────────────────────────────────────
merci_tpl = (TEMPLATES / "merci.html").read_text(encoding="utf-8")
merci_html = apply_vars(merci_tpl, build_vars())
write_page(OUTPUT / "merci", merci_html)
print("✓ merci/index.html")

# ── PAGE : réalisations ───────────────────────────────────────────────────────
reals_tpl = (TEMPLATES / "realisations.html").read_text(encoding="utf-8")
reals_vars = build_vars()
for i, src in enumerate(real_photos[:5], 1):
    reals_vars[f"PHOTO_REAL_{i}"] = photo_tag(src, f"Réalisation maçonnerie {i}")
reals_html = apply_vars(reals_tpl, reals_vars)
write_page(OUTPUT / "realisations", reals_html)
print("✓ realisations/index.html")

# ── PAGE : mentions légales ───────────────────────────────────────────────────
mentions_tpl = (TEMPLATES / "mentions-legales.html").read_text(encoding="utf-8")
mentions_html = apply_vars(mentions_tpl, build_vars())
write_page(OUTPUT / "mentions-legales", mentions_html)
print("✓ mentions-legales/index.html")

# ── PAGES SERVICE ─────────────────────────────────────────────────────────────
service_tpl = (TEMPLATES / "service.html").read_text(encoding="utf-8")
services = config.get("SERVICES", [])

AVANTAGE_ICONS = [
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="20 6 9 17 4 12"/></svg>',
]

for svc in services:
    # Avantages → Option B (icône + titre)
    avantages_html = ""
    for i, av in enumerate([_apply_simple(a) for a in svc.get("AVANTAGES", [])]):
        icon = AVANTAGE_ICONS[i % len(AVANTAGE_ICONS)]
        avantages_html += (
            '<div class="avantage">'
            f'<div class="avantage-icon">{icon}</div>'
            f'<h4>{av}</h4>'
            '</div>\n'
        )

    # FAQ → HTML accordion
    faq_html = ""
    for item in svc.get("FAQ", []):
        q = _apply_simple(item.get("Q", ""))
        a = _apply_simple(item.get("A", ""))
        faq_html += (
            '<div class="faq-item">'
            f'<button class="faq-q">{q}'
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>'
            f'</button><div class="faq-a"><p>{a}</p></div></div>\n'
        )

    # FAQ Schema JSON-LD
    faq_entities = []
    for item in svc.get("FAQ", []):
        q = _apply_simple(item.get("Q", ""))
        a = _apply_simple(item.get("A", ""))
        faq_entities.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    faq_schema_json = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_entities}, ensure_ascii=False)

    # Google Reviews section + script
    gmaps_key = config.get("GOOGLE_MAPS_KEY", "")
    place_id  = config.get("GOOGLE_PLACE_ID", "")
    gmb_url   = config.get("GOOGLE_GMB_URL", "")
    if gmaps_key and place_id:
        gmb_btn = (f'<div class="gmb-footer reveal d3"><a href="{gmb_url}" target="_blank" rel="noopener" class="btn btn-outline">Voir tous les avis sur Google</a>'
                   f'<p class="gmb-note">Avis collectés via Google My Business</p></div>') if gmb_url else ""
        gmb_section_html = (
            '<section class="section" id="avis-google">'
            '<div class="inner">'
            '<div class="section-label reveal">Avis Google</div>'
            f'<h2 class="section-h2 reveal d1">Ce que disent<br>nos clients</h2>'
            '<div id="gmb-reviews" class="gmb-grid reveal d2"><div class="gmb-loading">Chargement des avis…</div></div>'
            f'{gmb_btn}'
            '</div></section>'
        )
        gmb_script = (
            '<script>'
            f'window.__PLACE_ID="{place_id}";'
            'function __initGMB(){'
            'var d=document.createElement("div");'
            'var s=new google.maps.places.PlacesService(d);'
            'var el=document.getElementById("gmb-reviews");'
            'if(!el)return;'
            'el.innerHTML="<div class=\\"gmb-loading\\">Chargement…</div>";'
            'try{s.getDetails({placeId:window.__PLACE_ID,fields:["reviews","rating"]},function(p,st){'
            'if(st!==google.maps.places.PlacesServiceStatus.OK||!p||!p.reviews){el.innerHTML="";return;}'
            'el.innerHTML=p.reviews.slice(0,5).map(function(r){'
            'var stars="★".repeat(r.rating)+"☆".repeat(5-r.rating);'
            'var av=r.profile_photo_url'
            '?"<img class=\\"gmb-avatar\\" src=\\""+r.profile_photo_url+"\\" alt=\\""+r.author_name+"\\" loading=\\"lazy\\">"'
            ':"<div class=\\"gmb-avatar-letter\\">"+r.author_name.charAt(0)+"</div>";'
            'return"<div class=\\"gmb-card\\"><div class=\\"gmb-header\\">"+av'
            '+"<div><div class=\\"gmb-name\\">"+r.author_name+"</div><div class=\\"gmb-stars\\">"+stars+"</div></div>"'
            '+"<div class=\\"gmb-date\\">"+r.relative_time_description+"</div></div>"'
            '+"<p class=\\"gmb-text\\">"+r.text+"</p></div>";'
            '}).join("");'
            '});}catch(e){el.innerHTML="";}'
            '}'
            '</script>'
            f'<script async src="https://maps.googleapis.com/maps/api/js?key={gmaps_key}&libraries=places&callback=__initGMB"></script>'
        )
    else:
        gmb_section_html = ""
        gmb_script = ""

    # Galerie photos
    gallery_photos = svc.get("GALLERY", [])
    if not gallery_photos:
        gallery_photos = [p for p in real_photos[:3] if p]
    gallery_html = ""
    for photo in gallery_photos[:3]:
        gallery_html += (
            f'<div class="svc-gallery-item">'
            f'<img src="{photo}" alt="Réalisation {svc["NOM_COURT"]} {config["VILLE"]}" '
            f'loading="lazy" decoding="async" width="600" height="450">'
            f'</div>\n'
        )

    # Témoignage
    temo = svc.get("TEMOIGNAGE", {})
    if temo:
        temo_html = (
            '<div class="svc-temo-stars">★★★★★</div>'
            f'<blockquote>« {temo.get("TEXTE","")} »</blockquote>'
            '<div class="svc-temo-author">'
            f'<div class="svc-temo-avatar">{temo.get("INITIALES","")}</div>'
            '<div>'
            f'<div class="svc-temo-nom">{temo.get("NOM","")}</div>'
            f'<div class="svc-temo-projet">{temo.get("PROJET","")}</div>'
            '</div></div>'
        )
    else:
        temo_html = ""

    # Prix
    prix = svc.get("PRIX", {})
    check_svg = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
    prix_lignes_html = "".join(
        f'<div class="prix-ligne">{check_svg}{ligne}</div>\n'
        for ligne in prix.get("LIGNES", [])
    )
    if prix:
        prix_html = (
            '<div class="prix-left">'
            f'<div class="prix-fourchette">{prix.get("FOURCHETTE","")}</div>'
            f'<div class="prix-unite">{prix.get("UNITE","")}</div>'
            f'<p class="prix-note">{prix.get("NOTE","")}</p>'
            '<a href="/devis/" class="prix-cta-devis">Obtenir mon devis gratuit →</a>'
            '</div>'
            '<div class="prix-right">'
            '<div class="prix-inclus-title">Compris dans notre devis :</div>'
            f'{prix_lignes_html}'
            '<p class="prix-bas">Devis gratuit et détaillé sous 48h après visite sur place. Sans engagement.</p>'
            '</div>'
        )
    else:
        prix_html = ""

    svc_photo = svc.get("PHOTO", "")
    svc_photo_html = (
        f'<div class="service-hero-media reveal d2">'
        f'<img src="{svc_photo}" alt="{svc["NOM"]} {config["VILLE"]}" '
        f'width="480" height="360" loading="eager" decoding="async">'
        f'</div>'
    ) if svc_photo else ""

    svc_vars = build_vars({
        "SERVICE_NOM":              svc["NOM"],
        "SERVICE_SLUG":             svc["SLUG"],
        "SERVICE_NOM_COURT":        svc["NOM_COURT"],
        "SERVICE_TITRE_H1":         svc["TITRE_H1"],
        "SERVICE_DESCRIPTION_SEO":  svc["DESCRIPTION_SEO"],
        "SERVICE_INTRO":            svc["INTRO"],
        "SERVICE_AVANTAGES_HTML":   avantages_html,
        "SERVICE_FAQ_HTML":         faq_html,
        "SERVICE_HERO_PHOTO_HTML":  svc_photo_html,
        "SERVICE_GALLERY_HTML":     gallery_html,
        "SERVICE_TEMOIGNAGE_HTML":  temo_html,
        "SERVICE_PRIX_HTML":        prix_html,
        "SERVICE_FAQ_SCHEMA":       faq_schema_json,
        "GMB_SECTION_HTML":         gmb_section_html,
        "GMB_SCRIPT":               gmb_script,
        "ZONE_CHIPS":               zone_chips_html,
    })
    # Résoudre les variables internes (ex: {{VILLE}} dans TITRE_H1)
    for key in ("SERVICE_TITRE_H1", "SERVICE_DESCRIPTION_SEO", "SERVICE_INTRO"):
        svc_vars[key] = apply_vars(svc_vars[key], svc_vars)

    svc_html = apply_vars(service_tpl, svc_vars)
    write_page(OUTPUT / svc["SLUG"], svc_html)
    print(f"✓ {svc['SLUG']}/index.html")

# ── PAGES ZONE ────────────────────────────────────────────────────────────────
zone_tpl = (TEMPLATES / "zone.html").read_text(encoding="utf-8")

for zone in zones:
    z_ville = zone["VILLE"]
    z_ent   = config["ENTREPRISE"]
    z_title_long  = f"Maçon à {z_ville} — {z_ent} | Devis gratuit"
    z_title_short = f"Maçon à {z_ville} — {z_ent}"
    zone_title = z_title_long if len(z_title_long) <= 60 else z_title_short
    zone_vars = build_vars({
        "ZONE_VILLE":      z_ville,
        "ZONE_SLUG":       zone["SLUG"],
        "ZONE_CODE_POSTAL": zone["CODE_POSTAL"],
        "ZONE_TITLE":      zone_title,
    })
    zone_html = apply_vars(zone_tpl, zone_vars)
    write_page(OUTPUT / f"macon-{zone['SLUG']}", zone_html)
    print(f"✓ macon-{zone['SLUG']}/index.html")

# ── SITEMAP XML ──────────────────────────────────────────────────────────────
domain = config["DOMAIN"]
sitemap_urls = [f"https://{domain}/"]
for svc in services:
    sitemap_urls.append(f"https://{domain}/{svc['SLUG']}/")
for zone in zones:
    sitemap_urls.append(f"https://{domain}/macon-{zone['SLUG']}/")
sitemap_urls += [
    f"https://{domain}/realisations/",
    f"https://{domain}/devis/",
]
# merci et mentions légales exclus du sitemap (noindex)

sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url in sitemap_urls:
    sitemap_xml += f"  <url><loc>{url}</loc><changefreq>monthly</changefreq><priority>{'1.0' if url.endswith(domain+'/') else '0.8'}</priority></url>\n"
sitemap_xml += "</urlset>\n"
(OUTPUT / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
print("✓ sitemap.xml")

# ── _REDIRECTS Cloudflare Pages ───────────────────────────────────────────────
redirects = "/contact/  /devis/  301\n"
(OUTPUT / "_redirects").write_text(redirects, encoding="utf-8")
print("✓ _redirects")

# ── robots.txt ────────────────────────────────────────────────────────────────
robots = f"User-agent: *\nAllow: /\nDisallow: /mentions-legales/\nSitemap: https://{domain}/sitemap.xml\n"

# ── llms.txt ──────────────────────────────────────────────────────────────────
llms_tpl = (TEMPLATES / "llms.txt").read_text(encoding="utf-8")
llms_txt = apply_vars(llms_tpl, build_vars())
(OUTPUT / "llms.txt").write_text(llms_txt, encoding="utf-8")
print("✓ llms.txt")
(OUTPUT / "robots.txt").write_text(robots, encoding="utf-8")
print("✓ robots.txt")

# ── Résumé ────────────────────────────────────────────────────────────────────
pages = list(OUTPUT.rglob("index.html"))
print(f"\n🎉 Site généré : {len(pages)} pages dans {OUTPUT}")
print("   Dossiers :")
for p in sorted(pages):
    rel = p.relative_to(OUTPUT)
    folder = str(rel.parent) if str(rel.parent) != "." else "(racine)"
    print(f"   · {folder}")
