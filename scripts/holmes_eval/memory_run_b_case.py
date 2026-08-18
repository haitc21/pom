"""Run a paired HolmesGPT + local Mem0 evaluation for one disposable case."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def redact(text: str) -> str:
    text = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(password\s*[=:]\s*)[^\s]+", r"\1[REDACTED]", text)
    return text


def memory_prompt(memory: str) -> str:
    return (
        "\n\n[MEMORY THAM KHẢO — KHÔNG PHẢI KẾT LUẬN HIỆN TẠI]\n"
        "Đây là resolution của một sự cố trước đây đã được kỹ sư xác nhận. "
        "Hãy dùng nó để ưu tiên giả thuyết, nhưng phải kiểm chứng bằng dữ liệu Kubernetes "
        "và Prometheus hiện tại; không sao chép remediation nếu bằng chứng khác nhau.\n"
        f"{memory}\n[ KẾT THÚC MEMORY — HÃY KIỂM CHỨNG ]\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--memory-document", required=True)
    args = parser.parse_args()

    from mem0 import Memory
    import httpx

    args.data_path.mkdir(parents=True, exist_ok=True)
    api_key = os.environ["LITELLM_API_KEY"]
    memory = Memory.from_config(
        {
            "llm": {"provider": "openai", "config": {
                "model": "mistral-3.5", "api_key": api_key,
                "openai_base_url": "https://llmpipe.vnpost.vn/v1",
                "temperature": 0, "max_tokens": 1000,
            }},
            "embedder": {"provider": "fastembed", "config": {
                "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "embedding_dims": 384,
            }},
            "vector_store": {"provider": "qdrant", "config": {
                "collection_name": f"postops_{args.case_id.lower().replace('-', '_')}",
                "path": str(args.data_path / "qdrant"), "embedding_model_dims": 384,
            }},
            "history_db_path": str(args.data_path / "history.db"),
        }
    )
    added = memory.add(
        args.memory_document, user_id="postops-poc", agent_id="holmes-k8s-poc",
        run_id=f"{args.case_id}-run-a", metadata={
            "case_id": args.case_id, "resolution_id": "run-a-approved-resolution",
            "approval_status": "approved", "source": f"docs/testing/holmesgpt/{args.case_id}/run-a-holmesgpt.md",
        }, infer=False,
    )
    found = memory.search(args.prompt, filters={"user_id": "postops-poc", "agent_id": "holmes-k8s-poc"}, limit=3)
    results = found.get("results", found if isinstance(found, list) else [])
    top = results[0] if results else {}
    recalled = top.get("memory", "")
    response = httpx.post(
        f"{args.base_url.rstrip('/')}/api/chat",
        json={"ask": args.prompt + memory_prompt(recalled), "model": "mistral"}, timeout=300,
    )
    response.raise_for_status()
    print(json.dumps({
        "case_id": args.case_id, "seed_count": len(added) if isinstance(added, list) else 1,
        "retrieved_count": len(results), "memory_id": top.get("id"), "score": top.get("score"),
        "response": redact(response.text),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
