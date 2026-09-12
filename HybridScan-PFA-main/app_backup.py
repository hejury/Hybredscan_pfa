#!/usr/bin/env python3
"""app.py — Interface du systeme hybride de detection de malwares."""
import os, sys, json, tempfile
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.expanduser("~/pfe"))
from analyze import analyser, HISTORY, QUARANTINE
from style import CSS

st.set_page_config(page_title="Detection de malwares", page_icon="🛡",
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)

VERT, ROUGE, JAUNE = "#00E676", "#FF3D3D", "#FFC400"

def couleur(verdict):
    return {"malveillant": ROUGE, "sain": VERT}.get(verdict, JAUNE)

def classe(verdict):
    return {"malveillant": "v-mal", "sain": "v-sain"}.get(verdict, "v-ind")

def bandeau(res):
    """Signature de l'interface : le verdict occupe la page."""
    st.markdown(
        '<div class="verdict %s">'
        '<div class="via">Conclu par : etape %s</div>'
        '<div class="etat">%s</div>'
        '<div class="msg">%s</div>'
        '</div>' % (classe(res["verdict"]), res["etape"],
                    res["verdict"].upper(), res["message"]),
        unsafe_allow_html=True)

def jauge(proba):
    """Barre de confiance graduee : vert -> jaune -> rouge."""
    pct = proba * 100
    c = ROUGE if proba >= 0.5 else (JAUNE if proba >= 0.3 else VERT)
    st.markdown(
        '<div class="jauge-lbl"><span>Probabilite malveillant</span>'
        '<span style="color:%s">%.1f %%</span></div>'
        '<div class="jauge"><div style="width:%.1f%%;background:%s"></div></div>'
        % (c, pct, pct, c), unsafe_allow_html=True)

def carte(k, v, c=None):
    st.markdown('<div class="carte"><div class="k">%s</div>'
                '<div class="v" style="color:%s">%s</div></div>'
                % (k, c or "#E4E9EF", v), unsafe_allow_html=True)

def barres_shap(contribs):
    """Barres divergentes : vert a gauche (sain), rouge a droite (malveillant)."""
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

st.markdown('<div class="hdr"><h1>Detection hybride de malwares</h1>'
            '<div class="sub">Signature VirusTotal &middot; Classification par '
            'apprentissage automatique &middot; Analyse statique</div></div>',
            unsafe_allow_html=True)

onglet1, onglet2, onglet3 = st.tabs(["Analyse", "Historique", "Quarantaine"])

with onglet1:
    c1, c2 = st.columns([3, 1])
    with c1:
        fichier = st.file_uploader("Deposer un executable PE", type=None,
                                   label_visibility="collapsed")
        st.caption("Le fichier n'est jamais execute. Seules ses "
                   "caracteristiques structurelles sont lues.")
    with c2:
        isoler = st.checkbox("Quarantaine automatique", value=True)
        shap_on = st.checkbox("Explication SHAP", value=True)

    if fichier is not None:
        suffixe = os.path.splitext(fichier.name)[1] or ".bin"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffixe)
        tmp.write(fichier.getbuffer()); tmp.close()
        chemin = tmp.name

        if st.button("Analyser"):
            with st.spinner("Etape 1 — interrogation de VirusTotal..."):
                res = analyser(chemin, isoler=isoler)

            bandeau(res)

            a, b, c = st.columns(3)
            with a: carte("Fichier", res["fichier"][:22])
            with b: carte("Etape", res["etape"])
            with c: carte("Verdict", res["verdict"].upper(), couleur(res["verdict"]))

            st.markdown('<div class="hash"><b>SHA-256</b> &nbsp; %s</div>'
                        % res["sha256"], unsafe_allow_html=True)

            if res["action"] != "aucune":
                st.markdown('<div style="margin-top:14px;font-size:0.75rem;'
                            'color:%s">&#9679; %s</div>' % (JAUNE, res["action"]),
                            unsafe_allow_html=True)

            st.write("")
            with st.expander("Etape 1 — reponse VirusTotal"):
                st.json(res["etape1"])

            if "etape2" in res:
                ia = res["etape2"]
                st.markdown("---")
                st.markdown('<div class="verdict" style="border-color:%s;'
                            'background:transparent;padding:0 0 0 14px;margin:6px 0 18px 0">'
                            '<div class="via">Etape 2 &mdash; classification par IA</div>'
                            '</div>' % couleur(res["verdict"]), unsafe_allow_html=True)

                if ia["statut"].startswith("erreur"):
                    st.warning(ia.get("detail", ia["statut"]))
                else:
                    jauge(ia["confiance"])
                    st.write("")
                    if shap_on and os.path.exists(chemin):
                        with st.spinner("Calcul des valeurs de Shapley..."):
                            try:
                                from explain import expliquer
                                exp = expliquer(chemin, top=10)
                                if "erreur" in exp:
                                    st.warning(exp["erreur"])
                                else:
                                    st.markdown('<div style="font-size:0.7rem;'
                                                'letter-spacing:1.5px;text-transform:uppercase;'
                                                'color:#7A8899;margin:18px 0 12px 0">'
                                                'Contribution de chaque caracteristique'
                                                '</div>', unsafe_allow_html=True)
                                    barres_shap(exp["contribs"])
                            except Exception as e:
                                st.warning("SHAP indisponible : %s" % e)

            if os.path.exists(chemin):
                try: os.unlink(chemin)
                except Exception: pass

