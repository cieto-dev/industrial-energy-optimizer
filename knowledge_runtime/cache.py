
from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any


class KnowledgeCache:
    """
    Thread-safe in-process cache for parsed knowledge-base datasets.

    Performance goals:
    - avoid repeated JSON parsing
    - avoid unnecessary deep-copy work for internal reads
    - expose hit/miss statistics for benchmarking
    - preserve backwards compatibility with the old cache API

    The cache stores the canonical object once.

    By default, callers receive a deepcopy to preserve the old safety
    contract. High-performance internal consumers can request a shared
    read via get_shared().
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = RLock()
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Standard safe API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any | None:
        """
        Return a defensive copy of a cached value.

        This preserves the behaviour expected by existing code.
        """
        with self._lock:
            value = self._data.get(key)

            if value is None:
                self._misses += 1
                return None

            self._hits += 1
            return deepcopy(value)

    # ------------------------------------------------------------------
    # Fast internal API
    # ------------------------------------------------------------------

    def get_shared(self, key: str) -> Any | None:
        """
        Return the cached object without copying.

        IMPORTANT:
        Callers must treat the returned object as read-only.

        This is used by performance-sensitive repository/optimizer paths.
        """
        with self._lock:
            value = self._data.get(key)

            if value is None:
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """
        Store a defensive copy.

        The cache owns its canonical value, preventing callers from
        mutating the cache after insertion.
        """
        with self._lock:
            self._data[key] = deepcopy(value)

    def set_owned(self, key: str, value: Any) -> None:
        """
        Store an already-owned value without an extra deepcopy.

        Only use this when the caller will no longer mutate `value`.
        """
        with self._lock:
            self._data[key] = value

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._hits = 0
            self._misses = 0

    def contains(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @property
    def hits(self) -> int:
        with self._lock:
            return self._hits

    @property
    def misses(self) -> int:
        with self._lock:
            return self._misses

    @property
    def hit_rate(self) -> float:
        with self._lock:
            total = self._hits + self._misses

            if total == 0:
                return 0.0

            return self._hits / total

    def stats(self) -> dict[str, float | int]:
        with self._lock:
            total = self._hits + self._misses

            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (
                    self._hits / total
                    if total > 0
                    else 0.0
                ),
                "entries": len(self._data),
            }

