import shutil
from pathlib import Path

import pytest

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus"


@pytest.fixture()
def corpus_dir() -> Path:
    """The read-only fixture corpus (~10 tiny .md files)."""
    return FIXTURE_CORPUS


@pytest.fixture()
def tmp_corpus(tmp_path) -> Path:
    """A writable copy of the fixture corpus."""
    dst = tmp_path / "corpus"
    shutil.copytree(FIXTURE_CORPUS, dst)
    return dst


@pytest.fixture()
def db_path(tmp_path) -> Path:
    return tmp_path / "index.db"
