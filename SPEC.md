# Cahier des charges – Système de recommandation sémantique de livres

## 1. Contexte et objectifs

Le projet construit une web app qui recommande les 3 livres les plus adaptés aux préférences littéraires d'un utilisateur, par similarité sémantique et avec des explications transparentes. Il est techniquement faisable avec des outils open source mats, sur un ordinateur portable, sans GPU.

- **Thème :** recommandation de livres fondée sur les préférences littéraires (genres, thèmes, style, atmosphère, complexité).
- **Résultat attendu :** un système explicable, fondé sur la similarité sémantique contextuelle, qui va au-delà de la simple correspondance de mots-clés.
- **Choix structurant :** pas d'entraînement de modèle. Le problème est non supervisé (pas de labels), on utilise donc des modèles d'embeddings pré-entraînés. La valeur ajoutée porte sur la représentation des données, le scoring pondéré et l'explicabilité.
- **Stack :** back-end Python (FastAPI), front-end JavaScript (React + Vite).
- **Livrables (Boostcamp) :** code source et documentation sur un repo, support de présentation.

## 2. Périmètre fonctionnel

Le système couvre les 6 exigences de la consigne. Le chatbot est un bonus, réalisé seulement si le reste est terminé.

| Exigence | Ce qui est attendu | Réponse du projet |
| --- | --- | --- |
| 1. Collecte utilisateur | Questionnaire web : questions ouvertes, Likert, guidées, choix multiples ; assez de texte libre | Page Questionnaire (React), champs définis en section 3 |
| 2. Jeu de données | Catégories, attributs, descriptions, mots-clés ; origine, structure et prétraitement documentés | Best Books Ever filtré et enrichi (section 4) |
| 3. Moteur sémantique | Prétraitement, embeddings statiques et contextuels, cosinus, choix justifié | Comparaison TF-IDF / fastText / SBERT multilingue (section 5) |
| 4. Scoring | Formule définie et justifiée (similarités, poids, seuils, contraintes) | Somme pondérée + pénalité + filtres (section 6) |
| 5. Recommandation | Top 3 classé avec score, critères contributeurs et explication | Explications par templates, sans IA générative |
| 6. Visualisation (web app) | Profil, scores, affinité par catégorie, classement, graphiques | Page Résultats : radar, barres, carte de similarité UMAP |
| Bonus : chatbot | Questions de clarification, affinage du profil ; s'appuie sur le moteur | Slot filling qui appelle le moteur, sans le remplacer |

## 3. Données d'entrée utilisateur

Le questionnaire compte 14 champs, chacun avec un rôle précis : similarité sémantique, poids, filtre dur ou filtre souple. Le budget initial est remplacé par la longueur, car le dataset ne fournit pas de prix fiable.

| Champ | Type | Widget | Rôle dans le moteur |
| --- | --- | --- | --- |
| Description libre | str | Question ouverte, min. \~20 mots | Similarité avec la description du livre |
| Livre aimé | str ou vide | Autocomplétion sur le titre | Point de référence (terme w7 du score) ; exclu des résultats |
| Genres | list\[str\] | Multi-select, liste fermée (8 à 12 genres) | Match avec le genre normalisé du livre |
| Thèmes | list\[str\] | Tags + champ « autre » | Similarité avec les thèmes extraits |
| Atmosphère | list\[str\] | Tags (sombre, lumineuse, mélancolique…) | Similarité sémantique |
| Période | str | Choix unique, « indifférent » possible | Filtre souple |
| Style narratif | list\[str\] ou vide | Tags (1re personne, dialogues, poétique…) | Similarité avec la colonne Style |
| Complexité | int | Likert 1-5 (légère → exigeante) | Score de proximité |
| Importance thèmes | int | Likert 1-5 | Poids de la formule |
| Importance style | int | Likert 1-5 | Poids de la formule |
| Importance atmosphère | int | Likert 1-5 | Poids de la formule |
| À éviter | str | Texte libre sans négation + cases rapides | Pénalité |
| Âge | int | Nombre | Filtre dur : < 13 → Juvenile ; 13-17 → YA + Juvenile ; ≥ 18 → tout |
| Longueur | str | Court (< 200 p.), moyen (200-400), long (> 400), indifférent | Filtre souple sur le nombre de pages |

