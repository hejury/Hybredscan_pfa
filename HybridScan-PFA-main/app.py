#!/usr/bin/env python3
"""app.py - Interface du systeme hybride de detection de malwares."""
import os, sys, json, tempfile, base64
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import analyser, HISTORY, QUARANTINE, BASE
from auth import verify, verify_compte_configure, register
from style import CSS
import quarantine_manager
from backend_shared import (
    _cible_interdite, _config_racines_scan, _racines_autorisees,
    _cible_dans_racines_autorisees, valider_dossier_scan, charger_historique,
)

st.set_page_config(page_title="Detection de malwares", page_icon="\U0001F6E1",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

# --- Authentification : verrou pose avant tout rendu de page/barre laterale.
# Aucun code de page (upload, scan, watcher, export) ne s'execute avant que
# cette section ait confirme une session authentifiee — voir auth.py pour le
# mecanisme (verify_compte_configure : compte unique configure via
# .streamlit/secrets.toml, jamais via users.json).
if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

def page_connexion():
    st.markdown('<div class="hdr"><h1>Connexion à HybridScan</h1>'
                "<div class=\"sub\">Accédez à la plateforme d'analyse de fichiers.</div></div>",
                unsafe_allow_html=True)
    st.caption("Connectez-vous avec votre compte, ou créez-en un nouveau ci-dessous.")
    _c1, _c2, _c3 = st.columns([1, 1.2, 1])
    with _c2:
        _onglet_connexion, _onglet_creation = st.tabs(["Se connecter", "Créer un compte"])

        with _onglet_connexion:
            with st.form("form_connexion", clear_on_submit=True):
                _identifiant = st.text_input("Identifiant")
                _mot_de_passe = st.text_input("Mot de passe", type="password")
                _soumis = st.form_submit_button("Se connecter")
            if _soumis:
                _nom = _identifiant.strip()
                if verify(_nom, _mot_de_passe) or verify_compte_configure(_identifiant, _mot_de_passe):
                    st.session_state.authentifie = True
                    st.session_state.utilisateur = _nom
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

        with _onglet_creation:
            with st.form("form_creation", clear_on_submit=True):
                _nouvel_identifiant = st.text_input("Nom d'utilisateur", key="creation_identifiant")
                _nouveau_mdp = st.text_input("Mot de passe", type="password", key="creation_mdp")
                _confirmation_mdp = st.text_input("Confirmer le mot de passe", type="password",
                                                  key="creation_mdp_confirmation")
                _soumis_creation = st.form_submit_button("Créer un compte")
            if _soumis_creation:
                if _nouveau_mdp != _confirmation_mdp:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    _ok, _message = register(_nouvel_identifiant, _nouveau_mdp)
                    if _ok:
                        st.success(_message)
                    else:
                        st.error(_message)

if not st.session_state.authentifie:
    page_connexion()
    st.stop()

VERT, ROUGE, JAUNE = "#047857", "#B91C1C", "#92400E"

# Mapping centralise et exhaustif des valeurs de verdict reellement
# renvoyees par analyze.analyser() : "malveillant", "sain", "indetermine"
# (voir analyze.py). Toute valeur non repertoriee ici est traitee comme
# une erreur technique neutre et n'est JAMAIS assimilee a "sain".
VERDICTS = {
    "malveillant": {"libelle": "MALVEILLANT",  "couleur": ROUGE, "classe": "v-mal"},
    "sain":        {"libelle": "SAIN",         "couleur": VERT,  "classe": "v-sain"},
    "indetermine": {"libelle": "INDETERMINE",  "couleur": JAUNE, "classe": "v-ind"},
}
_VERDICT_INCONNU = {"libelle": "ERREUR TECHNIQUE", "couleur": JAUNE, "classe": "v-ind"}

def info_verdict(verdict):
    return VERDICTS.get(verdict, _VERDICT_INCONNU)

def classe(verdict):
    return info_verdict(verdict)["classe"]

def bandeau(res):
    st.markdown(
        '<div class="verdict %s">'
        '<div class="via">Conclu par : etape %s</div>'
        '<div class="etat">%s</div>'
        '<div class="msg">%s</div>'
        '</div>' % (classe(res["verdict"]), res["etape"],
                    info_verdict(res["verdict"])["libelle"], res["message"]),
        unsafe_allow_html=True)

def jauge(proba):
    pct = proba * 100
    c = ROUGE if proba >= 0.5 else (JAUNE if proba >= 0.3 else VERT)
    st.markdown(
        '<div class="jauge-lbl"><span>Probabilite malveillant</span>'
        '<span style="color:%s">%.1f %%</span></div>'
        '<div class="jauge"><div style="width:%.1f%%;background:%s"></div></div>'
        % (c, pct, pct, c), unsafe_allow_html=True)

def carte(k, v, c=None, icone=None):
    bordure = ('border-left-color:%s;' % c) if c else ''
    if icone:
        st.markdown(
            '<div class="carte carte-stat" style="%s">'
            '<div class="stat-tete"><div class="stat-icone">%s</div>'
            '<div class="v" style="color:%s">%s</div></div>'
            '<div class="k">%s</div></div>'
            % (bordure, icone, c or "var(--txt)", v, k), unsafe_allow_html=True)
    else:
        st.markdown('<div class="carte" style="%s"><div class="k">%s</div>'
                    '<div class="v" style="color:%s">%s</div></div>'
                    % (bordure, k, c or "var(--txt)", v), unsafe_allow_html=True)

def carte_dossier(libelle, present):
    """Carte de dossier surveille (page Protection) : nom + badge present/absent,
    memes tokens semantiques --vert/--jaune que les autres badges de l'application."""
    classe = "ok" if present else "warn"
    etat = "Présent" if present else "Absent"
    st.markdown(
        '<div class="carte carte-dossier"><span class="nom">%s</span>'
        '<span class="dossier-badge %s">%s</span></div>'
        % (libelle, classe, etat), unsafe_allow_html=True)

def section_titre(texte):
    """Titre de section avec barre d'accent — remplace le texte en gras nu
    pour une hierarchie visuelle claire (titre de page -> section -> contenu)."""
    st.markdown('<div class="section-titre"><div class="barre"></div>'
                '<div class="texte">%s</div></div>' % texte, unsafe_allow_html=True)

def barres_shap(contribs):
    st.markdown('<div class="shap-ax"><span>&larr; pousse vers sain</span>'
                '<span>pousse vers malveillant &rarr;</span></div>',
                unsafe_allow_html=True)
    vmax = max(abs(s) for _, s, _ in contribs) or 1
    for nom, sval, val in contribs:
        larg = abs(sval) / vmax * 100
        if sval > 0:
            barre = ('<div class="shap-half g"></div><div class="shap-half">'
                     '<div class="shap-fill" style="width:%.0f%%;background:%s"></div></div>'
                     % (larg, ROUGE))
        else:
            barre = ('<div class="shap-half g"><div class="shap-fill" '
                     'style="width:%.0f%%;background:%s"></div></div>'
                     '<div class="shap-half"></div>' % (larg, VERT))
        st.markdown('<div class="shap-l"><div class="shap-nom">%s</div>'
                    '<div class="shap-bar">%s</div>'
                    '<div class="shap-val">%+.4f</div></div>'
                    % (nom, barre, sval), unsafe_allow_html=True)

def taille_lisible(n_octets):
    """Formatage humain d'une taille en octets — valeur reelle
    (UploadedFile.size), jamais estimee."""
    n = float(n_octets)
    for unite in ("o", "Ko", "Mo", "Go"):
        if n < 1024 or unite == "Go":
            return ("%.0f %s" % (n, unite)) if unite == "o" else ("%.1f %s" % (n, unite))
        n /= 1024

def hash_display(label, valeur):
    """Composant reutilisable pour une empreinte SHA-256 : police
    monospace, retour a la ligne sur, valeur complete disponible et bouton
    de copie natif Streamlit (st.code) — pas de HTML/JS personnalise."""
    st.caption(label)
    st.code(valeur, language=None)

_SOURCE_LIBELLES = {
    "1 (signature)": "Détection par signature (VirusTotal)",
    "2 (IA)": "Analyse statique par modèle",
    "2 (document)": "Vérification par signature (document — analyse IA non applicable)",
    "2 (ia_pdf)": "Analyse statique par modèle PDF",
    "2 (ia_docx)": "IA_DOCX — prototype de recherche (non certifié)",
    "2 (format invalide)": "Format de fichier invalide (aucune analyse statique)",
}
def source_libelle(etape):
    return _SOURCE_LIBELLES.get(etape, etape)

# Familles routees comme "document" cote backend (analyze.identifier_fichier) :
# jamais transmises au modele PE. Seul le PDF dispose d'un pipeline ML dedie
# (document_ml/pdf) ; DOC/DOCX restent au comportement phase 1 (signature
# uniquement) — voir analyze.analyser(). Regroupees ici uniquement pour les
# sections d'UI generiques (masquer jauge/SHAP PE, captions dediees) qui
# s'appliquent identiquement aux trois, quel que soit leur etat ML respectif.
_FAMILLES_DOCUMENT = {"pdf", "doc", "docx"}

def etat_quarantaine(action):
    """Derive un statut sans jamais exposer le chemin absolu contenu dans
    analyze.py:action (voir SECURITY-NOTE.md)."""
    if action.startswith("quarantaine"):
        return "Mis en quarantaine"
    if action.startswith("echec quarantaine"):
        return "Échec de la mise en quarantaine"
    return "Aucune"

# Correspondance francaise optionnelle, additive uniquement : le nom brut
# de la caracteristique reste toujours disponible a cote (voir
# design-system/malware-detection/PAGE-SPECIFICATIONS.md §9.6).
_SHAP_LABELS = {
    "sect_entropy_max": "Entropie maximale des sections",
    "sect_entropy_mean": "Entropie moyenne des sections",
    "entropy": "Entropie globale du fichier",
    "entry_point": "Point d'entrée",
    "size_code": "Taille du code",
    "size_image": "Taille de l'image en mémoire",
    "nb_imports": "Nombre de fonctions importées",
    "nb_dll": "Nombre de bibliothèques liées",
    "nb_sections": "Nombre de sections",
    "subsystem": "Sous-système",
    "dll_char": "Caractéristiques DLL",
    "machine": "Architecture cible",
    "file_size": "Taille du fichier",
}
def libelle_feature(nom):
    fr = _SHAP_LABELS.get(nom)
    return "%s (%s)" % (fr, nom) if fr else nom

_ETAPE_CLASSE_VERDICT = {"sain": "ok", "malveillant": "bad", "indetermine": "warn"}

def etapes_analyse(res, shap_etat, shap_detail):
    """Resume, apres coup, la chaine reellement executee par analyser().
    L'appel etant synchrone, ceci n'est jamais un flux d'evenements simule."""
    via_signature = res["etape"].startswith("1")

    if res.get("famille") in _FAMILLES_DOCUMENT:
        # Chaine document (.pdf/.doc/.docx) : 5 etapes fixes, distinctes de
        # la chaine PE. L'etape 4 reflete honnetement ce qui s'est reellement
        # produit : "non applicable" (DOC/DOCX, ou PDF sans modele entraine
        # disponible), "format invalide" (PDF structurellement invalide,
        # jamais transmis a un modele), ou une veritable classification par
        # le modele PDF dedie (document_ml/pdf) quand il est disponible —
        # jamais presente comme un echec d'IA lorsque ce n'en est pas un
        # (cahier des charges §7).
        lignes = [
            ("01", "Fichier reçu", "ok", res["fichier"]),
            ("02", "Empreinte SHA-256 calculée", "ok", res["sha256"][:16] + "…"),
        ]
        if via_signature:
            lignes.append(("03", "Vérification par signature", "ok", "Résultat obtenu par signature"))
            lignes.append(("04", "Analyse IA", "skip", "Non nécessaire — résultat déjà obtenu par signature"))
        else:
            vt_statut = res["etape1"].get("statut", "")
            if vt_statut == "inconnu":
                lignes.append(("03", "Vérification par signature", "ok", "Fichier inconnu de VirusTotal"))
            else:
                lignes.append(("03", "Vérification par signature", "warn",
                                "VirusTotal indisponible (%s) — bascule contrôlée" % vt_statut))
            if res["etape"] == "2 (format invalide)":
                lignes.append(("04", "Analyse IA", "warn",
                                "Format invalide — aucune analyse statique effectuée"))
            elif res["etape"] == "2 (ia_pdf)":
                if res["confiance"] != "":
                    lignes.append(("04", "Analyse statique par modèle PDF", "ok",
                                    "Classification effectuée (confiance %.0f %%)" % (res["confiance"] * 100)))
                else:
                    lignes.append(("04", "Analyse statique par modèle PDF", "warn",
                                    "Échec technique : %s" % res["message"]))
            elif res["etape"] == "2 (ia_docx)":
                if res["confiance"] != "":
                    lignes.append(("04", "IA_DOCX — prototype de recherche", "ok",
                                    "Classification expérimentale, non certifiée (confiance %.0f %%)"
                                    % (res["confiance"] * 100)))
                else:
                    lignes.append(("04", "IA_DOCX — prototype de recherche", "warn",
                                    "Échec technique : %s" % res["message"]))
            else:
                lignes.append(("04", "Analyse IA", "skip", "Non applicable à ce format"))
        detail_resultat = info_verdict(res["verdict"])["libelle"]
        if res["action"].startswith("quarantaine"):
            detail_resultat += " — mis en quarantaine"
        lignes.append(("05", "Résultat", _ETAPE_CLASSE_VERDICT.get(res["verdict"], "warn"), detail_resultat))

        html = ['<div class="etapes">']
        for n, titre, etat, detail in lignes:
            html.append('<div class="etape-l %s"><span class="n">%s</span>'
                         '<span class="t">%s</span><span class="e">%s</span></div>'
                         % (etat, n, titre, detail))
        html.append('</div>')
        st.markdown("".join(html), unsafe_allow_html=True)
        return

    lignes = [
        ("01", "Fichier reçu", "ok", res["fichier"]),
        ("02", "Empreinte SHA-256 calculée", "ok", res["sha256"][:16] + "…"),
    ]
    if via_signature:
        lignes.append(("03", "Vérification par signature", "ok", "Résultat obtenu par signature"))
        lignes.append(("04", "Analyse statique par modèle", "skip",
                        "Non nécessaire — résultat déjà obtenu par signature"))
    else:
        vt_statut = res["etape1"].get("statut", "")
        if vt_statut == "inconnu":
            lignes.append(("03", "Vérification par signature", "ok", "Fichier inconnu de VirusTotal"))
        else:
            lignes.append(("03", "Vérification par signature", "warn",
                            "VirusTotal indisponible (%s) — bascule contrôlée" % vt_statut))
        ia = res.get("etape2", {})
        if str(ia.get("statut", "")).startswith("erreur"):
            lignes.append(("04", "Analyse statique par modèle", "warn",
                            "Échec technique : %s" % ia.get("detail", ia.get("statut"))))
        else:
            lignes.append(("04", "Analyse statique par modèle", "ok",
                            "Classification effectuée (confiance %.0f %%)" % (ia.get("confiance", 0) * 100)))
    lignes.append(("05", "Verdict", _ETAPE_CLASSE_VERDICT.get(res["verdict"], "warn"),
                    info_verdict(res["verdict"])["libelle"]))
    lignes.append(("06", "Mise en quarantaine",
                    "ok" if res["action"].startswith("quarantaine") else "skip",
                    etat_quarantaine(res["action"])))
    lignes.append(("07", "Explication SHAP", shap_etat, shap_detail))

    html = ['<div class="etapes">']
    for n, titre, etat, detail in lignes:
        html.append('<div class="etape-l %s"><span class="n">%s</span>'
                     '<span class="t">%s</span><span class="e">%s</span></div>'
                     % (etat, n, titre, detail))
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)

