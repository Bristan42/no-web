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

# ══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR v2 — corrections automatiques (fin des retouches manuelles par démo)
# ══════════════════════════════════════════════════════════════════════════════
_EXP   = str(config.get("EXPERIENCE", "")).strip()
_ANNEE = str(config.get("ANNEE_CREATION", "")).strip()
_EMAIL = str(config.get("EMAIL", "")).strip()
_SPEC      = config.get("SPECIALITE", "").strip() or "Maçonnerie"
_SPEC_SUB  = config.get("SPECIALITE_SUB", "").strip() or "générale"
_SPEC_PHR  = config.get("SPECIALITE_PHRASE", "").strip() or f"spécialiste en {_SPEC.lower()}"
_SPEC_PHR_CAP = _SPEC_PHR[:1].upper() + _SPEC_PHR[1:]
_WHATSAPP  = str(config.get("WHATSAPP", "")).strip()   # ex "33668181811" (sans +) ; vide = pas de WhatsApp
SERVICE_LABELS = {s["SLUG"]: (s.get("NOM") or "").strip() for s in config.get("SERVICES", []) if s.get("SLUG")}


def _fix_empty_fields(text):
    """Nettoie les placeholders liés à l'ancienneté/année AVANT substitution
    (on matche {{EXPERIENCE}}/{{ANNEE_CREATION}} → aucun risque de toucher un vrai « 10 ans »)."""
    if not _EXP:
        # paires num/label (stat + certification)
        text = text.replace(
            '<div class="t-num">{{EXPERIENCE}} ans</div><div class="t-label">d\'expérience</div>',
            f'<div class="t-num">{_SPEC}</div><div class="t-label">{_SPEC_SUB}</div>')
        text = text.replace('<div class="cert-name">{{EXPERIENCE}} ans</div>',
                            f'<div class="cert-name">{_SPEC}</div>')
        text = text.replace('<div class="cert-desc">d\'expérience</div>',
                            f'<div class="cert-desc">{_SPEC_SUB}</div>')
        # inline "X ans d'expérience" (hero-sub, trust pills)
        text = text.replace("{{EXPERIENCE}} ans d'expérience", _SPEC_PHR)
        # phrases "depuis X ans"
        text = text.replace("Artisan local depuis {{EXPERIENCE}} ans — ", "Artisan local — ")
        text = text.replace("à {{VILLE}} depuis {{EXPERIENCE}} ans.", f"à {{{{VILLE}}}}, {_SPEC_PHR}.")
        text = text.replace("depuis {{EXPERIENCE}} ans.", ".")
        text = text.replace("{{EXPERIENCE}} ans de savoir-faire", "un vrai savoir-faire")
        # reste générique
        text = text.replace("{{EXPERIENCE}} ans", _SPEC)
        text = text.replace("depuis {{EXPERIENCE}}", "")
    if not _ANNEE:
        text = text.replace("Depuis {{ANNEE_CREATION}}, nous réalisons", "Nous réalisons")
        text = text.replace("Depuis {{ANNEE_CREATION}}", _SPEC)
        text = text.replace("depuis {{ANNEE_CREATION}}", "")
    return text


