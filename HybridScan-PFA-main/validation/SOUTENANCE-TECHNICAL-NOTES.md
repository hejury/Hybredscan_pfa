# HybridScan — Notes techniques pour la soutenance

Points de discours techniquement exacts, à réutiliser tels quels ou
presque. Objectif : rester précis et honnête sur ce que le système fait
réellement, sans survendre ses capacités.

## Architecture

> « HybridScan utilise une architecture web séparant l'interface Next.js,
> l'API FastAPI et le moteur d'analyse Python existant. »

```
Navigateur
  ↓
Next.js (App Router, TypeScript, Tailwind CSS)
  ↓ HTTP/JSON, cookie de session
FastAPI (/api/v1/*)
  ↓ appels directs, aucune logique dupliquée
Moteur HybridScan (analyze.py, quarantine_manager.py, watcher.py, auth.py)
  ├── VirusTotal (signature)
  ├── Random Forest PE
  ├── Modèle PDF (prototype de recherche)
  ├── Modèle DOCX (prototype de recherche)
  ├── Historique (history.csv)
  ├── Quarantaine (quarantine/)
  └── Watcher / Protection
```

L'API FastAPI est un pont HTTP mince : elle ne réimplémente aucune
logique de détection, de sécurité de chemin, ou de quarantaine — chaque
service sous `api/services/` appelle directement le code Python déjà
testé (`analyze.analyser`, `quarantine_manager.*`, `backend_shared.*`,
`watcher.Protection`). Streamlit reste disponible comme interface de
repli, utilisant les mêmes modules.

## PE (exécutables Windows)

> « Les exécutables PE sont analysés statiquement sans exécution. »

Le fichier n'est jamais lancé. Une empreinte SHA-256 est calculée, une
vérification par signature est tentée auprès de VirusTotal, et si elle
ne conclut pas, un modèle Random Forest entraîné sur des caractéristiques
structurelles (taille, entropie, sections, imports, API suspectes, etc.)
produit un verdict avec un score de confiance. Seuil de décision : 0.45
(optimisé par validation croisée, voir `exp_seuil.py`).

## PDF

> « L'analyse PDF par IA constitue un prototype de recherche. Les tests
> réels ont mis en évidence au moins un faux positif, ce qui interdit de
> la présenter comme un moteur prêt pour la production. »

Le pipeline PDF valide d'abord la structure du fichier (signature
`%PDF-`) avant tout transfert au modèle — un fichier renommé en `.pdf`
sans structure PDF réelle n'est jamais analysé par le modèle. Lors des
tests d'intégration réels de ce projet, un PDF de test inoffensif et
structurellement minimal a été classé « malveillant » avec ~88% de
confiance par le modèle — un exemple direct et documenté de faux
positif, conservé tel quel dans le rapport d'intégration plutôt que
masqué.

## DOCX

> « L'analyse DOCX est également un prototype de recherche. Les très
> fortes performances observées sur le jeu de données doivent être
> interprétées avec prudence en raison d'un risque d'artefacts de
> corpus et d'un manque de validation externe. »

Comme pour PDF, la structure du fichier (archive ZIP/OOXML valide) est
vérifiée avant tout transfert au modèle. Un verdict « malveillant »
produit **uniquement** par ce modèle (sans confirmation VirusTotal)
n'entraîne **pas** de mise en quarantaine automatique par défaut — une
garde de sécurité délibérée et documentée (`analyze.py::analyser`,
garde de fin de fonction), non modifiée durant cette phase de
finalisation.

## VirusTotal

Interrogé en premier pour PE, PDF et DOCX via l'empreinte SHA-256
(jamais le contenu du fichier). En l'absence de clé API configurée
(`VT_API_KEY`), le pipeline bascule silencieusement et automatiquement
vers l'étape d'analyse statique par IA — aucune erreur affichée à
l'utilisateur, aucun appel réseau tenté inutilement.

## Quarantaine

> « La quarantaine isole les fichiers lorsque la politique de détection
> l'autorise. Pour un upload navigateur, HybridScan ne peut pas
> supprimer arbitrairement le fichier original présent sur le poste
> client. »

Un fichier téléversé depuis le navigateur est d'abord écrit dans une
copie temporaire côté serveur ; seule cette copie peut être isolée. Le
fichier réel de l'utilisateur (Bureau, Téléchargements, etc.) n'est ni
connu ni accessible par le serveur. Pour un scan de dossier ou une
détection du watcher, en revanche, le chemin traité est un chemin local
réel et vérifié : la mise en quarantaine y déplace effectivement le
fichier d'origine (`original_removed=true` dans les métadonnées). La
quarantaine ne stocke que des métadonnées consultables depuis
l'interface — jamais d'ouverture, de téléchargement ou de restauration
du contenu isolé n'est proposée.

## Scan de dossier

Couvre `.exe`, `.dll`, `.pdf` et `.docx` (mis à jour le 2026-08-19 —
initialement limité à `.exe`/`.dll`). Chaque fichier candidat est
routé vers le même `analyser()` que l'analyse d'un seul fichier, via la
seule liste d'extensions partagée entre Streamlit et l'API
(`backend_shared.EXTENSIONS_SCAN_DOSSIER`) : même identification
réelle du fichier, même anti-spoofing (un exécutable renommé `.docx`
suit toujours le routage PE, une archive quelconque renommée `.docx`
échoue toujours la validation DOCX), et même politique de quarantaine
— y compris la garde de sécurité qui empêche un verdict DOCX
malveillant (prototype de recherche seul, sans confirmation
VirusTotal) de déclencher une quarantaine automatique. `.doc` (legacy)
reste hors périmètre du scan de dossier.

Le chemin est validé côté serveur contre une liste de racines
autorisées configurée par l'administrateur (`HYBRIDSCAN_ALLOWED_SCAN_DIRS`) — la
confirmation d'appartenance à une racine autorisée utilise une
résolution canonique de chemin (`Path.relative_to()` après
`resolve()`), pas une comparaison de préfixe de chaîne, pour éviter
qu'un dossier comme `C:\SafeBackup` soit accepté à tort quand seul
`C:\Safe` est autorisé. Cette validation de chemin n'a pas changé.

## Session et authentification

Authentification par cookie de session HttpOnly (jamais de jeton ou de
mot de passe stocké côté navigateur), `SameSite=Lax`. Les sessions sont
conservées en mémoire, propres au processus API — un redémarrage de
l'API invalide toutes les sessions actives ; acceptable pour un usage
académique/local à un seul worker, documenté comme limitation connue
plutôt que masqué.

## Ce que le système ne fait pas (à ne jamais affirmer)

- Aucune exécution de fichier, de macro, ou de script — analyse
  strictement statique.
- Aucune métrique de précision globale ("98,7% de précision") n'est
  affichée : l'historique runtime ne contient pas de vérité terrain
  pour calculer un taux de détection fiable.
- La quarantaine ne propose ni restauration ni suppression définitive.
- Le scan de dossier ne couvre pas PDF/DOCX.
- La protection en temps réel ne surveille que les dossiers configurés
  et s'arrête à la fermeture du processus API — ce n'est pas un service
  système persistant.
