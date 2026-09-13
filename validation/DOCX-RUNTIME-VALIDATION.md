# DOCX-RUNTIME-VALIDATION.md — Validation runtime du prototype IA_DOCX

## DOCX MODEL STATUS : RESEARCH / PFA PROTOTYPE — NOT PRODUCTION READY

Ce document rapporte les tests de fidélité runtime effectués sur
`model_docx_candidate.pkl` **avant sa promotion** en `model_docx.pkl`, à
travers le pipeline réel (`document_ml/docx/validate.py`,
`features.py`, `predict.py`) — jamais un test d'inférence isolé sur des
vecteurs synthétiques. Aucun document Word/LibreOffice n'a été ouvert,
aucune macro exécutée, aucun processus externe lancé, aucune relation
externe suivie. Toutes les fixtures sont construites localement avec
`zipfile` ; les fichiers "à contenu haute entropie" utilisent
`os.urandom()` en guise de données d'image compressée réaliste — jamais un
téléchargement.

## 1. Vérification du contrat de schéma

`document_ml.docx.predict._verifier_contrat_schema(bundle)` exécuté
directement sur le bundle réel : **OK** — version de schéma (2), famille
de modèle (`RandomForestClassifier`), format supporté (`docx`), ordre des
caractéristiques, tous conformes.

## 2. Fixtures bénignes réalistes — pipeline complet (`predict.predire()`)

| Fixture | Taille (octets) | `has_vba_macros` | Probabilité | Seuil | Verdict |
|---|---|---|---|---|---|
| DOCX minimal | 1 444 | 0 | 0.0000 | 0.5 | sain |
| Document texte ordinaire | 1 484 | 0 | 0.0000 | 0.5 | sain |
| Paragraphes multiples (50) | 1 634 | 0 | 0.0000 | 0.5 | sain |
| Document avec tableau (20 lignes) | 1 540 | 0 | 0.0000 | 0.5 | sain |
| Document avec hyperlien + relation interne | 1 517 | 0 | 0.0000 | 0.5 | sain |
| Document avec relation externe (métadonnée, jamais résolue) | 1 505 | 0 | 0.0000 | 0.5 | sain |
| Image intégrée (~80 Ko, octets aléatoires simulant une image compressée) | 83 549 | 0 | 0.0000 | 0.5 | sain |
| Image intégrée (~500 Ko) | 513 762 | 0 | 0.0000 | 0.5 | sain |
| Petit document bénin | 1 484 | 0 | 0.0000 | 0.5 | sain |
| Grand document bénin (~2000 paragraphes) | 7 559 | 0 | 0.0000 | 0.5 | sain |
| Contenu haute entropie bénin (média aléatoire, ~1 Mo) | 1 050 503 | 0 | 0.0000 | 0.5 | sain |

**11/11 fixtures bénignes classées correctement, sur une plage de taille
allant de 1,4 Ko à plus de 1 Mo, sans aucun faux positif.** Toutes ces
fixtures ont `has_vba_macros=0`, dominant massivement la décision du
modèle (voir `DOCX-RESEARCH-MODEL-TRAINING.md` §10) — la probabilité
reste à 0.0000 même pour la fixture de 1 Mo, confirmant que
`file_size_bytes` seul ne déclenche pas de faux positif dans la plage
testée en l'absence de macro détectée.

**Non testé (limite explicite)** : un document macro-activé réellement
*bénin* (ex. modèle de facture professionnel légitime). Fabriquer un flux
`vbaProject.bin` réellement décompilable par `oletools` nécessiterait de
reproduire le format binaire MS-OVBA d'Office (même limite déjà documentée
dans `validation/DOCX-FEATURES.md` §6 pour la phase de fondation). Sur la
base de la composition du corpus d'entraînement (§10 de
`DOCX-RESEARCH-MODEL-TRAINING.md`), il faut **s'attendre** à ce qu'un tel
document soit classé malveillant par ce prototype — limitation documentée,
pas testée empiriquement ici.

