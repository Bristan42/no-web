#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publication planifiée du blog no-web.fr — robuste, indépendante de l'indentation.
Conçu pour tourner dans GitHub Actions (cloud) OU en local.

Usage:
  publish_due.py --today YYYY-MM-DD   # publie tous les articles dus (date <= today) pas encore en ligne
  publish_due.py --simulate           # simulation en mémoire sur une copie, ne touche rien de suivi

Le manifeste liste, dans l'ordre, les articles à publier (le pilier maçon est déjà en ligne).
Les champs de carte (couverture, titre, description, temps de lecture) sont DÉRIVÉS de l'article
lui-même → pas de duplication de données.
"""
import os, re, sys, shutil, subprocess, datetime

REPO=os.environ.get("REPO_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IDX=os.path.join(REPO,"blog","index.html")
SMAP=os.path.join(REPO,"sitemap.xml")

# (date ISO, date affichée FR, slug, catégorie carte, titre carte "up-card" à retirer ou None)
MANIFEST=[
 ("2026-07-28","28 juil. 2026","macon-visible-google","Référencement","Être visible sur Google quand on est maçon"),
 ("2026-07-30","30 juil. 2026","fiche-google-business-macon","Fiche Google","La fiche Google Business Profile du maçon"),
 ("2026-08-02","2 août 2026","prix-site-internet-macon","Budget","Combien coûte un site internet pour un maçon ?"),
 ("2026-08-05","5 août 2026","avis-clients-macon","Avis clients","Avis clients en maçonnerie : comment en obtenir"),
 ("2026-08-08","8 août 2026","photos-chantier-macon","Photos","Photos de chantier : décrocher plus de devis"),
 ("2026-08-11","11 août 2026","devis-maconnerie","Devis","Devis de maçonnerie : le rédiger pour qu'il passe"),
 ("2026-08-14","14 août 2026","site-ou-facebook-macon","Stratégie",None),
 ("2026-08-17","17 août 2026","site-sur-mesure-ou-wordpress-macon","Technique",None),
 ("2026-08-20","20 août 2026","macon-auto-entrepreneur-se-faire-connaitre","Débuter",None),
 ("2026-08-23","23 août 2026","erreurs-macon-invisible-google","Référencement",None),
 ("2026-08-26","26 août 2026","trouver-chantiers-maconnerie","Développer",None),
 ("2026-08-29","29 août 2026","plateformes-chantiers-macon","Développer",None),
 ("2026-09-01","1 sept. 2026","google-ads-macon","Visibilité",None),
 ("2026-09-04","4 sept. 2026","trouver-clients-artisan","Artisans",None),
 ("2026-09-07","7 sept. 2026","pourquoi-site-internet-artisan","Présence en ligne",None),
 ("2026-09-10","10 sept. 2026","prix-site-internet-artisan","Budget",None),
 ("2026-09-13","13 sept. 2026","site-vitrine-ou-ecommerce-artisan","Choisir son site",None),
 ("2026-09-16","16 sept. 2026","creer-son-site-artisan-soi-meme-ou-pro","Créer son site",None),
 ("2026-09-19","19 sept. 2026","site-internet-gratuit-artisan","Budget",None),
 ("2026-09-22","22 sept. 2026","nom-de-domaine-email-pro-artisan","Image de marque",None),
 ("2026-09-25","25 sept. 2026","que-mettre-site-artisan","Créer son site",None),
 ("2026-09-28","28 sept. 2026","etre-visible-google-artisan","Référencement",None),
 ("2026-10-01","1 oct. 2026","site-ou-reseaux-sociaux-artisan","Présence en ligne",None),
 ("2026-10-04","4 oct. 2026","site-internet-rentable-artisan","Budget",None),
 ("2026-10-07","7 oct. 2026","agence-web-ou-freelance-saint-etienne","Choisir",None),
 ("2026-10-10","10 oct. 2026","agence-web-ou-freelance-avantages-inconvenients","Choisir",None),
 ("2026-10-13","13 oct. 2026","comment-choisir-agence-web","Choisir",None),
 ("2026-10-16","16 oct. 2026","prix-site-internet-agence-web","Budget",None),
 ("2026-10-19","19 oct. 2026","freelance-web-webmaster-definition","Comprendre",None),
 ("2026-10-22","22 oct. 2026","prestataire-web-local-saint-etienne","Local",None),
 ("2026-10-25","25 oct. 2026","agence-web-pas-chere","Budget",None),
 ("2026-10-28","28 oct. 2026","questions-avant-signer-agence-web","Choisir",None),
 ("2026-10-31","31 oct. 2026","agence-web-pieges-arnaques","Choisir",None),
 ("2026-11-03","3 nov. 2026","delai-creation-site-internet","Comprendre",None),
 ("2026-11-06","6 nov. 2026","modele-no-web-ni-agence-ni-freelance","No Web",None),
]

POST_CSS=(" .post-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}\n"
 " .post-card{display:flex;flex-direction:column;background:var(--bg-card);border:1px solid var(--border);border-radius:16px;overflow:hidden;text-decoration:none;color:var(--text);transition:border-color .25s,transform .2s}\n"
 " .post-card:hover{border-color:var(--border-h);transform:translateY(-4px)}\n"
 " .post-thumb-img{aspect-ratio:16/10;overflow:hidden;border-bottom:1px solid var(--border)}\n"
 " .post-thumb-img img{width:100%;height:100%;object-fit:cover;display:block}\n"
 " .post-content{padding:20px 22px 22px;display:flex;flex-direction:column;flex:1}\n"
 " .post-cat{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;margin-bottom:10px}\n"
 " .post-content h3{font-size:16px;font-weight:700;line-height:1.32;margin-bottom:10px}\n"
 " .post-content p{font-size:13px;color:var(--text-2);line-height:1.55;margin-bottom:16px;flex:1}\n"
 " .post-meta{font-size:12px;color:var(--text-3);display:flex;gap:8px;align-items:center}.post-meta .dot{width:3px;height:3px;border-radius:50%;background:var(--text-3);opacity:.6}\n"
 " @media(max-width:860px){.post-grid{grid-template-columns:1fr 1fr}}\n @media(max-width:600px){.post-grid{grid-template-columns:1fr}}\n")

def esc(s): return s  # texte déjà propre

def article_meta(slug, datefr, cat):
    """Dérive les champs de la carte depuis l'article lui-même."""
    p=os.path.join(REPO,"blog",slug,"index.html")
    h=open(p,encoding="utf-8").read()
    cover=re.search(r'og:image" content="https://no-web\.fr(/blog/img/[^"]+)"',h).group(1)
    title=re.search(r'og:title" content="([^"]+)"',h).group(1)
    desc=re.search(r'name="description" content="([^"]+)"',h).group(1)
    if len(desc)>105: desc=desc[:102].rsplit(" ",1)[0]+"…"
    m=re.search(r'<span>(\d+ min) de lecture</span>',h); read=m.group(1) if m else "min"
    alt=re.search(r'<img src="'+re.escape(cover)+r'"[^>]*alt="([^"]*)"',h)
    alt=alt.group(1) if alt else title
    return cover,title,desc,read,alt