with onglet2:
    if os.path.exists(HISTORY):
        hist = pd.read_csv(HISTORY).iloc[::-1]
        nb_mal = int((hist["verdict"] == "malveillant").sum())
        nb_sain = int((hist["verdict"] == "sain").sum())
        nb_sig = int(hist["etape"].astype(str).str.startswith("1").sum())
        a, b, c, d = st.columns(4)
        with a: carte("Analyses", len(hist))
        with b: carte("Malveillants", nb_mal, ROUGE)
        with c: carte("Sains", nb_sain, VERT)
        with d: carte("Via signature", nb_sig, JAUNE)
        st.write("")
        filtre = st.multiselect("Filtrer", options=sorted(hist["verdict"].unique()),
                                default=sorted(hist["verdict"].unique()),
                                label_visibility="collapsed")
        st.dataframe(hist[hist["verdict"].isin(filtre)],
                     use_container_width=True, hide_index=True)
        st.download_button("Exporter en CSV", hist.to_csv(index=False).encode(),
                           file_name="historique_analyses.csv", mime="text/csv")
    else:
        st.markdown('<div class="carte" style="text-align:center;padding:40px">'
                    '<div class="k">Aucune analyse enregistree</div>'
                    '<div style="font-size:0.75rem;color:#7A8899;margin-top:8px">'
                    'Deposez un fichier dans l\'onglet Analyse.</div></div>',
                    unsafe_allow_html=True)

with onglet3:
    if os.path.isdir(QUARANTINE):
        elems = [f for f in sorted(os.listdir(QUARANTINE)) if not f.endswith(".json")]
        if elems:
            a, b = st.columns([1, 3])
            with a: carte("Fichiers isoles", len(elems), ROUGE)
            with b: carte("Emplacement", QUARANTINE)
            st.caption("Chaque fichier est deplace hors de son emplacement "
                       "d'origine et prive de tout droit (chmod 000).")
            st.write("")
            for e in elems:
                with st.expander(e):
                    meta = os.path.join(QUARANTINE, e + ".json")
                    if os.path.exists(meta):
                        with open(meta) as fh:
                            st.json(json.load(fh))
                    else:
                        st.caption("Metadonnees absentes.")
        else:
            st.markdown('<div class="carte" style="text-align:center;padding:40px">'
                        '<div style="color:%s;font-size:1.1rem">Aucun fichier en quarantaine</div>'
                        '</div>' % VERT, unsafe_allow_html=True)
    else:
        st.markdown('<div class="carte" style="text-align:center;padding:40px">'
                    '<div class="k">Repertoire de quarantaine non cree</div></div>',
                    unsafe_allow_html=True)

st.markdown('<div class="note">Projet de fin d\'annee &middot; Detection hybride '
            'de malwares &middot; Analyse statique uniquement : aucun fichier '
            'n\'est execute.</div>', unsafe_allow_html=True)
