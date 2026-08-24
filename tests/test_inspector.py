"""Tests for schema inspection."""

import pytest
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from jsonschema.validators import validator_for

from rsm_schema import Schema, __version__, schema, validate_document


def test_bundled_schema_is_valid() -> None:
    """The bundled schema should be a valid JSON Schema document."""
    schema.validate_schema()


def test_root_properties_expose_required_state() -> None:
    """Inspection should expose field names and required state."""
    fields = {field.name: field for field in schema.root.properties}

    assert fields["project_slug"].types == ("string",)
    assert fields["project_slug"].required is True
    assert fields["project_name"].types == ("string",)
    assert fields["project_name"].required is False


def test_local_ref_resolution() -> None:
    """Local JSON Pointer references should resolve."""
    item = schema.at("/properties/contributors/properties/entries").items

    assert item is not None
    assert item.ref == "#/$defs/contributor"
    assert item.resolve().pointer == "/$defs/contributor"


def test_definition_lookup() -> None:
    """Named definitions should be reachable by name."""
    person = schema.definition("person")

    assert person.pointer == "/$defs/person"
    assert [field.name for field in person.properties if field.required] == ["name"]

    with pytest.raises(KeyError):
        schema.definition("no_such_definition")


def test_external_ref_is_not_resolved_silently() -> None:
    """A non-local ``$ref`` should raise rather than trigger network I/O."""
    node = Schema({"$ref": "https://example.org/other.schema.json"}).root

    with pytest.raises(ValueError, match="External"):
        node.resolve()


def test_walk_visits_nested_definitions_and_terminates() -> None:
    """Traversal should reach nested definitions without following refs."""
    pointers = [node.pointer for node in schema.walk()]

    assert "/$defs/person" in pointers
    assert "/$defs/person/properties/affiliations" in pointers
    assert "/properties/contributors/properties/entries" in pointers
    # `$ref` targets are not expanded in place, so the person entity is visited
    # once via `$defs` rather than once per property that references it.
    assert pointers.count("/$defs/person") == 1


def test_id_is_published_under_the_release_version() -> None:
    """The ``$id`` must name the URL the docs build publishes the schema at.

    The docs site serves each release at ``/schema/<version>/``, so a ``$ref``
    written against the ``$id`` only resolves while the two agree. Bumping the
    package version therefore means bumping the ``$id`` in the same change.
    """
    expected = f"https://lumc-dcc.github.io/rsm-schema/schema/{__version__}/rsm.schema.json"

    assert schema.raw["$id"] == expected


def test_contributors_must_credit_an_author() -> None:
    """A non-empty contributor list needs at least one author.

    Citation metadata requires an author, so the schema refuses a list that
    credits only maintainers. The rule is written as ``if``/``then`` so the
    empty default stays valid.

    It is enforced by JSON Schema validation only. ``datamodel-code-generator``
    cannot express a conditional across list items, so ``Contributors`` accepts
    an author-less list; see the note in ``docs/schema-workflow.md``.
    """
    validator = validator_for(schema.raw)(schema.raw)

    def errors(entries: list[dict[str, object]]) -> list[str]:
        document = {"project_slug": "demo", "contributors": {"entries": entries}}
        return [error.message for error in validator.iter_errors(document)]

    assert errors([]) == []
    assert errors([{"name": "Ada", "roles": ["Original author"]}]) == []
    assert errors([{"name": "Bob", "roles": ["Maintainer"]}]) != []
    # Every entry must still declare its own roles, author present or not.
    assert errors([{"name": "Ada", "roles": ["Co-author"]}, {"name": "Bob"}]) != []


def test_validate_document_is_authoritative() -> None:
    """The public helper should enforce JSON Schema conditional rules."""
    validate_document(
        {
            "project_slug": "demo",
            "contributors": {"entries": [{"name": "Ada", "roles": ["Original author"]}]},
        }
    )

    with pytest.raises(JsonSchemaValidationError, match="does not contain"):
        validate_document(
            {
                "project_slug": "demo",
                "contributors": {"entries": [{"name": "Bob", "roles": ["Maintainer"]}]},
            }
        )
