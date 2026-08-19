"""Seed one engineer-approved resolution into the Compose Mem0/Qdrant store."""

import os
from mem0 import Memory

memory = Memory.from_config({
    "llm": {"provider": "openai", "config": {
        "model": os.environ.get("AIC_MODEL", "mistral-3.5"),
        "api_key": os.environ["LITELLM_API_KEY"],
        "openai_base_url": os.environ["LITELLM_BASE_URL"],
        "temperature": 0,
    }},
    "embedder": {"provider": "fastembed", "config": {
        "model": os.environ.get("MEM0_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        "embedding_dims": int(os.environ.get("MEM0_EMBEDDING_DIMS", "384")),
    }},
    "vector_store": {"provider": "qdrant", "config": {
        "url": os.environ.get("QDRANT_URL", "http://localhost:6333"),
        "collection_name": os.environ.get("MEM0_COLLECTION", "aic_incident_memory"),
        "embedding_model_dims": int(os.environ.get("MEM0_EMBEDDING_DIMS", "384")),
    }},
})

result = memory.add(
    "Approved resolution: CrashLoopBackOff caused by an injected command overriding the nginx entrypoint. The pod log showed /etc/demo/app.yaml not found and exit code 1. Remove the injected command/args, then verify AvailableReplicas, Ready condition, restart count and clean events.",
    user_id="aic-demo",
    agent_id="holmes-k8s-poc",
    metadata={"resolution_id": "demo-crashloop-approved", "approval_status": "approved", "case_id": "AIC-DEMO-CRASHLOOP-001"},
    infer=False,
)
print({"seeded": True, "result_count": len(result) if isinstance(result, list) else 1})
