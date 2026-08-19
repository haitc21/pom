from typing import Any


FAILURE_SIGNATURES: tuple[tuple[str, str], ...] = (
    ("ImagePullBackOff", "image_pull_failure"),
    ("ErrImagePull", "image_pull_failure"),
    ("CrashLoopBackOff", "container_crash"),
    ("OOMKilled", "resource_exhaustion"),
    ("FailedScheduling", "scheduling_failure"),
)


def should_recall_memory(iteration: int, command_output_count: int) -> bool:
    """Require current command evidence before historical guidance is eligible."""
    return iteration > 1 and command_output_count > 0


def extract_incident_signature(text: str) -> dict[str, str]:
    for failure_reason, incident_type in FAILURE_SIGNATURES:
        if failure_reason.lower() in text.lower():
            canonical_reason = "ImagePullBackOff" if incident_type == "image_pull_failure" else failure_reason
            return {"failure_reason": canonical_reason, "incident_type": incident_type}
    normalized = text.lower()
    if "selector" in normalized and "endpoints=null" in normalized:
        return {
            "failure_reason": "service_selector_mismatch",
            "incident_type": "service_routing_failure",
        }
    return {}


def candidate_allowed(
    *,
    score: float | None,
    minimum_score: float,
    metadata: dict[str, Any],
    required_metadata: dict[str, str],
) -> bool:
    if score is None or score < minimum_score:
        return False
    if metadata.get("approval_status") != "approved":
        return False
    return all(metadata.get(key) == value for key, value in required_metadata.items())
