"""Tests for the published schema archive.

Every released version stays served at its own URL, which only works if every
release is archived and never edited afterwards. These tests make both of those
properties fail loudly in CI rather than quietly on the live site.
"""

import json
from pathlib import Path

import pytest

from rsm_schema import __version__

_ROOT = Path(__file__).resolve().parents[1]
_ARCHIVE = _ROOT / "schema-archive"
_PACKAGED_SCHEMA = _ROOT / "src" / "rsm_schema" / "schema" / "rsm.schema.json"
_BASE_URL = "https://lumc-dcc.github.io/rsm-schema/schema"


def _archived_versions() -> list[str]:
    """Return the version directories present in the archive."""
    return sorted(entry.name for entry in _ARCHIVE.iterdir() if entry.is_dir())


def test_current_release_is_archived() -> None:
    """The release being built must be in the archive, byte for byte.

    The archive is what the docs build republishes. A release that is not in it
    is served once and then disappears at the next deploy.
    """
    archived = _ARCHIVE / __version__ / "rsm.schema.json"

    assert archived.is_file(), (
        f"schema-archive/{__version__}/ is missing. Copy the packaged schema into it."
    )
    assert archived.read_bytes() == _PACKAGED_SCHEMA.read_bytes(), (
        f"schema-archive/{__version__}/rsm.schema.json differs from the packaged schema."
    )


@pytest.mark.parametrize("version", _archived_versions())
def test_archived_schema_declares_its_own_url(version: str) -> None:
    """Each archived schema's ``$id`` must name the path it is published at."""
    document = json.loads((_ARCHIVE / version / "rsm.schema.json").read_text(encoding="utf-8"))

    assert document["$id"] == f"{_BASE_URL}/{version}/rsm.schema.json"
