
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cache import KnowledgeCache
from .errors import KnowledgeDataError, KnowledgeFileNotFoundError


class KnowledgeLoader:
    """
    Runtime loader for project knowledge sources.

    Performance improvements:
    - parsed JSON is cached
    - directory datasets are loaded lazily
    - shared cached reads avoid unnecessary deep-copy overhead
    - filesystem access is centralized
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

    # ------------------------------------------------------------------
    # Path handling
    # ------------------------------------------------------------------

    def resolve_project_path(self, relative_path: str) -> Path:
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
        candidate = (self.datasets_dir / relative_path).resolve()

        try:
            candidate.relative_to(self.datasets_dir)
        except ValueError as exc:
            raise KnowledgeDataError(
                relative_path,
                "path escapes the datasets directory",
            ) from exc

        return candidate

    # ------------------------------------------------------------------
    # JSON loading
    # ------------------------------------------------------------------

    def load_json(
        self,
        relative_path: str,
        *,
        base: str = "knowledge-base",
        shared: bool = True,
    ) -> Any:
        """
        Load and cache JSON.

        shared=True is intended for read-only internal access and avoids
        deepcopy on cache hits.
        """
        cache_key = f"{base}:{relative_path}"

        if shared:
            cached = self.cache.get_shared(cache_key)
        else:
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

        # The loader now owns the object.
        self.cache.set_owned(cache_key, data)
        return data

    def load_knowledge_json(
        self,
        relative_path: str,
        *,
        shared: bool = True,
    ) -> Any:
        return self.load_json(
            relative_path,
            base="knowledge-base",
            shared=shared,
        )

    def load_dataset_json(
        self,
        relative_path: str,
        *,
        shared: bool = True,
    ) -> Any:
        return self.load_json(
            relative_path,
            base="datasets",
            shared=shared,
        )

    # ------------------------------------------------------------------
    # Lazy directory loading
    # ------------------------------------------------------------------

    def list_json_files(
        self,
        relative_directory: str,
        *,
        base: str = "knowledge-base",
    ) -> tuple[str, ...]:
        """
        Return JSON filenames without opening/parsing them.

        This is the first stage of lazy loading.
        """
        if base == "knowledge-base":
            directory = self.resolve_knowledge_path(relative_directory)
        elif base == "datasets":
            directory = self.resolve_dataset_path(relative_directory)
        else:
            raise KnowledgeDataError(
                relative_directory,
                f"unsupported directory base: '{base}'",
            )

        if not directory.exists():
            raise KnowledgeFileNotFoundError(
                f"{base}/{relative_directory}"
            )

        if not directory.is_dir():
            raise KnowledgeDataError(
                f"{base}/{relative_directory}",
                "expected a directory",
            )

        return tuple(
            sorted(
                path.name
                for path in directory.glob("*.json")
                if path.is_file()
            )
        )

    def load_json_directory(
        self,
        relative_directory: str,
        *,
        base: str = "knowledge-base",
    ) -> list[Any]:
        """
        Load all JSON files in a directory lazily on first request.

        The resulting list is cached as one aggregate object.
        """
        aggregate_key = (
            f"{base}:__directory__:{relative_directory}"
        )

        cached = self.cache.get_shared(aggregate_key)
        if cached is not None:
            return cached

        files = self.list_json_files(
            relative_directory,
            base=base,
        )

        values: list[Any] = []

        for filename in files:
            relative_file = (
                f"{relative_directory}/{filename}"
            )

            values.append(
                self.load_json(
                    relative_file,
                    base=base,
                    shared=True,
                )
            )

        self.cache.set_owned(
            aggregate_key,
            values,
        )

        return values

    def clear_cache(self) -> None:
        self.cache.clear()

