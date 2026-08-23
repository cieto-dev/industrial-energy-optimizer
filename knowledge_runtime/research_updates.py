from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_UPDATE_CATEGORIES = {
    "tariffs": "knowledge-base/master/tariffs.json",
    "policies": "knowledge-base/policies/central_policies.json",
    "schemes": "knowledge-base/finance/subsidies.json",
    "emission_factors": "knowledge-base/emissions/emission_factors.json",
    "grid_factors": "knowledge-base/emissions/grid_factors.json",
}


@dataclass(frozen=True)
class UpdateResult:
    category: str
    status: str
    active_path: str
    dataset_version: str | None
    updated_at: str
    message: str


class ResearchUpdateManager:
    """
    Safe, data-only update manager for research datasets.

    The calculation engine continues reading the same canonical dataset path.
    New values therefore do not require Python/code changes.

    Update package:

        package/
        ├── metadata.json
        └── payload.json

    Example metadata:

        {
          "category": "tariffs",
          "dataset_version": "2026.09",
          "source_ids": ["SRC_TNERC_ORDER_2026_09"],
          "source_date": "2026-09-01",
          "accessed": "2026-09-05",
          "status": "verified",
          "confidence": 0.95,
          "notes": "Latest verified tariff order"
        }

    Safety guarantees:
    - validates metadata
    - validates payload structure
    - validates SHA-256 when supplied
    - creates a backup before replacement
    - replaces the active dataset atomically
    - records update provenance
    - never executes Python from update packages
    """

    ALLOWED_STATUSES = {
        "verified",
        "current",
        "historical",
        "inference",
        "proposed",
        "draft",
    }

    def __init__(
        self,
        project_root: str | Path | None = None,
    ) -> None:
        if project_root is None:
            project_root = Path(__file__).resolve().parents[1]

        self.project_root = Path(project_root).resolve()

        self.knowledge_base_dir = (
            self.project_root / "knowledge-base"
        )

        self.update_root = (
            self.knowledge_base_dir / "updates"
        )

        self.backup_root = (
            self.knowledge_base_dir / "backups"
        )

        self.registry_path = (
            self.update_root / "registry.json"
        )

        self.update_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ---------------------------------------------------------
    # Generic helpers
    # ---------------------------------------------------------

    @staticmethod
    def _utc_now() -> str:
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
        )

    @staticmethod
    def _sha256_bytes(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _read_json(path: Path) -> Any:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as handle:
            return json.load(handle)

    @staticmethod
    def _write_json(
        path: Path,
        data: Any,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                data,
                handle,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")

    # ---------------------------------------------------------
    # Registry
    # ---------------------------------------------------------

    def _registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {
                "schema_version": "1.0",
                "updated_at": self._utc_now(),
                "datasets": {},
            }

        data = self._read_json(
            self.registry_path
        )

        if not isinstance(data, dict):
            raise ValueError(
                "Research update registry must "
                "contain a JSON object."
            )

        data.setdefault(
            "schema_version",
            "1.0",
        )

        data.setdefault(
            "datasets",
            {},
        )

        return data

    def get_registry(self) -> dict[str, Any]:
        return self._registry()

    # ---------------------------------------------------------
    # Dataset resolution
    # ---------------------------------------------------------

    def _resolve_target(
        self,
        category: str,
    ) -> Path:
        if category not in DEFAULT_UPDATE_CATEGORIES:
            raise ValueError(
                "Unsupported research update category: "
                f"{category}. Supported categories: "
                f"{sorted(DEFAULT_UPDATE_CATEGORIES)}"
            )

        return (
            self.project_root
            / DEFAULT_UPDATE_CATEGORIES[category]
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @staticmethod
    def _validate_metadata(
        category: str,
        metadata: dict[str, Any],
    ) -> None:
        required = {
            "category",
            "dataset_version",
            "source_ids",
            "source_date",
            "status",
            "confidence",
        }

        missing = sorted(
            required - set(metadata)
        )

        if missing:
            raise ValueError(
                "Update metadata is missing: "
                + ", ".join(missing)
            )

        if metadata["category"] != category:
            raise ValueError(
                "Metadata category does not match "
                "the requested update category."
            )

        if not isinstance(
            metadata["source_ids"],
            list,
        ) or not metadata["source_ids"]:
            raise ValueError(
                "metadata.source_ids must be a "
                "non-empty list."
            )

        if metadata["status"] not in (
            ResearchUpdateManager.ALLOWED_STATUSES
        ):
            raise ValueError(
                f"Unsupported update status: "
                f"{metadata['status']}"
            )

        try:
            confidence = float(
                metadata["confidence"]
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "metadata.confidence must be numeric."
            ) from exc

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "metadata.confidence must be "
                "between 0 and 1."
            )

    @staticmethod
    def _validate_payload(
        category: str,
        payload: Any,
    ) -> None:
        if category == "emission_factors":
            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "Emission-factor payload must "
                    "be a JSON object."
                )
            return

        if category == "grid_factors":
            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "Grid-factor payload must "
                    "be a JSON object."
                )
            return

        if category in {
            "tariffs",
            "policies",
            "schemes",
        }:
            if not isinstance(
                payload,
                (dict, list),
            ):
                raise ValueError(
                    f"{category} payload must be "
                    "a JSON object or list."
                )
            return

        raise ValueError(
            f"Unsupported update category: {category}"
        )

    def validate_package(
        self,
        package_root: str | Path,
    ) -> dict[str, Any]:
        package_root = Path(
            package_root
        ).resolve()

        metadata_path = (
            package_root / "metadata.json"
        )

        payload_path = (
            package_root / "payload.json"
        )

        if not metadata_path.is_file():
            raise FileNotFoundError(
                f"Missing update metadata: "
                f"{metadata_path}"
            )

        if not payload_path.is_file():
            raise FileNotFoundError(
                f"Missing update payload: "
                f"{payload_path}"
            )

        metadata = self._read_json(
            metadata_path
        )

        payload = self._read_json(
            payload_path
        )

        if not isinstance(
            metadata,
            dict,
        ):
            raise ValueError(
                "metadata.json must contain "
                "a JSON object."
            )

        category = str(
            metadata.get(
                "category",
                "",
            )
        )

        self._validate_metadata(
            category,
            metadata,
        )

        self._validate_payload(
            category,
            payload,
        )

        payload_bytes = (
            payload_path.read_bytes()
        )

        checksum = self._sha256_bytes(
            payload_bytes
        )

        expected_checksum = metadata.get(
            "payload_sha256"
        )

        if (
            expected_checksum
            and expected_checksum != checksum
        ):
            raise ValueError(
                "payload_sha256 does not match "
                "payload.json."
            )

        metadata["payload_sha256"] = checksum

        metadata["validated_at"] = (
            self._utc_now()
        )

        return {
            "metadata": metadata,
            "payload": payload,
        }

    # ---------------------------------------------------------
    # Activation
    # ---------------------------------------------------------

    def activate_package(
        self,
        package_root: str | Path,
    ) -> UpdateResult:
        validated = self.validate_package(
            package_root
        )

        metadata = validated["metadata"]
        payload = validated["payload"]

        category = metadata["category"]

        target = self._resolve_target(
            category
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        registry = self._registry()

        datasets = registry.setdefault(
            "datasets",
            {},
        )

        previous = datasets.get(
            category
        )

        backup_path = None

        # -----------------------------------------------------
        # Backup current version
        # -----------------------------------------------------

        if target.exists():
            timestamp = (
                datetime.now(
                    timezone.utc
                ).strftime(
                    "%Y%m%dT%H%M%SZ"
                )
            )

            backup = (
                self.backup_root
                / category
                / f"{timestamp}.json"
            )

            backup.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                target,
                backup,
            )

            backup_path = str(
                backup.relative_to(
                    self.project_root
                )
            )

        # -----------------------------------------------------
        # Atomic replacement
        # -----------------------------------------------------

        temp_dir = Path(
            tempfile.mkdtemp(
                prefix="research-update-"
            )
        )

        temp_target = (
            temp_dir / target.name
        )

        try:
            self._write_json(
                temp_target,
                payload,
            )

            temp_target.replace(
                target
            )

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True,
            )

        # -----------------------------------------------------
        # Registry entry
        # -----------------------------------------------------

        activated_at = (
            self._utc_now()
        )

        datasets[category] = {
            "active_path": str(
                target.relative_to(
                    self.project_root
                )
            ),
            "dataset_version": str(
                metadata["dataset_version"]
            ),
            "source_ids": list(
                metadata["source_ids"]
            ),
            "source_date": metadata[
                "source_date"
            ],
            "accessed": metadata.get(
                "accessed",
                str(date.today()),
            ),
            "status": metadata[
                "status"
            ],
            "confidence": float(
                metadata["confidence"]
            ),
            "notes": metadata.get(
                "notes",
                "",
            ),
            "payload_sha256": metadata[
                "payload_sha256"
            ],
            "activated_at": activated_at,
            "backup_path": backup_path,
            "previous": previous,
        }

        registry[
            "updated_at"
        ] = activated_at

        self._write_json(
            self.registry_path,
            registry,
        )

        return UpdateResult(
            category=category,
            status="activated",
            active_path=str(
                target.relative_to(
                    self.project_root
                )
            ),
            dataset_version=str(
                metadata["dataset_version"]
            ),
            updated_at=activated_at,
            message=(
                f"Activated {category} dataset "
                f"version "
                f"{metadata['dataset_version']}"
            ),
        )