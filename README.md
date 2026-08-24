# rsm-schema

This repository defines the [Research Software Management (RSM) Metadata Schema](https://lumc-dcc.github.io/rsm-schema/schema/1.0.0/rsm.schema.json)
and its Python representation.

The package includes:

- the JSON Schema itself
- generated Pydantic v2 models for validating RSM documents
- a small inspection API for traversing the JSON Schema

The documentation is available at [lumc-dcc.github.io/rsm-schema](https://lumc-dcc.github.io/rsm-schema/).

## Quick start

```bash
pip install rsm-schema
```

Python 3.14 is required.

## Validate a document

`RSMMetadata` is the document root. Only `project_slug` is required.

```python
from rsm_schema import RSMMetadata, validate_document

document = {
    "project_slug": "my-project",
    "project_name": "My Project",
    "development_status": "wip",
    "topics": {
        "entries": [
            {
                "term": "Data analysis",
                "uri": "https://edamontology.org/topic_3474",
            }
        ]
    },
    "contributors": {
        "entries": [
            {
                "name": "Ada Lovelace",
                "email": "ada@example.org",
                "roles": ["Original author", "Maintainer"],
                "affiliations": [
                    {"name": "Leiden University Medical Center"},
                    {"name": "Leiden University"},
                ],
            }
        ]
    },
}

validate_document(document)
metadata = RSMMetadata.model_validate(document)

print(metadata.contributors.entries[0].affiliations[0].name)
print(metadata.topics.entries[0].term)
```

`topics` describes the project-level research domains using EDAM terms.
Function-specific `software_functions` separately describes operations, inputs,
outputs, commands, and notes.

`validate_document()` is the authoritative validation path and enforces JSON
Schema conditionals that generated Pydantic models cannot represent.

## Inspect the schema

```python
from rsm_schema import schema

print(schema.title)

for field in schema.root.properties:
    print(field.name, field.types, field.required)

person = schema.definition("person")
for field in person.properties:
    print(field.pointer, field.types, field.required)
```

`SchemaNode.resolve()` follows local JSON Pointer `$ref` values, and `Schema.walk()`
traverses properties, definitions, array items, and composition keywords such as
`oneOf`, `anyOf`, and `allOf`. External references are never fetched.

## Development

```bash
git clone https://github.com/lumc-dcc/rsm-schema.git
cd rsm-schema
poetry install --with dev,docs
poetry run pre-commit install
```

```bash
poetry run pre-commit run --all-files
poetry run pytest
```

The JSON Schema at `src/rsm_schema/schema/rsm.schema.json` is canonical. After
changing it, regenerate the models and commit both together:

```bash
poetry run datamodel-codegen
poetry run pytest
```

Build the documentation locally with:

```bash
poetry run sphinx-build -b html -W --keep-going docs docs/_build/html
```

Released schemas are archived under `schema-archive/`, one immutable directory per
version. The documentation site publishes every archived version so versioned `$ref`s
continue to resolve.
See [CONTRIBUTING.md](CONTRIBUTING.md) and the
[schema workflow](https://lumc-dcc.github.io/rsm-schema/schema-workflow.html) for the
release steps.

---

## License

This project is licensed under Apache 2.0. See the [LICENSE](LICENSE) file for details.