def card_html(slug, datefr, cat):
    cover,title,desc,read,alt=article_meta(slug,datefr,cat)
    return ('   <a href="/blog/%s/" class="post-card">\n'%slug+
     '    <div class="post-thumb-img"><img src="%s" width="1000" height="750" loading="lazy" alt="%s"></div>\n'%(cover,alt)+
     '    <div class="post-content">\n'
     '     <div class="post-cat">%s</div>\n'%cat+
     '     <h3>%s</h3>\n'%title+
     '     <p>%s</p>\n'%desc+
     '     <div class="post-meta"><span>Bristan Farré</span><span class="dot"></span><span>%s</span><span class="dot"></span><span>%s</span></div>\n'%(datefr,read)+
     '    </div>\n   </a>\n')

def wire_grid(h, slug, card):
    if '/blog/%s/'%slug in h: return h
    if '.post-thumb-img' not in h:
        h=h.replace("</style>",POST_CSS+" </style>",1)
    tag='<div class="post-grid">'
    if tag in h:
        i=h.find(tag)+len(tag)
        h=h[:i]+"\n"+card+h[i:]
    else:
        block=('<div class="section-eyebrow">Derniers articles</div>\n'
               ' <div class="post-grid">\n'+card+' </div>\n\n ')
        cta='<div class="blog-cta">'
        j=h.find(cta)
        h=h[:j]+block+h[j:]
    return h

def remove_up_card(h, title):
    if not title: return h
    lines=h.split("\n")
    kept=[l for l in lines if not ('class="up-card"' in l and title in l)]
    return "\n".join(kept)

def remove_empty_prochainement(h):
    if 'class="up-card"' in h: return h  # il reste des cartes à venir
    return re.sub(r'\s*<div class="section-eyebrow">Prochainement</div>\s*<div class="up-grid">\s*</div>','',h,flags=re.S)

def wire_sitemap(s, slug, date):
    if '/blog/%s/'%slug in s: return s
    block=('  <url>\n    <loc>https://no-web.fr/blog/%s/</loc>\n'%slug+
           '    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n'%date)
    return s.replace("\n</urlset>","\n"+block+"\n</urlset>",1)

