"""Inspection helpers for the bundled RSM JSON Schema."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from jsonschema.validators import validator_for

_SCHEMA_RESOURCE = "schema/rsm.schema.json"


def _decode_pointer_token(token: str) -> str:
    """Decode a JSON Pointer token.

    Parameters
    ----------
    token
        Encoded JSON Pointer token.

    Returns
    -------
    str
        Decoded token.
    """
    return token.replace("~1", "/").replace("~0", "~")


@dataclass(frozen=True, slots=True)
class SchemaNode:
    """A view onto one node in a JSON Schema document.

    Parameters
    ----------
    schema
        Owning schema document.
    raw
        Raw mapping for this node.
    pointer
        JSON Pointer locating the node in the document.
    name
        Property or definition name, when the node has one.
    required
        Whether the node is required by its parent object.
    """

    schema: Schema
    raw: Mapping[str, Any]
    pointer: str
    name: str | None = None
    required: bool = False

    @property
    def title(self) -> str | None:
        """Return the schema title, if present."""
        value = self.raw.get("title")
        return value if isinstance(value, str) else None

    @property
    def description(self) -> str | None:
        """Return the schema description, if present."""
        value = self.raw.get("description")
        return value if isinstance(value, str) else None

    @property
    def ref(self) -> str | None:
        """Return the `$ref` value, if present."""
        value = self.raw.get("$ref")
        return value if isinstance(value, str) else None

    @property
    def types(self) -> tuple[str, ...]:
        """Return declared JSON Schema types.

        Returns
        -------
        tuple[str, ...]
            Zero, one, or multiple declared types. An empty tuple means the schema does
            not explicitly declare ``type``.
        """
        value = self.raw.get("type")
        if isinstance(value, str):
            return (value,)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(value)
        return ()

    @property
    def properties(self) -> tuple[SchemaNode, ...]:
        """Return direct object properties."""
        properties = self.raw.get("properties", {})
        if not isinstance(properties, Mapping):
            return ()
        required_names = self.raw.get("required", [])
        required = set(required_names) if isinstance(required_names, list) else set()
        return tuple(
            SchemaNode(
                schema=self.schema,
                raw=value,
                pointer=f"{self.pointer}/properties/{self.schema.encode_pointer_token(name)}",
                name=name,
                required=name in required,
            )
            for name, value in properties.items()
            if isinstance(name, str) and isinstance(value, Mapping)
        )

    @property
    def items(self) -> SchemaNode | None:
        """Return the array item schema, when it is a single schema object."""
        value = self.raw.get("items")
        if not isinstance(value, Mapping):
            return None
        return SchemaNode(self.schema, value, f"{self.pointer}/items")

    def resolve(self) -> SchemaNode:
        """Resolve a local ``$ref`` or return this node unchanged.

        Returns
        -------
        SchemaNode
            Referenced node for local JSON Pointer references.

        Raises
        ------
        ValueError
            If the reference is external. External reference resolution is deliberately
            not hidden behind network I/O in this package.
        KeyError
            If a local reference cannot be resolved.
        """
        if self.ref is None:
            return self
        if not self.ref.startswith("#"):
            raise ValueError(f"External $ref is not supported by resolve(): {self.ref}")
        return self.schema.at(self.ref[1:] or "/")


class Schema:
    """Loaded JSON Schema document with lightweight traversal helpers."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        self._document = dict(document)

    @classmethod
    def bundled(cls) -> Schema:
        """Load the schema bundled with the installed package.

        Returns
        -------
        Schema
            Bundled RSM schema.
        """
        resource = files("rsm_schema").joinpath(_SCHEMA_RESOURCE)
        with resource.open("r", encoding="utf-8") as stream:
            document = json.load(stream)
        if not isinstance(document, dict):
            raise TypeError("The bundled schema root must be a JSON object.")
        return cls(document)

    @staticmethod
    def encode_pointer_token(token: str) -> str:
        """Encode one JSON Pointer token."""
        return token.replace("~", "~0").replace("/", "~1")

    @property
    def raw(self) -> Mapping[str, Any]:
        """Return the raw schema document as a mapping."""
        return self._document

    @property
    def root(self) -> SchemaNode:
        """Return the root schema node."""
        return SchemaNode(self, self._document, "")

    @property
    def title(self) -> str | None:
        """Return the document title, if present."""
        return self.root.title

    def validate_schema(self) -> None:
        """Validate the schema against the declared JSON Schema meta-schema.

        Raises
        ------
        jsonschema.exceptions.SchemaError
            If the schema itself is invalid.
        """
        validator = validator_for(self._document)
        validator.check_schema(self._document)

    def validate_document(self, document: Mapping[str, Any]) -> None:
        """Validate an RSM document against this JSON Schema.

        Unlike validation through the generated Pydantic model, this enforces
        composition and conditional keywords such as the requirement that a
        non-empty contributor list credit at least one author.

        Parameters
        ----------
        document
            JSON-compatible RSM document.

        Raises
        ------
        jsonschema.exceptions.ValidationError
            If the document does not conform to the schema.
        """
        validator = validator_for(self._document)
        validator(self._document).validate(document)

    def at(self, pointer: str) -> SchemaNode:
        """Return the node at a JSON Pointer.

        Parameters
        ----------
        pointer
            JSON Pointer such as ``/$defs/person`` or ``#/properties/project_slug``.

        Returns
        -------
        SchemaNode
            Located schema node.
        """
        normalized = pointer[1:] if pointer.startswith("#") else pointer
        if normalized in ("", "/"):
            return self.root
        if not normalized.startswith("/"):
            raise ValueError(f"Not a JSON Pointer: {pointer}")

        current: Any = self._document
        for encoded_token in normalized.lstrip("/").split("/"):
            token = _decode_pointer_token(encoded_token)
            if isinstance(current, Mapping):
                current = current[token]
            elif isinstance(current, list):
                current = current[int(token)]
            else:
                raise KeyError(pointer)

        if not isinstance(current, Mapping):
            raise TypeError(f"JSON Pointer does not identify a schema object: {pointer}")
        return SchemaNode(self, current, normalized)

    def definition(self, name: str) -> SchemaNode:
        """Return a named schema definition from ``$defs`` or ``definitions``.

        Parameters
        ----------
        name
            Definition name.

        Returns
        -------
        SchemaNode
            Definition node.
        """
        for keyword in ("$defs", "definitions"):
            definitions = self._document.get(keyword)
            if isinstance(definitions, Mapping) and name in definitions:
                raw = definitions[name]
                if isinstance(raw, Mapping):
                    return SchemaNode(
                        self,
                        raw,
                        f"/{keyword}/{self.encode_pointer_token(name)}",
                        name=name,
                    )
        raise KeyError(name)

    def walk(self, start: SchemaNode | None = None) -> Iterator[SchemaNode]:
        """Depth-first traversal over structural child schemas.

        Parameters
        ----------
        start
            Node to start from. Defaults to the document root.

        Yields
        ------
        SchemaNode
            Each reachable schema node once per structural location. References are not
            followed automatically, which prevents recursive schemas from looping.
        """
        node = start or self.root
        yield node

        for child in node.properties:
            yield from self.walk(child)

        for keyword in ("$defs", "definitions"):
            definitions = node.raw.get(keyword)
            if isinstance(definitions, Mapping):
                for name, raw in definitions.items():
                    if isinstance(name, str) and isinstance(raw, Mapping):
                        child = SchemaNode(
                            self,
                            raw,
                            f"{node.pointer}/{keyword}/{self.encode_pointer_token(name)}",
                            name=name,
                        )
                        yield from self.walk(child)

        items = node.items
        if items is not None:
            yield from self.walk(items)

        for keyword in ("oneOf", "anyOf", "allOf"):
            values = node.raw.get(keyword)
            if isinstance(values, list):
                for index, raw in enumerate(values):
                    if isinstance(raw, Mapping):
                        yield from self.walk(
                            SchemaNode(self, raw, f"{node.pointer}/{keyword}/{index}")
                        )
