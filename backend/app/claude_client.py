"""Anthropic client wrapper for the Insure parsers.

All Claude calls funnel through here so the model, token ceiling, and JSON
handling are defined once. When no API key is configured the module reports
that it is unavailable and callers fall back to the labelled sample parser —
the demo stays runnable without credentials, and every response says which
path produced it.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from .config import get_settings

# Fixed by the Phase 2 specification.
MODEL = "claude-sonnet-4-6"

# The parsers return small JSON objects; this leaves ample headroom without
# risking a mid-object truncation.
MAX_TOKENS = 4096


class ClaudeUnavailableError(RuntimeError):
    """Raised when no Anthropic credentials are configured."""


class ClaudeResponseError(RuntimeError):
    """Raised when Claude's reply is not the JSON object we asked for."""


def is_configured() -> bool:
    """True when an Anthropic API key is present."""
    return bool(get_settings().anthropic_api_key)


def _client():
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ClaudeUnavailableError(
            "ANTHROPIC_API_KEY is not set; cannot call Claude."
        )

    import anthropic  # imported lazily so the app boots without the SDK

    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _response_text(message: Any) -> str:
    """Concatenate the text blocks of a Messages API response."""
    parts = [
        block.text
        for block in message.content
        if getattr(block, "type", None) == "text"
    ]
    return "".join(parts).strip()


def extract_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object out of a model reply.

    The prompts ask for JSON only, but a fenced code block is a common and
    harmless deviation, so unwrap that before parsing.
    """
    text = raw.strip()

    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ClaudeResponseError(
            f"Claude did not return valid JSON: {text[:200]!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ClaudeResponseError(
            f"Expected a JSON object, got {type(parsed).__name__}."
        )

    return parsed


def complete_json(
    *,
    system: str,
    content: list[dict[str, Any]],
) -> dict[str, Any]:
    """Send one message to Claude and parse its reply as a JSON object."""
    message = _client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": content}],
    )

    if message.stop_reason == "refusal":
        raise ClaudeResponseError("Claude declined to process this document.")

    return extract_json_object(_response_text(message))
