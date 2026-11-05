"""
FRAUDNET AI — Official Groq Client & API Verification Engine
=============================================================
Manages secure connection, model discovery, connectivity verification,
and natural language forensic synthesis via the official Groq SDK.

Specialized for Groq GPT-OSS Models:
  - Supports 'openai/gpt-oss-120b' and reasoning models.
  - Suppresses separate internal reasoning stream ('include_reasoning=False', 'reasoning_effort=low').
  - Employs 'max_completion_tokens' with suitable token budget to avoid reasoning starvation.
  - Strictly extracts user-facing message content without exposing internal reasoning.
  - Provides diagnostic classification for empty completions, token exhaustion, refusals, tool calls, and API errors.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import groq
from groq import Groq

from config.settings import (
    DEFAULT_GROQ_MODEL,
    GROQ_CONNECTIVITY_TOKEN_BUDGET,
    GROQ_MAX_TOKENS,
    GROQ_REASONING_EFFORT,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT_SECONDS,
    get_groq_api_key,
    get_groq_model,
)

logger = logging.getLogger("fraudnet.groq")

# Regex pattern for sanitizing Groq / Bearer API keys in error messages
_KEY_PATTERN = re.compile(r"(gsk_[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9_.-]{8,})", re.IGNORECASE)


def sanitize_error_message(raw_message: Any) -> str:
    """
    Remove any API keys, Bearer tokens, or raw authentication headers from error strings.
    """
    msg = str(raw_message)
    sanitized = _KEY_PATTERN.sub("[REDACTED_API_KEY]", msg)
    return sanitized


def mask_api_key(api_key: Optional[str] = None) -> str:
    """
    Produce a safe masked preview of an API key (e.g. 'gsk_...a1b2') without leaking the secret.
    """
    key = api_key if api_key is not None else get_groq_api_key()
    if not key or not key.strip():
        return "[NOT CONFIGURED]"
    key_str = key.strip()
    if len(key_str) <= 8:
        return "[CONFIGURED: *******]"
    return f"{key_str[:4]}...{key_str[-4:]}"


def get_groq_client(
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Groq:
    """
    Instantiate the official Groq client with configured timeout.

    Raises:
        ValueError: If no GROQ_API_KEY is found in environment or secrets.
    """
    key = api_key.strip() if (api_key and api_key.strip()) else get_groq_api_key()
    if not key:
        raise ValueError("GROQ_API_KEY is not configured.")

    t_sec = float(timeout) if timeout is not None else GROQ_TIMEOUT_SECONDS
    return Groq(api_key=key, timeout=t_sec)


def extract_completion_content(response: Any, model_name: str) -> Dict[str, Any]:
    """
    Safely extract user-facing assistant content and diagnostic metadata from a Groq Chat Completion.

    Distinguishes:
      - Normal non-empty text completion.
      - Token-limit exhaustion (finish_reason='length' with empty content).
      - Model refusal (message.refusal present).
      - Unexpected tool-call response.
      - Empty completion.

    Rules:
      - Does NOT treat internal reasoning fields as user-facing answers.
      - Never includes sensitive credentials in output.
    """
    choices = getattr(response, "choices", None)
    if not choices or len(choices) == 0:
        return {
            "success": False,
            "content": "",
            "error_type": "EMPTY_CHOICES",
            "fallback_reason": "Groq returned a response object with zero choices.",
            "diagnostics": {
                "model": getattr(response, "model", model_name),
                "finish_reason": "none",
                "has_content": False,
                "content_length": 0,
                "has_refusal": False,
                "has_tool_calls": False,
                "has_reasoning": False,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }

    choice = choices[0]
    message = getattr(choice, "message", None)
    finish_reason = getattr(choice, "finish_reason", None)
    finish_reason_str = str(finish_reason) if finish_reason is not None else "unknown"

    raw_content = getattr(message, "content", None)
    # Check if raw_content is a mock or actual text
    if raw_content is None or hasattr(raw_content, "_mock_return_value"):
        content = ""
    else:
        content = str(raw_content).strip()

    raw_refusal = getattr(message, "refusal", None)
    has_refusal = bool(raw_refusal) and not hasattr(raw_refusal, "_mock_return_value") and bool(str(raw_refusal).strip())

    raw_tools = getattr(message, "tool_calls", None)
    has_tools = bool(raw_tools) and not hasattr(raw_tools, "_mock_return_value") and isinstance(raw_tools, (list, tuple)) and len(raw_tools) > 0

    raw_reasoning = getattr(message, "reasoning", None)
    has_reasoning = bool(raw_reasoning) and not hasattr(raw_reasoning, "_mock_return_value") and bool(str(raw_reasoning).strip())

    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage and not hasattr(usage, "_mock_return_value") else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage and not hasattr(usage, "_mock_return_value") else None
    total_tokens = getattr(usage, "total_tokens", None) if usage and not hasattr(usage, "_mock_return_value") else None

    diagnostics = {
        "model": getattr(response, "model", model_name) if not hasattr(getattr(response, "model", None), "_mock_return_value") else model_name,
        "finish_reason": finish_reason_str,
        "has_content": bool(content),
        "content_length": len(content),
        "has_refusal": has_refusal,
        "has_tool_calls": has_tools,
        "has_reasoning": has_reasoning,
        "prompt_tokens": prompt_tokens if isinstance(prompt_tokens, int) else None,
        "completion_tokens": completion_tokens if isinstance(completion_tokens, int) else None,
        "total_tokens": total_tokens if isinstance(total_tokens, int) else None,
    }

    # Case 1: Model Refusal
    if has_refusal:
        clean_refusal = sanitize_error_message(raw_refusal)
        return {
            "success": False,
            "content": "",
            "error_type": "REFUSAL",
            "fallback_reason": f"Model refused completion: {clean_refusal}",
            "diagnostics": diagnostics,
        }

    # Case 2: Tool Call instead of message text
    if has_tools and not content:
        return {
            "success": False,
            "content": "",
            "error_type": "TOOL_CALL_RESPONSE",
            "fallback_reason": f"Model returned unexpected tool call(s) ({len(raw_tools)} calls) instead of text completion.",
            "diagnostics": diagnostics,
        }

    # Case 3: Token budget exhausted before user-facing content generated
    if finish_reason_str == "length" and not content:
        return {
            "success": False,
            "content": "",
            "error_type": "TOKEN_LIMIT_EXHAUSTED",
            "fallback_reason": (
                f"Token budget exhausted before user-facing content could be emitted "
                f"(finish_reason='length', completion_tokens={completion_tokens})."
            ),
            "diagnostics": diagnostics,
        }

    # Case 4: Completely empty content (even though finish_reason is stop/unknown)
    if not content:
        return {
            "success": False,
            "content": "",
            "error_type": "EMPTY_COMPLETION",
            "fallback_reason": (
                f"Groq returned an empty user-facing message content "
                f"(finish_reason='{finish_reason_str}', completion_tokens={completion_tokens})."
            ),
            "diagnostics": diagnostics,
        }

    # Case 5: Valid, non-empty user-facing content
    return {
        "success": True,
        "content": content,
        "error_type": None,
        "fallback_reason": None,
        "diagnostics": diagnostics,
    }


def build_completion_kwargs(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    token_budget: int,
) -> Dict[str, Any]:
    """
    Construct optimal Chat Completion parameters tailored for Groq models (including GPT-OSS).
    """
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": token_budget,
        "stream": False,
    }

    # For GPT-OSS models, configure reasoning suppression and effort
    is_gpt_oss = "gpt-oss" in model.lower()
    if is_gpt_oss:
        kwargs["include_reasoning"] = False
        kwargs["reasoning_effort"] = GROQ_REASONING_EFFORT

    return kwargs


def verify_groq_connectivity(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Verify live Groq API connectivity and target model availability.

    Performs:
      1. Key presence validation.
      2. Model availability verification via models.list() endpoint.
      3. Live minimal chat completion test with GPT-OSS parameters:
         - User message: "Reply with exactly the word VERIFIED."
         - max_completion_tokens: GROQ_CONNECTIVITY_TOKEN_BUDGET (250 tokens)
         - include_reasoning: False
         - reasoning_effort: "low"
         - stream: False

    Returns:
        Structured result dict with 'connected', 'mode', 'model', 'message', 'error_type', 'diagnostics'.
    """
    target_key = api_key.strip() if (api_key and api_key.strip()) else get_groq_api_key()
    target_model = model.strip() if (model and model.strip()) else get_groq_model()

    if not target_key:
        return {
            "connected": False,
            "mode": "DETERMINISTIC FALLBACK",
            "model": target_model,
            "message": "GROQ_API_KEY is not configured. Deterministic fallback engine is active.",
            "error_type": "MISSING_KEY",
            "available_models": [],
            "diagnostics": None,
        }

    try:
        client = get_groq_client(api_key=target_key, timeout=timeout)

        # Step 1: Model List Endpoint Verification
        models_resp = client.models.list()
        available_model_ids: List[str] = [m.id for m in models_resp.data] if hasattr(models_resp, "data") else []

        if target_model not in available_model_ids:
            return {
                "connected": False,
                "mode": "DETERMINISTIC FALLBACK",
                "model": target_model,
                "message": (
                    f"Configured model '{target_model}' is not available on Groq Cloud. "
                    f"Available models count: {len(available_model_ids)}. "
                    "Per project rules, model will not be silently replaced."
                ),
                "error_type": "MODEL_UNAVAILABLE",
                "available_models": available_model_ids,
                "diagnostics": None,
            }

        # Step 2: Live Chat Completion Verification with GPT-OSS Parameters
        test_messages = [
            {"role": "user", "content": "Reply with exactly the word VERIFIED."},
        ]

        kwargs = build_completion_kwargs(
            model=target_model,
            messages=test_messages,
            temperature=0.0,
            token_budget=GROQ_CONNECTIVITY_TOKEN_BUDGET,
        )

        try:
            chat_resp = client.chat.completions.create(**kwargs)
        except groq.BadRequestError as bad_req:
            # If the specific endpoint rejected reasoning parameters, retry with base parameters
            clean_bad = sanitize_error_message(bad_req)
            if "reasoning" in clean_bad.lower():
                kwargs.pop("include_reasoning", None)
                kwargs.pop("reasoning_effort", None)
                chat_resp = client.chat.completions.create(**kwargs)
            else:
                raise

        extracted = extract_completion_content(chat_resp, target_model)

        if not extracted["success"]:
            return {
                "connected": False,
                "mode": "DETERMINISTIC FALLBACK",
                "model": target_model,
                "message": extracted["fallback_reason"],
                "error_type": extracted["error_type"],
                "available_models": available_model_ids,
                "diagnostics": extracted["diagnostics"],
            }

        content = extracted["content"]
        return {
            "connected": True,
            "mode": "GROQ LIVE",
            "model": target_model,
            "sample_response": content[:60],
            "message": f"Groq API connection and model '{target_model}' verified successfully (Response: '{content[:60]}').",
            "error_type": None,
            "available_models": available_model_ids,
            "diagnostics": extracted["diagnostics"],
        }

    except groq.AuthenticationError as exc:
        logger.warning("Groq authentication failure: %s", sanitize_error_message(exc))
        return {
            "connected": False,
            "mode": "DETERMINISTIC FALLBACK",
            "model": target_model,
            "message": "Groq API authentication failed. Please verify that GROQ_API_KEY is valid.",
            "error_type": "AUTH_ERROR",
            "available_models": [],
            "diagnostics": None,
        }

    except groq.RateLimitError as exc:
        logger.warning("Groq rate limit reached: %s", sanitize_error_message(exc))
        return {
            "connected": False,
            "mode": "DETERMINISTIC FALLBACK",
            "model": target_model,
            "message": "Groq API rate limit exceeded. Operating in deterministic fallback mode.",
            "error_type": "RATE_LIMIT",
            "available_models": [],
            "diagnostics": None,
        }

    except (groq.APIConnectionError, groq.APITimeoutError) as exc:
        logger.warning("Groq network connection issue: %s", sanitize_error_message(exc))
        return {
            "connected": False,
            "mode": "DETERMINISTIC FALLBACK",
            "model": target_model,
            "message": "Network connection to Groq API timed out or failed. Deterministic fallback engaged.",
            "error_type": "NETWORK_ERROR",
            "available_models": [],
            "diagnostics": None,
        }

    except groq.APIStatusError as exc:
        logger.warning("Groq API status error (%s): %s", exc.status_code, sanitize_error_message(exc))
        return {
            "connected": False,
            "mode": "DETERMINISTIC FALLBACK",
            "model": target_model,
            "message": f"Groq API returned HTTP {exc.status_code}. Deterministic fallback active.",
            "error_type": "API_STATUS_ERROR",
            "available_models": [],
            "diagnostics": None,
        }

    except Exception as exc:
        clean_err = sanitize_error_message(exc)
        logger.warning("Unexpected Groq connectivity error: %s", clean_err)
        return {
            "connected": False,
            "mode": "DETERMINISTIC FALLBACK",
            "model": target_model,
            "message": f"Groq API error ({clean_err}). Deterministic fallback active.",
            "error_type": "UNEXPECTED_ERROR",
            "available_models": [],
            "diagnostics": None,
        }


