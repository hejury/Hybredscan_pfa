"""style"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* Espace de travail — coque sombre (page/sidebar), cartes blanches en
     surface. Deux jeux de tokens texte/bordure : le jeu "page" (--txt,
     --dim, --line, ...) pour le texte pose directement sur le fond sombre
     (titres, libelles hors carte) ; le jeu "carte" (--card-txt, --card-dim,
     --card-line, ...) pour le texte a l'interieur des cartes blanches
     (--surface). Ne jamais les croiser : un texte sur fond sombre qui
     utiliserait --card-txt (fonce) deviendrait illisible, et inversement. */
  --bg:#0F1117; --bg-subtle:#14161F; --surface:#FFFFFF; --surface-2:#F8F9FB;
  --line:rgba(255,255,255,.08); --line2:rgba(255,255,255,.16);
  --txt:#FFFFFF; --txt-2:#C7C7D1; --dim:#9494A6; --dim2:#5D5D6E;

  --card-line:#E5E7EB; --card-line2:#D1D5DB;
  --card-txt:#1B2333; --card-txt-2:#4B5563; --card-dim:#6B7280; --card-dim2:#9CA3AF;

  /* Barre laterale — meme famille de sombre que le fond de page. */
  --sb-bg:#0F1117; --sb-bg-2:#14161F; --sb-txt:#FFFFFF; --sb-txt-2:#A9B4CC;
  --sb-hover:rgba(245,179,1,.12); --sb-border:rgba(255,255,255,.10);

  /* Accent de marque — or/jaune ambre : boutons, actifs, focus, logo. */
  --action:#F5B301; --action-hover:#FFC933; --action-active:#D89A00; --focus:#F5B301;
  --action-bg:#FDF0D5; --on-gold:#1B2333;

  /* Accent secondaire — ambre profond (degrades avec --action, meme famille "or"). */
  --accent:#C98A00; --accent-bg:#FBE8C7;

  /* Statuts semantiques — pastilles pleines (fond clair + texte sature),
     lisibles sur les cartes blanches. */
  --vert:#047857;  --vert-bg:#D1FAE5;   /* operationnel / sain / autorise */
  --rouge:#B91C1C; --rouge-bg:#FEE2E2;  /* malveillant / refuse */
  --jaune:#92400E; --jaune-bg:#FEF3C7;  /* en attente / avertissement */
  --info:#1D4ED8;  --info-bg:#DBEAFE;   /* informatif neutre */

  /* Rayons et ombres */
  --r-sm:8px; --r-md:12px; --r-lg:18px; --r-pill:999px;
  --shadow-card:0 1px 3px rgba(0,0,0,.4), 0 4px 14px rgba(0,0,0,.35);
  --shadow-raised:0 10px 26px rgba(245,179,1,.20), 0 6px 18px rgba(0,0,0,.4);
  --shadow-overlay:0 20px 50px rgba(0,0,0,.5);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}

*:focus-visible {
  outline: 2px solid var(--focus) !important;
  outline-offset: 2px !important;
}

.stApp { background:var(--bg); }
html, body, [class*="css"], .stMarkdown, p, span, div, label {
  font-family:'Inter',sans-serif !important; color:var(--txt); }
/* La regle ci-dessus ecrasait aussi la police d'icones (Material Symbols)
   de Streamlit sur tout <span>/<div> — ses icones (ex. le chevron des
   expanders) s'affichaient alors en texte brut ("keyboard_arrow_down")
   au lieu du glyphe attendu. Restauration explicite ci-dessous plutot
   qu'un ":not()" sur la regle precedente, qui aurait involontairement
   augmente sa specificite et casse d'autres couleurs a classe unique
   (ex. .kl-t). Bug trouve et corrige lors de la revue finale. */
[data-testid*="Icon"] { font-family:"Material Symbols Rounded" !important; }
.block-container { padding-top:2.75rem !important; padding-left:3.25rem !important;
  padding-right:3.25rem !important; padding-bottom:3rem !important; max-width:1140px; }

[data-testid="stSidebar"] { background:linear-gradient(180deg,var(--sb-bg),var(--sb-bg-2) 130%);
  border-right:1px solid var(--sb-border); min-width:284px !important; max-width:284px !important; }
/* Le controle natif de repli/deploiement de la barre laterale reste visible
   et fonctionnel : necessaire pour un usage tablette/mobile (voir MASTER.md
   §7.12). Seule la largeur en etat deploye est fixee ci-dessus. */
section[data-testid="stSidebar"][aria-expanded="false"] { margin-left:0 !important; }
[data-testid="stSidebar"] > div { padding-top:1.5rem; }
[data-testid="stSidebar"] * { color:var(--sb-txt); }

.kl { display:flex; align-items:center; gap:12px; padding:0 8px 22px 8px;
  border-bottom:1px solid var(--sb-border); margin-bottom:14px; }
/* Repli texte (voir app.py:_logo_html()) — utilise uniquement si logo.png
   est absent ou illisible. */
.kl-hex { width:46px; height:46px; border-radius:var(--r-md);
  background:linear-gradient(135deg,var(--action),var(--accent));
  display:flex; align-items:center; justify-content:center;
  color:var(--on-gold); font-size:20px; font-weight:900; flex-shrink:0;
  box-shadow:0 4px 12px rgba(245,179,1,.35); }
/* Logo image (logo.png) — taille recommandee 48-56px, sans cadre ni ombre
   imposee : le mark en H dore porte deja son propre poids visuel. */
.kl-logo { width:52px; height:52px; object-fit:contain; flex-shrink:0; display:block; }
.kl-t { font-size:0.94rem; font-weight:800; color:var(--sb-txt); line-height:1.2; }
.kl-s { font-size:0.66rem; color:var(--sb-txt-2); margin-top:3px; letter-spacing:0.3px; }

.kl-lbl { font-size:0.6rem; letter-spacing:1.6px; text-transform:uppercase;
  color:var(--sb-txt-2); padding:4px 10px 8px; font-weight:700; }

.kf { font-size:0.64rem; color:var(--sb-txt-2); padding:18px 4px 0 4px;
  border-top:1px solid var(--sb-border); margin-top:16px; line-height:1.5; }

[data-testid="stSidebar"] .stButton > button {
  background:transparent !important; border:none !important; box-shadow:none !important;
  color:var(--sb-txt-2) !important; text-align:left !important; justify-content:flex-start !important;
  font-size:0.88rem !important; font-weight:500 !important; padding:11px 16px !important;
  height:auto !important; border-radius:var(--r-sm) !important; width:100% !important;
  transition:background 0.15s, color 0.15s !important; }
[data-testid="stSidebar"] .stButton > button:hover {
  background:var(--sb-hover) !important; color:#FFFFFF !important; transform:none !important;
  box-shadow:none !important; }
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background:linear-gradient(90deg,rgba(245,179,1,.24),rgba(245,179,1,.06)) !important;
  color:#FFFFFF !important; font-weight:700 !important;
  box-shadow:inset 3px 0 0 var(--action) !important; }
[data-testid="stSidebar"] .stButton { margin-bottom:3px; }

.hdr { padding:0 0 10px 0; margin-bottom:26px; border-bottom:1px solid var(--line); }
.hdr h1 { font-size:1.75rem; font-weight:800; margin:0 0 6px 0 !important; color:var(--txt);
  letter-spacing:-0.5px; }
.hdr .sub { font-size:0.9rem; color:var(--dim); margin-top:2px; }

/* En-tete de page (toutes pages sauf connexion) — libelle en majuscules,
   titre, sous-titre a gauche (poses sur le fond sombre : tokens "page") ;
   colonne d'action au milieu (voir app.py : _col_entete_action, rempli
   uniquement par les pages qui ont une action principale, ex. Dashboard) ;
   colonne compte/deconnexion a droite, presente sur toutes les pages (voir
   app.py : _col_entete_compte / _deconnexion()). Classes distinctes de .hdr
   (utilisee uniquement par la page de connexion, une seule colonne) pour
   ne jamais affecter cette derniere. */
.entete-eyebrow { font-size:0.68rem; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--dim); font-weight:700; margin-bottom:6px; }
.entete-titre { font-size:1.75rem; font-weight:800; margin:0 0 6px 0 !important;
  color:var(--txt); letter-spacing:-0.5px; }
.entete-sous { font-size:0.9rem; color:var(--dim); margin-top:2px; }
.entete-ligne { border-bottom:1px solid var(--line); margin:14px 0 26px; }
/* Les deux colonnes d'en-tete ci-dessous (action de page, deconnexion)
   forcent explicitement une rangee horizontale : st.container() genere un
   "stVerticalBlock" empilant ses enfants en colonne par defaut, ce qui
   faisait deriver tout element pose ici vers un empilement vertical
   indesirable plutot qu'un alignement propre a droite. */
.st-key-entete_action_dashboard, .st-key-entete_compte {
  display:flex !important; flex-direction:row !important;
  align-items:center !important; justify-content:flex-end !important; }

/* Bouton de deconnexion, coin superieur droit de chaque page — icone seule
   (voir app.py : icon=":material/logout:", label vide, infobulle "Se
   deconnecter" via help=). Delibrement "outline" (transparent + bordure)
   plutot que plein or, pour ne jamais rivaliser visuellement avec le
   bouton d'action principal de la page (ex. "Analyser un fichier") — l'or
   n'apparait qu'au survol, comme accent discret. L'identifiant du compte
   reste visible dans la barre laterale uniquement (voir .kl-lbl) : pas de
   doublon ici. */
.st-key-entete_compte .stButton > button {
  background:transparent !important; color:var(--txt-2) !important;
  border:1px solid var(--line2) !important; box-shadow:none !important;
  width:38px !important; height:38px !important; padding:0 !important; min-width:0 !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  border-radius:var(--r-sm) !important; }
.st-key-entete_compte .stButton > button [data-testid="stIconMaterial"] {
  font-size:1.2rem !important; }
.st-key-entete_compte .stButton > button:hover {
  background:var(--action-bg) !important; border-color:var(--action) !important;
  color:var(--on-gold) !important; box-shadow:none !important; transform:none !important; }

/* Titres de section — barre d'accent degradee + libelle, pour une hierarchie
   visuelle claire entre le titre de page et le contenu (remplace le texte
   en gras nu utilise auparavant). Pose sur le fond sombre : tokens "page". */
.section-titre { display:flex; align-items:center; gap:10px; margin:30px 0 14px; }
.section-titre .barre { width:5px; height:20px; border-radius:var(--r-pill);
  background:linear-gradient(180deg,var(--action),var(--accent)); flex-shrink:0; }
.section-titre .texte { font-size:1.05rem; font-weight:800; color:var(--txt);
  letter-spacing:-0.2px; }

.verdict { border-radius:var(--r-lg); padding:28px 32px; margin:20px 0;
  border:1px solid var(--card-line); border-left:6px solid;
  background:var(--surface); box-shadow:var(--shadow-card); }
.verdict .etat { font-size:2.15rem; font-weight:800; line-height:1; }
.verdict .via { font-size:0.66rem; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--card-dim); margin-bottom:8px; font-weight:700; }
.verdict .msg { font-size:0.9rem; margin-top:12px; color:var(--card-txt-2); }
.v-mal { border-color:var(--rouge) !important;
  background:linear-gradient(135deg,var(--rouge-bg),var(--surface) 70%) !important; }
.v-mal .etat { color:var(--rouge); }
.v-sain { border-color:var(--vert) !important;
  background:linear-gradient(135deg,var(--vert-bg),var(--surface) 70%) !important; }
.v-sain .etat { color:var(--vert); }
.v-ind { border-color:var(--jaune) !important;
  background:linear-gradient(135deg,var(--jaune-bg),var(--surface) 70%) !important; }
.v-ind .etat { color:var(--jaune); }

/* Jauge de confiance (page Analyse) — posee directement sur le fond sombre,
   pas dans une carte : tokens "page". */
.jauge-lbl { display:flex; justify-content:space-between; font-size:0.7rem;
  color:var(--dim); margin-bottom:6px; font-weight:600; }
.jauge { height:9px; background:var(--bg-subtle); border-radius:var(--r-pill); overflow:hidden; }
.jauge > div { height:100%; border-radius:var(--r-pill);
  background:linear-gradient(90deg,var(--action),var(--accent)); }

/* Resume des etapes d'analyse (page Analyse et Protection) — cartes
   blanches : tokens "carte" a l'interieur. */
.etapes { display:flex; flex-direction:column; gap:8px; margin:12px 0; }
.etape-l { display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 10px;
  font-size:0.83rem; padding:11px 16px; border-radius:var(--r-md);
  background:var(--surface); border:1px solid var(--card-line); border-left:4px solid var(--card-line2);
  box-shadow:var(--shadow-card); transition:box-shadow .15s, transform .15s; }
.etape-l:hover { box-shadow:var(--shadow-raised); transform:translateY(-1px); }
.etape-l .n { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:var(--card-dim); flex-shrink:0; }
.etape-l .t { font-weight:600; color:var(--card-txt); }
.etape-l .e { color:var(--card-dim); font-size:0.78rem; margin-left:auto;
  text-align:right; word-break:break-word; max-width:100%; }
.etape-l.ok { border-left-color:var(--vert); }
.etape-l.bad { border-left-color:var(--rouge); }
.etape-l.warn { border-left-color:var(--jaune); }
.etape-l.skip { opacity:0.65; }
@media (max-width:640px) {
  .etape-l .e { margin-left:0; text-align:left; width:100%; }
}

/* st.code (utilise pour l'empreinte SHA-256 : bouton de copie natif) doit
   retourner a la ligne plutot que deborder horizontalement a l'etroit. */
[data-testid="stCode"] pre, [data-testid="stCodeBlock"] pre,
[data-testid="stCode"] code, [data-testid="stCodeBlock"] code {
  white-space:pre-wrap !important; word-break:break-all !important;
  border-radius:var(--r-sm) !important; }

/* Historique / Quarantaine / Scan de dossier / Protection — une ligne
   compacte par element + badge, cartes blanches : tokens "carte". */
.hist-l { display:flex; flex-wrap:wrap; align-items:center; gap:6px 12px;
  padding:12px 16px; border-radius:var(--r-md); background:var(--surface);
  border:1px solid var(--card-line); margin-bottom:8px; box-shadow:var(--shadow-card);
  transition:box-shadow .15s, transform .15s; }
.hist-l:hover { box-shadow:var(--shadow-raised); transform:translateY(-1px); }
.hist-l .t { font-weight:600; color:var(--card-txt); word-break:break-word; }
.hist-l .e { color:var(--card-dim); font-size:0.78rem; margin-left:auto;
  word-break:break-word; text-align:right; }
.verdict-badge { display:inline-flex; align-items:center; padding:4px 12px;
  border-radius:var(--r-pill); font-size:0.7rem; font-weight:700;
  letter-spacing:0.3px; flex-shrink:0; }
.verdict-badge.v-mal { background:var(--rouge-bg); color:var(--rouge); }
.verdict-badge.v-sain { background:var(--vert-bg); color:var(--vert); }
.verdict-badge.v-ind { background:var(--jaune-bg); color:var(--jaune); }
@media (max-width:640px) {
  .hist-l .e { margin-left:0; text-align:left; width:100%; }
}

/* Quarantaine — badge d'etat d'enregistrement (coherence des metadonnees),
   volontairement distinct du badge de verdict (.verdict-badge) : un
   enregistrement de quarantaine "isole" ne doit jamais evoquer "sain". */
.q-badge { display:inline-flex; align-items:center; padding:4px 12px;
  border-radius:var(--r-pill); font-size:0.7rem; font-weight:700; letter-spacing:0.3px; flex-shrink:0; }
.q-badge.ok { background:var(--info-bg); color:var(--info); }
.q-badge.warn { background:var(--jaune-bg); color:var(--jaune); }

/* Tableau de bord — repartition sobre (source de detection), posee
   directement sur le fond sombre, pas dans une carte : tokens "page". */
.repart { display:flex; flex-direction:column; gap:10px; margin:10px 0; }
.repart-l { display:flex; align-items:center; gap:10px; font-size:0.82rem; }
.repart-l .lbl { width:42%; color:var(--txt-2); text-align:right; flex-shrink:0; }
.repart-l .barre { flex:1; height:11px; background:var(--bg-subtle);
  border-radius:var(--r-pill); overflow:hidden; }
.repart-l .barre > div { height:100%; background:var(--action); border-radius:var(--r-pill); }
.repart-l .val { width:84px; text-align:right; color:var(--dim); font-size:0.78rem; flex-shrink:0; }
@media (max-width:640px) {
  .repart-l { flex-wrap:wrap; }
  .repart-l .lbl { width:100%; text-align:left; }
}

/* Cartes metriques generiques — cartes blanches : tokens "carte". Bordure
   gauche neutre par defaut, teintee par la couleur de statut transmise
   (voir app.py:carte()) sans jamais changer la mise en page. */
.carte { background:var(--surface); border:1px solid var(--card-line); border-left:4px solid var(--card-line2);
  border-radius:var(--r-md); padding:18px 22px; box-shadow:var(--shadow-card);
  transition:transform 0.15s, box-shadow 0.15s, border-color 0.15s; }
.carte:hover { transform:translateY(-2px); box-shadow:var(--shadow-raised); }
.carte .k { font-size:0.62rem; letter-spacing:1.3px; text-transform:uppercase;
  color:var(--card-dim); margin-bottom:8px; font-weight:700; }
.carte .v { font-size:1.35rem; font-weight:800; color:var(--card-txt); }

/* Cartes "stat" (icone + grand nombre en tete, libelle pleine largeur en
   dessous) — variante optionnelle de .carte utilisee pour les indicateurs
   cles en haut de page (voir app.py:carte(..., icone=...)). Libelle sous
   l'icone (plutot qu'a cote) pour eviter le retour a la ligne premature
   dans une grille serree a 5 colonnes. N'affecte jamais les appels
   existants qui n'utilisent pas ce parametre. */
.carte-stat { display:flex; flex-direction:column; gap:12px; }
.carte-stat .stat-tete { display:flex; align-items:center; gap:12px; }
.carte-stat .stat-icone { width:40px; height:40px; border-radius:var(--r-md); flex-shrink:0;
  display:flex; align-items:center; justify-content:center; font-size:1.15rem;
  background:var(--action-bg); }
.carte-stat .v { font-size:1.45rem; margin:0; }
.carte-stat .k { margin-bottom:0; }

/* Protection — carte d'etat proeminente (surveillance active/inactive) :
   badge de grande taille + bouton Activer/Desactiver a cote (voir app.py,
   st.container(key="surveillance_etat")). Carte blanche : tokens "carte"
   pour la case a cocher native qu'elle contient. */
.st-key-surveillance_etat { background:var(--surface); border:1px solid var(--card-line);
  border-radius:var(--r-lg); padding:22px 24px 18px; box-shadow:var(--shadow-card); margin:4px 0 28px; }
.st-key-surveillance_etat [data-testid="stCheckbox"] label p {
  color:var(--card-txt) !important; }
.surveillance-badge { display:inline-flex; align-items:center; gap:10px;
  padding:10px 18px; border-radius:var(--r-pill); font-size:1rem; font-weight:700; }
.surveillance-badge .point { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.surveillance-badge.ok { background:var(--vert-bg); color:var(--vert); }
.surveillance-badge.ok .point { background:var(--vert); box-shadow:0 0 0 4px rgba(4,120,87,.16); }
.surveillance-badge.warn { background:var(--jaune-bg); color:var(--jaune); }
.surveillance-badge.warn .point { background:var(--jaune); box-shadow:0 0 0 4px rgba(146,64,14,.16); }

/* Protection — carte de dossier surveille : nom + badge present/absent,
   memes tokens semantiques --vert/--jaune que les autres badges. */
.carte-dossier { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.carte-dossier .nom { font-weight:600; color:var(--card-txt); font-size:0.85rem;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dossier-badge { display:inline-flex; align-items:center; padding:4px 12px;
  border-radius:var(--r-pill); font-size:0.68rem; font-weight:700; letter-spacing:0.3px; flex-shrink:0; }
.dossier-badge.ok { background:var(--vert-bg); color:var(--vert); }
.dossier-badge.warn { background:var(--jaune-bg); color:var(--jaune); }

/* Panneaux d'information (safenote / analyse-alerte) — teinte pastel pleine
   (famille "carte blanche"), texte fonce a l'interieur : tokens "carte". */
.safenote { display:flex; align-items:center; gap:12px; margin:16px 0 8px;
  font-size:0.85rem; color:var(--card-txt-2); line-height:1.5;
  background:var(--info-bg); border:1px solid var(--info);
  border-radius:var(--r-md); padding:14px 18px; box-shadow:var(--shadow-card); }
.safenote .dot { color:var(--info); font-size:0.7rem; flex-shrink:0; }

/* Alerte d'information de la page Analyse — carte sans puce, teinte or
   douce, texte aligne a gauche. Distincte de .safenote (utilisee ailleurs)
   pour ne pas affecter les autres pages. */
.analyse-alerte { margin:4px 0 28px; font-size:0.92rem; color:var(--card-txt-2);
  line-height:1.65; text-align:left;
  background:var(--action-bg); border:1px solid var(--card-line);
  border-radius:var(--r-lg); padding:20px 24px; box-shadow:var(--shadow-card); }

/* Cartes d'options de la page Analyse (Quarantaine automatique, Explication
   SHAP) — scoping via la classe generee par st.container(key="analyse_options")
   pour ne jamais affecter les cases a cocher des autres pages (Scan de
   dossier, Protection), qui reutilisent le meme composant natif. Cartes
   blanches : tokens "carte". */
.st-key-analyse_options { margin:0 0 24px; }
.st-key-analyse_options [data-testid="stCheckbox"] {
  background:var(--surface); border:1px solid var(--card-line);
  border-radius:var(--r-md); padding:16px 20px; box-shadow:var(--shadow-card);
  transition:border-color 0.15s, box-shadow 0.15s; }
.st-key-analyse_options [data-testid="stCheckbox"]:hover {
  border-color:var(--action); box-shadow:var(--shadow-raised); }
.st-key-analyse_options [data-testid="stCheckbox"] label p {
  font-weight:600 !important; color:var(--card-txt) !important; font-size:0.92rem !important; }

/* Barres SHAP (page Analyse) — posees directement sur le fond sombre, pas
   dans une carte : tokens "page". */
.shap-ax { display:flex; justify-content:space-between; font-size:0.6rem;
  letter-spacing:1px; text-transform:uppercase; color:var(--dim);
  padding-bottom:10px; border-bottom:1px solid var(--line); margin-bottom:12px; font-weight:700; }
.shap-l { display:flex; align-items:center; height:28px; font-size:0.74rem; }
.shap-nom { width:30%; color:var(--dim); text-align:right; padding-right:12px;
  font-family:'JetBrains Mono',monospace; font-size:0.7rem; }
.shap-bar { width:52%; display:flex; align-items:center; position:relative; }
.shap-bar::before { content:''; position:absolute; left:50%; top:-3px; bottom:-3px;
  width:1px; background:var(--dim2); }
.shap-half { width:50%; display:flex; }
.shap-half.g { justify-content:flex-end; }
.shap-fill { height:10px; border-radius:var(--r-pill); }
.shap-val { width:18%; text-align:right; font-size:0.72rem; color:var(--dim); font-weight:600; }

.stButton > button { background:var(--action);
  color:var(--on-gold); border:none; border-radius:var(--r-sm); font-size:0.85rem; font-weight:700;
  padding:11px 32px; box-shadow:0 1px 3px rgba(245,179,1,.35);
  transition:background 0.15s, box-shadow 0.15s, transform 0.15s; }
.stButton > button:hover { background:var(--action-hover);
  box-shadow:var(--shadow-raised); color:var(--on-gold); transform:translateY(-1px); }

/* Formulaire de connexion (st.form — utilise uniquement par la page de
   connexion dans cette application) : carte blanche avec accent en tete,
   tokens "carte" pour son contenu (labels natifs des champs texte, non
   couverts par une classe personnalisee ailleurs dans l'application). */
[data-testid="stForm"] { background:var(--surface); border:1px solid var(--card-line);
  border-top:4px solid var(--action); border-radius:var(--r-lg);
  padding:8px 8px 4px; box-shadow:var(--shadow-overlay); }
[data-testid="stForm"] label, [data-testid="stForm"] label p {
  color:var(--card-txt) !important; }
[data-testid="stForm"] [data-testid="stTextInputRootElement"] {
  background:var(--surface-2) !important; border:1px solid var(--card-line) !important; }
[data-testid="stForm"] [data-testid="stTextInputRootElement"] input {
  background:transparent !important; color:var(--card-txt) !important; }
[data-testid="stForm"] [data-testid="stTextInputRootElement"] button[aria-label="Show password"],
[data-testid="stForm"] [data-testid="stTextInputRootElement"] button[aria-label="Hide password"] {
  background-color:transparent !important; background:transparent !important;
  border:none !important; box-shadow:none !important; }
[data-testid="stForm"] [data-testid="stTextInputRootElement"] svg { fill:var(--card-dim) !important; }
[data-testid="stFormSubmitButton"] button {
  background:var(--action) !important; color:var(--on-gold) !important;
  border:none !important; border-radius:var(--r-sm) !important; font-weight:700 !important;
  box-shadow:0 1px 3px rgba(245,179,1,.35) !important;
  transition:background 0.15s, box-shadow 0.15s, transform 0.15s !important; }
[data-testid="stFormSubmitButton"] button:hover {
  background:var(--action-hover) !important; box-shadow:var(--shadow-raised) !important;
  transform:translateY(-1px) !important; }
[data-testid="stFormSubmitButton"] button p { color:var(--on-gold) !important; font-weight:700 !important; }

/* Zone de televersement (page Analyse uniquement) — devient elle aussi une
   surface claire (famille "carte blanche"), tokens "carte" pour son
   contenu. Le libelle natif au-dessus de la zone reste sur le fond sombre :
   tokens "page" (inchange). */
[data-testid="stFileUploader"] label { color:var(--txt) !important; font-weight:700 !important;
  font-size:1.05rem !important; }
[data-testid="stFileUploader"] { max-width:100%; width:100%; margin:8px 0 0 0; display:flex !important; flex-direction:column !important; align-items:center !important; }
[data-testid="stFileUploader"] svg { display:none !important; }
[data-testid="stFileUploader"] section {
  align-items:center !important; text-align:center !important;
  background:var(--surface-2) !important; border:2px dashed var(--card-line2) !important;
  border-radius:var(--r-lg) !important; width:100% !important;
  padding:52px 0 !important; display:flex !important; flex-direction:column !important;
  justify-content:center !important; gap:24px !important;
  transition:border-color 0.15s, background 0.15s; }
[data-testid="stFileUploader"] section:hover {
  border-color:var(--action) !important; background:var(--action-bg) !important; }
[data-testid="stFileUploader"] section::before {
  content:'' !important; display:block !important; width:100px !important; height:116px !important;
  background-repeat:no-repeat !important; background-position:center !important;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 116' fill='none'><path d='M20 6 h44 l18 18 v86 h-62 z' stroke='%236B7280' stroke-width='3'/><path d='M64 6 v18 h18' stroke='%236B7280' stroke-width='3'/><line x1='8' y1='44' x2='92' y2='44' stroke='%23F5B301' stroke-width='6'/></svg>") !important; }

[data-testid="stExpander"] summary,
[data-testid="stExpander"] details summary {
  display:flex !important; align-items:center !important;
  white-space:nowrap !important; overflow:hidden !important;
  letter-spacing:normal !important; }
/* Uniquement le texte du libelle (balise <p>) — jamais "summary > *", qui
   forcait aussi la police monospace sur l'icone native de bascule
   (rendue par une police d'icones) et lui faisait afficher son nom brut
   ("arrow_down") en texte au lieu du chevron attendu. Bug trouve et
   corrige lors de la revue finale. */
[data-testid="stExpander"] summary p {
  position:static !important; float:none !important;
  transform:none !important; margin:0 !important;
  font-family:'JetBrains Mono','Courier New',monospace !important; font-size:0.8rem !important;
  color:var(--txt) !important; white-space:nowrap !important;
  overflow:hidden !important; text-overflow:ellipsis !important; }
[data-testid="stExpander"] summary { gap:8px !important; list-style:none !important; }
[data-testid="stExpander"] summary::-webkit-details-marker { display:none !important; }
[data-testid="stExpander"] { border-radius:var(--r-md) !important; border-color:var(--line) !important; }

[data-testid="stFileUploader"] section > button {
  all:unset !important; box-sizing:border-box !important; cursor:pointer !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  width:auto !important; margin:0 auto !important; padding:12px 40px !important;
  border:1px solid var(--card-line2) !important; border-radius:var(--r-sm) !important;
  color:var(--card-txt-2) !important; font-size:1rem !important; font-weight:500 !important;
  font-family:'Inter',sans-serif !important; text-align:center !important; }
[data-testid="stFileUploader"] section > button:hover {
  border-color:var(--action) !important; color:var(--action) !important; }
[data-testid="stFileUploader"] section > button > * {
  all:unset !important; font:inherit !important; color:inherit !important; }
[data-testid="stFileUploader"] section > button::first-letter { margin:0 !important; }
[data-testid="stBaseButton-secondary"] {
  display:flex !important; align-items:center !important; justify-content:center !important; }
[data-testid="stBaseButton-secondary"] > * { margin:0 auto !important; }

/* Onglets natifs (page de connexion : "Se connecter" / "Creer un compte")
   — poses sur le fond sombre (tokens "page"), soulignement actif en accent or. */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid var(--line); }
[data-testid="stTabs"] [data-baseweb="tab"] { color:var(--dim); font-weight:600; }
[data-testid="stTabs"] [aria-selected="true"] { color:var(--txt) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color:var(--action) !important; }
</style>
"""
