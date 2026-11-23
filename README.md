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

## Préparation des données

```bash
cd backend
uv run book-recommender download          # datasets → data/raw/
uv run book-recommender prepare-catalog   # → data/processed/books_clean.parquet + preparation_report.json
```

## Conventions

Projet mené seul : pas de répartition des rôles.

- **Branches :** `master` reste stable ; une branche par tâche ou groupe de tâches (`p1-nettoyage`, `p2-sbert`…), fusionnée quand elle est terminée.
- **Commits :** en français, à l'impératif, avec l'identifiant de tâche quand il existe (« Ajoute les règles de nettoyage (P1-03) »).
- **Terminé =** les tests passent (`uv run pytest`), `uv run ruff check .` ne signale rien, la doc concernée est à jour et [TASK.md](TASK.md) est mis à jour.