## 3. Fixtures invalides / usurpées — doivent être rejetées AVANT le modèle

| Fixture | Statut retourné | Résultat |
|---|---|---|
| Texte brut renommé `.docx` | `erreur_extraction` | OK — rejeté avant ML |
| Archive ZIP quelconque renommée `.docx` | `erreur_extraction` | OK — rejeté avant ML |
| ZIP corrompu/tronqué | `erreur_extraction` | OK — rejeté avant ML |
| PE (type notepad) renommé `.docx` | `erreur_extraction` | OK — rejeté avant ML |

**4/4 fixtures invalides rejetées avant tout appel au modèle** — confirmé
par assertion dans le script de validation (pas seulement observé).

## 4. Décision de la porte d'intégration (cahier des charges §12)

**PASS.** Aucun comportement catastrophique observé (aucune fixture
bénigne ordinaire, y compris de grande taille ou à haute entropie, n'a été
classée malveillante). `model_docx_candidate.pkl` promu en
`model_docx.pkl` (copie directe, SHA-256 identique :
`7ef9f2702af4e7fa28bbf61eb9a88cb08f698ab3e64d7bb6e95c6a3a50f9dde9`).

**Ce test ne prouve PAS la généralisation à des DOCX réels arbitraires**
(rappel explicite, cahier des charges) — il prouve seulement l'absence de
faux positif catastrophique sur les familles de fixtures synthétiques
bénignes testées. Aucune affirmation de performance en conditions réelles
n'est faite.

## 5. Intégration production (cahier des charges §13)

Routage minimal ajouté à `analyze.py` :

```
DOCX (upload) -> SHA-256 -> VirusTotal
  -> si VirusTotal concluant : verdict signature existant (inchangé)
  -> si VirusTotal non concluant :
       identifier_fichier() valide reellement la structure DOCX
         -> si invalide : indetermine (jamais transmis au modele)
         -> si valide : document_ml.docx.predict -> IA_DOCX -> SAIN|MALVEILLANT + confiance
```

- **DOC legacy** : comportement inchangé (`VirusTotal -> si inconclusif ->
  indetermine`), aucune validation structurelle, aucun modèle.
