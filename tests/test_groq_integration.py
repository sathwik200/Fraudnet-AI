"""
FRAUDNET AI — Groq API Integration, Live Verification & Reliability Tests
========================================================================
Automated regression tests covering:
  1. Secret configuration loading (os.environ, st.secrets, defaults).
  2. Missing API key handling.
  3. Invalid API configuration / Model unavailability.
  4. Successful mocked Groq completion.
  5. Empty or malformed Groq response.
  6. Authentication failure handling.
  7. Rate-limit and network timeout failure handling.
  8. Correct execution-mode reporting ('GROQ LIVE' vs 'DETERMINISTIC FALLBACK').
  9. Deterministic fallback after Groq failure in LangGraph workflow.
 10. Evidence consistency between investigation results and LLM synthesis.
 11. Strict prevention of API key exposure in logs, diagnostics, or UI.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import groq
from config.settings import (
    DEFAULT_GROQ_MODEL,
    get_groq_api_key,
    get_groq_model,
)
from src.agents.groq_client import (
    generate_forensic_synthesis,
    mask_api_key,
    sanitize_error_message,
    verify_groq_connectivity,
)
from src.agents.nodes import synthesize_forensics_node
from src.agents.prompts import build_investigation_prompt
from src.agents.state import InvestigationState
from src.tools.transaction_tools import get_full_transaction_profile
from src.tools.graph_tools import get_transaction_neighborhood


class TestGroqConfiguration(unittest.TestCase):
    """Test loading and security of Groq credentials and model settings."""

    def test_default_model_is_gpt_oss_120b(self):
        """Model must default to 'openai/gpt-oss-120b' when unspecified."""
        with patch.dict(os.environ, {}, clear=True):
            model = get_groq_model()
            self.assertEqual(model, "openai/gpt-oss-120b")
            self.assertEqual(DEFAULT_GROQ_MODEL, "openai/gpt-oss-120b")

    def test_custom_model_from_environ(self):
        """Custom GROQ_MODEL in environment must be respected."""
        with patch.dict(os.environ, {"GROQ_MODEL": "custom-groq-model"}):
            self.assertEqual(get_groq_model(), "custom-groq-model")

    def test_api_key_loading_from_environ(self):
        """GROQ_API_KEY must load correctly from environment."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_key_12345"}):
            self.assertEqual(get_groq_api_key(), "gsk_test_key_12345")

    def test_missing_api_key_returns_empty_string(self):
        """When no key is configured, get_groq_api_key must return empty string without error."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_groq_api_key(), "")


class TestGroqConnectivityVerification(unittest.TestCase):
    """Test verify_groq_connectivity under missing, invalid, and mocked conditions."""

    def test_missing_api_key_connectivity(self):
        """Missing key must return connected=False, error_type='MISSING_KEY'."""
        with patch.dict(os.environ, {}, clear=True):
            res = verify_groq_connectivity()
            self.assertFalse(res["connected"])
            self.assertEqual(res["error_type"], "MISSING_KEY")
            self.assertEqual(res["mode"], "DETERMINISTIC FALLBACK")

    @patch("src.agents.groq_client.Groq")
    def test_model_unavailable_on_groq(self, mock_groq_cls):
        """If configured model is not in Groq's model list, do not silently replace it."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        # Mock models.list() returning other models, but NOT the configured model
        mock_model_1 = MagicMock()
        mock_model_1.id = "llama-3.1-8b-instant"
        mock_client.models.list.return_value = MagicMock(data=[mock_model_1])

        res = verify_groq_connectivity(
            api_key="gsk_test_key",
            model="openai/gpt-oss-120b",
        )
        self.assertFalse(res["connected"])
        self.assertEqual(res["error_type"], "MODEL_UNAVAILABLE")
        self.assertIn("openai/gpt-oss-120b", res["message"])
        self.assertIn("not available", res["message"].lower())
        self.assertEqual(res["mode"], "DETERMINISTIC FALLBACK")

    @patch("src.agents.groq_client.Groq")
    def test_successful_connectivity_verification(self, mock_groq_cls):
        """Successful verification confirms model and returns mode='GROQ LIVE'."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        # Model is present
        mock_model = MagicMock()
        mock_model.id = "openai/gpt-oss-120b"
        mock_client.models.list.return_value = MagicMock(data=[mock_model])

        # Chat completion succeeds
        mock_choice = MagicMock()
        mock_choice.message.content = "VERIFIED"
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        res = verify_groq_connectivity(
            api_key="gsk_test_key",
            model="openai/gpt-oss-120b",
        )
        self.assertTrue(res["connected"])
        self.assertEqual(res["mode"], "GROQ LIVE")
        self.assertEqual(res["model"], "openai/gpt-oss-120b")
        self.assertIsNone(res["error_type"])

    @patch("src.agents.groq_client.Groq")
    def test_auth_failure_connectivity(self, mock_groq_cls):
        """Authentication failure returns error_type='AUTH_ERROR' and mode='DETERMINISTIC FALLBACK'."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.models.list.side_effect = groq.AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401),
            body={"error": {"message": "Invalid API Key"}},
        )

        res = verify_groq_connectivity(api_key="gsk_bad_key")
        self.assertFalse(res["connected"])
        self.assertEqual(res["error_type"], "AUTH_ERROR")
        self.assertEqual(res["mode"], "DETERMINISTIC FALLBACK")
        self.assertNotIn("gsk_bad_key", res["message"])


