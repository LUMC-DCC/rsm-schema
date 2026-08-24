# Contributing

Thanks for working on this.

## Setup

Use Python 3.14 and Poetry.

```bash
poetry install --with dev,docs
poetry run pre-commit install
```

Before opening a pull request, run the hooks and the remaining CI checks:

```bash
poetry run pre-commit run --all-files
poetry run pytest
poetry run sphinx-build -b html -W --keep-going docs docs/_build/html
```

These correspond to `lint.yml`, `test.yml`, and `docs.yml`. `publish.yml` runs only
for a published release.

## Changing the schema

`src/rsm_schema/schema/rsm.schema.json` is the source of truth. When it changes,
regenerate `src/rsm_schema/generated/models.py` and commit both in the same change:

```bash
poetry run datamodel-codegen
```

CI regenerates the models and rejects a stale generated module.

If the change adds a name to `$defs`, export its generated counterpart from
`src/rsm_schema/generated/__init__.py`.

## Releasing

The release version appears in both the schema's `$id` and its published URL. Update
them together:

1. Bump `version` in `pyproject.toml`.
2. Set `$id` to `https://lumc-dcc.github.io/rsm-schema/schema/<version>/rsm.schema.json`.
3. Archive the release:

   ```bash
   mkdir -p schema-archive/<version>
   cp src/rsm_schema/schema/rsm.schema.json schema-archive/<version>/
   ```

4. Update the versioned URL quoted at the top of `README.md` and `docs/index.md`.

Steps 2 and 3 are enforced by `tests/test_inspector.py` and
`tests/test_schema_archive.py`, and the docs build refuses to publish a release that
is not archived.

Then publish a GitHub Release tagged `v<version>`. `publish.yml` checks that the tag,
`pyproject.toml`, the schema's `$id`, and the archive all agree, builds the
distributions, installs the wheel into a throwaway environment outside the source
tree to prove the bundled schema really ships, and uploads to PyPI via Trusted
Publishing. Run it manually with the `testpypi` option first if you want a dry run.

`schema-archive/` holds one immutable directory per released version. The docs build
publishes every archived schema on each deploy. Never edit or delete an archived
version because existing documents may reference it. Correct a mistake in a new
release.

## Reporting problems

Open an issue at [LUMC-DCC/rsm-schema/issues](https://github.com/LUMC-DCC/rsm-schema/issues).