- **PE renommé `.docx`** : continue de router comme PE (garde anti-spoof
  déjà existante, prioritaire sur l'extension déclarée — vérifié par test).
- **PDF** : comportement entièrement inchangé (code non touché).

## 6. Sécurité de la quarantaine (cahier des charges §14)

**La quarantaine automatique N'EST PAS déclenchée par un verdict
"malveillant" émis SEULEMENT par IA_DOCX** — nouvelle garde
`permettre_quarantaine_auto` dans `analyser()`, désactivée uniquement pour
ce cas précis. Un verdict "malveillant" par signature VirusTotal continue
de déclencher la quarantaine normalement (non-régression vérifiée par
test, voir `tests/test_docx_model_integration.py::test_vt_conclusive_malveillant_docx_still_quarantined_normally`).
Testé (monkeypatch, pas une prétention de détection réelle) : un verdict
IA_DOCX malveillant force `action = "aucune (quarantaine automatique
desactivee pour IA_DOCX — prototype de recherche)"`.

## 7. Interface utilisateur (cahier des charges §15)

Libellé ajouté : **"IA_DOCX — prototype de recherche (non certifié)"**.
Un avertissement persistant (`st.caption`) s'affiche pour tout résultat
IA_DOCX, quel que soit le verdict : *"IA_DOCX est un prototype de
recherche académique, entraîné sur un corpus externe aux limites
documentées. Résultat expérimental, non certifié — ne pas considérer comme
une détection fiable en production."* Aucune mention de "production-ready"/
"certifié"/"99% fiable"/"détection garantie" nulle part.

## 8. Explicabilité (cahier des charges §16)

`document_ml/docx/explain.py` créé (SHAP `TreeExplainer`, même schéma que
PE/PDF — coût d'implémentation minimal, 2 caractéristiques). Testé et
fonctionnel (voir exemple ci-dessous). **Non câblé dans le flux Streamlit
de calcul SHAP** — ce flux est aujourd'hui strictement gated sur
`"etape2" in res` (une clé spécifique au chemin PE) ; PDF lui-même n'y est
pas câblé (le module `document_ml/pdf/explain.py` existe mais l'UI affiche
un message statique "non disponible pour le moment"). Étendre ce
gating aurait nécessité de toucher une logique partagée PE/PDF/DOCX, ce
qui est explicitement hors périmètre ("Do NOT modify PE/PDF explainability
behavior"). Le message d'interface pour IA_DOCX a été rendu honnête
(même formulation que PDF) plutôt que de forcer un branchement plus large.

Exemple de sortie (fixture bénigne minimale) :
```
{'proba': 0.0, 'contribs': [
    ('has_vba_macros', -0.377, 0),
    ('file_size_bytes', -0.123, 492)
]}
```

## 9. Tests et non-régression (cahier des charges §17)

Nouveau fichier `tests/test_docx_model_integration.py` (11/11 tests) :
chargement du modèle, contrat de schéma, prédiction DOCX valide, rejet
DOCX invalide/usurpé, DOC legacy jamais transmis au modèle, PE renommé
`.docx` toujours routé PE, VirusTotal concluant n'invoque jamais le
modèle, VirusTotal non concluant invoque le modèle, sécurité de la
quarantaine (les deux sens : IA_DOCX ne quarantaine pas, signature
continue de quarantiner), non-régression PDF, non-régression PE.

`tests/test_docx_regression.py` mis à jour (4/4 tests) : le contrat a
changé (intégration désormais autorisée) — les anciennes assertions
"document_ml.docx jamais importé"/"identifier_fichier toujours
valide=True" sont remplacées par des assertions vérifiant le NOUVEAU
contrat (import restreint à `.predict`/`.validate`, validation
structurelle réelle). Historique conservé en commentaire, pas dans le
code. Artefacts modèle PE/PDF (`model.pkl`, `model_pdf.pkl`,
`document_ml/pdf/*`, `extract_features.py`, `train_model.py`) confirmés
strictement inchangés (`analyze.py`/`app.py` explicitement exclus de ce
contrôle car modifiés par conception cette phase).

Suite complète DOCX (5 fichiers, 40 tests) : **40/40 passent.**

## 10. Ré-vérification d'intégrité finale

| Fichier | SHA-256 |
|---|---|
| `model.pkl` | `4c0f8b73382febd1ef17deb3d81e3c8fda48a36fd1e6f561080b8619fb30622f` (inchangé) |
| `model_pdf.pkl` | `be1ade69e5acdc130478dac6dbe904fa557eb53a93bdfa9140fc9097a9b3a8bc` (inchangé) |
| `document_ml/pdf/predict.py` | `2cc5f401a945a2280eb08987d99612330826cba0448ba90f77e8fc62dd96e6c0` (inchangé) |
| `extract_features.py` | `63fb50df4f96480f918fa95ac3e7039689306239c391f5021b0a06d339c6cc65` (inchangé) |
| `train_model.py` | `bfe207668c4297e6b7f28afbc177d992b7f79adde87f88c061de12d9a5dd0654` (inchangé) |
| `analyze.py` | `61192affce3cbb55a404a16c71338031b31b224981c35a48552beea671484ab0` (modifié par conception — intégration DOCX) |
| `app.py` | `ab4bcfea98f7eb52809b2c0fe41e8fe30c2e9bc5110abd9eacc9eb52744d5035` (modifié par conception — libellés UI) |
| `model_docx.pkl` | `7ef9f2702af4e7fa28bbf61eb9a88cb08f698ab3e64d7bb6e95c6a3a50f9dde9` (nouveau) |
