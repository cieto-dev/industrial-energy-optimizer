from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cache import KnowledgeCache
from .errors import KnowledgeDataError, KnowledgeFileNotFoundError


class KnowledgeLoader:
    """
    Runtime loader for the project's knowledge sources.

    The loader centralizes filesystem access and JSON parsing.
    Application/decision-engine code should not open knowledge files directly.
    """

    def __init__(
        self,
        project_root: str | Path | None = None,
        cache: KnowledgeCache | None = None,
    ) -> None:
        if project_root is None:
            project_root = Path(__file__).resolve().parents[1]

        self.project_root = Path(project_root).resolve()
        self.knowledge_base_dir = self.project_root / "knowledge-base"
        self.datasets_dir = self.project_root / "datasets"

        self.cache = cache or KnowledgeCache()

    def resolve_project_path(self, relative_path: str) -> Path:
        """
        Resolve a path relative to the repository root.

        This is restricted to the repository root so callers cannot use
        '..' to escape the project directory.
        """
        candidate = (self.project_root / relative_path).resolve()

        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise KnowledgeDataError(
                relative_path,
                "path escapes the project directory",
            ) from exc

        return candidate

    def resolve_knowledge_path(self, relative_path: str) -> Path:
        """Resolve a path relative to knowledge-base/."""
        candidate = (self.knowledge_base_dir / relative_path).resolve()

        try:
            candidate.relative_to(self.knowledge_base_dir)
        except ValueError as exc:
            raise KnowledgeDataError(
                relative_path,
                "path escapes the knowledge-base directory",
            ) from exc

        return candidate

    def resolve_dataset_path(self, relative_path: str) -> Path:
        """Resolve a path relative to datasets/."""
        candidate = (self.datasets_dir / relative_path).resolve()

        try:
            candidate.relative_to(self.datasets_dir)
        except ValueError as exc:
            raise KnowledgeDataError(
                relative_path,
                "path escapes the datasets directory",
            ) from exc

        return candidate

    def load_json(
        self,
        relative_path: str,
        *,
        base: str = "knowledge-base",
    ) -> Any:
        """
        Load a JSON document with caching.

        base:
            "knowledge-base" -> knowledge-base/
            "datasets"       -> datasets/
            "project"        -> repository root
        """
        cache_key = f"{base}:{relative_path}"

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if base == "knowledge-base":
            path = self.resolve_knowledge_path(relative_path)
        elif base == "datasets":
            path = self.resolve_dataset_path(relative_path)
        elif base == "project":
            path = self.resolve_project_path(relative_path)
        else:
            raise KnowledgeDataError(
                relative_path,
                f"unsupported loader base: '{base}'",
            )

        if not path.exists():
            raise KnowledgeFileNotFoundError(
                f"{base}/{relative_path}"
            )

        if not path.is_file():
            raise KnowledgeDataError(
                f"{base}/{relative_path}",
                "expected a file",
            )

        try:
            with path.open("r", encoding="utf-8-sig") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise KnowledgeDataError(
                f"{base}/{relative_path}",
                (
                    f"invalid JSON at line {exc.lineno}, "
                    f"column {exc.colno}: {exc.msg}"
                ),
            ) from exc
        except OSError as exc:
            raise KnowledgeDataError(
                f"{base}/{relative_path}",
                f"unable to read file: {exc}",
            ) from exc

        self.cache.set(cache_key, data)
        return data

    def load_knowledge_json(self, relative_path: str) -> Any:
        """Convenience wrapper for knowledge-base JSON."""
        return self.load_json(
            relative_path,
            base="knowledge-base",
        )

    def load_dataset_json(self, relative_path: str) -> Any:
        """Convenience wrapper for converted dataset JSON."""
        return self.load_json(
            relative_path,
            base="datasets",
        )

    def clear_cache(self) -> None:
        self.cache.clear()