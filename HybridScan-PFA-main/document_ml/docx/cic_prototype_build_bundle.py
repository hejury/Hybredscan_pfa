#!/usr/bin/env python3
"""cic_prototype_build_bundle.py — Assemble le bundle model_docx_candidate.pkl
a partir du Modele A deja entraine (cic_prototype_train.py). Ecrit le
bundle a la racine du projet (BASE), au meme emplacement que
model.pkl/model_pdf.pkl -- jamais directement model_docx.pkl (promotion
separee, apres validation runtime -- voir document_ml/docx/predict.py et
validation/DOCX-RUNTIME-VALIDATION.md)."""
import json
import pickle
import platform
from datetime import datetime, timezone

import sklearn
import numpy as np

PROJECT_ROOT = r"C:\Users\user\Desktop\PFA_PRJECT-main\PFA_PRJECT-main\Desktop\project_pfa\pfe"

with open(PROJECT_ROOT + r"\datasets\docx\cic_prototype_model_a.pkl", "rb") as fh:
    model_a = pickle.load(fh)
with open(PROJECT_ROOT + r"\datasets\docx\cic_prototype_results.json", encoding="utf-8") as fh:
    resultats = json.load(fh)

ra = resultats["modele_a"]

with open(PROJECT_ROOT + r"\datasets\docx\Word_All_features.csv", "rb") as fh:
    import hashlib
    dataset_hash = hashlib.sha256(fh.read()).hexdigest()

bundle = {
    "model": model_a,
    "features": ra["colonnes"],  # ["file_size_bytes", "has_vba_macros"]
    "seuil": ra["seuil"],
    "metadata": {
        "model_family": "RandomForestClassifier",
        "supported_formats": ["docx"],
        "feature_schema_version": 2,
        "training_date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "random_seed": 42,
        "hyperparameters": ra["hyperparametres"],
        "threshold": ra["seuil"],
        "threshold_selection_method": "F2-score maximise sur la VALIDATION uniquement "
                                       "(jamais sur le test tenu a l'ecart)",
        "class_distribution_train": ra["classes_train"],
        "class_distribution_validation": ra["classes_val"],
        "class_distribution_test": ra["classes_test"],
        "evaluation_metrics_validation": ra["metrics_validation"],
        "evaluation_metrics_test": ra["metrics_test"],
        "label_shuffle_sanity_auc_validation": ra["label_shuffle_auc_validation"],
        "single_feature_auc": ra["single_feature_auc"],
        "ablation": ra["ablation"],
        "duplicate_leakage_proof_overlap": ra["duplicate_leakage_proof_overlap"],
        "library_versions": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "dataset_provenance": {
            "source": "CIC-Trap4Phish 2025 (Canadian Institute for Cybersecurity, UNB)",
            "file": "datasets/docx/Word_All_features.csv",
            "sha256": dataset_hash,
            "rows_before_exclusion": resultats["n_lignes_avant_exclusion"],
            "rows_excluded_extraction_failure": resultats["n_lignes_exclues"],
            "rows_used": resultats["n_lignes_retenues"],
        },
        # --- Champs de transparence explicitement requis par le cahier des
        # charges de cette phase -- ne JAMAIS retirer ni assouplir sans
        # instruction explicite ---
        "research_only": True,
        "production_ready": False,
        "external_validation": False,
        "known_corpus_artifact_risk": True,
        "known_limitations": [
            "Le CSV CIC-Trap4Phish livre ne prouve pas que chaque ligne est un .docx : le "
            "code de reference officiel couvre .doc/.dot/.docx/.docm/.dotx/.dotm sans colonne "
            "de format -- voir validation/DOCX-CIC-FEATURE-DEFINITIONS.md section 6.",
            "has_vba_macros separe les classes de facon quasi parfaite dans ce dataset "
            "(AUC descriptive 1.0000) -- tres probablement un artefact de construction du "
            "corpus (criteres de selection des echantillons) plutot qu'un signal de "
            "malveillance generalisable. Consequence pratique directe : ce prototype "
            "classera tres probablement TOUT document contenant une macro VBA comme "
            "malveillant, y compris des documents professionnels legitimes utilisant des "
            "macros (modeles de facture, publipostage, etc.).",
            "file_size_bytes separe egalement les classes de facon quasi parfaite par rang "
            "(AUC descriptive 0.9937) malgre une correlation lineaire faible -- meme risque "
            "d'artefact de corpus.",
            "Aucune validation externe (dataset independant, echantillons reels HybridScan) "
            "n'a ete effectuee au-dela des fixtures synthetiques benignes de "
            "validation/DOCX-RUNTIME-VALIDATION.md.",
            "dde_present a ete explicitement exclu (contradiction prouvee avec le code de "
            "reference officiel).",
            "Ce modele ne doit JAMAIS etre presente comme pret pour la production, certifie, "
            "ou fiable a un pourcentage quelconque.",
        ],
    },
}

chemin_candidat = PROJECT_ROOT + r"\model_docx_candidate.pkl"
with open(chemin_candidat, "wb") as fh:
    pickle.dump(bundle, fh)

print("Bundle candidat ecrit :", chemin_candidat)
print("Caracteristiques :", bundle["features"])
print("Seuil :", bundle["seuil"])
print("Version de schema :", bundle["metadata"]["feature_schema_version"])