def _localbusiness_schema():
    mentions = config.get("MENTIONS", {})
    data = {
        "@context": "https://schema.org", "@type": "GeneralContractor",
        "name": config["ENTREPRISE"],
        "telephone": "+33" + str(config["TEL_RAW"]).lstrip("0"),
        "address": {"@type": "PostalAddress", "streetAddress": config.get("ADRESSE", ""),
                    "addressLocality": config["VILLE"], "postalCode": str(config["CODE_POSTAL"]),
                    "addressCountry": "FR"},
        "url": f'https://{config["DOMAIN"]}/',
        "areaServed": f'{config["VILLE"]} et le {config["DEPARTEMENT"]}',
        "priceRange": "€€",
    }
    if config.get("LAT") and config.get("LNG"):
        data["geo"] = {"@type": "GeoCoordinates", "latitude": config["LAT"], "longitude": config["LNG"]}
    if config.get("NOTE") and config.get("NB_AVIS"):
        data["aggregateRating"] = {"@type": "AggregateRating",
                                   "ratingValue": str(config["NOTE"]).replace(",", "."),
                                   "reviewCount": str(config["NB_AVIS"])}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def _whatsapp_bits():
    """Retourne (lien_footer, bulle_mobile, style_media) ou ('','','') si pas de WhatsApp."""
    if not _WHATSAPP:
        return "", "", ""
    path = ("M16 .5C7.4.5.5 7.4.5 16c0 2.8.7 5.4 2 7.7L.5 31.5l8-2.1c2.2 1.2 4.8 1.9 7.5 1.9 8.6 0 "
            "15.5-6.9 15.5-15.5S24.6.5 16 .5zm0 28c-2.4 0-4.7-.6-6.7-1.8l-.5-.3-4.8 1.3 1.3-4.6-.3-.5C3.6 "
            "20.4 3 18.2 3 16 3 8.8 8.8 3 16 3s13 5.8 13 13-5.8 12.5-13 12.5zm7.1-9.4c-.4-.2-2.3-1.1-2.6-1.3-.4-.1-.6-.2-.9.2-.3.4-1 "
            "1.3-1.2 1.5-.2.2-.4.3-.8.1-.4-.2-1.6-.6-3.1-1.9-1.1-1-1.9-2.3-2.1-2.7-.2-.4 0-.6.2-.8.2-.2.4-.4.5-.7.2-.2.2-.4.4-.6.1-.3 "
            "0-.5 0-.7-.1-.2-.9-2.1-1.2-2.9-.3-.8-.6-.7-.9-.7h-.7c-.2 0-.6.1-1 .5-.3.4-1.3 1.3-1.3 3.1s1.3 3.6 1.5 3.9c.2.2 2.6 "
            "4 6.3 5.6.9.4 1.6.6 2.1.8.9.3 1.7.2 2.3.1.7-.1 2.3-.9 2.6-1.8.3-.9.3-1.7.2-1.8-.1-.2-.3-.3-.7-.5z")
    href = (f'https://wa.me/{_WHATSAPP}?text=Bonjour%2C%20je%20vous%20contacte%20via%20'
            f'votre%20site%20pour%20un%20projet%20de%20ma%C3%A7onnerie.')
    footer = (f'\n          <a href="{href}" target="_blank" rel="noopener" aria-label="Contacter sur WhatsApp">'
              f'<svg width="14" height="14" viewBox="0 0 32 32" fill="#25D366" aria-hidden="true"><path d="{path}"/></svg>WhatsApp</a>')
    bubble = (f'<a href="{href}" target="_blank" rel="noopener" class="wa-float" aria-label="Contacter sur WhatsApp" '
              f'style="position:fixed;right:18px;bottom:calc(84px + env(safe-area-inset-bottom, 0px));z-index:301;'
              f'width:54px;height:54px;border-radius:50%;background:#25D366;display:flex;align-items:center;'
              f'justify-content:center;box-shadow:0 6px 20px rgba(0,0,0,.28)">'
              f'<svg width="30" height="30" viewBox="0 0 32 32" fill="#fff" aria-hidden="true"><path d="{path}"/></svg></a>\n')
    style = '<style>@media(min-width:769px){.wa-float{display:none!important}}</style>\n'
    return footer, bubble, style


_WA_FOOTER, _WA_BUBBLE, _WA_STYLE = _whatsapp_bits()


def postprocess(html):
    """Passe finale (après substitution) : labels services, mailto, schema, WhatsApp, srcset, FAQ."""
    # 1) Libellés services = NOM du config (nav, drawer, footer, cartes)
    for slug, nom in SERVICE_LABELS.items():
        if not nom:
            continue
        html = re.sub(r'(href="/' + re.escape(slug) + r'/"[^>]*>)[^<]{1,70}(</a>)',
                      lambda m: m.group(1) + nom + m.group(2), html)
        # titre <h3> de la carte service sur la home (premier h3 après le href du slug)
        html = re.sub(r'(href="/' + re.escape(slug) + r'/"[^>]*>(?:(?!</a>).){0,600}?<h3[^>]*>)[^<]{1,70}(</h3>)',
                      lambda m: m.group(1) + nom + m.group(2), html, count=1, flags=re.S)
    # 2) E-mail absent → retirer les liens mailto vides
    if not _EMAIL:
        html = re.sub(r'\s*<a href="mailto:">\s*</a>', '', html)
        html = re.sub(r'\s*<a href="mailto:">\s*<svg.*?</svg>\s*</a>', '', html, flags=re.S)
        html = re.sub(r'<a href="mailto:">(.*?)</a>', r'\1', html, flags=re.S)
        html = re.sub(r'(<br>)?\s*E-mail\s*:\s*(<a href="mailto:">\s*</a>)?', '', html)
    # 3) Schema.org LocalBusiness (une fois, dans le head)
    if 'GeneralContractor' not in html and '</head>' in html:
        html = html.replace('</head>', _localbusiness_schema() + '\n</head>', 1)
    # 4) FAQ : espace insécable avant ? ! (typo FR, évite l'orphelin)
    html = re.sub(r'(class="faq-q">[^<]*?) ([?!])', r'\1 \2', html)
    # 5) srcset + preload sur le héros eager (si variante -960 dispo)
    def _hero_srcset(m):
        tag = m.group(0)
        mm = re.search(r'src="(/images/([a-z0-9-]+)\.webp)"', tag)
        if not mm or 'srcset' in tag:
            return tag
        base = mm.group(2)
        if not (IMAGES_SRC / f"{base}-960.webp").exists():
            return tag
        add = (f'srcset="/images/{base}-960.webp 960w, /images/{base}.webp 1600w" '
               f'sizes="(max-width:700px) 92vw, 480px" fetchpriority="high" ')
        return tag[:5] + add + tag[5:]
    html = re.sub(r'<img[^>]*loading="eager"[^>]*>', _hero_srcset, html)
    # 6) WhatsApp : lien footer + bulle mobile
    if _WHATSAPP:
        tel_anchor = f'{config["TEL_DISPLAY"]}\n          </a>'
        fstart = html.find('<footer')
        if fstart >= 0 and 'wa.me/' not in html[fstart:html.find('</footer>', fstart) + 9]:
            html = html.replace(tel_anchor, tel_anchor + _WA_FOOTER, 1)
        if '</body>' in html and 'wa-float' not in html:
            html = html.replace('</body>', _WA_BUBBLE + '</body>', 1)
        if '</head>' in html and '.wa-float{display:none' not in html:
            html = html.replace('</head>', _WA_STYLE + '</head>', 1)
    return html

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
index_src = _fix_empty_fields(index_src)   # v2 : nettoie ancienneté/année vides avant extraction header/footer

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
    "HORAIRES":             config.get("HORAIRES", "Mo-Fr 07:30-18:00"),
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
        "HORAIRES":       config.get("HORAIRES", "Mo-Fr 07:30-18:00"),
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
    _gmb = config.get("GOOGLE_GMB_URL", "")
    v["GMB_BTN"] = (f'<div class="gmb-footer reveal d4" style="text-align:center;margin-top:18px"><a href="{_gmb}" target="_blank" rel="noopener" class="btn btn-outline">Voir tous les avis sur Google</a></div>') if _gmb else ""
    v["GOOGLE_MAPS_KEY"] = config.get("GOOGLE_MAPS_KEY", "")
    v["GOOGLE_PLACE_ID"] = config.get("GOOGLE_PLACE_ID", "")
    v["GOOGLE_GMB_URL"]  = config.get("GOOGLE_GMB_URL", "")

    if extra:
        v.update(extra)
    return v


