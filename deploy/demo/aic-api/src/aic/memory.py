import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from aic.config import Settings
from aic.memory_policy import candidate_allowed


@dataclass(frozen=True)
class RecalledMemory:
    memory_id: str
    text: str
    score: float | None
    resolution_id: str
    metadata: dict[str, Any]


class MemoryStore:
    """Mem0 adapter; PostgreSQL remains the business source of truth."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        os.environ["MEM0_TELEMETRY"] = str(self.settings.mem0_telemetry).lower()
        from mem0 import Memory  # type: ignore[import-untyped]

        endpoint = urlparse(self.settings.qdrant_url)
        if not endpoint.hostname or not endpoint.port:
            raise RuntimeError("QDRANT_URL must include host and port")
        self._client = Memory.from_config(
            {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": self.settings.aic_model,
                        "api_key": self.settings.litellm_api_key.get_secret_value(),
                        "openai_base_url": self.settings.litellm_base_url,
                        "temperature": 0,
                        "max_tokens": 1000,
                    },
                },
                "embedder": {
                    "provider": "fastembed",
                    "config": {
                        "model": self.settings.mem0_embedding_model,
                        "embedding_dims": self.settings.mem0_embedding_dims,
                    },
                },
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": self.settings.mem0_collection,
                        "host": endpoint.hostname,
                        "port": endpoint.port,
                        "https": endpoint.scheme == "https",
                        "path": None,
                        "embedding_model_dims": self.settings.mem0_embedding_dims,
                        "on_disk": True,
                    },
                },
                "history_db_path": "/tmp/aic_mem0_history.db",
            }
        )
        return self._client

    def search(
        self, query: str, limit: int = 5, required_metadata: dict[str, str] | None = None
    ) -> list[RecalledMemory]:
        result = self._get_client().search(
            query,
            filters={"user_id": self.settings.mem0_user_id, "agent_id": self.settings.mem0_agent_id},
            limit=min(max(limit, 1), 10),
        )
        candidates = result.get("results", []) if isinstance(result, dict) else result
        memories: list[RecalledMemory] = []
        for candidate in candidates or []:
            metadata = dict(candidate.get("metadata") or {})
            score = float(candidate["score"]) if candidate.get("score") is not None else None
            if not metadata.get("resolution_id") or not candidate_allowed(
                score=score,
                minimum_score=self.settings.mem0_min_score,
                metadata=metadata,
                required_metadata=required_metadata or {},
            ):
                continue
            memories.append(
                RecalledMemory(
                    memory_id=str(candidate.get("id", "")),
                    text=str(candidate.get("memory", "")),
                    score=score,
                    resolution_id=str(metadata["resolution_id"]),
                    metadata=metadata,
                )
            )
        return memories

    def add_approved(self, text: str, metadata: dict[str, Any]) -> str:
        if metadata.get("approval_status") != "approved" or not metadata.get("resolution_id"):
            raise ValueError("Only engineer-approved resolutions with a resolution_id may be indexed")
        result = self._get_client().add(
            text,
            user_id=self.settings.mem0_user_id,
            agent_id=self.settings.mem0_agent_id,
            run_id=str(metadata["resolution_id"]),
            metadata=metadata,
            infer=False,
        )
        if isinstance(result, dict):
            rows = result.get("results", [])
        else:
            rows = result or []
        if not rows:
            raise RuntimeError("Mem0 did not return a memory identifier")
        return str(rows[0].get("id", ""))