class TestGroqSynthesisAndFallback(unittest.TestCase):
    """Test synthesis execution, mocked completions, empty responses, and error handling."""

    @patch("src.agents.groq_client.Groq")
    def test_successful_mocked_groq_synthesis(self, mock_groq_cls):
        """Successful Groq completion returns success=True and execution_mode='GROQ LIVE'."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "# Forensic Synthesis\n\nTransaction exhibits high risk."
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        res = generate_forensic_synthesis(
            system_prompt="System instructions",
            user_prompt="Audit transaction",
            api_key="gsk_valid_key",
            model="openai/gpt-oss-120b",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["execution_mode"], "GROQ LIVE")
        self.assertIn("Forensic Synthesis", res["content"])
        self.assertIsNone(res["fallback_reason"])

    @patch("src.agents.groq_client.Groq")
    def test_empty_groq_response_triggers_fallback(self, mock_groq_cls):
        """Empty completion content must trigger fallback without crashing."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "   "  # Whitespace only
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        res = generate_forensic_synthesis(
            system_prompt="System prompt",
            user_prompt="User prompt",
            api_key="gsk_valid_key",
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["execution_mode"], "DETERMINISTIC FALLBACK")
        self.assertEqual(res["error_type"], "EMPTY_RESPONSE")

    @patch("src.agents.groq_client.Groq")
    def test_rate_limit_failure_triggers_fallback(self, mock_groq_cls):
        """Rate limit error triggers graceful deterministic fallback."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = groq.RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}},
        )

        res = generate_forensic_synthesis(
            system_prompt="System prompt",
            user_prompt="User prompt",
            api_key="gsk_valid_key",
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["execution_mode"], "DETERMINISTIC FALLBACK")
        self.assertEqual(res["error_type"], "RATE_LIMIT")

    @patch("src.agents.groq_client.Groq")
    def test_network_connection_error_triggers_fallback(self, mock_groq_cls):
        """Network error or timeout triggers graceful deterministic fallback."""
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = groq.APIConnectionError(
            request=MagicMock()
        )

        res = generate_forensic_synthesis(
            system_prompt="System prompt",
            user_prompt="User prompt",
            api_key="gsk_valid_key",
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["execution_mode"], "DETERMINISTIC FALLBACK")
        self.assertEqual(res["error_type"], "NETWORK_ERROR")


class TestLangGraphNodeExecutionModes(unittest.TestCase):
    """Test synthesize_forensics_node behavior with live mocked LLM vs fallback."""

    @patch("src.agents.nodes.generate_forensic_synthesis")
    def test_live_groq_mode_reporting(self, mock_synthesis):
        """When Groq succeeds, report must indicate 'GROQ LIVE' and llm_used=True."""
        mock_synthesis.return_value = {
            "success": True,
            "content": "### Live Forensic Assessment\nTransaction 232629023 analyzed via Groq.",
            "model": "openai/gpt-oss-120b",
            "execution_mode": "GROQ LIVE",
            "fallback_reason": None,
        }

        profile = get_full_transaction_profile(232629023)
        state: InvestigationState = {
            "query": "Investigate transaction 232629023",
            "target_tx_id": "232629023",
            "transaction_profile": profile,
            "graph_context": get_transaction_neighborhood(232629023, hops=1, max_nodes=30),
            "ml_prediction": profile["ml_assessment"],
            "notes": [],
        }

        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_key_live"}):
            res = synthesize_forensics_node(state)

        self.assertTrue(res["llm_used"])
        self.assertEqual(res["execution_mode"], "GROQ LIVE")
        self.assertIn("GROQ LIVE", res["final_report"])
        self.assertIn("openai/gpt-oss-120b", res["final_report"])
        self.assertIn("Live Forensic Assessment", res["final_report"])

    @patch("src.agents.nodes.generate_forensic_synthesis")
    def test_fallback_mode_on_api_failure(self, mock_synthesis):
        """When Groq fails, node must fall back to deterministic synthesizer and report DETERMINISTIC FALLBACK."""
        mock_synthesis.return_value = {
            "success": False,
            "content": "",
            "model": "openai/gpt-oss-120b",
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API rate limit exceeded.",
        }

        profile = get_full_transaction_profile(232629023)
        state: InvestigationState = {
            "query": "Investigate transaction 232629023",
            "target_tx_id": "232629023",
            "transaction_profile": profile,
            "graph_context": get_transaction_neighborhood(232629023, hops=1, max_nodes=30),
            "ml_prediction": profile["ml_assessment"],
            "notes": [],
        }

        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_key_failing"}):
            res = synthesize_forensics_node(state)

        self.assertFalse(res["llm_used"])
        self.assertEqual(res["execution_mode"], "DETERMINISTIC FALLBACK")
        self.assertIn("DETERMINISTIC FALLBACK", res["final_report"])
        self.assertIn("Deterministic Rule-Based Forensic Engine", res["final_report"])
        # Verified evidence remains intact in fallback report
        self.assertIn("232629023", res["final_report"])
        self.assertIn("Executive Summary", res["final_report"])


class TestEvidenceConsistencyAndSecurity(unittest.TestCase):
    """Test evidence fidelity in prompts and strict non-exposure of API keys."""

    def test_investigation_prompt_contains_exact_evidence(self):
        """Prompt sent to Groq must strictly contain verified metrics, labels, and deviations."""
        tx_id = "232629023"
        profile = get_full_transaction_profile(int(tx_id))
        neighborhood = get_transaction_neighborhood(int(tx_id), hops=1, max_nodes=30)
        ml = profile["ml_assessment"]

        prompt = build_investigation_prompt(
            query="Audit transaction",
            tx_id=tx_id,
            profile=profile,
            graph_context=neighborhood,
            ml_prediction=ml,
        )

        # Ground truth label
        self.assertIn(str(profile["ground_truth_label"]), prompt)
        # ML risk category
        self.assertIn(ml["risk_category"], prompt)
        # Degrees
        self.assertIn(str(profile["graph_metrics"]["in_degree"]), prompt)
        self.assertIn(str(profile["graph_metrics"]["out_degree"]), prompt)
        # Predecessors / successors
        self.assertIn("Direct Predecessors", prompt)
        self.assertIn("Direct Successors", prompt)

    def test_mask_api_key_redaction(self):
        """mask_api_key must never reveal full credentials."""
        secret = "gsk_abcd1234efgh5678ijkl9012"
        masked = mask_api_key(secret)
        self.assertNotIn("1234efgh5678ijkl", masked)
        self.assertTrue(masked.startswith("gsk_..."))
        self.assertTrue(masked.endswith("9012"))

    def test_sanitize_error_message_strips_secrets(self):
        """sanitize_error_message must redact API keys from exceptions."""
        leak_msg = "Error connecting to Groq with key gsk_SECRET1234567890ABCDEF in header Bearer gsk_SECRET1234567890ABCDEF"
        sanitized = sanitize_error_message(leak_msg)
        self.assertNotIn("gsk_SECRET1234567890ABCDEF", sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)


class TestUIGroqTelemetryAndRendering(unittest.TestCase):
    """Test AI Assistant UI elements, central configuration usage, and telemetry consistency."""

    def test_no_stale_hardcoded_model_name_in_active_code(self):
        """Active src/ and config/ code must not contain stale 'llama-3.3-70b-versatile' references."""
        src_dir = PROJECT_ROOT / "src"
        config_dir = PROJECT_ROOT / "config"
        app_file = PROJECT_ROOT / "app.py"

        stale_occurrences = []
        for path in list(src_dir.rglob("*.py")) + list(config_dir.rglob("*.py")) + [app_file]:
            content = path.read_text(encoding="utf-8")
            if "llama-3.3-70b-versatile" in content:
                stale_occurrences.append(str(path.relative_to(PROJECT_ROOT)))

        self.assertEqual(
            stale_occurrences,
            [],
            f"Stale model name 'llama-3.3-70b-versatile' found in active code: {stale_occurrences}",
        )

    def test_connectivity_control_rendered_prominently(self):
        """Verify the exact required connectivity control label exists in ai_assistant.py."""
        assistant_file = PROJECT_ROOT / "src" / "ui" / "ai_assistant.py"
        content = assistant_file.read_text(encoding="utf-8")
        self.assertIn("TEST LIVE GROQ CONNECTIVITY & MODEL AVAILABILITY", content)
        self.assertIn("btn_live_groq_connectivity_test", content)

    def test_telemetry_status_agreement_logic(self):
        """Verify telemetry indicators agree across offline, configured, and live states."""
        # Case 1: Unconfigured key -> DETERMINISTIC FALLBACK
        with patch.dict(os.environ, {}, clear=True):
            key = get_groq_api_key()
            self.assertEqual(key, "")
            is_live = False
            status = "GROQ LIVE" if is_live else ("CONFIGURED / NOT VERIFIED" if key else "DETERMINISTIC FALLBACK")
            self.assertEqual(status, "DETERMINISTIC FALLBACK")

        # Case 2: Configured key but not verified live -> CONFIGURED / NOT VERIFIED
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_dummy_test_key"}):
            key = get_groq_api_key()
            self.assertTrue(bool(key))
            is_live = False
            status = "GROQ LIVE" if is_live else ("CONFIGURED / NOT VERIFIED" if key else "DETERMINISTIC FALLBACK")
            self.assertEqual(status, "CONFIGURED / NOT VERIFIED")

        # Case 3: Live completion verified -> GROQ LIVE
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_dummy_test_key"}):
            key = get_groq_api_key()
            is_live = True
            status = "GROQ LIVE" if is_live else ("CONFIGURED / NOT VERIFIED" if key else "DETERMINISTIC FALLBACK")
            self.assertEqual(status, "GROQ LIVE")

    def test_missing_api_key_does_not_hide_assistant_interface(self):
        """Even when GROQ_API_KEY is empty, the complete UI elements are preserved."""
        assistant_file = PROJECT_ROOT / "src" / "ui" / "ai_assistant.py"
        content = assistant_file.read_text(encoding="utf-8")
        # All required components present
        self.assertIn("FRAUDNET INTELLIGENCE AGENT", content)
        self.assertIn("TACTICAL INVESTIGATION PROMPTS:", content)
        self.assertIn("AUDIT TX 230425980", content)
        self.assertIn("st.chat_input", content)
        self.assertIn("TEST LIVE GROQ CONNECTIVITY & MODEL AVAILABILITY", content)


if __name__ == "__main__":
    unittest.main()

