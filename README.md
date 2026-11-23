# Book Recommender NLP

Web app qui recommande les 3 livres les plus adaptés aux préférences littéraires d'un utilisateur, par similarité sémantique (SBERT multilingue) et scoring pondéré, avec des explications transparentes.

- Cahier des charges : [SPEC.md](SPEC.md)
- Découpage des tâches : [Backlog.md](Backlog.md) · suivi : [TASK.md](TASK.md)

## Structure

```
docs/       documentation (dataset, formule de scoring, API, architecture)
backend/    Python : FastAPI, pipeline de données, moteur de recommandation
frontend/   React + Vite
```

Le back-end suit la Clean Architecture et est rangé par cas d'usage (`backend/src/book_recommender/`).

## Installation (back-end)

Avec [uv](https://docs.astral.sh/uv/) :

```bash
cd backend
uv sync                 # cœur + outils de dev
uv sync --extra nlp     # + modèles NLP (torch CPU en local)
uv run pytest
```

Avec pip (ex. Colab, GPU) :

```bash
pip install -e "backend[nlp]"
```

## Données

Le dataset [Best Books Ever](https://doi.org/10.5281/zenodo.4265096) va dans `backend/data/raw/` (non versionné). Les listes du questionnaire sont dans [backend/data/options.json](backend/data/options.json).
