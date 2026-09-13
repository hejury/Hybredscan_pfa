# QUARANTINE-MVP.md — Centralisation de la quarantaine (MVP)

**Statut : MVP terminé.** DETECT → ISOLATE → STORE METADATA → LIST → SELECT
→ SHOW REASON. Pas de Restore, pas de suppression permanente (reporté).
Aucun modèle (`model.pkl`/`model_pdf.pkl`/`model_docx.pkl`) modifié.

## 1. Note d'implémentation — état existant avant changement

### 1.1 Où le verdict malveillant déclenche la quarantaine aujourd'hui

`analyze.py::analyser()` (fin de fonction) :

```python
if r["verdict"] == "malveillant" and isoler and permettre_quarantaine_auto:
    r["action"] = "quarantaine : " + quarantaine(path, r["etape"], r["message"])
elif r["verdict"] == "malveillant" and not permettre_quarantaine_auto:
    r["action"] = "aucune (quarantaine automatique desactivee pour IA_DOCX — prototype de recherche)"
else:
    r["action"] = "aucune"
```

`permettre_quarantaine_auto` est déjà mis à `False` spécifiquement pour un
verdict malveillant émis **seulement** par le prototype IA_DOCX (garde de
sécurité ajoutée lors de l'intégration DOCX — voir
`validation/DOCX-RUNTIME-VALIDATION.md` §6). C'est la politique
actuellement en vigueur, **préservée telle quelle** par cette phase.

### 1.2 Fonction de quarantaine actuelle (`analyze.py::quarantaine`)

```python
def quarantaine(path, motif, details):
    os.makedirs(QUARANTINE, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(QUARANTINE, horodatage + "_" + os.path.basename(path))
    meta = {"nom_origine": ..., "chemin_origine": ..., "date_isolation": ...,
            "detecte_par": motif, "details": details}
    shutil.move(path, dest)
    os.chmod(dest, 0o000)
    with open(dest + ".json", "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    return dest
```

Constats :
- Le fichier déplacé **conserve son extension et son nom d'origine**
  (préfixé d'un horodatage) — pas un nom opaque. `chmod 0o000` retire les
  droits (protection partielle, effet limité sous Windows).
- Métadonnées : 4 champs seulement (`nom_origine`, `chemin_origine`,
  `date_isolation`, `detecte_par`, `details`) — pas de SHA-256, pas de
  taille, pas de confiance, pas de distinction upload/chemin local réel.
- **Appelée indifféremment depuis deux contextes** avec le même code :
  1. Upload Streamlit (page principale) : `path` est un fichier
     **temporaire** créé par `tempfile.NamedTemporaryFile` — jamais le
     fichier réel de l'utilisateur (Desktop/Téléchargements). `shutil.move`
     déplace donc une COPIE, pas l'original de l'utilisateur.
  2. Scan de dossier (`_actif("scan_dossier")`, fonction
     `valider_dossier_scan`) : `path` est un **chemin local réel et
     validé** sur la machine serveur (dans une racine autorisée),
     obtenu via `os.listdir`/`os.path.join`. `shutil.move` déplace ici
     effectivement le fichier original.
  - **Le code actuel ne distingue jamais ces deux cas** — aucun champ
    n'indique si le "chemin_origine" enregistré est un vrai chemin
    utilisateur ou un fichier temporaire éphémère. Ce n'est pas
    trompeur en soi (le chemin stocké est réel), mais rien n'empêche un
    lecteur de mal l'interpréter. Corrigé par cette phase (`source_context`,
    `original_removed`).
- Pas de JSON sidecar "orphelin" observé par défaut, mais le format est
  prévu pour : `app.py::charger_quarantaine()` gère déjà explicitement les
  cas fichier-sans-metadata / metadata-sans-fichier / metadata illisible.

### 1.3 Page Quarantaine existante (`app.py`, ~L820–1047)

