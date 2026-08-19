import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from aic.config import get_settings
from aic.db import get_db
from aic.holmes import HolmesClient
from aic.memory import MemoryStore
from aic.models import Conversation, Message, RequestRecord, ResolutionRecord, ToolApprovalRecord
from aic.schemas import (
    ChatRequest,
    ChatResponse,
    ApprovalDecisionRequest,
    ApprovalResponse,
    ConversationMessagesResponse,
    ConversationResponse,
    HealthResponse,
    MessageResponse,
    RequestResponse,
    ResolutionRequest,
    ResolutionResponse,
    PendingApprovalResponse,
    PendingToolCall,
)
from aic.redaction import redact, redact_value
from aic.service import ChatService, DomainError

settings = get_settings()
logging.basicConfig(level=settings.aic_log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("aic")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chat_service = ChatService(settings, MemoryStore(settings), HolmesClient(settings))
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
DbSession = Annotated[Session, Depends(get_db)]


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health(session: DbSession) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("database healthcheck failed", exc_info=False)
        raise HTTPException(status_code=503, detail={"code": "database_unavailable"}) from exc
    return HealthResponse()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, session: DbSession) -> ChatResponse:
    service: ChatService = app.state.chat_service
    try:
        return service.handle(session, request)
    except DomainError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)}
        ) from exc
    except Exception as exc:
        session.rollback()
        logger.exception("unhandled AIC request failure")
        raise HTTPException(status_code=500, detail={"code": "internal_error"}) from exc


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse, tags=["conversations"])
def get_conversation(conversation_id: UUID, session: DbSession) -> ConversationResponse:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "conversation does not exist"})
    return ConversationResponse(
        conversation_id=conversation.id,
        model=conversation.model,
        status=conversation.status,
        iteration=conversation.iteration,
        context=conversation.context_json,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@app.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
    tags=["conversations"],
)
def get_conversation_messages(conversation_id: UUID, session: DbSession) -> ConversationMessagesResponse:
    if session.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "conversation does not exist"})
    messages = session.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.role.desc())
    ).all()
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[
            MessageResponse(
                id=item.id,
                request_id=item.request_id,
                role=item.role,
                iteration=item.iteration,
                content=item.content,
                created_at=item.created_at,
            )
            for item in messages
        ],
    )


@app.get("/api/requests/{request_id}", response_model=RequestResponse, tags=["requests"])
def get_request(request_id: UUID, session: DbSession) -> RequestResponse:
    record = session.get(RequestRecord, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "request does not exist"})
    response = ChatResponse.model_validate(record.response_json) if record.response_json else None
    return RequestResponse(
        request_id=record.request_id,
        conversation_id=record.conversation_id,
        iteration=record.iteration,
        status=record.status,
        error_code=record.error_code,
        response=response,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _approval_response(record: ToolApprovalRecord) -> ApprovalResponse:
    request = record.request_id
    return ApprovalResponse(
        approval_id=record.id,
        conversation_id=record.conversation_id,
        request_id=request,
        status=record.status,
        actions=[
            PendingToolCall(
                tool_call_id=str(item["tool_call_id"]),
                tool_name=str(item.get("tool_name", "unknown")),
                description=str(item.get("description", "HolmesGPT remediation action")),
                params=item.get("params") if isinstance(item.get("params"), dict) else {},
            )
            for item in record.pending_calls_json
        ],
        expires_at=record.expires_at,
        approved_by=record.approved_by,
        decided_at=record.decided_at,
        final_response=ChatResponse.model_validate(record.final_response_json)
        if record.final_response_json
        else None,
    )


@app.get("/api/approvals/{approval_id}", response_model=ApprovalResponse, tags=["approvals"])
def get_approval(approval_id: UUID, session: DbSession) -> ApprovalResponse:
    record = session.get(ToolApprovalRecord, approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "approval does not exist"})
    if record.status == "pending" and record.expires_at <= datetime.now(UTC):
        record.status = "expired"
        session.commit()
    return _approval_response(record)


