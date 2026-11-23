from pathlib import Path

import pytest

from book_recommender.main.settings import DEFAULT_SBERT_MODEL, Settings


def test_defaults_point_to_backend_data() -> None:
    settings = Settings.from_env({})
    assert settings.data_dir.name == "data"
    assert settings.options_path.is_file()
    assert settings.device == "cpu"
    assert settings.sbert_model == DEFAULT_SBERT_MODEL


def test_environment_overrides(tmp_path: Path) -> None:
    settings = Settings.from_env(
        {"BOOKREC_DATA_DIR": str(tmp_path), "BOOKREC_DEVICE": "cuda", "BOOKREC_SBERT_MODEL": "m"}
    )
    assert settings.embeddings_dir == tmp_path / "embeddings"
    assert settings.device == "cuda"
    assert settings.sbert_model == "m"


def test_unknown_device_is_rejected() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"BOOKREC_DEVICE": "gpu"})
