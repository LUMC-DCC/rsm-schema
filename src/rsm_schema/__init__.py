"""RSM JSON Schema, generated Pydantic models, and inspection helpers."""

from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from rsm_schema.generated import RSMMetadata
from rsm_schema.inspector import Schema, SchemaNode

try:
    __version__ = version("rsm-schema")
except PackageNotFoundError:  # pragma: no cover - source tree without an install
    __version__ = "0.0.0"

schema = Schema.bundled()
"""The bundled RSM JSON Schema, loaded once at import."""


def validate_document(document: Mapping[str, Any]) -> None:
    """Validate a complete RSM document against the canonical JSON Schema.

    This is the authoritative validation path when callers need conditional
    JSON Schema rules that generated Pydantic models cannot express.
    """
    schema.validate_document(document)


__all__ = [
    "RSMMetadata",
    "Schema",
    "SchemaNode",
    "__version__",
    "schema",
    "validate_document",
]
