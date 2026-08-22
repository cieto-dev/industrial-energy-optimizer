from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any


class KnowledgeCache:
    """
    In-process cache for parsed knowledge-base datasets.

    Cached values are deep-copied on both write and read so callers cannot
    accidentally mutate shared cached state.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._data:
                return None

            return deepcopy(self._data[key])

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = deepcopy(value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def contains(self, key: str) -> bool:
        with self._lock:
            return key in self._data