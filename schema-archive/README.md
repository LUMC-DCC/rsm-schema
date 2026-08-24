# Schema archive

Each directory contains the schema published for one release. Archived schemas are
**immutable**. Correct mistakes in a new release.

The docs build republishes every directory on each deployment. Removing an archive
would break `$ref`s pinned to that version.

The current release appears here and in
`src/rsm_schema/schema/rsm.schema.json`. Tests require both copies to match.

This directory is not part of the installed package. Only the packaged copy ships
in the wheel.
