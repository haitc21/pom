import unittest
from uuid import UUID

from aic.holmes import HolmesClient
from aic.service import build_holmes_prompt
from aic.schemas import ApprovalDecisionRequest, ChatResponse, PendingApprovalResponse, ToolDecision


class ToolApprovalContractTest(unittest.TestCase):
    def test_prompt_requires_native_approval_tool_for_bounded_remediation(self) -> None:
        prompt = build_holmes_prompt([], {}, [], [])

        self.assertIn("BẮT BUỘC gọi tool Kubernetes remediation", prompt)
        self.assertIn("không in lệnh thay đổi dưới dạng văn bản", prompt)

    def test_extracts_pending_holmes_approval(self) -> None:
        approval = HolmesClient._approval_from_event(
            {
                "requires_approval": True,
                "conversation_history": [{"role": "user", "content": "restart deployment"}],
                "pending_approvals": [
                    {
                        "tool_call_id": "call-1",
                        "tool_name": "run_kubectl_command",
                        "description": "rollout restart deployment/api",
                        "params": {"command": "kubectl rollout restart deployment/api -n demo"},
                    }
                ],
            }
        )

        self.assertIsNotNone(approval)
        assert approval is not None
        self.assertEqual(approval.pending_calls[0]["tool_call_id"], "call-1")
        self.assertEqual(approval.conversation_history[0]["role"], "user")

    def test_rejects_malformed_approval_event(self) -> None:
        self.assertIsNone(HolmesClient._approval_from_event({"requires_approval": True}))

    def test_pending_chat_response_and_explicit_decision_contract(self) -> None:
        approval_id = UUID("01900000-0000-7000-8000-000000000501")
        conversation_id = UUID("01900000-0000-7000-8000-000000000502")
        request_id = UUID("01900000-0000-7000-8000-000000000503")
        pending = PendingApprovalResponse.model_validate(
            {
                "approval_id": str(approval_id),
                "conversation_id": str(conversation_id),
                "request_id": str(request_id),
                "status": "pending",
                "actions": [
                    {
                        "tool_call_id": "call-1",
                        "tool_name": "run_kubectl_command",
                        "description": "patch configmap",
                        "params": {"command": "kubectl patch configmap"},
                    }
                ],
                "expires_at": "2026-08-19T12:00:00Z",
            }
        )
        response = ChatResponse(
            conversation_id=conversation_id,
            request_id=request_id,
            model="mistral-3.5",
            iteration=1,
            status="pending_approval",
            pending_approval=pending,
        )
        decision = ApprovalDecisionRequest(
            approved_by="devops-engineer",
            decisions=[ToolDecision(tool_call_id="call-1", approved=False, feedback="need change window")],
        )

        self.assertEqual(response.status, "pending_approval")
        self.assertIsNone(response.answer)
        self.assertFalse(decision.decisions[0].approved)


if __name__ == "__main__":
    unittest.main()
