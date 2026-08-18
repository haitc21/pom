"""Minimal local Mem0 + HolmesGPT Run B harness for CKAD-LIFE-001."""

from __future__ import annotations

import os
import re
import argparse
import json
from pathlib import Path
from typing import Any


CASE_ID = "CKAD-LIFE-001"
MODEL = "mistral"
LITELLM_BASE_URL = "https://llmpipe.vnpost.vn/v1"


def build_resolution_document() -> str:
    """Return the engineer-approved Run A resolution used as the seed memory."""

    return (
        f"Approved incident resolution {CASE_ID}. "
        "Symptom: nginx container enters CrashLoopBackOff and Deployment is unavailable. "
        "Confirmed root cause: injected command/args print a missing configuration-file "
        "error and exit 1, overriding the image entrypoint. "
        "Evidence: container log says '/etc/demo/app.yaml not found', exit code is 1, "
        "and the BackOff event repeats while the image is already present and scheduled. "
        "Effective remediation: remove the injected command/args or restore the normal "
        "nginx entrypoint. Verify Deployment AvailableReplicas, Pod Ready, stable restart "
        "count, and clean logs/events. approval_status=approved."
    )


def build_memory_prompt(memory_text: str) -> str:
    """Wrap recalled memory as non-authoritative context for HolmesGPT."""

    return (
        "\n\n[MEMORY THAM KHẢO — KHÔNG PHẢI KẾT LUẬN HIỆN TẠI]\n"
        "Đây là resolution của một sự cố trước đây đã được kỹ sư xác nhận. "
        "Hãy dùng nó để ưu tiên giả thuyết, nhưng phải kiểm chứng bằng dữ liệu Kubernetes "
        "và Prometheus hiện tại; không sao chép remediation nếu namespace, workload hoặc "
        "bằng chứng khác nhau.\n"
        f"{memory_text}\n"
        "[KẾT THÚC MEMORY — HÃY KIỂM CHỨNG]\n"
    )


def redact_response(text: str) -> str:
    """Redact credential-like values before writing a result file."""

    text = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(password\s*[=:]\s*)[^\s]+", r"\1[REDACTED]", text)
    return text


def create_memory(data_path: Path):
    """Create a local Mem0 instance using FastEmbed and embedded Qdrant."""

    from mem0 import Memory

    api_key = os.environ["LITELLM_API_KEY"]
    return Memory.from_config(
        {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "mistral-3.5",
                    "api_key": api_key,
                    "openai_base_url": LITELLM_BASE_URL,
                    "temperature": 0,
                    "max_tokens": 1000,
                },
            },
            "embedder": {
                "provider": "fastembed",
                "config": {
                    "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    "embedding_dims": 384,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "postops_ckad_life_001",
                    "path": str(data_path / "qdrant"),
                    "embedding_model_dims": 384,
                },
            },
            "history_db_path": str(data_path / "history.db"),
        }
    )


def seed_and_recall(memory: Any, query: str) -> dict[str, Any]:
    """Seed approved Run A once and return the best scoped recall."""

    added = memory.add(
        build_resolution_document(),
        user_id="postops-poc",
        agent_id="holmes-k8s-poc",
        run_id="CKAD-LIFE-001-run-a",
        metadata={
            "case_id": CASE_ID,
            "resolution_id": "run-a-approved-resolution",
            "approval_status": "approved",
            "source": "docs/testing/holmesgpt/CKAD-LIFE-001/run-a-holmesgpt.md",
        },
        infer=False,
    )
    found = memory.search(
        query,
        filters={"user_id": "postops-poc", "agent_id": "holmes-k8s-poc"},
        limit=3,
    )
    results = found.get("results", found if isinstance(found, list) else [])
    top = results[0] if results else {}
    return {
        "seed_count": len(added) if isinstance(added, list) else 1,
        "retrieved_count": len(results),
        "memory_id": top.get("id"),
        "score": top.get("score"),
        "memory": top.get("memory"),
    }


def ask_holmesgpt(base_url: str, prompt: str) -> str:
    """Call HolmesGPT; never execute commands found in its response."""

    import httpx

    response = httpx.post(
        f"{base_url.rstrip('/')}/api/chat",
        json={"ask": prompt, "model": MODEL},
        timeout=300,
    )
    response.raise_for_status()
    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    args.data_path.mkdir(parents=True, exist_ok=True)
    memory = create_memory(args.data_path)
    recall = seed_and_recall(memory, args.prompt)
    response = redact_response(ask_holmesgpt(args.base_url, args.prompt + build_memory_prompt(recall["memory"] or "")))
    print(json.dumps({"recall": recall, "response": response}, ensure_ascii=False))


if __name__ == "__main__":
    main()