Règles d'ergonomie :

- Prévenir l'utilisateur de décrire ce qu'il aime dans le texte libre et de mettre ce qu'il n'aime pas dans « À éviter » : les embeddings gèrent mal la négation.
- Préciser dans l'interface que les livres recommandés peuvent être en anglais (VO).

## 4. Jeu de données

Le dataset principal est **Best Books Ever** (Goodreads, 52 478 livres, 25 variables) : il couvre le plus d'inputs. **Goodbooks-10k extended** sert à l'évaluation grâce à ses notes réelles d'utilisateurs.

|  | 7k Books (initial) | Best Books Ever | Goodbooks-10k ext. | CMU Book Summary |
| --- | --- | --- | --- | --- |
| Rôle | Abandonné | Principal | Évaluation | Alternative texte |
| Taille | \~6 800 | 52 478 | 10 000 | 16 559 |
| Description | Texte marketing | Oui (97 %) | Oui (99 %) | Résumé d'intrigue Wikipédia |
| Genres fiables | Non (« Fiction » pour 38 %) | Multiples (91 %) | \~4,7 par livre | Oui |
| Pages | Oui | Oui | Oui | Non |
| Langue | Non | Oui (93 %) | Non | Non |
| Cadre (setting) | Non | Partiel (22 %) | Non | Non |
| Notes utilisateurs | Non | Non | 6 M de notes | Non |

Le pourcentage entre parenthèses est le taux de remplissage (completeness) : la part des livres où la colonne est renseignée.

**Prétraitement :**

1. Garder la fiction, en anglais et en français.
2. Supprimer les livres sans description ou avec moins de \~30 mots, puis dédoublonner (titre + auteur).
3. Normaliser le texte (casse, HTML, espaces) et documenter le nombre de lignes retirées à chaque étape.

**Enrichissement (modèles existants, sans entraînement) :**

| Colonne ajoutée | Méthode |
| --- | --- |
| Genre normalisé | Mapping des genres Goodreads vers la liste fermée du questionnaire |
| Thèmes, style, atmosphère | Classification zero-shot sur des listes fixes |
| Mots-clés | KeyBERT |
| Complexité (1-5) | Indicateur : pages + lisibilité de la description, vérifié sur un échantillon annoté |
| Période | Champ setting quand il existe (22 %), sinon similarité avec la description |
| Âge minimum | Règle sur les genres (Juvenile, Young Adult) |
| Catégorie de longueur | Seuils sur le nombre de pages |

