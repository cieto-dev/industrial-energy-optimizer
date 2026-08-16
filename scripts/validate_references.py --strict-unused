#!/usr/bin/env python3
"""
Repository-wide provenance and reference validator.

Validates the canonical source registry and all source_id references
used throughout the Industrial Energy Transition Optimizer knowledge base.

Canonical reference architecture:

    knowledge-base/
        references/
            sources.json      <- canonical source registry
            citations.json    <- compatibility source_id index

All other knowledge-base JSON files may reference sources by source_id,
but must not maintain independent source metadata.

Usage:

    python scripts/validate_references.py

Optional:

    python scripts/validate_references.py --quiet
    python scripts/validate_references.py --strict-unused

Exit codes:

    0 - validation passed
    1 - validation failed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Repository configuration
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

KNOWLEDGE_BASE_DIR = REPO_ROOT / "knowledge-base"
REFERENCES_DIR = KNOWLEDGE_BASE_DIR / "references"

SOURCES_FILE = REFERENCES_DIR / "sources.json"
CITATIONS_FILE = REFERENCES_DIR / "citations.json"

# Canonical source metadata fields.
SOURCE_FIELDS = {
    "title",
    "organization",
    "year",
    "url",
}

# Compatibility citation records are intentionally minimal.
CITATION_FIELDS = {
    "source_id",
}

# Fields that previously appeared in competing citation/source schemas.
# They are forbidden as provenance metadata in knowledge-base JSON records.
LEGACY_CITATION_FIELDS = {
    "label",
    "publisher",
    "data_used",
}

# Files which define the provenance registry itself and therefore should
# not be treated as ordinary source-consuming knowledge-base records.
REFERENCE_FILES = {
    SOURCES_FILE.resolve(),
    CITATIONS_FILE.resolve(),
}

# A source URL may legitimately be null for internal project references.
ALLOWED_NULL_URL_SOURCE_IDS = {
    "SRC_PROJECT_DEFAULTS",
}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

class ValidationReport:
    """Collects validation errors, warnings, and informational messages."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    @property
    def passed(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        self.info.append(message)


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------

def load_json(path: Path, report: ValidationReport) -> Any | None:
    """Load a JSON file and report malformed JSON without crashing."""

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        report.error(f"Missing required file: {path.relative_to(REPO_ROOT)}")
    except json.JSONDecodeError as exc:
        relative_path = path.relative_to(REPO_ROOT)
        report.error(
            f"Invalid JSON in {relative_path}: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
    except OSError as exc:
        report.error(
            f"Unable to read {path.relative_to(REPO_ROOT)}: {exc}"
        )

    return None


# ---------------------------------------------------------------------------
# Generic recursive traversal
# ---------------------------------------------------------------------------

def walk_json(
    value: Any,
    path: str = "$",
) -> list[tuple[str, Any]]:
    """
    Recursively yield every JSON object field as:

        (JSON path, value)

    This allows source_id and legacy citation fields to be detected regardless
    of how deeply nested the knowledge-base record is.
    """

    results: list[tuple[str, Any]] = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            results.append((child_path, child))
            results.extend(walk_json(child, child_path))

    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            results.extend(walk_json(child, child_path))

    return results


# ---------------------------------------------------------------------------
# Canonical sources.json validation
# ---------------------------------------------------------------------------

def validate_sources_registry(
    sources: Any,
    report: ValidationReport,
) -> set[str]:
    """
    Validate knowledge-base/references/sources.json.

    The canonical structure is:

        {
            "SRC001": {
                "title": "...",
                "organization": "...",
                "year": 2026,
                "url": "..."
            }
        }

    The source ID is the JSON object key, not a duplicated field.
    """

    if not isinstance(sources, dict):
        report.error(
            "sources.json must contain a JSON object keyed by source ID."
        )
        return set()

    source_ids = set(sources.keys())

    if len(source_ids) != len(sources):
        # Defensive check; JSON object keys are inherently unique after parsing.
        report.error("sources.json contains duplicate source IDs.")

    for source_id, record in sources.items():
        if not isinstance(source_id, str) or not source_id.strip():
            report.error(
                "sources.json contains an empty or non-string source ID."
            )
            continue

        if not isinstance(record, dict):
            report.error(
                f"{source_id}: source record must be a JSON object."
            )
            continue

        actual_fields = set(record.keys())

        missing_fields = SOURCE_FIELDS - actual_fields
        extra_fields = actual_fields - SOURCE_FIELDS

        if missing_fields:
            report.error(
                f"{source_id}: missing canonical source fields: "
                f"{', '.join(sorted(missing_fields))}"
            )

        if extra_fields:
            report.error(
                f"{source_id}: unexpected source fields: "
                f"{', '.join(sorted(extra_fields))}"
            )

        title = record.get("title")
        organization = record.get("organization")
        year = record.get("year")
        url = record.get("url")

        if not isinstance(title, str) or not title.strip():
            report.error(
                f"{source_id}: 'title' must be a non-empty string."
            )

        if not isinstance(organization, str) or not organization.strip():
            report.error(
                f"{source_id}: 'organization' must be a non-empty string."
            )

        if not isinstance(year, int) or isinstance(year, bool):
            report.error(
                f"{source_id}: 'year' must be an integer."
            )
        elif year < 1900 or year > 2100:
            report.error(
                f"{source_id}: 'year' is outside the supported range "
                f"(1900-2100): {year}"
            )

        if url is None:
            if source_id not in ALLOWED_NULL_URL_SOURCE_IDS:
                report.error(
                    f"{source_id}: 'url' is null but this source is not "
                    "registered as an internal no-URL source."
                )
        elif not isinstance(url, str):
            report.error(
                f"{source_id}: 'url' must be a string or null."
            )
        elif not url.strip():
            report.error(
                f"{source_id}: 'url' cannot be an empty string."
            )

    return source_ids


# ---------------------------------------------------------------------------
# citations.json validation
# ---------------------------------------------------------------------------

def validate_citations_registry(
    citations: Any,
    source_ids: set[str],
    report: ValidationReport,
) -> set[str]:
    """
    Validate citations.json as a compatibility index.

    Expected structure:

        {
            "SRC001": {
                "source_id": "SRC001"
            }
        }

    It must not contain independent source metadata.
    """

    if not isinstance(citations, dict):
        report.error(
            "citations.json must contain a JSON object keyed by citation/source ID."
        )
        return set()

    citation_ids = set(citations.keys())

    for citation_id, record in citations.items():
        if not isinstance(record, dict):
            report.error(
                f"citations.json/{citation_id}: record must be a JSON object."
            )
            continue

        actual_fields = set(record.keys())

        missing_fields = CITATION_FIELDS - actual_fields
        extra_fields = actual_fields - CITATION_FIELDS

        if missing_fields:
            report.error(
                f"citations.json/{citation_id}: missing fields: "
                f"{', '.join(sorted(missing_fields))}"
            )

        if extra_fields:
            report.error(
                f"citations.json/{citation_id}: competing/extra fields: "
                f"{', '.join(sorted(extra_fields))}"
            )

        referenced_source_id = record.get("source_id")

        if not isinstance(referenced_source_id, str):
            report.error(
                f"citations.json/{citation_id}: 'source_id' must be a string."
            )
            continue

        if referenced_source_id != citation_id:
            report.error(
                f"citations.json/{citation_id}: source_id "
                f"'{referenced_source_id}' does not match its canonical key."
            )

        if referenced_source_id not in source_ids:
            report.error(
                f"citations.json/{citation_id}: references unknown "
                f"source ID '{referenced_source_id}'."
            )

    missing_citation_ids = source_ids - citation_ids

    if missing_citation_ids:
        report.error(
            "citations.json is missing canonical source IDs: "
            + ", ".join(sorted(missing_citation_ids))
        )

    extra_citation_ids = citation_ids - source_ids

    if extra_citation_ids:
        report.error(
            "citations.json contains IDs absent from sources.json: "
            + ", ".join(sorted(extra_citation_ids))
        )

    return citation_ids


# ---------------------------------------------------------------------------
# Knowledge-base source reference scanning
# ---------------------------------------------------------------------------

def find_knowledge_base_json_files() -> list[Path]:
    """Return all JSON files under knowledge-base recursively."""

    if not KNOWLEDGE_BASE_DIR.exists():
        return []

    return sorted(
        path
        for path in KNOWLEDGE_BASE_DIR.rglob("*.json")
        if path.is_file()
    )


def collect_source_references(
    json_files: list[Path],
    source_ids: set[str],
    report: ValidationReport,
) -> set[str]:
    """
    Scan all knowledge-base JSON records for source_id fields.

    The canonical sources.json and compatibility citations.json are excluded
    from ordinary consumer scanning because they define the provenance layer
    rather than consume it.
    """

    used_source_ids: set[str] = set()

    for json_file in json_files:
        if json_file.resolve() in REFERENCE_FILES:
            continue

        relative_path = json_file.relative_to(REPO_ROOT)

        document = load_json(json_file, report)

        if document is None:
            continue

        for json_path, value in walk_json(document):
            if not json_path.endswith(".source_id"):
                continue

            if not isinstance(value, str):
                report.error(
                    f"{relative_path}{json_path}: source_id must be a string."
                )
                continue

            used_source_ids.add(value)

            if value not in source_ids:
                report.error(
                    f"{relative_path}{json_path}: unknown source ID '{value}'."
                )

    return used_source_ids


# ---------------------------------------------------------------------------
# Legacy provenance-field detection
# ---------------------------------------------------------------------------

def detect_legacy_citation_fields(
    json_files: list[Path],
    report: ValidationReport,
) -> None:
    """
    Detect old competing citation/source schemas in knowledge-base JSON.

    Fields such as label, publisher, and data_used are intentionally not
    permitted as source-registry metadata because sources.json is now the
    canonical provenance registry.
    """

    for json_file in json_files:
        if json_file.resolve() in REFERENCE_FILES:
            continue

        relative_path = json_file.relative_to(REPO_ROOT)

        document = load_json(json_file, report)

        if document is None:
            continue

        for json_path, _ in walk_json(document):
            field_name = json_path.rsplit(".", 1)[-1]

            if field_name in LEGACY_CITATION_FIELDS:
                report.error(
                    f"{relative_path}{json_path}: legacy citation field "
                    f"'{field_name}' detected. Use source_id and resolve "
                    "metadata through knowledge-base/references/sources.json."
                )


# ---------------------------------------------------------------------------
# Repository-wide consistency checks
# ---------------------------------------------------------------------------

def validate_repository(
    report: ValidationReport,
    strict_unused: bool = False,
) -> tuple[set[str], set[str]]:
    """Run the complete repository provenance validation."""

    if not KNOWLEDGE_BASE_DIR.exists():
        report.error(
            f"Missing knowledge-base directory: {KNOWLEDGE_BASE_DIR}"
        )
        return set(), set()

    sources = load_json(SOURCES_FILE, report)
    citations = load_json(CITATIONS_FILE, report)

    if sources is None:
        return set(), set()

    source_ids = validate_sources_registry(sources, report)

    if citations is not None:
        validate_citations_registry(
            citations,
            source_ids,
            report,
        )

    json_files = find_knowledge_base_json_files()

    report.add_info(
        f"Scanned {len(json_files)} JSON files under knowledge-base/."
    )

    used_source_ids = collect_source_references(
        json_files,
        source_ids,
        report,
    )

    detect_legacy_citation_fields(
        json_files,
        report,
    )

    unused_source_ids = source_ids - used_source_ids

    if unused_source_ids:
        message = (
            f"{len(unused_source_ids)} registered source(s) are not "
            "referenced by ordinary knowledge-base JSON records: "
            + ", ".join(sorted(unused_source_ids))
        )

        if strict_unused:
            report.error(message)
        else:
            report.warning(message)

    unknown_source_ids = used_source_ids - source_ids

    if unknown_source_ids:
        # This is normally already reported at the exact JSON path, but the
        # aggregate check makes the final report easier to understand.
        report.error(
            "Unknown source IDs detected: "
            + ", ".join(sorted(unknown_source_ids))
        )

    report.add_info(
        f"Canonical source IDs: {len(source_ids)}"
    )

    report.add_info(
        f"Source IDs referenced by knowledge-base consumers: "
        f"{len(used_source_ids)}"
    )

    report.add_info(
        f"Registered but unused source IDs: {len(unused_source_ids)}"
    )

    return source_ids, used_source_ids


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the Industrial Energy Transition Optimizer "
            "knowledge-base provenance registry."
        )
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print failures; suppress informational output.",
    )

    parser.add_argument(
        "--strict-unused",
        action="store_true",
        help=(
            "Treat registered-but-unused source IDs as validation errors "
            "instead of warnings."
        ),
    )

    return parser.parse_args()


