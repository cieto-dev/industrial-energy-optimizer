# One-off migration scripts (already applied)

`migrate_reference_schema.py` and `migrate_reference_schema_pass2.py` were
used once, on 2026-08-17, to collapse the competing citation/source schemas
that existed across 16 knowledge-base files into the single canonical shape
`validate_references.py` expects. They already ran successfully against
this repo (see `../../docs/PROJECT_STATE.md` and the round-1 fix report).

They are kept here purely as a record of *why* the data looks the way it
does — not as tools you need to run again. Re-running them against an
already-migrated repo is safe (every step checks "is this already fixed?"
first) but should be unnecessary. If the repo's reference data ever needs
a similar bulk cleanup again, treat these as a worked example rather than
a general-purpose tool -- the id renames, dedup targets, and new-source
metadata are all hardcoded to this specific migration.

Safe to delete once the team is comfortable losing that history (git log
will still have it).