def apply_one(idx, smap, entry):
    date,datefr,slug,cat,upc=entry
    idx=wire_grid(idx,slug,card_html(slug,datefr,cat))
    idx=remove_up_card(idx,upc)
    idx=remove_empty_prochainement(idx)
    smap=wire_sitemap(smap,slug,date)
    return idx,smap

def due(today):
    return [e for e in MANIFEST if e[0]<=today]

def git(*a,check=True):
    r=subprocess.run(["git"]+list(a),cwd=REPO,capture_output=True,text=True)
    if check and r.returncode!=0: raise RuntimeError("git %s -> %s"%(" ".join(a),r.stderr.strip()))
    return r

QUEUE_REF=os.environ.get("QUEUE_REF","origin/blog-content")

def materialize(slug):
    """Récupère l'article + ses médias depuis la branche d'attente (mode cloud)."""
    git("checkout",QUEUE_REF,"--","blog/%s"%slug)
    h=open(os.path.join(REPO,"blog",slug,"index.html"),encoding="utf-8").read()
    assets=set(re.findall(r'/blog/(?:img|telechargements)/[^"\')\s]+\.(?:webp|jpg|jpeg|png|svg|pdf)',h))
    for a in assets:
        git("checkout",QUEUE_REF,"--",a.lstrip("/"),check=False)

def run_publish(today, dry=False, cloud=False):
    idx=open(IDX,encoding="utf-8").read(); smap=open(SMAP,encoding="utf-8").read()
    published=[]
    for e in due(today):
        slug=e[2]
        if '/blog/%s/'%slug in idx: continue  # déjà en ligne
        if not os.path.exists(os.path.join(REPO,"blog",slug,"index.html")):
            if cloud:
                try: materialize(slug)
                except Exception as ex: print("Matérialisation échouée",slug,ex); continue
            else:
                print("MANQUANT (ignoré):",slug); continue
        idx,smap=apply_one(idx,smap,e); published.append(slug)
    if not published: print("Rien à publier pour",today); return 0
    print(("[DRY] " if dry else "")+"À publier: "+", ".join(published))
    if dry: return 0
    open(IDX,"w",encoding="utf-8").write(idx); open(SMAP,"w",encoding="utf-8").write(smap)
    git("add","blog","sitemap.xml")
    if git("diff","--cached","--quiet",check=False).returncode==0: print("Rien à committer"); return 0
    git("commit","-m","Blog: publication auto ("+", ".join(published)+")\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
    if git("push","origin","main",check=False).returncode!=0:
        git("pull","--rebase","origin","main"); git("push","origin","main")
    print("PUBLIÉ:",", ".join(published)); return 0

def simulate():
    idx=open(IDX,encoding="utf-8").read(); smap=open(SMAP,encoding="utf-8").read()
    def state(idx,smap):
        cards=re.findall(r'href="/blog/([a-z0-9-]+)/" class="post-card"',idx)
        upc=idx.count('class="up-card"')
        proch='Prochainement' in idx
        divbal=idx[idx.index('<body>'):idx.index('</body>')]
        bal=divbal.count('<div')-divbal.count('</div>')
        return cards,upc,proch,smap.count('<loc>'),bal
    print("DÉPART: cartes=%d up-cards=%d Prochainement=%s sitemap=%d divbal=%d"%(*[len(state(idx,smap)[0])],*state(idx,smap)[1:]))
    for i,e in enumerate(MANIFEST):
        idx,smap=apply_one(idx,smap,e)
        cards,upc,proch,smU,bal=state(idx,smap)
        tag=" <-- 7e (Prochainement doit disparaître)" if i==5 else ""
        print("  +%-38s cartes=%2d up=%d Proch=%-5s sitemap=%d divbal=%d%s"%(e[2],len(cards),upc,str(proch),smU,bal,tag))
    cards,upc,proch,smU,bal=state(idx,smap)
    print("\nFIN: %d cartes | up-cards restantes=%d | Prochainement=%s | sitemap=%d | équilibre div=%d"%(len(cards),upc,proch,smU,bal))
    print("Ordre des cartes (haut -> bas):")
    for c in cards: print("   ",c)
    dups=[c for c in set(cards) if cards.count(c)>1]
    print("Doublons:", dups if dups else "aucun")

if __name__=="__main__":
    dry="--dry" in sys.argv; cloud="--cloud" in sys.argv
    if "--simulate" in sys.argv: simulate()
    elif "--today" in sys.argv:
        t=sys.argv[sys.argv.index("--today")+1]; sys.exit(run_publish(t,dry=dry,cloud=cloud))
    else:
        sys.exit(run_publish(datetime.date.today().isoformat(),dry=dry,cloud=cloud))