Sources : [Best Books Ever (Zenodo)](https://doi.org/10.5281/zenodo.4265096) · [Goodbooks-10k extended](https://github.com/malcolmosh/goodbooks-10k-extended) · [CMU Book Summary Dataset](https://www.cs.cmu.edu/~dbamman/booksummaries.html) · [7k Books (Kaggle)](https://www.kaggle.com/datasets/dylanjcastillo/7k-books-with-metadata)

## 5. Moteur sémantique

Le moteur utilise un SBERT multilingue pré-entraîné, sans fine-tuning, et le compare à deux baselines pour justifier ce choix. Le multilingue est obligatoire : l'utilisateur écrit en français, la plupart des descriptions sont en anglais.

| Approche | Outil | Rôle |
| --- | --- | --- |
| TF-IDF | scikit-learn | Baseline mots-clés |
| Embeddings statiques | fastText (cc.fr.300) ou Word2Vec entraîné sur les descriptions | Baseline sémantique ; seul « entraînement » du projet, quelques secondes |
| Embeddings contextuels | SBERT multilingue (paraphrase-multilingual-MiniLM-L12-v2 ou multilingual-e5-base) | Modèle retenu |

Pipeline :

1. Prétraiter et normaliser le texte (livres et utilisateur).
2. Encoder les livres une seule fois, hors ligne ; stocker les embeddings (.npy) par champ : description, thèmes, style, atmosphère.
3. À chaque requête, encoder les champs de l'utilisateur.
4. Calculer la similarité cosinus champ par champ.
5. Optionnel : clustering (KMeans) et projection UMAP pour la carte de similarité.

Pourquoi pas d'entraînement : sans données labellisées (« cet utilisateur a aimé ce livre »), un fine-tuning n'a rien à apprendre. Ce qu'on ajuste, ce sont les poids et les seuils du scoring, sur les profils de test (section 7).

## 6. Scoring et explications

Le score d'un livre est une somme pondérée de similarités par critère, moins une pénalité « à éviter », calculée uniquement sur les livres qui passent les filtres.

```latex
S = w_1\,\mathrm{sim}(\text{texte libre}, \text{description}) + w_2\,\mathrm{sim}(\text{thèmes}) + w_3\,\mathrm{sim}(\text{atmosphère}) + w_4\,\mathrm{sim}(\text{style}) + w_5\,\mathrm{genre} + w_6\left(1 - \frac{|c_u - c_l|}{4}\right) + w_7\,\mathrm{sim}(\text{livre aimé}, \text{livre}) - w_8\,\mathrm{sim}(\text{à éviter}, \text{livre})
```

- **Poids :** valeurs par défaut fixées sur les profils de test ; w2, w3 et w4 sont modulés par les réponses Likert d'importance (1-5).
- **Modulation Likert :** chaque poids modulé vaut `w_i × likert_i / 3` (3 = neutre, 1 → × 0,33, 5 → × 1,67). Les trois poids sont ensuite renormalisés pour que w2 + w3 + w4 garde la même somme que les valeurs par défaut : le Likert change la répartition entre thèmes, atmosphère et style, pas l'échelle du score, et le seuil garde le même sens pour tous les utilisateurs.
- **Genre :** 1 si le genre du livre est dans la sélection, sinon similarité entre genres.
- **Complexité :** c\_u et c\_l sur l'échelle 1-5 ; proximité, pas égalité.
- **Livre aimé :** choisi dans le catalogue par autocomplétion ; son embedding pré-calculé est comparé à chaque livre. Si le champ est vide, w7 = 0.
- **Filtres durs :** âge ; livre aimé exclu.
- **Filtres souples :** longueur et période réduisent le score au lieu d'exclure, pour ne pas vider les résultats.
- **Seuil :** un livre sous un score minimum n'est pas recommandé ; si moins de 3 livres passent, l'app le signale.

**Sortie par recommandation :** titre, auteur, couverture, score global, score par critère, mots-clés communs et une explication.

**Explications :** générées par templates à partir des critères qui contribuent le plus, sans IA générative. Exemple : « Recommandé car très proche de vos thèmes (identité, dilemmes moraux, 0,81) et de l'atmosphère mélancolique recherchée. »

La formule et la justification des poids sont documentées dans docs/scoring\_formula.md.

## 7. Évaluation

L'évaluation mesure Precision@3 et nDCG@3 pour TF-IDF, fastText et SBERT. Accuracy, F1 et matrice de confusion ne s'appliquent pas : le template de la consigne vient d'une tâche de classification.

1. **Profils fictifs :** 10 à 15 profils rédigés par l'équipe, chacun avec la liste des livres jugés pertinents (data/eval/test\_profiles.json).
2. **Utilisateurs réels (Goodbooks-10k) :** construire un profil à partir de quelques livres bien notés par un utilisateur, puis vérifier si le top 3 contient d'autres livres qu'il a bien notés.
3. **Réglage :** ajuster les poids et les seuils sur ces mesures, et noter chaque itération (phase « itérer » de la consigne).
4. **Limites à documenter :** négation, biais d'un corpus surtout anglophone et tiré de Goodreads, descriptions marketing, champ setting peu rempli.

Le tableau comparatif des trois approches sert à justifier le choix du modèle dans la présentation.

## 8. Architecture technique

Le back-end suit la **Clean Architecture** (R. C. Martin) : les règles métier et les cas d'usage ne dépendent ni de FastAPI, ni de Pydantic, ni de SBERT, ni des fichiers. Le front JavaScript (React + Vite) ne fait qu'appeler l'API.

| Couche | Contenu | Dépend de |
| --- | --- | --- |
| Domaine | Entités ReaderProfile, Book, ScoringPolicy, Match ; règles d'éligibilité ; métriques de classement | Rien |
| Application | Cas d'usage (RecommendBooks, PrepareCatalog…), modèles Request / Response (dataclasses), ports (Protocol) | Domaine |
| Adapters | Controllers et schémas Pydantic, presenters (phrases d'explication), encodeurs SBERT / fastText / TF-IDF, catalogue Parquet, index .npy, UMAP | Application, domaine |
| Infrastructure (main/) | Composition root : settings, container d'injection, app FastAPI, CLI | Tout, rien n'en dépend |

Le code est rangé par cas d'usage, pas par couche technique : il n'y a pas de dossier core/, api/ ou utils/.

&#91;embedded content: architecture · front, API, moteur, pipeline hors ligne\]

Les livres sont préparés et encodés une seule fois ; à chaque requête, seul le profil de l'utilisateur est encodé.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | /api/options | Listes du questionnaire (genres, thèmes, atmosphères, périodes) |
| GET | /api/books/search?q= | Autocomplétion du champ « Livre aimé » |
| POST | /api/recommend | Profil → top 3, scores par critère, explications, affinité par catégorie, point UMAP de l'utilisateur |
| GET | /api/map | Coordonnées 2D des livres pour la carte de similarité |
| POST | /api/chat | Bonus chatbot |

**Structure du repo :**

```
book-recommender-nlp/
├── README.md
├── docs/                                   # dataset.md, scoring_formula.md, api.md, architecture.md
├── backend/
│   ├── pyproject.toml
│   ├── data/                               # raw/, processed/, embeddings/, eval/
│   ├── notebooks/                          # appellent les cas d'usage, ne recodent pas la logique
│   ├── tests/                              # domaine + cas d'usage avec fakes ; adapters à part
│   └── src/book_recommender/
│       ├── recommendation/
│       │   ├── domain/                     # reader_profile, book, scoring_policy, eligibility, match
│       │   ├── application/                # recommend_books, models (Request/Response), ports
│       │   └── adapters/
│       │       ├── web/                    # recommend_controller, schemas (Pydantic), recommendation_presenter
│       │       ├── sbert_text_encoder.py   # + tfidf_ et fasttext_text_encoder.py
│       │       ├── parquet_book_catalog.py
│       │       ├── numpy_vector_index.py
│       │       └── umap_projector.py
│       ├── preference_options/             # ListPreferenceOptions
│       ├── book_search/                    # SearchBooks (autocomplétion « livre aimé »)
│       ├── catalog_preparation/            # PrepareCatalog (hors ligne) : domain/, application/, adapters/
│       ├── recommender_evaluation/         # EvaluateRecommender : Precision@3, nDCG@3
│       ├── profile_refinement/             # Bonus chatbot : RefineProfile → appelle RecommendBooks
│       └── main/                           # settings, container, web_app (FastAPI), cli
└── frontend/                               # React + Vite, rangé par fonctionnalité
    └── src/
        ├── questionnaire/
        ├── recommendations/                # résultats + graphiques
        ├── how-it-works/
        ├── chat/                           # bonus
        └── api-client/
```

**Règles techniques :**

- **Règle de dépendance :** les imports pointent vers l'intérieur. Le domaine et les cas d'usage n'importent jamais FastAPI, Pydantic, sentence-transformers, pandas ni numpy I/O.
- **Ports :** TextEncoder, BookCatalog, BookVectorIndex et SimilarityMapProjector sont définis dans application/ (Protocol Python) et implémentés dans adapters/. Changer de modèle (TF-IDF → SBERT) revient à changer d'adapter.
- **Modèles simples aux frontières :** les cas d'usage reçoivent et renvoient des dataclasses ; Pydantic reste dans adapters/web/.
- **Configuration :** lue uniquement dans main/settings.py ; les poids sont validés par ScoringPolicy puis injectés.
- **Explications :** le domaine produit des raisons structurées (critère, score, termes communs) ; le presenter les transforme en phrases.
- **Composition :** main/container.py construit les adapters et les injecte ; le modèle SBERT et les embeddings sont chargés une seule fois (lifespan FastAPI).
- **Tests :** domaine et cas d'usage testés avec un FakeTextEncoder et un catalogue en mémoire, sans FastAPI, modèle ni fichiers.
- **Juste mesure :** pas d'interface pour ce qui ne changera pas (les métriques restent des fonctions pures).
- **CORS :** activé dans main/web\_app.py, ou proxy Vite en développement. La carte UMAP est calculée hors ligne ; seul le point de l'utilisateur est projeté à la volée.

## 9. Planning, livrables et risques

Le projet tient en environ 10 à 13 jours de travail. L'ordre critique : données, moteur et scoring d'abord ; l'app ensuite ; le chatbot en dernier. Les durées sont indicatives : la date de rendu reste à fixer.

| Phase | Contenu | Durée indicative | Exigences |
| --- | --- | --- | --- |
| 0. Cadrage | Questionnaire final, schémas Pydantic (contrat API), repo, rôles | ½ jour | 1 |
| 1. Données | Exploration, nettoyage, enrichissement, documentation | 1 à 2 jours | 2 |
| 2. Moteur | TF-IDF, fastText, SBERT ; embeddings pré-calculés | 2 jours | 3 |
| 3. Scoring | Formule, filtres, explications, top 3 | 1 à 2 jours | 4, 5 |
| 4. Évaluation | Profils tests, Precision@3, nDCG@3, réglage des poids | 1 jour | 3, 4 |
| 5. API + front | Endpoints FastAPI, pages React, graphiques | 2 jours | 1, 6 |
| 6. Bonus chatbot | Slot filling branché sur le moteur | 1 à 2 jours | Bonus |
| 7. Livrables | README, docs, slides, répétition de la démo | 1 jour | Livrables |

Le front peut avancer en parallèle dès la phase 0, avec des données fictives conformes aux schémas Pydantic.

**Livrables (Boostcamp) :**

- [ ] Repo : code source fonctionnel, README (installation, données, architecture, formule, résultats), requirements.txt et package.json
- [ ] Documentation : dataset.md, scoring\_formula.md, api.md
- [ ] Support de présentation : problème, données, pipeline, comparaison des modèles, formule, démo, limites

**Risques :**

| Risque | Impact | Parade |
| --- | --- | --- |
| Négation mal comprise par les embeddings | Livres à éviter recommandés | Champ « À éviter » séparé + pénalité + consigne dans l'interface |
| Corpus surtout anglophone | Moins bonne similarité FR → EN | SBERT multilingue ; garder les livres FR du dataset |
| Champ setting rempli à 22 % | Période peu fiable | Bonus quand il existe, sinon similarité avec la description |
| Descriptions marketing | Thèmes bruités | Filtre de longueur ; CMU Book Summary en complément si besoin |
| Modèle rechargé à chaque requête | Réponses de plusieurs secondes | Chargement unique au démarrage de FastAPI |
| Chatbot trop ambitieux | Retard sur le cœur du projet | Le traiter seulement après la phase 5 |