def print_report(
    report: ValidationReport,
    source_ids: set[str],
    used_source_ids: set[str],
    quiet: bool,
) -> None:
    """Print a concise repository validation report."""

    if not quiet:
        print("=" * 72)
        print("Industrial Energy Transition Optimizer")
        print("Repository Reference Validation")
        print("=" * 72)
        print()

        for message in report.info:
            print(f"[INFO] {message}")

        if report.warnings:
            print()
            print("Warnings:")
            for message in report.warnings:
                print(f"  [WARN] {message}")

    if report.errors:
        print()
        print("Errors:")
        for message in report.errors:
            print(f"  [ERROR] {message}")

    print()

    if report.passed:
        print("[PASS] Reference validation completed successfully.")
        print(
            f"[PASS] {len(source_ids)} canonical source IDs are registered."
        )
        print(
            f"[PASS] {len(used_source_ids)} source IDs are referenced "
            "by knowledge-base consumers."
        )
    else:
        print("[FAIL] Reference validation failed.")
        print(f"[FAIL] {len(report.errors)} error(s) detected.")

    print("=" * 72)


def main() -> int:
    args = parse_args()

    report = ValidationReport()

    source_ids, used_source_ids = validate_repository(
        report,
        strict_unused=args.strict_unused,
    )

    print_report(
        report,
        source_ids,
        used_source_ids,
        args.quiet,
    )

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
