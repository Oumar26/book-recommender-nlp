# API – brouillon (P0-06)

Contrat entre le front React et le back-end FastAPI. La source de vérité est le code des schémas : [schemas.py](../backend/src/book_recommender/recommendation/adapters/web/schemas.py). Une fois l'API lancée, la documentation interactive est sur `/docs` (OpenAPI).

- Préfixe : `/api` ; JSON en UTF-8 ; clés en `snake_case`.
- Les identifiants d'options (genres, thèmes…) sont ceux de [options.json](../backend/data/options.json). Un identifiant inconnu renvoie `422`.
- Les données fictives conformes à ce contrat sont dans [frontend/src/api-client/mocks/](../frontend/src/api-client/mocks/). Un test vérifie qu'elles respectent les schémas.

| Méthode | Route | Rôle | Statut |
| --- | --- | --- | --- |
| GET | `/api/options` | Listes du questionnaire | contrat figé |
| GET | `/api/books/search?q=` | Autocomplétion du « livre aimé » | contrat figé |
| POST | `/api/recommend` | Profil → top 3 expliqué | contrat figé |
| GET | `/api/map` | Coordonnées 2D des livres (carte UMAP) | contrat figé, optionnel (P2-12) |
| POST | `/api/chat` | Bonus chatbot | à définir (phase 6) |

## GET /api/options

Renvoie les listes fermées du questionnaire, avec un `id` (envoyé à l'API) et un `label` (affiché).

```json
{
  "genres": [{"id": "fantasy", "label": "Fantasy"}, "…"],
  "themes": ["…"], "atmospheres": ["…"], "narrative_styles": ["…"],
  "periods": [{"id": "any", "label": "indifférent"}, "…"],
  "avoid_quick_options": ["…"], "length_categories": ["…"],
  "description_min_words": 20
}
```

## GET /api/books/search?q=

- `q` : au moins 2 caractères ; recherche sur le titre (et l'auteur).
- `limit` : facultatif, 10 par défaut.

```json
{"results": [{"id": "17899948-rebecca", "title": "Rebecca", "author": "Daphne du Maurier", "year": 1938, "cover_url": "https://…"}]}
```

## POST /api/recommend

### Requête

| Champ | Type | Défaut | Contrainte / rôle |
| --- | --- | --- | --- |
| `description` | str | requis | ≥ 20 mots ; ce que le lecteur aime |
| `liked_book_id` | str \| null | null | id de `/api/books/search` ; terme w6, exclu des résultats |
| `genres` | list[id] | [] | match avec le genre normalisé |
| `themes` | list[id] | [] | similarité avec les thèmes |
| `other_themes` | str | "" | champ « autre » des thèmes, ≤ 300 car. |
| `atmospheres` | list[id] | [] | similarité |
| `period` | id | "any" | filtre souple |
| `narrative_styles` | list[id] | [] | similarité avec le style |
| `importance_themes` | int 1-5 | 3 | module w2 |
| `importance_style` | int 1-5 | 3 | module w4 |
| `importance_atmosphere` | int 1-5 | 3 | module w3 |
| `avoid_text` | str | "" | pénalité ; sans négation, ≤ 500 car. |
| `avoid_options` | list[id] | [] | cases rapides « à éviter » |
| `age` | int 1-120 | requis | filtre dur |
| `length` | id | "any" | filtre souple |
| `no_series` | bool | false | exclut les livres d'une série |

Les champs inconnus sont refusés (`422`). Les doublons dans les listes sont retirés. Exemple complet : [recommend_request.json](../frontend/src/api-client/mocks/recommend_request.json).

### Réponse

```json
{
  "recommendations": [
    {
      "rank": 1,
      "book": {"id": "10210.Jane_Eyre", "title": "Jane Eyre", "author": "Charlotte Brontë", "cover_url": "…", "pages": 532, "year": 1847, "genres": ["classics", "romance", "historical"]},
      "score": 0.7075,
      "criteria": [
        {"criterion": "themes", "similarity": 0.81, "weight": 0.15, "contribution": 0.1215, "matched_terms": ["identité", "amour"]},
        "… un objet par critère : description, themes, atmosphere, style, genre, liked_book, avoid"
      ],
      "soft_filters": [{"filter": "period", "matched": true, "factor": 1.0}],
      "shared_keywords": ["governess", "secret"],
      "explanation": "Recommandé car très proche du livre que vous avez aimé (0,83)…"
    }
  ],
  "category_affinity": {
    "criteria": [{"key": "themes", "label": "Thèmes", "value": 0.673}],
    "genres": [{"key": "classics", "label": "Classiques", "value": 0.82}]
  },
  "user_map_point": {"x": 1.2, "y": -0.8},
  "warning": null
}
```

- `criteria[].contribution` = `weight × similarity`, négative pour `avoid`. `score` = somme des contributions × facteurs des `soft_filters`.
- `weight` est le poids effectif, après modulation Likert.
- `warning` est renseigné quand moins de 3 livres passent le seuil ; `recommendations` contient alors 0 à 2 livres.
- `user_map_point` vaut `null` si la carte UMAP n'est pas disponible.

## GET /api/map

```json
{"points": [{"book_id": "2767052-the-hunger-games", "title": "The Hunger Games", "x": 3.1, "y": -2.4, "genre": "fantasy", "cluster": 0}]}
```

## Erreurs

| Code | Cas |
| --- | --- |
| 422 | Corps invalide (format FastAPI), id d'option inconnu, `liked_book_id` introuvable |
| 503 | Modèle ou embeddings pas encore chargés |

## Points ouverts

- Les poids des mocks sont hypothétiques ; les valeurs par défaut seront fixées en phase 3 puis réglées en phase 4.
- Facteur des filtres souples (0,9 dans les mocks) : à trancher en P3-07.