# Identifiants canoniques des 6 destinations, distincts des libelles
# affiches. Corrige le bug audite : les libelles et le contenu affiche
# etaient auparavant desynchronises via un index positionnel partage
# entre la liste de libelles et les blocs `if _actif(N)` plus bas.
_pages = [
    ("dashboard",    "Tableau de bord"),
    ("analyse",      "Analyse"),
    ("historique",   "Historique"),
    ("quarantaine",  "Quarantaine"),
    ("protection",   "Protection"),
    ("parametres",   "Paramètres"),
]
# "scan_dossier" n'est plus une destination independante (fusionnee dans
# l'onglet "Scanner un dossier" de la page Analyse, voir plus bas) : ni
# _pages, ni _TITRES/_EYEBROW ne conservent plus d'entree pour cet id.
_TITRES = {
    "analyse":      ("Analyse",
                     "Analysez un fichier isolé ou l'ensemble des fichiers PE d'un dossier accessible "
                     "au serveur HybridScan — vérification par signature puis, si nécessaire et si le "
                     "format le permet, analyse statique par apprentissage automatique."),
    "historique":   ("Historique des analyses", "Ensemble des analyses effectuées et journalisées."),
    "quarantaine":  ("Quarantaine", "Consultez les fichiers isolés après une détection malveillante."),
    "protection":   ("Protection", "Surveillez automatiquement des dossiers pour analyser "
                     "tout nouveau fichier déposé."),
    "dashboard":    ("Tableau de bord", "Vue d'ensemble des analyses enregistrées par HybridScan."),
    "parametres":   ("Paramètres", "Informations sur le compte et l'application."),
}
_EYEBROW = {
    "analyse":      "ANALYSE",
    "historique":   "SUIVI DES ANALYSES",
    "quarantaine":  "FICHIERS ISOLÉS",
    "protection":   "SURVEILLANCE EN TEMPS RÉEL",
    "dashboard":    "VUE D'ENSEMBLE",
    "parametres":   "COMPTE",
}

