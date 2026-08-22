from __future__ import annotations

from typing import Any

from .errors import KnowledgeReferenceError


class EvidenceResolver:
    """
    Resolve knowledge provenance through:

        citations.json -> sources.json

    citations.json is the source-link/index layer.
    sources.json is the canonical source metadata registry.
    """

    def __init__(self, loader) -> None:
        self.loader = loader

    def get_source(self, source_id: str) -> dict[str, Any]:
        if not source_id:
            raise KnowledgeReferenceError(source_id)

        citations = self.loader.load_knowledge_json(
            "references/citations.json"
        )
        sources = self.loader.load_knowledge_json(
            "references/sources.json"
        )

        if not isinstance(citations, dict):
            raise KnowledgeReferenceError(source_id)

        if not isinstance(sources, dict):
            raise KnowledgeReferenceError(source_id)

        citation = citations.get(source_id)

        if not isinstance(citation, dict):
            raise KnowledgeReferenceError(source_id)

        resolved_source_id = citation.get("source_id")

        if resolved_source_id != source_id:
            raise KnowledgeReferenceError(source_id)

        source = sources.get(resolved_source_id)

        if not isinstance(source, dict):
            raise KnowledgeReferenceError(source_id)

        result = dict(source)
        result["source_id"] = source_id

        return result

    def resolve(self, record: Any) -> list[dict[str, Any]]:
        """
        Recursively discover source_id fields inside a knowledge record
        and resolve them to canonical source metadata.

        Duplicate source IDs are returned only once.
        """
        source_ids: list[str] = []

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "source_id" and isinstance(child, str):
                        source_ids.append(child)

                    walk(child)

            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(record)

        resolved: list[dict[str, Any]] = []
        seen: set[str] = set()

        for source_id in source_ids:
            if source_id in seen:
                continue

            resolved.append(self.get_source(source_id))
            seen.add(source_id)

        return resolved