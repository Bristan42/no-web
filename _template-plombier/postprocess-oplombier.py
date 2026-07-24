#!/usr/bin/env python3
"""Post-traitement démo Ô'Plombier : retire les affirmations non vérifiées (ancienneté)."""
import glob
R=[
 ("Dépannage, chauffe-eau, salle de bains, chauffage — 12 ans d'expérience, assurance décennale, artisan local. Devis gratuit, sans engagement.",
  "Dépannage, chauffe-eau, salle de bains, chauffage — disponible de 7h30 à 22h, assurance décennale, artisan local. Devis gratuit, sans engagement."),
 (">12 ans d'expérience</div>", ">Artisan local</div>"),
 ('<div class="t-num">12 ans</div><div class="t-label">d\'expérience</div>','<div class="t-num">7h30–22h</div><div class="t-label">disponibilité</div>'),
 ('<div class="cert-name">12 ans</div>\n      <div class="cert-desc">d\'expérience</div>','<div class="cert-name">7h30 – 22h</div>\n      <div class="cert-desc">disponibilité</div>'),
 ("<h3>12 ans d'expérience</h3>", "<h3>Large amplitude horaire</h3>"),
 ("Depuis 2013, nous réalisons tous vos travaux de plomberie et de chauffage avec le même soin et le respect des règles de l'art.",
  "Disponible de 7h30 à 22h, nous trouvons toujours un créneau pour vos dépannages comme pour vos projets."),
 ("Artisan local depuis 12 ans — un interlocuteur unique","Artisan local — un interlocuteur unique"),
 ("Plombier-chauffagiste à Veauche depuis 12 ans.","Plombier-chauffagiste à Veauche et dans la Plaine du Forez."),
 ("12 ans de savoir-faire à Veauche","le savoir-faire Ô'Plombier à Veauche"),
 ("12 ans de chantiers en maçonnerie","des interventions soignées"),
 ("Nous connaissons les matériaux et les contraintes locales du 42 depuis 12 ans.","Nous connaissons les installations et les contraintes locales du 42 — un artisan de la Plaine du Forez."),
 ("Nous connaissons les installations et les contraintes locales du 42 depuis 12 ans.","Nous connaissons les installations et les contraintes locales du 42 — un artisan de la Plaine du Forez."),
 ('"foundingDate": "2013",',''),('"foundingDate":"2013",',''),
]
n=0
for f in glob.glob('output/o-plombier/index.html')+glob.glob('output/o-plombier/*/index.html'):
    h=open(f).read();o=h
    for a,b in R: h=h.replace(a,b)
    if h!=o: open(f,'w').write(h); n+=1
print(f"post-traitement: {n} fichiers")
import subprocess
r=subprocess.run(['grep','-rl','12 ans','output/o-plombier'],capture_output=True,text=True)
print("résidus '12 ans':", r.stdout.strip() or "0 ✅")
