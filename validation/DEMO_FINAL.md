# HybridScan — Guide de démonstration finale

Séquence courte et fiable pour une démonstration de 5 à 10 minutes (PFA /
soutenance). Ne dépend pas d'Internet pour l'essentiel du parcours — voir
la note VirusTotal en bas de page.

## Avant la démonstration

1. Démarrer l'API et le frontend :
   ```
   .\scripts\start_hybridscan.ps1
   ```
   (ou séparément : `.\scripts\start_backend.ps1` puis `.\scripts\start_frontend.ps1`)
2. Vérifier que l'API répond : http://127.0.0.1:8000/api/v1/health
   → `{"status":"ok", "models": {"pe": true, "pdf": true, "docx": true}}`
3. Ouvrir http://localhost:3000 dans un navigateur.
4. Avoir sous la main :
   - un compte de connexion valide (compte administrateur configuré via
     `.streamlit/secrets.toml [auth]`, ou un compte enregistré via
     `POST /api/v1/auth/register` — voir `validation/HYBRIDSCAN-FINALISATION.md`
     §"Préparation du compte de démonstration")
   - un ou deux fichiers inoffensifs à téléverser (ex. un PDF ou DOCX de
     test quelconque)

## Séquence de démonstration

1. **Connexion** — montrer l'écran de connexion, se connecter avec le
   compte de démonstration.
2. **Tableau de bord** — montrer les indicateurs réels (analyses du jour,
   menaces détectées, fichiers en quarantaine, état de la protection),
   la répartition des verdicts, la répartition par type de fichier,
   l'activité récente.
3. **Analyser un fichier** — sur la page Analyse, téléverser un fichier
   inoffensif (PE, PDF ou DOCX).
4. **Expliquer le flux VirusTotal → IA** — signature d'abord, analyse
   statique par IA seulement si la signature ne conclut pas (voir le
   panneau "À propos de l'analyse" sur la même page).
5. **Montrer le résultat** — verdict, source de détection, confiance,
   SHA-256, action de quarantaine (le cas échéant).
6. **Historique** — ouvrir `/historique`, montrer que l'analyse vient
   d'apparaître ; démontrer la recherche (soit directement dans
   Historique, soit depuis la barre de recherche du haut, qui redirige
   vers Historique avec le filtre déjà appliqué).
7. **Scan de dossier** — sur la même page Analyse, lancer un scan sur le
   dossier autorisé configuré (`Racine(s) autorisée(s)` pré-rempli dans
   le champ) ; le dossier de démonstration contient des fichiers EXE,
   DLL, PDF et DOCX — montrer que chacun est routé vers le bon pipeline
   d'analyse (colonnes Type/Source du tableau de résultats), et rappeler
   que PDF et DOCX y restent des prototypes de recherche au même titre
   qu'en analyse de fichier unique. *(Mis à jour le 2026-08-19 : le scan
   de dossier couvrait auparavant EXE/DLL uniquement.)*
8. **Quarantaine** — ouvrir `/quarantaine`, montrer un enregistrement
   existant, ouvrir son détail ("Pourquoi ce fichier a-t-il été
   bloqué ?"), rappeler qu'il s'agit de métadonnées uniquement (jamais
   le contenu isolé).
9. **Protection** — ouvrir `/protection`, montrer l'état réel (actif/
   inactif), activer la protection en direct si le temps le permet,
   montrer que le statut se met à jour, puis la désactiver.
10. **Paramètres** — ouvrir `/parametres`, montrer les informations
    en lecture seule : formats pris en charge, racine de scan autorisée,
    état du service API, et la mention explicite des modèles PDF/DOCX
    comme prototypes de recherche.
11. **Limitations de recherche** — conclure en rappelant que PDF et DOCX
    restent des prototypes de recherche (un faux positif a été observé
    sur un PDF de test lors des essais réels), jamais présentés comme
    des moteurs de production certifiés.

## Repli hors ligne (sans VirusTotal)

Si `VT_API_KEY` n'est pas configurée (ou si la démonstration se déroule
sans connexion Internet fiable), `analyze.py::etape1_virustotal` bascule
automatiquement et silencieusement vers l'étape 2 (modèle IA) pour
chaque fichier — le parcours de démonstration reste identique, seule la
source de détection affichée change ("IA PE"/"IA PDF"/"IA DOCX" au lieu
de "VirusTotal"). Aucune étape de la séquence ci-dessus ne nécessite
Internet pour fonctionner.

## Repli Streamlit

Si le frontend Next.js ou l'API FastAPI rencontrent un problème
imprévu juste avant la démonstration, l'application Streamlit reste
disponible en repli :
```
streamlit run app.py
```
Elle couvre les mêmes fonctionnalités (Tableau de bord, Analyse,
Historique, Quarantaine, Protection, Paramètres) avec la même logique
métier — voir `validation/HYBRIDSCAN-FINALISATION.md` pour la
confirmation de son bon fonctionnement après cette phase.