**Déjà largement développée** — pas une page à créer de zéro :
- `charger_quarantaine()` : lecture défensive du répertoire, calcule un
  statut par enregistrement (`isole`, `incomplet`, `fichier_introuvable`,
  `metadonnees_illisibles`, `sans_metadonnees`) — **déjà tolérant aux
  métadonnées legacy/incomplètes**, jamais de crash sur une entrée
  malformée.
- Liste filtrable (nom, statut, étape de détection, période), paginée,
  avec un `st.expander` par élément affichant nom/date/source/détails.
- Bandeau explicite : *"La quarantaine est gérée côté serveur... Cette
  page ne propose ni restauration ni téléchargement."* — déjà conforme à
  l'interdiction Restore/Delete de cette phase.
- **Aucun endroit n'ouvre le contenu du fichier mis en quarantaine.**

### 1.4 Décision de conception pour cette phase

Ne PAS réécrire cette page. La centraliser : créer `quarantine_manager.py`
comme unique source de vérité (écriture ET lecture), migrer
`app.py::charger_quarantaine()` pour qu'elle délègue à ce module (même
vocabulaire de statuts, mêmes clés de dict consommées par le rendu
existant), et enrichir uniquement le contenu du `st.expander` de détail
avec les nouveaux champs (raison, confiance, SHA-256, upload vs chemin
réel) quand ils sont disponibles. `analyze.py::quarantaine()` est
remplacée par un appel à `quarantine_manager.quarantine_file()`.

---

## 2. Architecture

**Un seul module fait autorité : `quarantine_manager.py`** (racine du
projet, à côté de `analyze.py`). Ni `analyze.py` ni `app.py` ne
manipulent plus directement de fichiers sous `quarantine/`.

```
DETECT (analyze.py::analyser, verdict déjà établi — PE/PDF/DOCX/VirusTotal)
   │
   ▼  (si malveillant ET politique l'autorise, voir §5)
ISOLATE      quarantine_manager.quarantine_file()
   │            - SHA-256 calculé AVANT déplacement
   │            - shutil.move() -> nom de stockage opaque (UUID)
   │            - chmod 0o000 (best-effort)
   ▼
STORE METADATA   quarantine/<id>.json (UTF-8, voir schéma §3)
   │
   ▼
LIST         quarantine_manager.list_quarantine_items(base_dir)
   │            (app.py::charger_quarantaine() délègue directement)
   ▼
SELECT       clic sur un élément (st.expander existant)
   │
   ▼
SHOW REASON  quarantine_manager.get_quarantine_details(id, base_dir)
             "Pourquoi ce fichier a-t-il été bloqué ?" + confiance +
             SHA-256 + upload-vs-chemin-réel — MÉTADONNÉES UNIQUEMENT,
             jamais le contenu isolé.
```

Trois points d'entrée appellent `analyser()`, chacun avec un
`source_context` désormais explicite :

| Appelant | `source_context` | Nature de `path` |
|---|---|---|
| `app.py` (téléversement Streamlit) | `SOURCE_UPLOAD` | copie temporaire (`tempfile.NamedTemporaryFile`) |
| `app.py` (scan de dossier) | `SOURCE_FOLDER_SCAN` | chemin local réel, dans une racine autorisée |
| `watcher.py` (surveillance temps réel) | `SOURCE_WATCHER` | chemin local réel (Downloads/Desktop/Documents) |

## 3. Schéma de stockage

```
quarantine/
  <uuid_hex>.quarantine   ← charge utile opaque, permissions retirées
  <uuid_hex>.json         ← métadonnées UTF-8
```

