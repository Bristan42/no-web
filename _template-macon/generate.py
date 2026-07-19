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

# ── Nettoyage + création dossier output ──────────────────────────────────────
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir(parents=True)

print(f"✓ Dossier output : {OUTPUT}")

# ── Lecture index.html source ─────────────────────────────────────────────────
index_src = (BASE / "index.html").read_text(encoding="utf-8")

# ── Extraction CSS partagé ────────────────────────────────────────────────────
css_match = re.search(r'<style>([\s\S]*?)</style>', index_src)
shared_css = f"<style>{css_match.group(1)}</style>" if css_match else ""

# Ajoute styles spécifiques aux pages intérieures (dark mode cards manquants dans CSS base)
shared_css += """
<style>
@media(prefers-color-scheme:dark){
  :root{--bg:#111827;--bg-alt:#1a2535;--card:#1e2d40;--text:#F0EDE8;--text-2:#9BA5B4;--text-3:#6B7685;--border:#2a3a4e}
}
:root[data-theme="dark"]{--bg:#111827;--bg-alt:#1a2535;--card:#1e2d40;--text:#F0EDE8;--text-2:#9BA5B4;--text-3:#6B7685;--border:#2a3a4e}
:root[data-theme="light"]{--bg:#FFFFFF;--bg-alt:#F6F4F0;--card:#FFFFFF;--text:#1A1A1A;--text-2:#5E5A54;--text-3:#9B9690;--border:#E0DDD8}
.card{background:var(--card,var(--bg))}
</style>"""

# ── Extraction HEADER ─────────────────────────────────────────────────────────
header_match = re.search(r'(<header[\s\S]*?</header>)', index_src)
shared_header = header_match.group(1) if header_match else ""

# Drawer mobile (juste après </header>)
drawer_match = re.search(r'(</header>\s*<div class="mob-drawer"[\s\S]*?</div>)', index_src)
if drawer_match:
    shared_header += "\n" + drawer_match.group(1).replace("</header>\n", "")
else:
    # Fallback : chercher le drawer seul
    drawer_only = re.search(r'(<div class="mob-drawer"[\s\S]*?</div>\s*<!-- /drawer -->)', index_src)
    if drawer_only:
        shared_header += "\n" + drawer_only.group(1)

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
    "ANNEE":          config.get("ANNEE", "2025"),
    "ANNEE_CREATION": config.get("ANNEE_CREATION", "2010"),
    "LAT":            config.get("LAT", ""),
    "LNG":            config.get("LNG", ""),
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
        "ANNEE":          config.get("ANNEE", "2025"),
        "ANNEE_CREATION": config.get("ANNEE_CREATION", "2010"),
        "LAT":            config.get("LAT", ""),
        "LNG":            config.get("LNG", ""),
        "SHARED_STYLE":   shared_css,
        "HEADER":         shared_header,
        "FOOTER":         shared_footer,
        "SHARED_SCRIPT":  shared_script,
    }
    # Mentions légales
    mentions = config.get("MENTIONS", {})
    v["MENTIONS_FORME_JURIDIQUE"] = mentions.get("FORME_JURIDIQUE", "SARL")
    v["MENTIONS_CAPITAL"]         = mentions.get("CAPITAL", "")
    v["MENTIONS_RCS"]             = mentions.get("RCS", config["VILLE"])
    v["MENTIONS_TVA_INTRA"]       = mentions.get("TVA_INTRA", "")
    v["MENTIONS_HEBERGEUR"]       = mentions.get("HEBERGEUR", "Cloudflare Pages")
    v["MENTIONS_HEBERGEUR_ADRESSE"] = mentions.get("HEBERGEUR_ADRESSE", "")

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
        return f'<img src="{src}" alt="{alt}" loading="lazy">'
    return '<div class="real-photo-placeholder">M</div>'

# ── PAGE : index.html ─────────────────────────────────────────────────────────
base_vars = build_vars({
    "ZONE_CHIPS": zone_chips_html,
    "FOOTER_ZONE_LINKS": footer_zone_links_html,
    **avis_vars,
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

for svc in services:
    # Avantages → liste HTML
    avantages_html = ""
    for av in [_apply_simple(a) for a in svc.get("AVANTAGES", [])]:
        avantages_html += (
            '<div class="avantage">'
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
            f'<span>{av}</span></div>\n'
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

    svc_vars = build_vars({
        "SERVICE_NOM":             svc["NOM"],
        "SERVICE_SLUG":            svc["SLUG"],
        "SERVICE_NOM_COURT":       svc["NOM_COURT"],
        "SERVICE_TITRE_H1":        svc["TITRE_H1"],
        "SERVICE_DESCRIPTION_SEO": svc["DESCRIPTION_SEO"],
        "SERVICE_INTRO":           svc["INTRO"],
        "SERVICE_AVANTAGES_HTML":  avantages_html,
        "SERVICE_FAQ_HTML":        faq_html,
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
    zone_vars = build_vars({
        "ZONE_VILLE":      zone["VILLE"],
        "ZONE_SLUG":       zone["SLUG"],
        "ZONE_CODE_POSTAL": zone["CODE_POSTAL"],
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
redirects = "/contact/  /devis/  301\n/devis/?merci  /merci/  301\n"
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
