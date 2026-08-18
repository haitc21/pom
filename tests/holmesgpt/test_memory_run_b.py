import unittest

from scripts.holmes_eval import memory_run_b


class MemoryRunBUnitTests(unittest.TestCase):
    def test_build_resolution_document_preserves_engineer_approved_answer(self):
        document = memory_run_b.build_resolution_document()

        self.assertIn("CKAD-LIFE-001", document)
        self.assertIn("command/args", document)
        self.assertIn("exit 1", document)
        self.assertIn("approved", document)

    def test_build_memory_prompt_marks_recalled_context_as_non_authoritative(self):
        prompt = memory_run_b.build_memory_prompt("prior approved resolution")

        self.assertIn("tham khảo", prompt.lower())
        self.assertIn("kiểm chứng", prompt.lower())
        self.assertIn("prior approved resolution", prompt)

    def test_redact_response_removes_authorization_and_api_key_values(self):
        redacted = memory_run_b.redact_response(
            "Authorization: Bearer <token> api_key=<key>"
        )

        self.assertNotIn("<token>", redacted)
        self.assertNotIn("<key>", redacted)
        self.assertIn("[REDACTED]", redacted)


if __name__ == "__main__":
    unittest.main()