def apply_vars(template_str, variables):
    """Remplace tous les {{VAR}} par leur valeur."""
    result = _fix_empty_fields(template_str)   # v2 : nettoie champs vides avant substitution
    for key, val in variables.items():
        result = result.replace("{{" + key + "}}", str(val))
    return result


def write_page(folder, html_content):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(postprocess(html_content), encoding="utf-8")


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
photo_alts = photos.get("ALTS", [])
def _alt(i):
    return photo_alts[i-1] if i <= len(photo_alts) and photo_alts[i-1] else f"Réalisation maçonnerie {i}"
def _photo_slot(i):
    """Photo pour l'emplacement i (1-based). Cycle sur les photos dispo pour éviter les {{}} bruts."""
    avail = [s for s in real_photos if s]
    if not avail:
        return photo_tag("", _alt(i))
    src = avail[(i - 1) % len(avail)]
    return photo_tag(src, _alt(i))

photo_real_vars = {f"PHOTO_REAL_{i}": _photo_slot(i) for i in range(1, 7)}


def build_realisations_gallery():
    """Page Réalisations = VRAIES photos + libellés honnêtes (config PHOTOS.REAL_LABELS).
    Pas de faux titres, pas de placeholder, pas de filtres. Si pas de libellés → photos seules."""
    ph = config.get("PHOTOS", {})
    reals = [s for s in ph.get("REALISATIONS", []) if s]
    if not reals:
        return ""
    labels = ph.get("REAL_LABELS", [])
    alts = ph.get("ALTS", [])
    cards = []
    for i, src in enumerate(reals):
        alt = alts[i] if i < len(alts) and alts[i] else "Réalisation"
        lab = labels[i] if i < len(labels) else {}
        tag = lab.get("TAG", "")
        title = lab.get("TITRE", "")
        meta = lab.get("META", "")
        cat_html = f'\n      <div class="reals-cat">{tag}</div>' if tag else ""
        body_html = (f'\n    <div class="real-body"><div class="real-title">{title}</div>'
                     f'<div class="real-meta">{meta}</div></div>') if (title or meta) else ""
        cards.append(
            f'<div class="real-card reveal">\n'
            f'    <div class="real-photo">\n'
            f'      <img class="real-ph" src="{src}" alt="{alt}" loading="lazy" decoding="async" width="800" height="600">'
            f'{cat_html}\n    </div>{body_html}\n  </div>'
        )
    return '<div class="reals-grid">\n  ' + '\n  '.join(cards) + '\n</div>'

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
reals_vars["REALISATIONS_GALLERY"] = build_realisations_gallery()
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
            f'<h3>{av}</h3>'
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
        "ZONE_LOCAL":      (f'<p class="reveal d2" style="font-size:15px;color:var(--text-2);line-height:1.7;max-width:760px;margin-bottom:40px">{zone["LOCAL"]}</p>' if zone.get("LOCAL") else ""),
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
