from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Base exception for runtime knowledge-base errors."""


class KnowledgeFileNotFoundError(KnowledgeBaseError):
    """Raised when a requested knowledge-base file does not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Knowledge-base file not found: {path}")
        self.path = path


class KnowledgeDataError(KnowledgeBaseError):
    """Raised when a knowledge-base file cannot be parsed or has invalid shape."""

    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"Invalid knowledge-base data in {path}: {message}")
        self.path = path
        self.message = message


class KnowledgeItemNotFoundError(KnowledgeBaseError):
    """Raised when a requested item does not exist."""

    def __init__(self, dataset: str, key: str) -> None:
        super().__init__(
            f"Knowledge item not found in '{dataset}': '{key}'"
        )
        self.dataset = dataset
        self.key = key


class KnowledgeReferenceError(KnowledgeBaseError):
    """Raised when a source/citation reference cannot be resolved."""

    def __init__(self, source_id: str) -> None:
        super().__init__(
            f"Knowledge reference could not be resolved: '{source_id}'"
        )
        self.source_id = source_id