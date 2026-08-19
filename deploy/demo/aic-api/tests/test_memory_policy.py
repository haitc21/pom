import unittest

from aic.memory_policy import candidate_allowed, extract_incident_signature, should_recall_memory


class MemoryPolicyTest(unittest.TestCase):
    def test_iteration_one_never_recalls_memory(self) -> None:
        self.assertFalse(should_recall_memory(iteration=1, command_output_count=3))

    def test_later_iteration_requires_live_command_output(self) -> None:
        self.assertFalse(should_recall_memory(iteration=2, command_output_count=0))
        self.assertTrue(should_recall_memory(iteration=2, command_output_count=1))

    def test_extracts_image_pull_failure_signature(self) -> None:
        signature = extract_incident_signature(
            "Pod is Pending with ErrImagePull followed by ImagePullBackOff"
        )
        self.assertEqual(signature["failure_reason"], "ImagePullBackOff")
        self.assertEqual(signature["incident_type"], "image_pull_failure")

    def test_extracts_service_selector_mismatch_signature(self) -> None:
        signature = extract_incident_signature(
            'selector={"app":"web-api","tier":"frontend"}\n'
            'endpoints=null\n'
            'pod labels={"app":"web-api","tier":"backend"}'
        )
        self.assertEqual(signature["failure_reason"], "service_selector_mismatch")
        self.assertEqual(signature["incident_type"], "service_routing_failure")

    def test_rejects_low_score_and_failure_reason_mismatch(self) -> None:
        required = {"failure_reason": "ImagePullBackOff"}
        self.assertFalse(
            candidate_allowed(
                score=0.30,
                minimum_score=0.45,
                metadata={"failure_reason": "ImagePullBackOff"},
                required_metadata=required,
            )
        )
        self.assertFalse(
            candidate_allowed(
                score=0.80,
                minimum_score=0.45,
                metadata={"failure_reason": "CrashLoopBackOff"},
                required_metadata=required,
            )
        )

    def test_accepts_relevant_approved_candidate(self) -> None:
        self.assertTrue(
            candidate_allowed(
                score=0.71,
                minimum_score=0.45,
                metadata={
                    "approval_status": "approved",
                    "failure_reason": "ImagePullBackOff",
                },
                required_metadata={"failure_reason": "ImagePullBackOff"},
            )
        )


if __name__ == "__main__":
    unittest.main()
