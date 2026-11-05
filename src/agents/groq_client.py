"""
FRAUDNET AI — Official Groq Client & API Verification Engine
=============================================================
Manages secure connection, model discovery, connectivity verification,
and natural language forensic synthesis via the official Groq SDK.

Security Principles:
  1. Never print, log, display, or expose the raw GROQ_API_KEY.
  2. Sanitize all diagnostic output to strip tokens or authorization headers.
  3. Safe graceful fallback to local deterministic AML engine on any API failure.
  4. Never silently switch models if the configured model is unavailable.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import groq
from groq import Groq

from config.settings import (
    DEFAULT_GROQ_MODEL,
    GROQ_MAX_TOKENS,
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
      3. Live minimal chat completion test to confirm inference capabilities.

    Returns:
        Structured result dict with 'connected', 'mode', 'model', 'message', 'error_type'.
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
            }

        # Step 2: Live Chat Completion Verification
        chat_resp = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": "You are a health check agent."},
                {"role": "user", "content": "Respond with 'VERIFIED'."},
            ],
            max_tokens=10,
            temperature=0.0,
        )

        content = ""
        if chat_resp.choices and len(chat_resp.choices) > 0:
            content = (chat_resp.choices[0].message.content or "").strip()

        if not content:
            return {
                "connected": False,
                "mode": "DETERMINISTIC FALLBACK",
                "model": target_model,
                "message": "Groq returned an empty response during connectivity test.",
                "error_type": "EMPTY_RESPONSE",
                "available_models": available_model_ids,
            }

        return {
            "connected": True,
            "mode": "GROQ LIVE",
            "model": target_model,
            "message": f"Groq API connection and model '{target_model}' verified successfully.",
            "error_type": None,
            "available_models": available_model_ids,
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
      - Non-empty response validation.
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
        }

    try:
        client = get_groq_client(api_key=target_key, timeout=timeout)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=target_temp,
            max_tokens=target_tokens,
        )

        content = ""
        if response.choices and len(response.choices) > 0:
            content = (response.choices[0].message.content or "").strip()

        if not content:
            return {
                "success": False,
                "content": "",
                "model": target_model,
                "execution_mode": "DETERMINISTIC FALLBACK",
                "fallback_reason": "Groq returned an empty response.",
                "error_type": "EMPTY_RESPONSE",
            }

        return {
            "success": True,
            "content": content,
            "model": target_model,
            "execution_mode": "GROQ LIVE",
            "fallback_reason": None,
            "error_type": None,
        }

    except groq.AuthenticationError as exc:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API key authentication failed.",
            "error_type": "AUTH_ERROR",
        }

    except groq.RateLimitError as exc:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API rate limit exceeded.",
            "error_type": "RATE_LIMIT",
        }

    except (groq.APIConnectionError, groq.APITimeoutError) as exc:
        return {
            "success": False,
            "content": "",
            "model": target_model,
            "execution_mode": "DETERMINISTIC FALLBACK",
            "fallback_reason": "Groq API connection timeout or network failure.",
            "error_type": "NETWORK_ERROR",
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
        }