`<uuid_hex>` est un `uuid.uuid4().hex` généré à chaque appel — **jamais
dérivé du nom de fichier original ni du SHA-256** (un même contenu
quarantiné deux fois produit deux enregistrements distincts, jamais un
écrasement — voir test #10/#11). Le nom original n'est **jamais** utilisé
pour construire un chemin sur disque — protection structurelle contre la
traversée de chemin (test #12).

### 3.1 Schéma de métadonnées (format actuel)

```json
{
  "id": "c7fa9f13354247d0b41484c9d66f325d",
  "original_filename": "evil.exe",
  "original_path": "C:\\...\\evil.exe",
  "original_extension": ".exe",
  "sha256": "750b37f0...",
  "file_size_bytes": 102,
  "quarantined_at": "2026-08-15T00:23:09+00:00",
  "status": "bloque",
  "verdict": "malveillant",
  "detection_source": "1 (signature)",
  "confidence": 1.0,
  "reason": "VirusTotal a signalé le fichier comme malveillant.",
  "family": null,
  "virus_total_result": {"statut": "malveillant", "detections": 12, "total_moteurs": 60},
  "quarantine_storage_name": "c7fa9f13354247d0b41484c9d66f325d.quarantine",
  "original_removed": false,
  "source_context": "upload"
}
```

`family` reste toujours `null` : le pipeline actuel ne produit aucune
classification de famille de malware — jamais fabriqué. Aucun contenu de
malware, aucun secret/clé API n'est jamais écrit dans ce JSON.

## 4. Compatibilité ascendante (legacy)

Les anciens enregistrements (`<horodatage>_<nom>` + `.json` au format
`{nom_origine, chemin_origine, date_isolation, detecte_par, details}`,
produits par l'ancienne `analyze.py::quarantaine()`) restent **lisibles
tels quels** — ni réécrits, ni supprimés, ni migrés. `list_quarantine_items()`
détecte le format (présence de `original_filename` = nouveau format) et
normalise les deux vers la même forme d'affichage ; les champs absents du
format legacy (`sha256`, `confidence`, `family`, `virus_total_result`,
`source_context`, `original_removed`) restent `None` — **jamais devinés**.

**Bug réel découvert et corrigé sur les données existantes** : 7
enregistrements legacy réels du dépôt (`quarantine/2026081...*.json`) sont
encodés dans un jeu de caractères non-UTF-8 (probablement latin-1/cp1252)
et faisaient planter `list_quarantine_items()` (`UnicodeDecodeError` non
interceptée). Corrigé (le `except` couvre désormais `UnicodeDecodeError`)
et verrouillé par un test de non-régression
(`test_non_utf8_legacy_metadata_does_not_crash_listing`). Ces 7
enregistrements s'affichent désormais avec le statut "Métadonnées
illisibles" plutôt que de faire planter la page entière — **les binaires
legacy n'ont pas été réécrits**, conformément à la consigne.

## 5. Politique de déclenchement automatique (préservée, non élargie)

**Aucune règle de détection n'a été modifiée ou élargie.** Le sous-système
de quarantaine consomme le verdict final déjà produit par le pipeline
existant — il n'en crée aucun.

- Un verdict `malveillant` par **signature VirusTotal** (étape 1) déclenche
  la quarantaine si `isoler=True` — inchangé.
- Un verdict `malveillant` par **IA PE** (étape 2, seuil 0.45) déclenche la
  quarantaine si `isoler=True` — inchangé.
- Un verdict `malveillant` par **IA PDF** déclenche la quarantaine si
  `isoler=True` — inchangé.
- Un verdict `malveillant` par **IA DOCX (prototype de recherche)** —
  **NE déclenche PAS** de quarantaine automatique, politique déjà en
  vigueur avant cette phase (`permettre_quarantaine_auto = False`,
  introduite lors de l'intégration DOCX) et **explicitement préservée à
  l'identique**. L'utilisateur voit le verdict, mais aucun déplacement de
  fichier n'a lieu sur cette seule base.
- `indeterminate` et `sain` ne déclenchent **jamais** de quarantaine
  (vérifié par test #15/#16) — aucun seuil de modèle n'a été modifié.

## 6. Upload vs chemin local réel — jamais de suppression fictive

**Un fichier reçu par téléversement navigateur ne donne à HybridScan
aucune autorité pour supprimer un fichier original inconnu sur le
Bureau/Téléchargements de l'utilisateur.** HybridScan ne peut supprimer
que l'objet exact du système de fichiers dont il connaît/contrôle
réellement le chemin.

- **`source_context="upload"`** → `original_removed=false` **toujours** :
  seule la copie temporaire d'analyse est isolée et son fichier temporaire
  supprimé après succès ; le fichier réel de l'utilisateur (s'il existe
  encore ailleurs) n'a jamais été touché. L'interface l'indique
  explicitement (§7).
- **`source_context="folder_scan"` ou `"watcher"`** → `original_removed=true` :
  le chemin traité est un chemin local réel et vérifié ; `shutil.move()`
  déplace effectivement le fichier original hors de son emplacement
  d'origine.

## 7. Interface (modification minimale, page existante conservée)

Aucune redesign. `app.py` contenait déjà une page Quarantaine complète
(liste filtrable/paginée, détail par `st.expander`, bandeau "aucune
restauration/suppression"). Changements apportés :

1. `charger_quarantaine()` délègue à `quarantine_manager.list_quarantine_items()`
   au lieu de dupliquer la logique de lecture (même vocabulaire de statuts,
   `_STATUTS_QUARANTAINE` inchangé).
2. Le `st.expander` de détail affiche désormais une section **"Pourquoi
   ce fichier a-t-il été bloqué ?"** avec la raison, la confiance (si
   disponible), les 16 premiers caractères du SHA-256, et une mention
   honnête upload-vs-chemin-réel.
3. **Aucun endroit n'ouvre, n'exécute, ne sert ni ne télécharge le
   contenu `.quarantine`** — inchangé, déjà garanti par la page existante.

## 8. Sécurité

- Aucune exécution/ouverture/import du contenu isolé, à aucun moment.
- Aucun appel à Office/shell/subprocess/PowerShell/wscript/cscript sur une
  charge utile en quarantaine.
- Aucune extraction automatique d'archive, aucune résolution de lien
  externe.
- `list_quarantine_items`/`get_quarantine_details` n'exposent que des
  métadonnées — jamais un chemin vers la charge utile exploitable par
  l'UI pour l'ouvrir.
- Noms de fichiers et métadonnées traités comme non fiables (parsing
  défensif, `try/except` systématique, jamais de construction de chemin à
  partir d'une valeur de métadonnée).
- `chmod 0o000` appliqué en best-effort (portée réduite sous Windows —
  limite connue, déjà présente avant cette phase, non résolue ici).

## 9. Tests (21/21, `tests/test_quarantine_manager.py`)

Couvre les 20 scénarios demandés (déplacement autorisé, disparition de la
source, nom opaque, JSON créé, SHA-256 correct, statut `bloque`,
source/raison/confiance préservées, liste, détails métadonnées seules,
doublon de nom sans écrasement, tentatives répétées sans corruption,
traversée de chemin neutralisée, métadonnées legacy malformées sans
crash, upload jamais `original_removed=true`, verdicts sain/indéterminé
jamais quarantinés, non-régression PE/PDF/DOCX, hash des modèles inchangé)
plus un 21e test de régression sur le bug d'encodage réel découvert (§4).

Suite complète du projet : **61/61** (11+8+6+4+11+21, tous les fichiers
`tests/test_docx_*.py` + `tests/test_quarantine_manager.py`).

## 10. Limites connues

- Pas de restauration, pas de suppression permanente — reporté
  explicitement à une phase future.
- `chmod 0o000` a un effet limité sous Windows (pas un vrai retrait ACL) —
  limite préexistante, pas résolue par ce MVP.
- Les enregistrements legacy non-UTF-8 restent illisibles (contenu non
  réécrit) — consultables uniquement via le statut "Métadonnées
  illisibles", sans détail exploitable.
- `family` (famille de malware) n'est jamais renseigné — aucune source du
  pipeline actuel ne produit cette classification.
- Aucun verrou/atomicité inter-processus sur `quarantine/` au-delà de
  l'atomicité de `shutil.move()` — un accès concurrent extrêmement rare
  pourrait théoriquement entrelacer deux écritures de métadonnées
  distinctes (fichiers différents, donc IDs différents : pas de
  corruption possible, seulement une latence).
