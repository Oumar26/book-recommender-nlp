# Suivi des tâches

Tableau d'avancement du projet. Le détail de chaque tâche (critère de fin, dépendances) est dans [Backlog.md](Backlog.md).

**Statuts :** ⬜ À faire · 🔄 En cours · ✅ Terminé · ⛔ Bloqué
**Priorités :** P1 indispensable · P2 important · P3 optionnel

Mettre à jour la colonne **Statut** (et **Responsable**) à chaque changement ; noter la date de fin dans **Notes**.

## Vue d'ensemble

| Phase | Tâches | Terminées | Estimation | Statut |
| --- | --- | --- | --- | --- |
| 0. Cadrage | 8 | 8 | ½ j | ✅ |
| 1. Données | 14 | 8 | 1 à 2 j | 🔄 |
| 2. Moteur | 12 | 0 | 2 j | ⬜ |
| 3. Scoring | 16 | 0 | 1 à 2 j | ⬜ |
| 4. Évaluation | à découper | – | 1 j | ⬜ |
| 5. API + front | à découper | – | 2 j | ⬜ |
| 6. Bonus chatbot | à découper | – | 1 à 2 j | ⬜ |
| 7. Livrables | à découper | – | 1 j | ⬜ |

## Phase 0 – Cadrage

| ID | Tâche | Prio | Estim. | Responsable | Statut | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| P0-01 | Créer la structure du repo | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P0-02 | Initialiser le back-end Python (pyproject) | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P0-03 | Squelette Clean Architecture + test de dépendances | P2 | 0,1 j | | ✅ | 2026-11-23 |
| P0-04 | Initialiser le front-end React + Vite | P2 | 0,05 j | | ⬜ | |
| P0-05 | Figer le questionnaire (listes fermées, seuils) | P1 | 0,1 j | | ✅ | 2026-11-23 · backend/data/options.json |
| P0-06 | Contrat API (schémas Pydantic) + brouillon api.md | P1 | 0,1 j | | ✅ | 2026-11-23 |
| P0-07 | Données fictives pour le front | P2 | 0,05 j | | ✅ | 2026-11-23 |
| P0-08 | Rôles et conventions | P2 | 0,02 j | | ✅ | 2026-11-23 |

## Phase 1 – Données

| ID | Tâche | Prio | Estim. | Responsable | Statut | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| P1-01 | Télécharger les datasets | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P1-02 | Explorer Best Books Ever | P1 | 0,2 j | | ✅ | 2026-11-23 |
| P1-03 | Règles de nettoyage (domaine) | P1 | 0,1 j | | ✅ | 2026-11-23 |
| P1-04 | Filtrer fiction + langue (en, fr) | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P1-05 | Filtrer descriptions courtes + dédoublonner | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P1-06 | Normaliser le texte + journal des lignes retirées | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P1-07 | Genre normalisé (mapping) | P1 | 0,15 j | | ✅ | 2026-11-23 |
| P1-08 | Âge minimum + catégorie de longueur | P1 | 0,05 j | | ✅ | 2026-11-23 |
| P1-09 | Thèmes, style, atmosphère (zero-shot) | P1 | 0,3 j | | ⬜ | |
| P1-10 | Mots-clés (KeyBERT) | P2 | 0,1 j | | ⬜ | |
| P1-11 | Complexité 1-5 + échantillon annoté | P2 | 0,15 j | | 🔄 | Indicateur fait ; échantillon à annoter : data/eval/complexity_sample.csv |
| P1-12 | Période (setting ou similarité) | P2 | 0,1 j | | ⬜ | setting = lieux, pas d'époques → zero-shot sur la description |
| P1-13 | Cas d'usage PrepareCatalog + CLI → books.parquet | P1 | 0,15 j | | 🔄 | Partie CPU faite (books_clean.parquet) ; reste l'étape NLP |
| P1-14 | Rédiger docs/dataset.md | P1 | 0,1 j | | ⬜ | |