_DESTINATIONS_VALIDES = {_id for _id, _ in _pages}
if "pg" not in st.session_state or st.session_state.pg not in _DESTINATIONS_VALIDES:
    # Egalement le repli si une session anterieure a memorise une
    # destination retiree (ex. l'ancienne page "scan_dossier" independante,
    # desormais fusionnee dans "analyse") -- jamais une page blanche ni une
    # boucle de navigation.
    st.session_state.pg = "dashboard"

_LOGO_PATH = Path(__file__).resolve().parent / "logo.png"

def _logo_html():
    """Marque de la barre laterale : logo.png (mire H style HISNEO) si le
    fichier est present et lisible, sinon repli sur une simple pastille
    "H" doree — l'application ne doit jamais planter faute de logo."""
    if _LOGO_PATH.exists():
        try:
            _b64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
            return '<img class="kl-logo" src="data:image/png;base64,%s" alt="HISNEO">' % _b64
        except Exception:
            pass
    return '<div class="kl-hex">H</div>'

with st.sidebar:
    st.markdown('<div class="kl">%s'
                '<div><div class="kl-t">Malware Detection</div>'
                '<div class="kl-s">Threat Intelligence Portal</div></div></div>'
                % _logo_html(), unsafe_allow_html=True)
    st.markdown('<div class="kl-lbl">Menu</div>', unsafe_allow_html=True)
    for _id, _label in _pages:
        _type = "primary" if _id == st.session_state.pg else "secondary"
        if st.button(_label, key=f"kp_{_id}", use_container_width=True, type=_type):
            st.session_state.pg = _id
            st.rerun()
    st.markdown('<div class="kl-lbl" style="margin-top:10px">%s</div>'
                % (st.session_state.get("utilisateur") or "Session"), unsafe_allow_html=True)
    st.markdown('<div class="kf">Projet de fin d\'annee &middot; 2025/2026</div>',
                unsafe_allow_html=True)

def _deconnexion():
    """Deconnexion — identique a l'ancienne action de la barre laterale :
    arrete la surveillance de dossiers en cours si active, puis efface
    entierement la session avant de revenir a la page de connexion."""
    _prot_en_session = st.session_state.get("protection")
    if _prot_en_session is not None and getattr(_prot_en_session, "active", False):
        _prot_en_session.arreter()
    for _cle in list(st.session_state.keys()):
        del st.session_state[_cle]
    st.rerun()

def _actif(dest_id):
    return st.session_state.pg == dest_id

_titre, _sous_titre = _TITRES.get(st.session_state.pg, ("Detection hybride de malwares", ""))
_eyebrow = _EYEBROW.get(st.session_state.pg, "")
# Ligne d'en-tete : titre/sous-titre a gauche ; colonne d'action reservee au
# milieu — remplie uniquement par les pages qui ont une action principale
# (ex. Dashboard : "Analyser un fichier"), vide sinon sans impact visuel ;
# colonne deconnexion a droite, presente sur toutes les pages (voir
# _deconnexion() ci-dessus — bouton icone seule deplace depuis le bas de la
# barre laterale pour ne jamais etre duplique ; l'identifiant reste visible
# uniquement dans la barre laterale). vertical_alignment="top" place ce
# bouton au plus haut de l'en-tete plutot que centre sur tout le bloc
# titre/sous-titre.
_col_entete_titre, _col_entete_action, _col_entete_compte = st.columns(
    [3.7, 1, 0.5], vertical_alignment="top")
with _col_entete_titre:
    st.markdown(
        '<div class="entete-eyebrow">%s</div><div class="entete-titre">%s</div>'
        '<div class="entete-sous">%s</div>' % (_eyebrow, _titre, _sous_titre),
        unsafe_allow_html=True)
with _col_entete_compte:
    with st.container(key="entete_compte"):
        if st.button("", icon=":material/logout:", key="btn_deconnexion",
                     help="Se déconnecter"):
            _deconnexion()
st.markdown('<div class="entete-ligne"></div>', unsafe_allow_html=True)


# _cible_interdite / _config_racines_scan / _racines_autorisees /
# _cible_dans_racines_autorisees / valider_dossier_scan : extraites vers
# backend_shared.py (importees ci-dessus) pour etre partagees a l'identique
# avec l'API FastAPI -- voir backend_shared.py pour le code et
# validation/NEXTJS-FASTAPI-INTEGRATION.md pour le contexte de l'extraction.


