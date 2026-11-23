# Backlog – Système de recommandation sémantique de livres

Découpage des tâches des phases 0 à 3 du planning (SPEC.md, section 9), jusqu'à la fin du **Scoring**.
Les phases 4 à 7 (évaluation, API + front, chatbot, livrables) seront découpées plus tard.

- **Estimation** : en jours de travail (j). Les totaux suivent les durées indicatives de la SPEC.
- **Priorité** : P1 = indispensable au cœur du projet ; P2 = important ; P3 = optionnel.
- **Exigences** : numéros de la consigne (SPEC.md, section 2).
- Le suivi d'avancement se fait dans [TASK.md](TASK.md), avec les mêmes identifiants.

---

## Phase 0 – Cadrage (½ j · exigence 1)

Objectif : figer le questionnaire et le contrat de l'API, poser le squelette du repo pour que le front puisse avancer en parallèle.

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P0-01 | Créer la structure du repo | Arborescence `book-recommender-nlp/` de la SPEC (section 8) : `docs/`, `backend/`, `frontend/`, README minimal, `.gitignore` (dont `backend/data/raw`, `processed`, `embeddings`) | P1 | 0,05 | – |
| P0-02 | Initialiser le back-end Python | `pyproject.toml` (fastapi, pydantic, pandas, pyarrow, numpy, scikit-learn, sentence-transformers, transformers, keybert, gensim/fasttext, umap-learn, pytest, ruff) ; `pip install -e .` fonctionne | P1 | 0,05 | P0-01 |
| P0-03 | Squelette Clean Architecture | Packages vides `recommendation/{domain,application,adapters}`, `catalog_preparation/`, `preference_options/`, `book_search/`, `recommender_evaluation/`, `main/` ; `main/settings.py` lit la configuration ; un test vérifie que `domain/` et `application/` n'importent ni FastAPI, ni Pydantic, ni sentence-transformers, ni pandas | P2 | 0,1 | P0-02 |
| P0-04 | Initialiser le front-end | Projet React + Vite, dossiers par fonctionnalité (`questionnaire/`, `recommendations/`, `how-it-works/`, `api-client/`) ; proxy Vite vers l'API | P2 | 0,05 | P0-01 |
| P0-05 | Figer le questionnaire | Listes fermées : genres (8 à 12), thèmes, atmosphères, styles narratifs, périodes, cases rapides « à éviter » ; seuils de longueur (< 200, 200-400, > 400) ; règles d'âge. Fichier de référence unique (ex. `backend/data/options.json`) | P1 | 0,1 | – |
| P0-06 | Contrat API (schémas Pydantic) | Schémas dans `adapters/web/schemas.py` : `RecommendRequest` (14 champs, contraintes Likert 1-5, âge > 0), `RecommendResponse` (top 3, score global, scores par critère, mots-clés communs, explication, affinité par catégorie, point UMAP, avertissement si < 3), `OptionsResponse`, `BookSearchResult`, `MapPoint` ; brouillon de `docs/api.md` | P1 | 0,1 | P0-05 |
| P0-07 | Données fictives pour le front | JSON conformes aux schémas (réponses de `/api/options`, `/api/recommend`, `/api/map`) pour développer le front sans back-end | P2 | 0,05 | P0-06 |
| P0-08 | Rôles et conventions | Répartition des rôles, convention de branches et de commits, définition de « terminé » (tests passent, doc à jour) | P2 | 0,02 | – |

**Total phase 0 : ≈ 0,5 j**

---

## Phase 1 – Données (1 à 2 j · exigence 2)