## Phase 2 – Moteur sémantique

| ID | Tâche | Prio | Estim. | Responsable | Statut | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| P2-01 | Port TextEncoder + FakeTextEncoder | P1 | 0,05 j | | ⬜ | |
| P2-02 | Ports BookCatalog, BookVectorIndex, SimilarityMapProjector | P1 | 0,1 j | | ⬜ | |
| P2-03 | Similarité cosinus (fonction pure) | P1 | 0,05 j | | ⬜ | |
| P2-04 | Adapter TfidfTextEncoder | P1 | 0,15 j | | ⬜ | |
| P2-05 | Adapter FastTextTextEncoder | P2 | 0,25 j | | ⬜ | |
| P2-06 | Adapter SbertTextEncoder (choix du modèle) | P1 | 0,2 j | | ⬜ | |
| P2-07 | Encodage hors ligne par champ → .npy | P1 | 0,25 j | | ⬜ | |
| P2-08 | Adapter ParquetBookCatalog | P1 | 0,1 j | | ⬜ | |
| P2-09 | Adapter NumpyVectorIndex | P1 | 0,15 j | | ⬜ | |
| P2-10 | Encodage du profil utilisateur par champ | P1 | 0,15 j | | ⬜ | |
| P2-11 | Comparaison qualitative TF-IDF / fastText / SBERT | P2 | 0,2 j | | ⬜ | |
| P2-12 | Clustering + UMAP (optionnel) | P3 | 0,3 j | | ⬜ | |

## Phase 3 – Scoring et explications

| ID | Tâche | Prio | Estim. | Responsable | Statut | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| P3-01 | Entités ReaderProfile, Book, Match | P1 | 0,1 j | | ⬜ | |
| P3-02 | ScoringPolicy (poids, validation, modulation Likert) | P1 | 0,15 j | | ⬜ | |
| P3-03 | Filtres durs (âge, livre aimé exclu) | P1 | 0,1 j | | ⬜ | |
| P3-04 | Score genre | P1 | 0,1 j | | ⬜ | |
| P3-05 | Score complexité (proximité) | P1 | 0,05 j | | ⬜ | |
| P3-06 | Pénalité « à éviter » | P1 | 0,1 j | | ⬜ | |
| P3-07 | Filtres souples longueur et période | P1 | 0,1 j | | ⬜ | |
| P3-08 | Terme livre aimé (w7) | P1 | 0,1 j | | ⬜ | |
| P3-09 | Score global + seuil + top 3 | P1 | 0,1 j | | ⬜ | |
| P3-10 | Raisons structurées + mots-clés communs | P1 | 0,1 j | | ⬜ | |
| P3-11 | Affinité par catégorie | P2 | 0,1 j | | ⬜ | |
| P3-12 | Cas d'usage RecommendBooks | P1 | 0,15 j | | ⬜ | |
| P3-13 | Presenter d'explications (templates) | P1 | 0,1 j | | ⬜ | |
| P3-14 | Tests du domaine et du cas d'usage (fakes) | P1 | 0,2 j | | ⬜ | |
| P3-15 | Démo bout en bout (profil → top 3) | P1 | 0,1 j | | ⬜ | |
| P3-16 | Rédiger docs/scoring_formula.md | P1 | 0,1 j | | ⬜ | |

## Phases suivantes (à découper)

| ID | Tâche | Prio | Estim. | Responsable | Statut | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| P4 | Évaluation : profils tests, Precision@3, nDCG@3, réglage des poids | P1 | 1 j | | ⬜ | |
| P5 | API FastAPI + pages React + graphiques | P1 | 2 j | | ⬜ | |
| P6 | Bonus chatbot (slot filling) | P3 | 1 à 2 j | | ⬜ | Seulement après P5 |
| P7 | Livrables : README, docs, slides, répétition | P1 | 1 j | | ⬜ | |