@app.post("/api/approvals/{approval_id}/decision", response_model=ApprovalResponse, tags=["approvals"])
def decide_approval(approval_id: UUID, decision: ApprovalDecisionRequest, session: DbSession) -> ApprovalResponse:
    record = session.scalar(select(ToolApprovalRecord).where(ToolApprovalRecord.id == approval_id).with_for_update())
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "approval does not exist"})
    if record.status != "pending":
        raise HTTPException(status_code=409, detail={"code": "conflict", "message": "approval is not pending"})
    if record.expires_at <= datetime.now(UTC):
        record.status = "expired"
        session.commit()
        raise HTTPException(status_code=409, detail={"code": "expired", "message": "approval has expired"})
    expected_ids = {str(item["tool_call_id"]) for item in record.pending_calls_json}
    received_ids = {item.tool_call_id for item in decision.decisions}
    if received_ids != expected_ids or len(decision.decisions) != len(expected_ids):
        raise HTTPException(status_code=422, detail={"code": "invalid_decisions", "message": "decide every pending tool exactly once"})

    record.approved_by = redact(decision.approved_by)
    record.decisions_json = redact_value([item.model_dump() for item in decision.decisions])
    record.decided_at = datetime.now(UTC)
    if not all(item.approved for item in decision.decisions):
        record.status = "rejected"
        session.commit()
        return _approval_response(record)

    conversation = session.get(Conversation, record.conversation_id)
    request = session.get(RequestRecord, record.request_id)
    if conversation is None or request is None:
        raise HTTPException(status_code=409, detail={"code": "invalid_state", "message": "approval parent missing"})
    try:
        result = app.state.chat_service.holmes.chat(
            "Continue the approved remediation and then report verified current evidence.",
            conversation.model,
            conversation_history=record.conversation_history_json,
            tool_decisions=record.decisions_json,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"code": "holmes_unavailable", "message": "unable to resume HolmesGPT"}) from exc
    if result.approval is not None:
        record.pending_calls_json = redact_value(result.approval.pending_calls)
        record.conversation_history_json = redact_value(result.approval.conversation_history)
        record.approved_by = None
        record.decisions_json = None
        record.decided_at = None
        record.expires_at = datetime.now(UTC) + timedelta(seconds=settings.holmes_approval_ttl_seconds)
        session.commit()
        return _approval_response(record)

    pending_response = ChatResponse.model_validate(request.response_json)
    final = ChatResponse(
        conversation_id=conversation.id,
        request_id=request.request_id,
        model=conversation.model,
        iteration=request.iteration,
        answer=redact(result.answer or ""),
        memory_references=pending_response.memory_references,
    )
    session.add(Message(conversation_id=conversation.id, request_id=request.request_id, role="assistant", iteration=request.iteration, content=final.answer or ""))
    request.status = "completed"
    request.response_json = final.model_dump(mode="json")
    conversation.status = "active"
    record.status = "completed"
    record.final_response_json = final.model_dump(mode="json")
    session.commit()
    return _approval_response(record)


@app.post(
    "/api/conversations/{conversation_id}/resolution",
    response_model=ResolutionResponse,
    status_code=201,
    tags=["resolutions"],
)
def approve_resolution(
    conversation_id: UUID, request: ResolutionRequest, session: DbSession
) -> ResolutionResponse:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "conversation does not exist"})

    existing = session.scalar(
        select(ResolutionRecord).where(ResolutionRecord.resolution_id == request.resolution_id)
    )
    if existing is not None:
        if existing.conversation_id != conversation_id:
            raise HTTPException(
                status_code=409,
                detail={"code": "conflict", "message": "resolution_id belongs to another conversation"},
            )
        if existing.memory_id:
            return _resolution_response(existing)
        record = existing
    else:
        record = ResolutionRecord(
            resolution_id=request.resolution_id,
            conversation_id=conversation_id,
            approved_by=redact(request.approved_by),
            incident_type=request.incident_type,
            failure_reason=request.failure_reason,
            resource_kind=request.resource_kind,
            summary=redact(request.summary),
            evidence_json=redact_value(request.evidence),
            confirmed_facts_json=redact_value(request.confirmed_facts),
            unconfirmed_hypotheses_json=redact_value(request.unconfirmed_hypotheses),
            approval_status=request.approval_status,
        )
        session.add(record)
        session.flush()

    memory_text = "\n".join(
        [
            "Historical investigation guidance only; this is not evidence for the current incident.",
            f"Historical outcome: {record.summary}",
            "Previously confirmed facts (must be re-verified now):\n- "
            + "\n- ".join(record.confirmed_facts_json),
            "Unconfirmed hypotheses and causal links (never state as facts):\n- "
            + "\n- ".join(record.unconfirmed_hypotheses_json),
            "Useful discriminating checks from the historical case:\n- "
            + "\n- ".join(record.evidence_json),
        ]
    )
    metadata = {
        "resolution_id": record.resolution_id,
        "approval_status": record.approval_status,
        "approved_by": record.approved_by,
        "conversation_id": str(conversation_id),
        "model": conversation.model,
    }
    if record.incident_type:
        metadata["incident_type"] = record.incident_type
    if record.failure_reason:
        metadata["failure_reason"] = record.failure_reason
    if record.resource_kind:
        metadata["resource_kind"] = record.resource_kind
    try:
        record.memory_id = app.state.chat_service.memory.add_approved(memory_text, metadata)
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception("failed to index approved resolution")
        raise HTTPException(
            status_code=502,
            detail={"code": "memory_unavailable", "message": "approved resolution was not indexed"},
        ) from exc
    return _resolution_response(record)


def _resolution_response(record: ResolutionRecord) -> ResolutionResponse:
    return ResolutionResponse(
        resolution_id=record.resolution_id,
        approved_by=record.approved_by,
        incident_type=record.incident_type,
        failure_reason=record.failure_reason,
        resource_kind=record.resource_kind,
        summary=record.summary,
        evidence=record.evidence_json,
        confirmed_facts=record.confirmed_facts_json,
        unconfirmed_hypotheses=record.unconfirmed_hypotheses_json,
        approval_status="approved",
        conversation_id=record.conversation_id,
        memory_id=record.memory_id or "",
        created_at=record.created_at,
    )
