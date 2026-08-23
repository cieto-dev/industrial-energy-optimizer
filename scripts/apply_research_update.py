from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from knowledge_runtime.research_updates import (
    ResearchUpdateManager,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and activate a research "
            "dataset update package."
        )
    )

    parser.add_argument(
        "package",
        help=(
            "Directory containing metadata.json "
            "and payload.json"
        ),
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate without activating.",
    )

    args = parser.parse_args()

    manager = ResearchUpdateManager(
        PROJECT_ROOT
    )

    try:
        if args.validate_only:
            result = manager.validate_package(
                args.package
            )

            print(
                json.dumps(
                    result["metadata"],
                    indent=2,
                )
            )

            print(
                "\nValidation successful."
            )

            return 0

        result = manager.activate_package(
            args.package
        )

        print(
            json.dumps(
                {
                    "category": result.category,
                    "status": result.status,
                    "active_path": result.active_path,
                    "dataset_version": result.dataset_version,
                    "updated_at": result.updated_at,
                    "message": result.message,
                },
                indent=2,
            )
        )

        return 0

    except Exception as exc:
        print(
            f"Research update failed: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )