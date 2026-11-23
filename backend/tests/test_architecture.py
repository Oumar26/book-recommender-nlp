"""Règle de dépendance de la Clean Architecture (SPEC, section 8).

- domain/ et application/ n'importent aucune bibliothèque d'infrastructure ;
- les imports pointent vers l'intérieur : domain ← application ← adapters ← main ;
- rien n'importe main/ (composition root), sauf main/ lui-même.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "book_recommender"
PACKAGE = "book_recommender"

FORBIDDEN_IN_CORE = frozenset(
    {
        "fastapi",
        "starlette",
        "uvicorn",
        "pydantic",
        "sentence_transformers",
        "transformers",
        "torch",
        "keybert",
        "gensim",
        "sklearn",
        "umap",
        "pandas",
        "pyarrow",
    }
)


def module_name(path: Path, root: Path = PACKAGE_ROOT) -> str:
    parts = list(path.relative_to(root.parent).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imported_modules(path: Path, root: Path = PACKAGE_ROOT) -> set[str]:
    """Noms absolus des modules importés par un fichier (imports relatifs résolus)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    current = module_name(path, root)
    is_package = path.name == "__init__.py"
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
            else:
                anchor = current.split(".")
                drop = node.level - 1 if is_package else node.level
                anchor = anchor[: len(anchor) - drop]
                base = ".".join(anchor + ([node.module] if node.module else []))
            found.add(base)
            found.update(f"{base}.{alias.name}" for alias in node.names)
    return found


def layer_of(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == PACKAGE and parts[1] == "main":
        return "main"
    for layer in ("domain", "application", "adapters"):
        if layer in parts[2:]:
            return layer
    return None


ALLOWED_INNER = {
    "domain": {"domain"},
    "application": {"domain", "application"},
    "adapters": {"domain", "application", "adapters"},
}


def violations(path: Path, root: Path = PACKAGE_ROOT) -> list[str]:
    own_layer = layer_of(module_name(path, root))
    problems: list[str] = []
    for mod in imported_modules(path, root):
        top = mod.split(".")[0]
        if own_layer in {"domain", "application"} and top in FORBIDDEN_IN_CORE:
            problems.append(f"{own_layer} importe {mod}")
        if top != PACKAGE:
            continue
        target = layer_of(mod)
        if target == "main" and own_layer != "main":
            problems.append(f"{own_layer or 'module'} importe main ({mod})")
        elif own_layer in ALLOWED_INNER and target and target not in ALLOWED_INNER[own_layer]:
            problems.append(f"{own_layer} importe la couche {target} ({mod})")
    return problems


SOURCE_FILES = sorted(PACKAGE_ROOT.rglob("*.py"))


def test_core_layers_exist() -> None:
    """Évite un test vide : le scan doit trouver les couches du squelette."""
    layers = {layer_of(module_name(p)) for p in SOURCE_FILES}
    assert {"domain", "application", "adapters", "main"} <= layers


@pytest.mark.parametrize("path", SOURCE_FILES, ids=lambda p: str(p.relative_to(PACKAGE_ROOT)))
def test_dependency_rule(path: Path) -> None:
    assert violations(path) == []


# --- Le vérificateur lui-même détecte bien les violations -------------------


def _write(root: Path, rel: str, code: str) -> Path:
    path = root / PACKAGE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("rel", "code", "expected"),
    [
        ("feature/domain/x.py", "import pandas as pd\n", "domain importe pandas"),
        ("feature/application/x.py", "from pydantic import BaseModel\n", "importe pydantic"),
        ("feature/domain/x.py", "from ..adapters import repo\n", "couche adapters"),
        ("feature/application/x.py", "from book_recommender.main import x\n", "importe main"),
        ("feature/adapters/x.py", "from ...main.container import build\n", "adapters importe main"),
    ],
)
def test_checker_detects_violations(tmp_path: Path, rel: str, code: str, expected: str) -> None:
    root = tmp_path / PACKAGE
    path = _write(tmp_path, rel, code)
    assert any(expected in v for v in violations(path, root))


def test_checker_accepts_inward_imports(tmp_path: Path) -> None:
    root = tmp_path / PACKAGE
    path = _write(tmp_path, "feature/application/x.py", "import numpy\nfrom ..domain import book\n")
    assert violations(path, root) == []
