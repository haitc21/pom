import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MODEL_NAME = "mistral-3.5"
MAX_MESSAGE_LENGTH = 32 * 1024
MAX_CONTEXT_BYTES = 32 * 1024
MAX_COMMAND_LENGTH = 8 * 1024
MAX_COMMAND_OUTPUT_LENGTH = 256 * 1024
MAX_COMMAND_OUTPUTS = 20
MAX_RESOLUTION_ITEMS = 30


class CommandOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=1, max_length=MAX_COMMAND_LENGTH)
    exit_code: int
    output: str = Field(max_length=MAX_COMMAND_OUTPUT_LENGTH)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    conversation_id: UUID | None = None
    model: Literal["mistral-3.5"]
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    context: dict[str, Any] = Field(default_factory=dict)
    command_outputs: list[CommandOutput] = Field(default_factory=list, max_length=MAX_COMMAND_OUTPUTS)

    @field_validator("request_id")
    @classmethod
    def require_uuid7(cls, value: UUID) -> UUID:
        if value.version != 7:
            raise ValueError("request_id must be a UUIDv7")
        return value

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value

    @model_validator(mode="after")
    def bound_context(self) -> "ChatRequest":
        try:
            encoded = json.dumps(self.context, ensure_ascii=False, separators=(",", ":")).encode()
        except (TypeError, ValueError) as exc:
            raise ValueError("context must be JSON serializable") from exc
        if len(encoded) > MAX_CONTEXT_BYTES:
            raise ValueError(f"context exceeds {MAX_CONTEXT_BYTES} bytes")
        return self


class MemoryReference(BaseModel):
    memory_id: str
    score: float | None = None
    resolution_id: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    request_id: UUID
    model: Literal["mistral-3.5"]
    iteration: int = Field(ge=1, le=20)
    status: Literal["completed", "pending_approval"] = "completed"
    answer: str | None = None
    memory_references: list[MemoryReference] = Field(default_factory=list)
    pending_approval: "PendingApprovalResponse | None" = None


class PendingToolCall(BaseModel):
    tool_call_id: str
    tool_name: str
    description: str
    params: dict[str, Any] = Field(default_factory=dict)


class PendingApprovalResponse(BaseModel):
    approval_id: UUID
    conversation_id: UUID
    request_id: UUID
    status: Literal["pending"]
    actions: list[PendingToolCall] = Field(min_length=1)
    expires_at: datetime


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_by: str = Field(min_length=1, max_length=255)
    decisions: list["ToolDecision"] = Field(min_length=1, max_length=20)


class ToolDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_call_id: str = Field(min_length=1, max_length=255)
    approved: bool
    feedback: str | None = Field(default=None, max_length=4096)


class ApprovalResponse(PendingApprovalResponse):
    status: Literal["pending", "approved", "rejected", "expired", "completed"]
    approved_by: str | None = None
    decided_at: datetime | None = None
    final_response: ChatResponse | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "aic-api"


class MessageResponse(BaseModel):
    id: UUID
    request_id: UUID
    role: Literal["user", "assistant"]
    iteration: int = Field(ge=1)
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: UUID
    model: Literal["mistral-3.5"]
    status: str
    iteration: int = Field(ge=0)
    context: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: UUID
    messages: list[MessageResponse]


class RequestResponse(BaseModel):
    request_id: UUID
    conversation_id: UUID
    iteration: int = Field(ge=1)
    status: str
    error_code: str | None = None
    response: ChatResponse | None = None
    created_at: datetime
    updated_at: datetime


class ResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution_id: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    approved_by: str = Field(min_length=1, max_length=255)
    incident_type: str | None = Field(default=None, min_length=1, max_length=100)
    failure_reason: str | None = Field(default=None, min_length=1, max_length=100)
    resource_kind: str | None = Field(default=None, min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=32 * 1024)
    evidence: list[str] = Field(min_length=1, max_length=MAX_RESOLUTION_ITEMS)
    confirmed_facts: list[str] = Field(default_factory=list, max_length=MAX_RESOLUTION_ITEMS)
    unconfirmed_hypotheses: list[str] = Field(default_factory=list, max_length=MAX_RESOLUTION_ITEMS)
    approval_status: Literal["approved"] = "approved"


class ResolutionResponse(ResolutionRequest):
    conversation_id: UUID
    memory_id: str
    created_at: datetime
