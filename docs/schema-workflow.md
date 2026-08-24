# Schema workflow

`src/rsm_schema/schema/rsm.schema.json` is canonical. Everything else in the package
is derived from it.

## After changing the schema

Regenerate the models and run the checks:

```bash
poetry run datamodel-codegen
poetry run pre-commit run --all-files
poetry run pytest
```

Commit the schema and the regenerated `src/rsm_schema/generated/models.py` together.
CI regenerates the models and rejects a stale generated module.

Generation is configured under `[tool.datamodel-codegen]` in `pyproject.toml`.

If a change adds a name to `$defs`, export its generated counterpart from
`src/rsm_schema/generated/__init__.py` to include it in the public API.

## Releasing a new version

The release version appears in both the schema's `$id` and its published URL. Update
them together:

1. Bump `version` in `pyproject.toml`.
2. Set `$id` to `https://lumc-dcc.github.io/rsm-schema/schema/<version>/rsm.schema.json`.
3. Copy the schema into the archive:

   ```bash
   mkdir -p schema-archive/<version>
   cp src/rsm_schema/schema/rsm.schema.json schema-archive/<version>/
   ```

4. Update the versioned URL quoted at the top of `README.md` and
   [the documentation home](index.md).

## Where the two validation paths differ

The package has two validation paths with one documented difference.

When `contributors` is non-empty, JSON Schema validation requires at least one
author. `datamodel-code-generator` cannot express this list-wide `if`/`then`
condition in a Pydantic model. A list containing only maintainers therefore fails
`validate_document()` but passes `RSMMetadata.model_validate()`.

Everything else the schema states is enforced on both paths, including the per-entry
`roles` requirement. Use `rsm_schema.validate_document()` when conditional rules
must be enforced. It validates against the bundled JSON Schema.

## Inspection scope

The inspection API provides JSON Pointer lookup, local
`$ref` resolution, property and definition traversal, array items, and
`oneOf`/`anyOf`/`allOf` traversal. It does not fetch external `$ref` targets.

## Building the docs locally

```bash
poetry install --with docs
poetry run sphinx-build -b html -W --keep-going docs docs/_build/html
```

`-W` matches CI and treats warnings as errors.