def generate_forensic_synthesis(
    system_prompt: str,
    user_prompt: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Generate natural-language forensic synthesis using Groq's official Chat Completions API.

    Guarantees:
      - Sanitized error handling with zero unhandled exceptions.
      - Uses 'max_completion_tokens' with full token headroom for GPT-OSS models.
      - Suppresses reasoning overhead ('include_reasoning=False', 'reasoning_effort=low').
      - Extracts user-facing message content without treating reasoning as content.
      - Explicit execution_mode reporting ('GROQ LIVE' vs 'DETERMINISTIC FALLBACK').
    """
    target_key = api_key.strip() if (api_key and api_key.strip()) else get_groq_api_key()
    target_model = model.strip() if (model and model.strip()) else get_groq_model()
    target_temp = float(temperature) if temperature is not None else GROQ_TEMPERATURE
    target_tokens = int(max_tokens) if max_tokens is not None else GROQ_MAX_TOKENS

    if not target_key:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "GROQ_API_KEY is not configured.",
            "error_type": "MISSING_KEY",
            "diagnostics": None,
        }

    try:
        client = get_groq_client(api_key=target_key, timeout=timeout)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = build_completion_kwargs(
            model=target_model,
            messages=messages,
            temperature=target_temp,
            token_budget=target_tokens,
        )

        try:
            response = client.chat.completions.create(**kwargs)
        except groq.BadRequestError as bad_req:
            clean_bad = sanitize_error_message(bad_req)
            if "reasoning" in clean_bad.lower():
                kwargs.pop("include_reasoning", None)
                kwargs.pop("reasoning_effort", None)
                response = client.chat.completions.create(**kwargs)
            else:
                raise

        extracted = extract_completion_content(response, target_model)

        if not extracted["success"]:
            return {
                "success": False,
                "content": "",
                "model": target_model,
                "execution_mode": "DETERMINISTIC FALLBACK",
                "fallback_reason": extracted["fallback_reason"],
                "error_type": extracted["error_type"],
                "diagnostics": extracted["diagnostics"],
            }

        return {
            "success": True,
            "content": extracted["content"],
            "model": target_model,
            "execution_mode": "GROQ LIVE",
            "fallback_reason": None,
            "error_type": None,
            "diagnostics": extracted["diagnostics"],
        }

    except groq.AuthenticationError as exc:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API key authentication failed.",
            "error_type": "AUTH_ERROR",
            "diagnostics": None,
        }

    except groq.RateLimitError as exc:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API rate limit exceeded.",
            "error_type": "RATE_LIMIT",
            "diagnostics": None,
        }

    except (groq.APIConnectionError, groq.APITimeoutError) as exc:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API connection timeout or network failure.",
            "error_type": "NETWORK_ERROR",
            "diagnostics": None,
        }

    except Exception as exc:
        clean_err = sanitize_error_message(exc)
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": f"Groq inference error: {clean_err}",
            "error_type": "INFERENCE_ERROR",
            "diagnostics": None,
        }
