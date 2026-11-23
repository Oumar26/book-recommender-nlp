# Jeu de données

Ce document décrit l'origine du catalogue de livres, sa structure, le prétraitement appliqué et ses limites. Tous les chiffres sont reproductibles avec les commandes de la section « Reproduire ».

> **Statut :** nettoyage et enrichissements par règles terminés. La section « Enrichissements NLP » sera complétée après le passage sur GPU (Colab).

## 1. Sources

| Dataset | Rôle | Taille | Licence / source |
| --- | --- | --- | --- |
| **Best Books Ever** (Goodreads, 2020) | Catalogue principal | 52 478 livres, 25 colonnes | [Zenodo 4265096](https://doi.org/10.5281/zenodo.4265096) |
| **Goodbooks-10k extended** | Évaluation (phase 4) : notes réelles de lecteurs | 10 000 livres, 6 M de notes | [GitHub](https://github.com/malcolmosh/goodbooks-10k-extended) |

Best Books Ever a été retenu parce qu'il couvre le plus de champs du questionnaire : description (97 %), genres multiples (91 %), langue (93 %), pages (96 %). Les jeux écartés et la comparaison complète figurent dans la [SPEC](../SPEC.md), section 4.

## 2. Ce que l'exploration a montré

Détails et graphiques : [notebooks/01_exploration.ipynb](../backend/notebooks/01_exploration.ipynb).

| Constat | Conséquence |
| --- | --- |
| Le tag « Fiction » n'est présent que sur 60 % des livres, jamais avec « Nonfiction » | La fiction est détectée par plusieurs tags (Fiction, Fantasy, Romance, Mystery…), en excluant « Nonfiction » |
| Langue absente pour 7,3 % des livres | Ces livres sont retirés (pas de détection automatique) |
| Descriptions : médiane 130 mots, 6,4 % sous 30 mots | Seuil à 30 mots ; argument pour un encodeur qui lit 512 tokens (e5-base) plutôt que 128 (MiniLM) |
| Pas de HTML, mais des phrases collées (« FORTUNE.LOSING ») | Espace ajouté après la ponctuation |
| `setting` rempli à 22 %, et **uniquement des lieux** (0 année, 0 siècle) | La période ne peut pas venir de ce champ : elle est déduite de la description par zero-shot |
| `firstPublishDate` au format MM/JJ/AA (siècle perdu) | Année reconstruite à partir de l'année de l'édition (voir limites) |
| Auteurs avec rôles : « Charlotte Brontë, Michael Mason (Editor) » | Auteur principal extrait |
| 54 `bookId` en double, 88 couples titre + auteur en double | Dédoublonnage sur les deux |

## 3. Prétraitement

Cas d'usage `PrepareCatalog` (`backend/src/book_recommender/catalog_preparation/`). Les règles sont des fonctions pures testées ; leurs paramètres sont dans [options.json](../backend/data/options.json) (`catalog_filters`, `catalog_exclusions`).

| Étape | Règle | Retirés | Restants |
| --- | --- | ---: | ---: |
| Entrée | | | 52 478 |
| Identifiant en double | même `bookId` : on garde la première ligne | 54 | 52 424 |
| Langue | anglais ou français uniquement | 9 216 | 43 208 |
| Fiction | au moins un tag de fiction, aucun tag « Nonfiction » | 11 002 | 32 206 |
| Formats exclus | romans graphiques / BD / manga et poésie (tag dans les 3 premiers) ; erotica (tag n'importe où) | 3 729 | 28 477 |
| Description | normalisée, puis au moins 30 mots | 923 | 27 554 |
| Doublon titre + auteur | clé sans casse, accents ni ponctuation ; on garde l'édition la plus notée | 29 | **27 525** |

Le détail des exclusions de formats : erotica 1 871, romans graphiques 1 401, poésie 462.

**Normalisation du texte :** entités et balises HTML, phrases collées, espaces multiples. **La casse est conservée** : les modèles (SBERT, NLI) y sont sensibles ; TF-IDF met lui-même en minuscules.

## 4. Catalogue obtenu

27 525 livres, dont **27 165 en anglais et 360 en français**.

### Colonnes

| Colonne | Type | Origine |
| --- | --- | --- |
| `book_id` | str | `bookId` |
| `title`, `description` | str | normalisés |
| `author` | str | auteur principal, sans les rôles |
| `language` | str | `en` ou `fr` |
| `genre_tags` | list[str] | tags Goodreads d'origine, par votes décroissants |
| `genres` | list[str] | **genres normalisés** (10 genres du questionnaire), dans l'ordre des tags |
| `min_age` | int | **âge minimum** : 0 (Childrens, Middle Grade, Juvenile), 13 (Young Adult, Teen), 18 sinon ; plusieurs tags → le plus bas |
| `pages` | int \| null | `pages` ; valeurs < 10 ou > 5 000 considérées comme inconnues |
| `length_category` | str \| null | **longueur** : court (< 200), moyen (200-400), long (> 400) |
| `year` | int \| null | année de première publication reconstruite |
| `series` | str \| null | série (sert au filtre « pas de série ») |
| `cover_url`, `rating`, `num_ratings` | | métadonnées d'affichage |
| `themes`, `atmospheres`, `narrative_styles`, `period`, `keywords` | | **enrichissements NLP**, voir section 5 |
| `theme_scores`, `atmosphere_scores`, `narrative_style_scores`, `period_scores` | list[float] | probabilité NLI de chaque étiquette, dans l'ordre d'options.json |

### Répartition

| Genre normalisé | Livres | Part |
| --- | ---: | ---: |
| Fantasy | 12 523 | 45 % |
| Romance | 11 679 | 42 % |
| Littérature contemporaine | 11 146 | 40 % |
| Policier / thriller | 7 496 | 27 % |
| Historique | 7 182 | 26 % |
| Science-fiction | 5 854 | 21 % |
| Aventure | 5 481 | 20 % |
| Classiques | 4 089 | 15 % |
| Humour | 2 565 | 9 % |
| Horreur | 2 252 | 8 % |

Un livre a en moyenne 2,55 genres normalisés ; 387 livres (1,4 %) n'en ont aucun.

| Âge minimum | Livres | | Longueur | Livres |
| --- | ---: | --- | --- | ---: |
| 0 | 3 958 | | court | 3 697 |
| 13 | 6 365 | | moyen | 16 142 |
| 18 | 17 202 | | long | 6 967 |
| | | | inconnue | 719 |

59 % des livres appartiennent à une série.

## 5. Enrichissements NLP

Cas d'usage `EnrichCatalog`, exécuté sur GPU avec [notebooks/02_colab_enrichment.ipynb](../backend/notebooks/02_colab_enrichment.ipynb).

| Colonne | Méthode |
| --- | --- |
| Thèmes (16), atmosphères (10), styles narratifs (7), période (9) | **Zero-shot NLI** : pour chaque étiquette, le modèle juge si la description implique une hypothèse (« This story is about betrayal. »). Modèle : `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` (multilingue). Chaque étiquette est jugée indépendamment : probabilité = softmax(entailment, contradiction). On retient les étiquettes au-dessus d'un seuil, au plus 3 thèmes, 2 atmosphères, 2 styles, 1 période. |
| Mots-clés | **KeyBERT** (`all-MiniLM-L6-v2`) : 8 expressions de 1 à 2 mots, diversifiées (MMR). |

Les scores bruts sont conservés : les seuils (dans `options.json`, section `enrichment`) peuvent être recalibrés sans relancer le GPU.

*À compléter après le passage complet : durée, répartition des étiquettes, part des livres sans étiquette, exemples, seuils retenus.*

## 6. Limites

- **Corpus quasi anglophone** (98,7 %) et tiré de Goodreads : biais vers les livres populaires anglo-saxons, publiés surtout aux XXe et XXIe siècles. L'utilisateur écrit en français : le modèle d'embeddings doit être multilingue, et les livres recommandés seront souvent en VO.
- **Descriptions marketing** : ce sont des quatrièmes de couverture, pas des résumés. Thèmes, style et atmosphère sont déduits d'un texte écrit pour vendre ; le style narratif, en particulier, y apparaît rarement.
- **Période** : déduite uniquement de la description (le champ `setting` ne donne que des lieux). Elle sert donc de filtre souple, jamais excluant.
- **Année** : `firstPublishDate` n'a que deux chiffres. L'année est la plus récente qui ne dépasse pas l'édition ; un classique peut être décalé d'un siècle (Jane Eyre, 1847, apparaît en 1947). Elle ne sert qu'à l'affichage.
- **Tags Goodreads** : attribués par les lecteurs, parfois approximatifs. Les exclusions par tag ont des effets de bord voulus mais à connaître : la poésie retire aussi des épopées en vers (L'Odyssée, La Divine Comédie) ; l'erotica retire aussi de la romance paranormale très explicite.
- **Âge minimum** : déduit des tags uniquement ; un livre pour adultes sans tag d'âge vaut 18, un livre jeunesse mal tagué peut aussi valoir 18 (filtre prudent).
- **Complexité de lecture** : non représentée. Le critère a été retiré faute de donnée fiable pour le mesurer (seule la lisibilité du résumé marketing était disponible).

## 7. Reproduire

```bash
cd backend
uv run book-recommender download          # datasets → data/raw/
uv run book-recommender prepare-catalog   # → data/processed/books_clean.parquet + preparation_report.json
uv run book-recommender enrich-catalog    # GPU conseillé (Colab) → data/processed/books.parquet
```