if _actif("analyse"):
    st.caption("Analysez un fichier ou scannez un dossier depuis un seul espace.")
    with st.container(border=True, key="analyse_scan_card"):
        section_titre("Analyse &amp; Scan")

        # --- Section FICHIER (analyse d'un fichier isole) -------------------
        st.markdown('<div class="kl-lbl">FICHIER</div>', unsafe_allow_html=True)
        st.markdown("**Analyser un fichier**")
        # B. Panneau d'information de securite — carte pleine largeur, sans puce.
        st.markdown(
            '<div class="analyse-alerte">'
            "Le fichier n'est jamais exécuté ; seule sa structure est lue (analyse statique). "
            "Une vérification par signature est effectuée en premier — l'analyse statique par "
            "apprentissage automatique n'intervient que si nécessaire. Un fichier classé "
            "malveillant peut être mis en quarantaine côté serveur."
            '</div>', unsafe_allow_html=True)

        # C. Options d'analyse — rangee de deux cartes alignees, au-dessus de la
        # zone de televersement. Le container cible (via sa classe st-key-*)
        # permet de styliser ces cases a cocher sans affecter celles des pages
        # Scan de dossier / Protection qui reutilisent le meme composant natif.
        with st.container(key="analyse_options"):
            oc1, oc2 = st.columns(2)
            with oc1:
                isoler = st.checkbox("Quarantaine automatique", value=True)
            with oc2:
                shap_on = st.checkbox("Explication SHAP", value=True)

        # D. Zone de televersement — large et proeminente, focus visuel de la page.
        fichier = st.file_uploader("Choisir un fichier à analyser",
                                   type=["exe", "dll", "pdf", "doc", "docx"],
                                   label_visibility="visible")
        st.caption("Formats acceptés : .exe, .dll, .pdf, .doc et .docx. "
                   "L’analyse IA avancée est actuellement disponible uniquement pour les "
                   "exécutables Windows (.exe, .dll). Les documents sont vérifiés par signature.")
        if fichier is not None:
            fc1, fc2 = st.columns(2)
            with fc1: carte("Fichier sélectionné", fichier.name)
            with fc2: carte("Taille", taille_lisible(fichier.size))

        # D. Action d'analyse — desactivee tant qu'aucun fichier n'est choisi.
        # Le modele d'execution synchrone et mono-thread de Streamlit (tout le
        # script est rejoue a chaque interaction) empeche deja une double
        # soumission concurrente pendant le calcul ; la desactivation ci-dessous
        # est la protection pratique supplementaire disponible cote frontend.
        lancer = st.button("Lancer l'analyse", disabled=(fichier is None))

        if fichier is not None and lancer:
            suffixe = os.path.splitext(fichier.name)[1] or ".bin"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffixe)
            tmp.write(fichier.getbuffer()); tmp.close()
            chemin = tmp.name

            with st.spinner("Analyse en cours…"):
                # Copie temporaire du televersement -- jamais le fichier reel
                # de l'utilisateur (Desktop/Telechargements) : voir
                # validation/QUARANTINE-MVP.md pour la distinction
                # upload/chemin local reel.
                res = analyser(chemin, isoler=isoler, source_context=quarantine_manager.SOURCE_UPLOAD)

                # Calcul de l'explication SHAP avant le rendu (pas apres), pour
                # pouvoir la refleter honnetement dans le resume des etapes (E)
                # sans jamais simuler un flux d'evenements qui n'existe pas.
                exp = None
                shap_etat, shap_detail = "skip", "Non applicable — étape 2 non exécutée"
                if "etape2" in res and not str(res["etape2"].get("statut", "")).startswith("erreur"):
                    if shap_on:
                        if os.path.exists(chemin):
                            try:
                                from explain import expliquer
                                resultat_shap = expliquer(chemin, top=10)
                                if "erreur" in resultat_shap:
                                    shap_etat = "warn"
                                    shap_detail = "Indisponible : %s" % resultat_shap["erreur"]
                                else:
                                    exp = resultat_shap
                                    shap_etat, shap_detail = "ok", "Facteurs calculés"
                            except Exception as e:
                                shap_etat, shap_detail = "warn", "Indisponible : %s" % e
                        else:
                            shap_etat, shap_detail = "warn", "Fichier temporaire indisponible"
                    else:
                        shap_etat, shap_detail = "skip", "Non demandée"

            if os.path.exists(chemin):
                try: os.unlink(chemin)
                except Exception: pass

            # F. Section resultat.
            bandeau(res)
            if res.get("famille") in _FAMILLES_DOCUMENT:
                # Chaine document : jamais les captions PE ci-dessous (elles
                # supposent une classification par le modele PE), des messages
                # dedies a la place — voir cahier des charges §6. Le verdict
                # lui-meme (sain/malveillant/indetermine) reste celui de la
                # signature VirusTotal ou, pour un PDF valide avec modele
                # disponible, du modele PDF dedie — jamais deduit de l'extension.
                _ia_pdf_executee = (res["etape"] == "2 (ia_pdf)")
                _ia_docx_executee = (res["etape"] == "2 (ia_docx)")
                _ia_document_executee = _ia_pdf_executee or _ia_docx_executee
                if res["verdict"] == "sain":
                    st.caption("Cette classification ne constitue pas une garantie absolue d'innocuité.")
                elif res["verdict"] == "indetermine":
                    if res["etape"] == "2 (format invalide)":
                        st.caption("Le fichier ne correspond pas à la structure attendue pour son "
                                   "extension déclarée ; par sécurité, aucune analyse statique n’a "
                                   "été effectuée.")
                    elif _ia_document_executee:
                        st.caption("Aucun résultat sain ne doit être déduit de cet état.")
                    else:
                        st.caption("Le fichier n’est pas connu par le service de signature et ce format "
                                   "n’est pas pris en charge par le modèle IA actuel.")
                if _ia_docx_executee:
                    # IA_DOCX est un PROTOTYPE DE RECHERCHE PFA -- jamais
                    # presente comme fiable/certifie/pret pour la production,
                    # quel que soit le verdict (voir
                    # validation/DOCX-RESEARCH-MODEL-TRAINING.md).
                    st.caption("⚠️ IA_DOCX est un prototype de recherche académique, entraîné sur un "
                               "corpus externe aux limites documentées. Résultat expérimental, non "
                               "certifié — ne pas considérer comme une détection fiable en production.")
                if not _ia_document_executee:
                    st.caption("Analyse IA : non applicable à ce format")
            elif res["verdict"] == "sain":
                st.caption("Cette classification ne constitue pas une garantie absolue d'innocuité.")
            elif res["verdict"] == "indetermine":
                if str(res.get("etape2", {}).get("statut", "")).startswith("erreur"):
                    st.caption("L'analyse n'a pas pu être complétée en raison d'une erreur technique "
                               "— ceci n'est pas un verdict de sécurité.")
                else:
                    st.caption("Aucun résultat sain ne doit être déduit de cet état.")

            if "etape2" in res and not str(res["etape2"].get("statut", "")).startswith("erreur"):
                st.write("")
                jauge(res["etape2"]["confiance"])

            st.write("")
            # E. Resume des etapes reellement executees (synthese apres coup).
            etapes_analyse(res, shap_etat, shap_detail)

            # G. Details techniques — valeurs reellement renvoyees uniquement.
            st.write("")
            g1, g2, g3 = st.columns(3)
            with g1: carte("Fichier", res["fichier"])
            with g2: carte("Taille", taille_lisible(fichier.size))
            with g3: carte("Source de détection", source_libelle(res["etape"]))
            g4, g5, g6 = st.columns(3)
            with g4:
                conf = res["confiance"]
                carte("Confiance", ("%.0f %%" % (conf * 100)) if conf != "" else "—")
            with g5: carte("Quarantaine", etat_quarantaine(res["action"]))
            with g6:
                try:
                    date_lisible = datetime.fromisoformat(res["date"]).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_lisible = res["date"]
                carte("Analysé le", date_lisible)

            st.write("")
            hash_display("SHA-256", res["sha256"])

            with st.expander("Détails techniques — réponse VirusTotal"):
                st.json(res["etape1"])

            # H. Explication SHAP.
            st.write("")
            if exp is not None:
                section_titre("Contribution de chaque caractéristique")
                st.caption("Ces valeurs de Shapley décrivent les facteurs ayant influencé la décision "
                           "du modèle pour ce fichier précis ; elles ne constituent pas une preuve "
                           "causale définitive.")
                barres_shap(exp["contribs"])
                with st.expander("Version texte (alternative accessible aux couleurs et au lecteur d'écran)"):
                    tableau = pd.DataFrame([{
                        "Caractéristique": libelle_feature(nom),
                        "Valeur": valeur,
                        "Contribution": round(float(contribution), 4),
                        "Sens": "→ malveillant" if contribution > 0 else "→ sain",
                    } for nom, contribution, valeur in exp["contribs"]])
                    st.dataframe(tableau, use_container_width=True, hide_index=True)
            elif shap_etat == "warn":
                st.info(shap_detail)
            elif res.get("famille") in _FAMILLES_DOCUMENT:
                if res["etape"] == "2 (ia_pdf)":
                    st.caption("Aucune explication détaillée n’est disponible pour l’analyse statique "
                               "PDF pour le moment.")
                elif res["etape"] == "2 (ia_docx)":
                    # document_ml/docx/explain.py existe et fonctionne (voir
                    # validation/DOCX-RUNTIME-VALIDATION.md) mais n'est pas
                    # encore cable dans ce flux d'interface — meme situation
                    # que PDF ci-dessus (module backend pret, non branche a
                    # l'UI). Pas de changement plus large du calcul SHAP
                    # partage PE/PDF entrepris ici (portee minimale).
                    st.caption("Aucune explication détaillée n’est disponible pour l’analyse IA_DOCX "
                               "(prototype de recherche) pour le moment.")
                else:
                    st.caption("Analyse IA : non applicable à ce format — aucune explication SHAP à afficher.")
            elif "etape2" not in res:
                st.caption("Étape 2 non nécessaire pour ce résultat : aucune explication SHAP à afficher.")

        # --- Separateur visuel entre les deux sections, a l'interieur de la
        # MEME carte (jamais deux cartes distinctes, jamais un onglet) --
        # uniquement des primitives Streamlit natives (st.divider) et le
        # style deja existant (var(--dim)) -- aucune nouvelle classe CSS
        # ajoutee a style.py pour ce simple separateur.
        st.divider()
        st.markdown(
            '<div style="text-align:center;color:var(--dim);font-size:0.75rem;'
            'letter-spacing:.08em;margin-top:-20px;margin-bottom:4px">OU</div>',
            unsafe_allow_html=True)
        st.divider()

        # --- Section DOSSIER (scan d'un dossier local) -----------------------
        st.markdown('<div class="kl-lbl">DOSSIER</div>', unsafe_allow_html=True)
        st.markdown("**Scanner un dossier**")
        st.markdown(
            '<div class="safenote"><span class="dot">&#9679;</span>'
            "Les fichiers ne sont jamais exécutés. Les exécutables (.exe/.dll), PDF et DOCX pris en "
            "charge sont analysés ; chacun peut déclencher la vérification par signature puis, si "
            "nécessaire, l'analyse statique par modèle (les modèles PDF et DOCX restent des "
            "prototypes de recherche), selon le pipeline existant. Un fichier malveillant peut être "
            "mis en quarantaine côté serveur. Chaque analyse est enregistrée dans l'historique. Les "
            "dossiers volumineux peuvent prendre du temps : les fichiers sont traités un par un, "
            "sans traitement parallèle."
            "</div>", unsafe_allow_html=True)
        st.caption("Le dossier indiqué doit exister sur la machine qui exécute HybridScan. Cette "
                   "interface ne parcourt pas directement les dossiers de votre navigateur.")

        _racines_dispo = _racines_autorisees()
        if not _racines_dispo:
            st.error("Le scan de dossiers n'est pas configuré par l'administrateur.")
        else:
            st.caption("Dossiers autorisés : %s" % ", ".join(
                sorted((r.name or str(r)) for r in _racines_dispo)))

        dossier_saisi = st.text_input(
            "Chemin du dossier à analyser", value="",
            placeholder=r"ex. C:\Temp\a_verifier ou /home/utilisateur/dossier",
            help="Doit exister sur le serveur qui exécute HybridScan, à l'intérieur d'un dossier autorisé.",
            disabled=(not _racines_dispo))
        c1, c2 = st.columns(2)
        recursif = c1.checkbox("Inclure les sous-dossiers", value=True, disabled=(not _racines_dispo))
        isoler_scan = c2.checkbox("Quarantaine automatique", value=False, key="quar_scan",
                                  disabled=(not _racines_dispo))

        dossier = dossier_saisi.strip()
        if _racines_dispo:
            erreur_validation, fichiers, libelle_dossier, n_sousdossiers_ignores = (
                valider_dossier_scan(dossier, recursif))
        else:
            erreur_validation, fichiers, libelle_dossier, n_sousdossiers_ignores = (
                "Le scan de dossiers n'est pas configuré par l'administrateur.", [], None, 0)

        if not _racines_dispo:
            pass  # message deja affiche ci-dessus ; pas de doublon
        elif erreur_validation:
            st.error(erreur_validation)
        elif dossier and not fichiers:
            st.info("Aucun fichier compatible n'a été trouvé dans ce dossier.")
        elif dossier and fichiers:
            s1, s2, s3 = st.columns(3)
            with s1: carte("Dossier", libelle_dossier)
            with s2: carte("Fichiers éligibles", len(fichiers))
            with s3: carte("Mode", "Récursif" if recursif else "Dossier seul")
            detail_extensions = "Extensions prises en charge : .exe, .dll, .pdf, .docx."
            if n_sousdossiers_ignores:
                detail_extensions += (" %d sous-dossier(s) ignoré(s) (accès refusé)."
                                      % n_sousdossiers_ignores)
            st.caption(detail_extensions)
            if isoler_scan:
                st.caption("Les fichiers détectés comme malveillants peuvent être déplacés en "
                           "quarantaine par le backend.")

        lancer = st.button("Lancer le scan",
                           disabled=(not dossier or erreur_validation is not None or not fichiers))
        if not dossier:
            st.caption("Aucun scan ne démarre tant qu'aucun dossier n'est indiqué et validé.")
        st.caption("Le scan s'exécute en une seule fois, sans possibilité d'annulation une fois lancé.")

        if lancer and fichiers:
            barre = st.progress(0)
            zone = st.empty()
            resultats = []
            for i, f in enumerate(fichiers, 1):
                nom_sur = os.path.basename(f)
                zone.text("Analyse %d sur %d — %s" % (i, len(fichiers), nom_sur))
                try:
                    # `f` est un chemin local reel et verifie (racine
                    # autorisee) -- une mise en quarantaine deplace bien le
                    # fichier original de l'utilisateur, pas une copie.
                    r = analyser(f, isoler=isoler_scan, source_context=quarantine_manager.SOURCE_FOLDER_SCAN)
                    resultats.append({
                        "fichier": nom_sur, "verdict": r.get("verdict", ""),
                        "etape": r.get("etape", ""), "confiance": r.get("confiance", ""),
                        "action": r.get("action", "aucune"),
                    })
                except Exception:
                    resultats.append({"fichier": nom_sur, "verdict": "erreur",
                                      "etape": "", "confiance": "", "action": "aucune"})
                barre.progress(i / len(fichiers))
            zone.empty()
            st.session_state["scan_resultats"] = resultats
            st.session_state["scan_resultats_dossier"] = dossier
            st.session_state["scan_page"] = 1

        resultats = st.session_state.get("scan_resultats")
        if resultats and st.session_state.get("scan_resultats_dossier") == dossier:
            n_total = len(resultats)
            n_mal = sum(1 for r in resultats if r["verdict"] == "malveillant")
            n_sain = sum(1 for r in resultats if r["verdict"] == "sain")
            n_ind = sum(1 for r in resultats if r["verdict"] == "indetermine")
            n_erreur = sum(1 for r in resultats if r["verdict"] not in VERDICTS)
            n_quar = sum(1 for r in resultats if etat_quarantaine(r["action"]) == "Mis en quarantaine")

            st.write("")
            section_titre("Résumé du scan")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: carte("Fichiers examinés", n_total)
            with m2: carte("Malveillants", n_mal, ROUGE if n_mal else None)
            with m3: carte("Sains", n_sain, VERT if n_sain else None)
            with m4: carte("Indéterminés", n_ind, JAUNE if n_ind else None)
            with m5: carte("Échecs techniques", n_erreur, JAUNE if n_erreur else None)
            if n_quar:
                st.caption("%d fichier(s) mis en quarantaine." % n_quar)

            st.write("")
            TAILLE_PAGE = 20
            nb_pages = max(1, (n_total - 1) // TAILLE_PAGE + 1)
            page_actuelle = min(max(1, st.session_state.get("scan_page", 1)), nb_pages)
            st.session_state["scan_page"] = page_actuelle
            debut_i = (page_actuelle - 1) * TAILLE_PAGE

            for r in resultats[debut_i:debut_i + TAILLE_PAGE]:
                try:
                    info = info_verdict(r["verdict"])
                    source = source_libelle(r["etape"]) if r["etape"] else "Non disponible"
                    st.markdown(
                        '<div class="hist-l"><span class="verdict-badge %s">%s</span>'
                        '<span class="t">%s</span><span class="e">%s</span></div>'
                        % (info["classe"], info["libelle"], r["fichier"], source),
                        unsafe_allow_html=True)
                    with st.expander("Voir le détail — %s" % r["fichier"]):
                        d1, d2 = st.columns(2)
                        with d1: carte("Source de détection", source)
                        with d2:
                            conf = r["confiance"]
                            try:
                                conf_txt = "%.0f %%" % (float(conf) * 100) if conf else "Non disponible"
                            except ValueError:
                                conf_txt = "Non disponible"
                            carte("Confiance", conf_txt)
                        carte("Quarantaine", etat_quarantaine(r["action"]))
                except Exception:
                    st.caption("Un résultat n'a pas pu être affiché correctement.")

            if nb_pages > 1:
                pc1, pc2, pc3 = st.columns([1, 2, 1])
                with pc1:
                    if st.button("← Précédent", disabled=(page_actuelle <= 1), key="scan_prec"):
                        st.session_state["scan_page"] = page_actuelle - 1
                        st.rerun()
                with pc2:
                    st.markdown(
                        '<div style="text-align:center;color:var(--dim);font-size:0.8rem;padding-top:8px">'
                        "Page %d / %d (%d résultat(s))</div>" % (page_actuelle, nb_pages, n_total),
                        unsafe_allow_html=True)
                with pc3:
                    if st.button("Suivant →", disabled=(page_actuelle >= nb_pages), key="scan_suiv"):
                        st.session_state["scan_page"] = page_actuelle + 1
                        st.rerun()


# charger_historique() : extraite vers backend_shared.py (importee
# ci-dessus) pour etre partagee a l'identique avec l'API FastAPI. Note :
# backend_shared.py verifie le verdict contre un ensemble {"malveillant",
# "sain", "indetermine"} equivalent a VERDICTS.keys() ici (memes valeurs,
# sans les metadonnees d'affichage libelle/couleur/classe non pertinentes
# pour le chargement).


if _actif("historique"):
    _statut_hist, hist, _avertissements_hist = charger_historique()

    if _statut_hist == "absent" or (hist is not None and hist.empty):
        st.markdown(
            '<div class="carte" style="text-align:center;padding:40px">'
            '<div class="k">Aucune analyse enregistrée</div>'
            '<div style="font-size:0.8rem;color:var(--dim);margin-top:8px">'
            "Les résultats apparaîtront ici après votre première analyse.</div></div>",
            unsafe_allow_html=True)
    elif _statut_hist == "erreur":
        st.error("L'historique n'a pas pu être chargé pour le moment. Réessayez plus tard.")
    else:
        for _a in _avertissements_hist:
            st.warning(_a)
        st.caption("%d analyse(s) enregistrée(s)." % len(hist))

        # --- Filtres (uniquement sur des colonnes reellement presentes) ---
        verdicts_presents = sorted(hist["verdict"].unique().tolist())
        sources_presentes = sorted(hist["etape"].unique().tolist())
        quarantaine_options = ["Mis en quarantaine", "Échec de la mise en quarantaine", "Aucune"]

        dates_parsees = pd.to_datetime(hist["date"], errors="coerce")
        a_des_dates = dates_parsees.notna().any()
        date_min = dates_parsees.min().date() if a_des_dates else None
        date_max = dates_parsees.max().date() if a_des_dates else None

        f1, f2 = st.columns(2)
        with f1:
            recherche_nom = st.text_input("Rechercher par nom de fichier", key="hist_q_nom")
        with f2:
            recherche_hash = st.text_input("Rechercher par SHA-256", key="hist_q_hash")

        f3, f4 = st.columns(2)
        with f3:
            verdicts_choisis = st.multiselect(
                "Filtrer par verdict", options=verdicts_presents, default=verdicts_presents,
                format_func=lambda v: info_verdict(v)["libelle"], key="hist_verdicts")
        with f4:
            sources_choisies = st.multiselect(
                "Filtrer par source de détection", options=sources_presentes,
                default=sources_presentes, format_func=source_libelle, key="hist_sources")

        quarantaine_choisis = st.multiselect(
            "Filtrer par statut de quarantaine", options=quarantaine_options,
            default=quarantaine_options, key="hist_quarantaine")

        periode = None
        if a_des_dates:
            periode = st.date_input("Période", value=(date_min, date_max),
                                    min_value=date_min, max_value=date_max, key="hist_periode")
        periode_modifiee = (a_des_dates and isinstance(periode, tuple)
                            and len(periode) == 2 and periode != (date_min, date_max))

        filtres_actifs = (bool(recherche_nom) or bool(recherche_hash)
                          or set(verdicts_choisis) != set(verdicts_presents)
                          or set(sources_choisies) != set(sources_presentes)
                          or set(quarantaine_choisis) != set(quarantaine_options)
                          or periode_modifiee)
        if filtres_actifs:
            if st.button("Réinitialiser les filtres"):
                for _cle in ("hist_q_nom", "hist_q_hash", "hist_verdicts", "hist_sources",
                            "hist_quarantaine", "hist_periode"):
                    st.session_state.pop(_cle, None)
                st.session_state["hist_page"] = 1
                st.rerun()

        # --- Application des filtres — ne modifie jamais `hist` lui-meme ---
        masque = pd.Series(True, index=hist.index)
        if recherche_nom:
            masque &= hist["fichier"].str.contains(recherche_nom, case=False, na=False, regex=False)
        if recherche_hash:
            masque &= hist["sha256"].str.contains(recherche_hash, case=False, na=False, regex=False)
        masque &= hist["verdict"].isin(verdicts_choisis)
        masque &= hist["etape"].isin(sources_choisies)
        masque &= hist["action"].apply(etat_quarantaine).isin(quarantaine_choisis)
        if periode_modifiee:
            masque &= dates_parsees.dt.date.between(periode[0], periode[1])
        vue = hist[masque]

        signature_filtres = (recherche_nom, recherche_hash, tuple(sorted(verdicts_choisis)),
                             tuple(sorted(sources_choisies)), tuple(sorted(quarantaine_choisis)),
                             periode if isinstance(periode, tuple) else None)
        if st.session_state.get("hist_sig") != signature_filtres:
            st.session_state["hist_sig"] = signature_filtres
            st.session_state["hist_page"] = 1

        if vue.empty:
            st.markdown('<div class="carte" style="text-align:center;padding:40px">'
                        '<div class="k">Aucun résultat correspondant</div></div>',
                        unsafe_allow_html=True)
        else:
            TAILLE_PAGE = 20
            nb_pages = max(1, (len(vue) - 1) // TAILLE_PAGE + 1)
            page_actuelle = min(max(1, st.session_state.get("hist_page", 1)), nb_pages)
            st.session_state["hist_page"] = page_actuelle

            debut_i = (page_actuelle - 1) * TAILLE_PAGE
            page_vue = vue.iloc[debut_i:debut_i + TAILLE_PAGE]

            for _idx, ligne in page_vue.iterrows():
                try:
                    info = info_verdict(ligne["verdict"])
                    try:
                        date_l = datetime.fromisoformat(ligne["date"]).strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        date_l = ligne["date"] or "Non disponible"
                    nom = ligne["fichier"] or "Non disponible"
                    hash_court = (ligne["sha256"][:12] + "…") if ligne["sha256"] else "Non disponible"

                    st.markdown(
                        '<div class="hist-l"><span class="verdict-badge %s">%s</span>'
                        '<span class="t">%s</span>'
                        '<span class="e">%s · %s · %s</span></div>'
                        % (info["classe"], info["libelle"], nom, date_l,
                           source_libelle(ligne["etape"]), hash_court),
                        unsafe_allow_html=True)

                    with st.expander("Voir le détail — %s" % nom):
                        d1, d2 = st.columns(2)
                        with d1: carte("Verdict", info["libelle"], info["couleur"])
                        with d2: carte("Source de détection", source_libelle(ligne["etape"]))
                        d3, d4 = st.columns(2)
                        with d3:
                            conf = ligne["confiance"]
                            try:
                                conf_txt = "%.0f %%" % (float(conf) * 100) if conf else "Non disponible"
                            except ValueError:
                                conf_txt = "Non disponible"
                            carte("Confiance", conf_txt)
                        with d4: carte("Quarantaine", etat_quarantaine(ligne["action"]))
                        if ligne["detections"]:
                            st.caption("Détections signature : %s" % ligne["detections"])
                        if ligne["sha256"]:
                            st.write("")
                            hash_display("SHA-256", ligne["sha256"])
                except Exception:
                    # Une ligne illisible n'interrompt jamais l'affichage des autres.
                    st.caption("Une entrée de l'historique n'a pas pu être affichée correctement.")

            pc1, pc2, pc3 = st.columns([1, 2, 1])
            with pc1:
                if st.button("← Précédent", disabled=(page_actuelle <= 1), key="hist_prec"):
                    st.session_state["hist_page"] = page_actuelle - 1
                    st.rerun()
            with pc2:
                st.markdown(
                    '<div style="text-align:center;color:var(--dim);font-size:0.8rem;padding-top:8px">'
                    "Page %d / %d (%d résultat(s))</div>" % (page_actuelle, nb_pages, len(vue)),
                    unsafe_allow_html=True)
            with pc3:
                if st.button("Suivant →", disabled=(page_actuelle >= nb_pages), key="hist_suiv"):
                    st.session_state["hist_page"] = page_actuelle + 1
                    st.rerun()

        st.write("")
        # Export : memes garanties de securite que l'affichage — jamais le
        # chemin absolu contenu dans la colonne CSV brute "action".
        export = vue.assign(action=vue["action"].apply(etat_quarantaine))
        st.download_button("Exporter la vue filtrée en CSV", export.to_csv(index=False).encode(),
                           file_name="historique_analyses.csv", mime="text/csv")

_STATUTS_QUARANTAINE = {
    "isole":                  {"libelle": "Isolé",                         "classe": "ok"},
    "incomplet":              {"libelle": "Métadonnées incomplètes",       "classe": "warn"},
    "fichier_introuvable":    {"libelle": "Fichier associé introuvable",   "classe": "warn"},
    "metadonnees_illisibles": {"libelle": "Métadonnées illisibles",        "classe": "warn"},
    "sans_metadonnees":       {"libelle": "Fichier sans métadonnées",     "classe": "warn"},
}

def charger_quarantaine():
    """Chargement defensif du repertoire de quarantaine -- delegue
    entierement a quarantine_manager.list_quarantine_items() (point
    d'entree UNIQUE de la quarantaine, voir validation/QUARANTINE-MVP.md).
    Cette page reste strictement en lecture seule (ne cree jamais le
    repertoire, contrairement a une veritable mise en quarantaine).
    Retour : (statut, enregistrements, avertissements)
      statut in {"absent", "erreur", "ok"}.

    Chaque enregistrement porte desormais, en plus des champs deja
    consommes par le rendu existant (id/statut/nom_affiche/date_isolation/
    detecte_par/details), les nouveaux champs enrichis (sha256, confidence,
    family, virus_total_result, verdict, source_context, original_removed,
    file_size_bytes, format) utilises par le detail "Pourquoi ce fichier
    a-t-il ete bloque ?" ci-dessous -- absents/None pour les anciens
    enregistrements (format legacy), jamais fabriques."""
    return quarantine_manager.list_quarantine_items(str(BASE))


if _actif("quarantaine"):
    st.markdown(
        '<div class="safenote"><span class="dot">&#9679;</span>'
        "La quarantaine est gérée côté serveur. Les fichiers isolés ne sont jamais exécutés "
        "par cette interface ; l'accès y a été retiré par le mécanisme existant. Cette page "
        "ne propose ni restauration ni téléchargement."
        "</div>", unsafe_allow_html=True)

    _statut_q, enregistrements, _avert_q = charger_quarantaine()

    if _statut_q == "absent" or (enregistrements is not None and len(enregistrements) == 0 and _statut_q == "ok"):
        st.markdown(
            '<div class="carte" style="text-align:center;padding:40px">'
            '<div class="k">Aucun fichier en quarantaine</div>'
            '<div style="font-size:0.8rem;color:var(--dim);margin-top:8px">'
            "Les fichiers détectés comme malveillants apparaîtront ici lorsqu'une mise en "
            "quarantaine est effectuée.</div></div>", unsafe_allow_html=True)
    elif _statut_q == "erreur":
        st.error("Le contenu de la quarantaine n'a pas pu être chargé pour le moment. "
                 "Réessayez plus tard.")
    else:
        for _a in _avert_q:
            st.warning(_a)

        n_isoles = sum(1 for e in enregistrements if e["statut"] == "isole")
        n_incoherents = len(enregistrements) - n_isoles
        s1, s2, s3 = st.columns(3)
        with s1: carte("Enregistrements", len(enregistrements))
        with s2: carte("Isolés", n_isoles)
        with s3: carte("Incomplets / incohérents", n_incoherents, JAUNE if n_incoherents else None)
        st.write("")

        # --- Filtres ---
        statuts_presents = sorted({e["statut"] for e in enregistrements})
        sources_presentes = sorted({e["detecte_par"] for e in enregistrements if e["detecte_par"]})

        dates_parsees = pd.to_datetime(
            pd.Series([e["date_isolation"] for e in enregistrements]), errors="coerce")
        a_des_dates = dates_parsees.notna().any()
        date_min = dates_parsees.min().date() if a_des_dates else None
        date_max = dates_parsees.max().date() if a_des_dates else None

        f1, f2 = st.columns(2)
        with f1:
            recherche_nom = st.text_input("Rechercher par nom de fichier", key="quar_q_nom")
        with f2:
            statuts_choisis = st.multiselect(
                "Filtrer par statut de l'enregistrement", options=statuts_presents,
                default=statuts_presents,
                format_func=lambda s: _STATUTS_QUARANTAINE.get(s, {}).get("libelle", s),
                key="quar_statuts")

        source_choisie = ["Toutes"]
        if sources_presentes:
            source_choisie = st.multiselect(
                "Filtrer par étape de détection", options=sources_presentes,
                default=sources_presentes, format_func=source_libelle, key="quar_sources")

        periode = None
        if a_des_dates:
            periode = st.date_input("Période d'isolation", value=(date_min, date_max),
                                    min_value=date_min, max_value=date_max, key="quar_periode")
        periode_modifiee = (a_des_dates and isinstance(periode, tuple)
                            and len(periode) == 2 and periode != (date_min, date_max))

        filtres_actifs = (bool(recherche_nom)
                          or set(statuts_choisis) != set(statuts_presents)
                          or (bool(sources_presentes) and set(source_choisie) != set(sources_presentes))
                          or periode_modifiee)
        if filtres_actifs:
            if st.button("Réinitialiser les filtres"):
                for _cle in ("quar_q_nom", "quar_statuts", "quar_sources", "quar_periode"):
                    st.session_state.pop(_cle, None)
                st.session_state["quar_page"] = 1
                st.rerun()

        vue = []
        for e in enregistrements:
            if recherche_nom and recherche_nom.lower() not in e["nom_affiche"].lower():
                continue
            if e["statut"] not in statuts_choisis:
                continue
            if sources_presentes and e["detecte_par"] not in source_choisie:
                continue
            if periode_modifiee:
                d = pd.to_datetime(e["date_isolation"], errors="coerce")
                if pd.isna(d) or not (periode[0] <= d.date() <= periode[1]):
                    continue
            vue.append(e)

        signature_filtres = (recherche_nom, tuple(sorted(statuts_choisis)),
                             tuple(sorted(source_choisie)),
                             periode if isinstance(periode, tuple) else None)
        if st.session_state.get("quar_sig") != signature_filtres:
            st.session_state["quar_sig"] = signature_filtres
            st.session_state["quar_page"] = 1

        if not vue:
            st.markdown('<div class="carte" style="text-align:center;padding:40px">'
                        '<div class="k">Aucun résultat correspondant</div></div>',
                        unsafe_allow_html=True)
        else:
            TAILLE_PAGE = 20
            nb_pages = max(1, (len(vue) - 1) // TAILLE_PAGE + 1)
            page_actuelle = min(max(1, st.session_state.get("quar_page", 1)), nb_pages)
            st.session_state["quar_page"] = page_actuelle

            debut_i = (page_actuelle - 1) * TAILLE_PAGE
            for e in vue[debut_i:debut_i + TAILLE_PAGE]:
                try:
                    info_statut = _STATUTS_QUARANTAINE.get(e["statut"], {"libelle": "Erreur technique", "classe": "warn"})
                    date_l = e["date_isolation"] or "Non disponible"
                    source_l = source_libelle(e["detecte_par"]) if e["detecte_par"] else "Non disponible"

                    st.markdown(
                        '<div class="hist-l"><span class="q-badge %s">%s</span>'
                        '<span class="t">%s</span>'
                        '<span class="e">%s · %s</span></div>'
                        % (info_statut["classe"], info_statut["libelle"], e["nom_affiche"],
                           date_l, source_l),
                        unsafe_allow_html=True)

                    with st.expander("Voir le détail — %s" % e["nom_affiche"]):
                        d1, d2 = st.columns(2)
                        with d1: carte("Fichier", e["nom_affiche"])
                        with d2: carte("Mis en quarantaine le", e["date_isolation"] or "Non disponible")
                        carte("Détecté par", source_l)
                        carte("État de l'enregistrement", info_statut["libelle"])

                        st.markdown("**Pourquoi ce fichier a-t-il été bloqué ?**")
                        if e["details"]:
                            st.caption(e["details"])
                        else:
                            st.caption("Raison non disponible (enregistrement incomplet).")

                        dd1, dd2 = st.columns(2)
                        with dd1:
                            carte("Confiance du modèle",
                                  ("%.0f %%" % (e["confidence"] * 100))
                                  if isinstance(e.get("confidence"), (int, float)) else "Non disponible")
                        with dd2:
                            carte("SHA-256", (e["sha256"][:16] + "…") if e.get("sha256") else "Non disponible")

                        # Distinction upload vs chemin local reel (BF6) --
                        # ne jamais affirmer qu'un fichier original de
                        # l'utilisateur (Desktop/Téléchargements) a été
                        # supprimé si seule une copie temporaire de
                        # televersement a ete traitee.
                        if e.get("source_context") == "upload":
                            st.caption("Ce fichier provenait d'un téléversement dans le navigateur : "
                                       "la copie d'analyse a été isolée côté serveur. HybridScan ne "
                                       "peut pas et n'a pas supprimé un éventuel fichier original sur "
                                       "l'ordinateur de l'utilisateur.")
                        elif e.get("source_context") in ("folder_scan", "watcher") and e.get("original_removed"):
                            st.caption("Ce fichier a été détecté à un emplacement local réel (scan de "
                                       "dossier ou surveillance en temps réel) : le fichier original a "
                                       "été déplacé en quarantaine à cet emplacement.")

                        st.caption("L'accès au fichier a été retiré par le mécanisme de "
                                   "quarantaine du serveur. Le contenu isolé n'est jamais ouvert, "
                                   "exécuté ni servi par cette interface.")
                except Exception:
                    st.caption("Un enregistrement de quarantaine n'a pas pu être affiché correctement.")

            pc1, pc2, pc3 = st.columns([1, 2, 1])
            with pc1:
                if st.button("← Précédent", disabled=(page_actuelle <= 1), key="quar_prec"):
                    st.session_state["quar_page"] = page_actuelle - 1
                    st.rerun()
            with pc2:
                st.markdown(
                    '<div style="text-align:center;color:var(--dim);font-size:0.8rem;padding-top:8px">'
                    "Page %d / %d (%d résultat(s))</div>" % (page_actuelle, nb_pages, len(vue)),
                    unsafe_allow_html=True)
            with pc3:
                if st.button("Suivant →", disabled=(page_actuelle >= nb_pages), key="quar_suiv"):
                    st.session_state["quar_page"] = page_actuelle + 1
                    st.rerun()


if _actif("protection"):
    st.markdown(
        '<div class="analyse-alerte">'
        "Fonctionnalité optionnelle et locale à cette session : lorsqu'activée, un nouveau "
        "fichier .exe ou .dll déposé directement dans l'un des dossiers listés ci-dessous est "
        "analysé automatiquement selon le même pipeline que la page Analyse. Elle s'arrête si "
        "l'application est fermée ou redémarrée et ne surveille pas les sous-dossiers."
        '</div>', unsafe_allow_html=True)

    from watcher import Protection, journal, DOSSIERS

    if "protection" not in st.session_state:
        st.session_state.protection = Protection()
    prot = st.session_state.protection

    # --- Carte d'etat proeminente : badge colore + bouton Activer/Desactiver,
    # puis l'option de quarantaine automatique juste en dessous.
    with st.container(key="surveillance_etat"):
        c_badge, c_bouton = st.columns([3, 1], vertical_alignment="center")
        with c_badge:
            if prot.active:
                st.markdown(
                    '<div class="surveillance-badge ok"><span class="point"></span>'
                    'Surveillance active</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="surveillance-badge warn"><span class="point"></span>'
                    'Surveillance inactive</div>', unsafe_allow_html=True)
        with c_bouton:
            if prot.active:
                if st.button("Désactiver", key="prot_toggle", use_container_width=True):
                    prot.arreter()
                    st.rerun()
            else:
                if st.button("Activer", key="prot_toggle", use_container_width=True):
                    surveilles = prot.demarrer(isoler=st.session_state.get("quar_rt", True))
                    st.success("%d dossier(s) surveillé(s)." % len(surveilles))
                    st.rerun()
        st.checkbox("Quarantaine automatique", value=True, key="quar_rt")

    st.write("")
    section_titre("Dossiers surveillés")
    _n_col = 4
    for _i in range(0, len(DOSSIERS), _n_col):
        _rangee = st.columns(_n_col)
        for _col, d in zip(_rangee, DOSSIERS[_i:_i + _n_col]):
            with _col:
                # Libelle seul : jamais le chemin absolu (peut contenir le
                # nom d'utilisateur du systeme).
                libelle = os.path.basename(d.rstrip("/\\")) or d
                carte_dossier(libelle, os.path.isdir(d))

    st.write("")
    section_titre("Détections récentes")
    if st.button("Rafraîchir"):
        st.rerun()

    entrees = journal()
    if not entrees:
        st.info("Aucune détection pour l'instant.")
    else:
        nb_mal = sum(1 for e in entrees
                     if str(e.get("verdict", "")).lower().startswith("malv"))
        m1, m2 = st.columns(2)
        with m1: carte("Fichiers détectés", len(entrees))
        with m2: carte("Malveillants", nb_mal, ROUGE if nb_mal else None)
        st.write("")
        for e in entrees[:8]:
            try:
                info = info_verdict(e.get("verdict", ""))
                nom = e.get("fichier") or "Non disponible"
                heure = e.get("heure") or "Non disponible"
                source = source_libelle(e.get("etape", "")) if e.get("etape") else "Non disponible"
                st.markdown(
                    '<div class="hist-l"><span class="verdict-badge %s">%s</span>'
                    '<span class="t">%s</span><span class="e">%s · %s</span></div>'
                    % (info["classe"], info["libelle"], nom, heure, source),
                    unsafe_allow_html=True)
            except Exception:
                st.caption("Une détection n'a pas pu être affichée correctement.")
        if len(entrees) > 8:
            st.caption("%d détection(s) au total (journal limité aux 100 plus récentes)."
                       % len(entrees))


def barres_repartition(paires):
    """Barres horizontales sobres avec valeur textuelle (compte + proportion)
    a cote de chaque barre — aucune dependance de graphique ajoutee."""
    total = sum(v for _, v in paires) or 1
    vmax = max((v for _, v in paires), default=1) or 1
    html = ['<div class="repart">']
    for libelle, effectif in paires:
        largeur = (effectif / vmax) * 100
        html.append(
            '<div class="repart-l"><span class="lbl">%s</span>'
            '<span class="barre"><div style="width:%.0f%%"></div></span>'
            '<span class="val">%d (%.0f %%)</span></div>'
            % (libelle, largeur, effectif, effectif / total * 100))
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def page_dashboard():
    with _col_entete_action:
        with st.container(key="entete_action_dashboard"):
            if st.button("Analyser un fichier", key="dash_vers_analyse"):
                st.session_state.pg = "analyse"
                st.rerun()

    with st.spinner("Chargement de l'historique..."):
        statut, df, avertissements = charger_historique()

    if statut == "absent" or (df is not None and df.empty):
        st.markdown(
            '<div class="carte" style="text-align:center;padding:40px">'
            '<div class="k">Aucune analyse enregistrée</div>'
            '<div style="font-size:0.8rem;color:var(--dim);margin-top:8px">'
            "Lancez une première analyse pour alimenter le tableau de bord.</div></div>",
            unsafe_allow_html=True)
        return

    if statut == "erreur":
        st.error("Le tableau de bord n'a pas pu être chargé pour le moment. Réessayez plus tard.")
        return

    for _a in avertissements:
        st.warning(_a)

    # --- Limites et origine des donnees (compact, secondaire) ---
    st.markdown(
        '<div class="safenote"><span class="dot">&#9679;</span>'
        "Ces valeurs proviennent de l'historique local des analyses : ce sont des enregistrements "
        "historiques, pas des indicateurs de protection en temps réel. Les métriques de validation "
        "expérimentales du modèle ne sont volontairement pas affichées tant que l'artefact déployé "
        "n'a pas été réconcilié avec le modèle final décrit dans le rapport de projet."
        "</div>", unsafe_allow_html=True)
    st.write("")

    # --- Metriques (valeurs reelles uniquement, mapping centralise) ---
    total = len(df)
    n_mal = int((df["verdict"] == "malveillant").sum())
    n_sain = int((df["verdict"] == "sain").sum())
    n_ind = int((df["verdict"] == "indetermine").sum())
    n_quar = int(df["action"].apply(etat_quarantaine).eq("Mis en quarantaine").sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: carte("Analyses enregistrées", total, icone="📁")
    with c2: carte("Malveillants", n_mal, ROUGE if n_mal else None, icone="🛑")
    with c3: carte("Sains", n_sain, VERT if n_sain else None, icone="✅")
    with c4: carte("Indéterminés", n_ind, JAUNE if n_ind else None, icone="❓")
    with c5: carte("Mises en quarantaine", n_quar, JAUNE if n_quar else None, icone="🔒")

    st.write("")
    col_a, col_b = st.columns(2)

    with col_a:
        section_titre("Source de détection")
        compteurs_source = df["etape"].value_counts()
        paires_source = [(source_libelle(k), int(v)) for k, v in compteurs_source.items() if k]
        if paires_source:
            barres_repartition(paires_source)
        else:
            st.caption("Aucune donnée de source de détection disponible.")

    with col_b:
        section_titre("Analyses récentes")
        for _, ligne in df.head(6).iterrows():
            try:
                info = info_verdict(ligne["verdict"])
                try:
                    date_l = datetime.fromisoformat(ligne["date"]).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_l = ligne["date"] or "Non disponible"
                nom = ligne["fichier"] or "Non disponible"
                st.markdown(
                    '<div class="hist-l"><span class="verdict-badge %s">%s</span>'
                    '<span class="t">%s</span>'
                    '<span class="e">%s · %s · %s</span></div>'
                    % (info["classe"], info["libelle"], nom, date_l,
                       source_libelle(ligne["etape"]), etat_quarantaine(ligne["action"])),
                    unsafe_allow_html=True)
            except Exception:
                st.caption("Une entrée récente n'a pas pu être affichée correctement.")
        if st.button("Voir l'historique complet", key="dash_vers_historique"):
            st.session_state.pg = "historique"
            st.rerun()

    # --- Activite dans le temps (uniquement si des dates fiables existent) ---
    dates = pd.to_datetime(df["date"], errors="coerce")
    dates_valides = dates.dropna()
    n_dates_invalides = int(dates.isna().sum())
    jours_distincts = dates_valides.dt.date.nunique() if not dates_valides.empty else 0

    st.write("")
    if jours_distincts >= 2:
        section_titre("Analyses par jour — 14 derniers jours enregistrés")
        if n_dates_invalides:
            st.caption("%d date(s) illisible(s) exclue(s) de ce graphique." % n_dates_invalides)
        dernier_jour = dates_valides.max().date()
        premier_jour = dernier_jour - pd.Timedelta(days=13)
        index_complet = pd.date_range(premier_jour, dernier_jour, freq="D").date
        comptage = dates_valides.dt.date.value_counts()
        serie = pd.Series([int(comptage.get(j, 0)) for j in index_complet], index=index_complet)
        st.bar_chart(serie)
        st.caption("%d analyse(s) enregistrée(s) entre le %s et le %s."
                   % (int(serie.sum()), premier_jour.strftime("%d/%m/%Y"),
                      dernier_jour.strftime("%d/%m/%Y")))
    elif n_dates_invalides:
        st.caption("Données temporelles insuffisantes ou illisibles pour un graphique d'activité.")


if _actif("dashboard"):
    page_dashboard()

if _actif("parametres"):
    # Page volontairement minimale (reorganisation de navigation
    # uniquement) : informations en lecture seule, aucun formulaire, aucun
    # parametre modifiable depuis l'interface a ce stade. Les seuils de
    # detection, la politique de quarantaine et la cle VirusTotal restent
    # configures cote serveur (.streamlit/secrets.toml / variables
    # d'environnement), jamais via cette page.
    carte("Compte connecté", st.session_state.get("utilisateur") or "Session")
    st.write("")
    st.caption("Les seuils de détection, la politique de quarantaine automatique et la clé "
               "VirusTotal sont configurés côté serveur et ne sont pas modifiables depuis cette "
               "interface pour le moment.")
