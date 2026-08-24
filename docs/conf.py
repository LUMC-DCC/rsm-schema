"""Sphinx configuration.

The prose is Markdown so it stays readable on GitHub; MyST renders it here
without a second source format. The API reference comes from the docstrings,
so nothing is written twice.

Build it with::

    poetry install --with docs
    poetry run sphinx-build -b html docs docs/_build/html
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from packaging.version import Version

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rsm_schema import __version__

project = "rsm-schema"
author = "Mariia Steeghs-Turchina"
copyright = f"{date.today().year}, Leiden University Medical Center"
release = __version__
version = __version__

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
]

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
exclude_patterns = ["_build"]

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3
# Mermaid diagrams are written as ```mermaid fences in the Markdown, which
# GitHub renders natively. This makes Sphinx render the same source.
myst_fence_as_directive = ["mermaid"]

html_theme = "sphinx_book_theme"
html_title = f"{project} {release}"
html_static_path: list[str] = []

# Every released schema is republished on every deploy. GitHub Pages replaces the
# whole site each time, so a version that stops being copied here stops resolving,
# and any `$ref` pinned to it breaks. `schema-archive/` is therefore the record of
# what has been published: one immutable directory per release, nothing ever
# removed. `_extra` is gitignored for the same reason `_build` is.
_ROOT = Path(__file__).resolve().parents[1]
_PACKAGED_SCHEMA = _ROOT / "src" / "rsm_schema" / "schema" / "rsm.schema.json"
_ARCHIVE = _ROOT / "schema-archive"
_EXTRA = Path(__file__).parent / "_extra"

_versions = sorted(
    (entry.name for entry in _ARCHIVE.iterdir() if entry.is_dir()),
    key=Version,
    reverse=True,
)

# The archive holds the current release as well as the older ones, so that
# "this release archived itself" is a condition rather than a habit. Failing
# here stops a deploy that would publish a version nobody can fetch later.
if release not in _versions:
    msg = (
        f"schema-archive/{release}/ is missing. Copy "
        f"src/rsm_schema/schema/rsm.schema.json into it before releasing {release}."
    )
    raise RuntimeError(msg)
if (_ARCHIVE / release / "rsm.schema.json").read_bytes() != _PACKAGED_SCHEMA.read_bytes():
    msg = (
        f"schema-archive/{release}/rsm.schema.json differs from the packaged schema. "
        "An archived version is immutable, so either re-copy the packaged schema "
        "into the archive, or bump the version and archive that instead."
    )
    raise RuntimeError(msg)


# These pages sit outside the Sphinx theme, so they carry just enough style to be
# readable on their own.
_PAGE_STYLE = "font-family: system-ui, sans-serif; max-width: 44rem; margin: 2rem auto"


def _write_page(destination: Path, title: str, body: str) -> None:
    """Write one plain HTML page outside the Sphinx theme."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title></head>
<body style="{_PAGE_STYLE}; padding: 0 1rem;">
{body}
</body></html>
""",
        encoding="utf-8",
    )


_version_rows = []
for _version in _versions:
    _destination = _EXTRA / "schema" / _version
    _destination.mkdir(parents=True, exist_ok=True)
    _names = []
    for _schema in sorted((_ARCHIVE / _version).glob("*.json")):
        (_destination / _schema.name).write_bytes(_schema.read_bytes())
        _names.append(_schema.name)

    _files = "\n".join(f'    <li><a href="{name}"><code>{name}</code></a></li>' for name in _names)
    _current = " (current release)" if _version == release else ""
    _version_rows.append(f'    <li><a href="{_version}/">{_version}</a>{_current}</li>')
    _write_page(
        _destination / "index.html",
        f"rsm-schema {_version}",
        f"""  <h1>rsm-schema schema, version {_version}</h1>
  <p>Each file is served at the URL its own <code>$id</code> declares, so a
  <code>$ref</code> written against it resolves. This path is immutable: a later
  release publishes a new path rather than replacing this one.</p>
  <ul>
{_files}
  </ul>
  <p><a href="../">All versions</a> &middot; <a href="../../">Documentation</a></p>""",
    )

_write_page(
    _EXTRA / "schema" / "index.html",
    "rsm-schema published schemas",
    f"""  <h1>rsm-schema published schemas</h1>
  <p>Every released version stays published at its own path, newest first. Pin a
  <code>$ref</code> to a specific version; there is deliberately no
  <code>latest</code> alias, because a reference that changes underneath you is
  not a reference.</p>
  <ul>
{chr(10).join(_version_rows)}
  </ul>
  <p><a href="../">Documentation</a></p>""",
)

# Sphinx writes into `_static` and `_sources`. GitHub Pages does not run
# Jekyll for artifact-based deployments, but a leading underscore is exactly
# what Jekyll strips, so this costs nothing and removes the failure mode.
(_EXTRA / ".nojekyll").write_text("", encoding="utf-8")

html_extra_path = ["_extra"]
html_theme_options = {
    "repository_url": "https://github.com/LUMC-DCC/rsm-schema",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "use_source_button": True,
    "home_page_in_toc": True,
    "show_toc_level": 2,
    "navigation_with_keys": False,
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_rtype = False
napoleon_use_ivar = True

# docs/api.md documents whole modules rather than named classes, so the reference
# follows `rsm_schema.generated.__all__` and the inspector's own contents. Adding a
# `$defs` entity and exporting it is enough to document it.
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