Objectif : produire `data/processed/books.parquet`, nettoyé et enrichi, avec un prétraitement documenté et reproductible (cas d'usage `PrepareCatalog`).

### 1.a Acquisition et exploration

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P1-01 | Télécharger les datasets | Best Books Ever (Zenodo) et Goodbooks-10k extended dans `data/raw/` ; script ou commande documentée | P1 | 0,05 | P0-01 |
| P1-02 | Explorer Best Books Ever | Notebook : taux de remplissage par colonne, langues, genres, distribution des pages et de la longueur des descriptions, part de fiction, part du champ setting | P1 | 0,2 | P1-01 |

### 1.b Nettoyage (`catalog_preparation`)

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P1-03 | Règles de nettoyage (domaine) | Fonctions pures testées : est-fiction, langue acceptée (en, fr), description suffisante (≥ ~30 mots), clé de dédoublonnage (titre + auteur normalisés) | P1 | 0,1 | P0-03 |
| P1-04 | Filtrer fiction + langue | Garder la fiction en anglais et en français | P1 | 0,05 | P1-03 |
| P1-05 | Filtrer descriptions + dédoublonner | Supprimer sans description ou < ~30 mots ; dédoublonner sur titre + auteur | P1 | 0,05 | P1-03 |
| P1-06 | Normaliser le texte | Casse, balises HTML, espaces ; journal du nombre de lignes retirées à chaque étape | P1 | 0,05 | P1-04, P1-05 |

### 1.c Enrichissement

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P1-07 | Genre normalisé | Table de correspondance genres Goodreads → liste fermée du questionnaire ; taux de livres sans genre mappé mesuré | P1 | 0,15 | P0-05, P1-06 |
| P1-08 | Âge minimum + catégorie de longueur | Règle Juvenile / Young Adult → âge minimum ; seuils sur les pages → court / moyen / long | P1 | 0,05 | P1-06 |
| P1-09 | Thèmes, style, atmosphère (zero-shot) | Classification zero-shot sur les listes fixes de P0-05 ; choix du modèle (ex. NLI multilingue) ; traitement par lots avec cache ; mesurer le temps CPU et réduire le corpus si trop long | P1 | 0,3 | P0-05, P1-06 |
| P1-10 | Mots-clés (KeyBERT) | 5 à 10 mots-clés par livre (servent aux « mots-clés communs » des explications) | P2 | 0,1 | P1-06 |
| ~~P1-11~~ | ~~Complexité 1-5~~ | **Retirée** (2026-11-23) : critère de complexité supprimé, voir Décisions | – | – | – |
| P1-12 | Période | Classification zero-shot de la description sur les périodes de options.json (le champ setting ne contient que des lieux) | P2 | 0,1 | P1-06 |

### 1.d Assemblage et documentation

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P1-13 | Cas d'usage `PrepareCatalog` + CLI | Enchaîne nettoyage et enrichissement ; adapter Parquet ; commande CLI qui produit `data/processed/books.parquet` ; notebooks appellent ce cas d'usage | P1 | 0,15 | P1-04 → P1-12 |
| P1-14 | `docs/dataset.md` | Origine, structure, colonnes ajoutées et méthodes, lignes retirées par étape, limites (anglophone, Goodreads, descriptions marketing, setting sans époque) | P1 | 0,1 | P1-13 |

**Total phase 1 : ≈ 1,75 j**

---

## Phase 2 – Moteur sémantique (2 j · exigence 3)

Objectif : encoder les livres une fois, hors ligne, avec trois approches interchangeables (TF-IDF, fastText, SBERT), et calculer la similarité cosinus champ par champ.

### 2.a Ports et domaine

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P2-01 | Port `TextEncoder` + `FakeTextEncoder` | Protocol dans `application/ports` ; fake déterministe pour les tests | P1 | 0,05 | P0-03 |
| P2-02 | Ports `BookCatalog`, `BookVectorIndex`, `SimilarityMapProjector` | Protocols dans `application/ports` ; catalogue en mémoire pour les tests | P1 | 0,1 | P0-03 |
| P2-03 | Similarité cosinus | Fonction pure (vecteur × matrice), testée (vecteurs identiques = 1, orthogonaux = 0, vecteur nul géré) | P1 | 0,05 | P0-03 |

### 2.b Encodeurs (adapters)

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P2-04 | `TfidfTextEncoder` | scikit-learn, ajusté sur les descriptions ; sauvegarde du vectoriseur | P1 | 0,15 | P2-01, P1-13 |
| P2-05 | `FastTextTextEncoder` | cc.fr.300 ou Word2Vec entraîné sur les descriptions (quelques secondes) ; moyenne des vecteurs de mots | P2 | 0,25 | P2-01, P1-13 |
| P2-06 | `SbertTextEncoder` | Choisir entre paraphrase-multilingual-MiniLM-L12-v2 et multilingual-e5-base (préfixes `query:` / `passage:` pour e5) ; vecteurs normalisés ; test FR → EN sur quelques paires | P1 | 0,2 | P2-01 |

### 2.c Indexation hors ligne

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P2-07 | Encodage du catalogue par champ | Commande CLI : description, thèmes, style, atmosphère → un `.npy` par champ et par encodeur + fichier d'alignement des identifiants dans `data/embeddings/` | P1 | 0,25 | P2-04, P2-05, P2-06, P1-13 |
| P2-08 | `ParquetBookCatalog` | Lecture de `books.parquet` ; accès par identifiant ; recherche par titre (servira à l'autocomplétion) | P1 | 0,1 | P2-02, P1-13 |
| P2-09 | `NumpyVectorIndex` | Charge les `.npy` une seule fois ; renvoie les similarités d'un vecteur requête pour un champ donné | P1 | 0,15 | P2-02, P2-03, P2-07 |
| P2-10 | Encodage du profil utilisateur | Transforme chaque champ du profil (texte libre, listes de tags) en texte, puis en vecteur, avec le même encodeur que le catalogue | P1 | 0,15 | P2-01 |

### 2.d Comparaison et carte

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P2-11 | Comparaison qualitative des 3 approches | Notebook : quelques requêtes types, top 5 par approche, temps d'encodage et latence ; la mesure chiffrée viendra en phase 4 | P2 | 0,2 | P2-09, P2-10 |
| P2-12 | Clustering + UMAP (optionnel) | KMeans + projection UMAP hors ligne → coordonnées 2D sauvegardées ; `UmapProjector` projette le point utilisateur à la volée | P3 | 0,3 | P2-07 |

**Total phase 2 : ≈ 2,2 j** (≈ 1,9 j sans UMAP)

---

## Phase 3 – Scoring et explications (1 à 2 j · exigences 4, 5)

Objectif : appliquer la formule de la SPEC (section 6) et renvoyer un top 3 expliqué, via le cas d'usage `RecommendBooks`.

```
S = w1·sim(texte libre, description) + w2·sim(thèmes) + w3·sim(atmosphère) + w4·sim(style)
  + w5·genre + w6·sim(livre aimé, livre) − w7·sim(à éviter, livre)
```

### 3.a Entités et politique de scoring (domaine)

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P3-01 | Entités `ReaderProfile`, `Book`, `Match` | Dataclasses du domaine, sans dépendance externe | P1 | 0,1 | P0-03 |
| P3-02 | `ScoringPolicy` | Poids par défaut w1 à w7, seuil minimum ; validation (poids ≥ 0) ; modulation de w2, w3, w4 par les Likert d'importance (w × likert / 3, puis renormalisation pour garder la somme w2 + w3 + w4 par défaut ; tests : Likert tous égaux → poids inchangés) ; valeurs lues dans `main/settings.py` puis injectées | P1 | 0,15 | P3-01 |
| P3-03 | Règles d'éligibilité (filtres durs) | Âge : < 13 → Juvenile ; 13-17 → YA + Juvenile ; ≥ 18 → tout. Livre aimé exclu | P1 | 0,1 | P3-01 |

### 3.b Critères de score

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P3-04 | Score genre | 1 si le genre du livre est sélectionné, sinon similarité entre genres (matrice précalculée avec l'encodeur) | P1 | 0,1 | P3-01, P2-06 |
| ~~P3-05~~ | ~~Score complexité~~ | **Retirée** (2026-11-23) : critère de complexité supprimé, voir Décisions | – | – | – |
| P3-06 | Pénalité « à éviter » | Similarité entre le texte « à éviter » (+ cases rapides) et le livre, multipliée par w7 ; ignorée si le champ est vide | P1 | 0,1 | P3-01, P2-10 |
| P3-07 | Filtres souples longueur et période | Réduisent le score au lieu d'exclure (malus ou facteur à fixer) ; « indifférent » = aucun effet | P1 | 0,1 | P3-01 |
| P3-08 | Terme livre aimé (w6) | Récupérer l'embedding pré-calculé du livre aimé par son identifiant (description, ou moyenne des champs : à trancher) ; similarité cosinus avec chaque livre × w6 ; w6 = 0 si le champ est vide ; critère « livre aimé » présent dans les raisons structurées pour l'explication | P1 | 0,1 | P3-02, P2-09 |

### 3.c Classement et explications

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P3-09 | Score global + seuil + top 3 | Somme pondérée sur les seuls livres éligibles ; seuil minimum ; tri ; signal si moins de 3 livres passent | P1 | 0,1 | P3-02 → P3-08 |
| P3-10 | Raisons structurées | Pour chaque match : score par critère, critères qui contribuent le plus, mots-clés communs (KeyBERT) | P1 | 0,1 | P3-09, P1-10 |
| P3-11 | Affinité par catégorie | Agrégats par critère / genre pour les graphiques (radar, barres) de la page Résultats | P2 | 0,1 | P3-09 |
| P3-12 | Cas d'usage `RecommendBooks` | Request / Response en dataclasses ; orchestre encodeur, catalogue, index, politique ; aucun import FastAPI / Pydantic / SBERT | P1 | 0,15 | P3-09, P3-10, P2-01, P2-02 |
| P3-13 | Presenter d'explications | Templates de phrases à partir des raisons structurées, sans IA générative (ex. « Recommandé car très proche de vos thèmes (identité, dilemmes moraux, 0,81)… ») | P1 | 0,1 | P3-10 |

### 3.d Tests, démo et documentation

| ID | Tâche | Détail / critère de fin | Prio | Estim. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| P3-14 | Tests du domaine et du cas d'usage | Avec `FakeTextEncoder` et catalogue en mémoire, sans modèle ni fichiers : filtres, scores, seuil, exclusion du livre aimé, cas < 3 résultats | P1 | 0,2 | P3-12 |
| P3-15 | Démo bout en bout | Commande CLI ou notebook : profil exemple → top 3 avec scores et explications, sur le vrai catalogue avec SBERT | P1 | 0,1 | P3-12, P3-13, P2-09 |
| P3-16 | `docs/scoring_formula.md` | Formule, rôle de chaque terme, poids par défaut et justification, modulation Likert, filtres durs / souples, seuil, terme livre aimé | P1 | 0,1 | P3-09, P3-08 |

**Total phase 3 : ≈ 1,8 j**

> Décisions :
> - le **rythme** a été retiré du questionnaire (aucune donnée dans le dataset pour le mesurer) ;
> - la **complexité** a été retirée (2026-11-23) : aucune donnée fiable pour la mesurer (seule la lisibilité du résumé marketing était disponible) ; P1-11 et P3-05 supprimées, les poids sont renumérotés (livre aimé w6, « à éviter » w7) ;
> - le **livre aimé** entre dans la formule par le terme w6 (similarité avec son embedding pré-calculé) ;
> - **modulation Likert** : w × likert / 3, puis renormalisation de w2 + w3 + w4.

---

## Points ouverts

| # | Question | Où elle se règle |
| --- | --- | --- |
| 1 | Forme des **filtres souples** (malus additif ou facteur multiplicatif) et valeur | P3-07 |
| 2 | Choix final **MiniLM vs e5** (vitesse sur CPU vs qualité) | P2-06, confirmé en phase 4 |
| 3 | Embedding du livre aimé : description seule ou moyenne des champs ? | P3-08 |
| 4 | Le zero-shot sur ~50 000 livres peut être long sur CPU : réduire le corpus ou le modèle ? | P1-09 |
