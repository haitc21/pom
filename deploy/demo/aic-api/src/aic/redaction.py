import re
from typing import Any

REDACTED = "[REDACTED]"

_PRIVATE_KEY = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----.*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)
_KEY_VALUE_PATTERNS = (
    re.compile(r"(?i)(\bauthorization\s*:\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)(\b(?:api[_-]?key|password|access[_-]?token|client-key-data)\s*[:=]\s*)[^\s,;]+"),
    re.compile(
        r"(?i)([\"'](?:api[_-]?key|password|access[_-]?token|client-key-data)[\"']\s*:\s*[\"'])[^\"']+"
    ),
)
_SENSITIVE_KEY = re.compile(
    r"(?i)^(?:authorization|api[_-]?key|password|access[_-]?token|token|client[_-]?key[_-]?data)$"
)


def redact(text: str) -> str:
    sanitized = _PRIVATE_KEY.sub(REDACTED, text)
    for pattern in _KEY_VALUE_PATTERNS:
        sanitized = pattern.sub(lambda match: f"{match.group(1)}{REDACTED}", sanitized)
    return sanitized


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {
            str(key): REDACTED if _SENSITIVE_KEY.match(str(key)) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value
