"""Provider-neutral access to a language model.

Two providers are supported, selected by which key is configured (or forced
with LLM_PROVIDER):

* anthropic — handles every call, including the two that carry a file: the
  insurance card image and the Evidence of Coverage PDF.
* deepseek — an OpenAI-compatible, **text-only** API. The hosted models take
  no image or document input, so with DeepSeek selected the two document
  parsers fall back to their labelled sample data and only the text calls —
  CPT mapping and appeal letters — reach the model.

`supports_documents()` is what the callers gate on, rather than asking which
provider is active. Adding a vision-capable provider later means changing the
table in this module and nothing else.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .config import get_settings

ANTHROPIC = "anthropic"
DEEPSEEK = "deepseek"

# Which providers can accept image and PDF content blocks.
_DOCUMENT_CAPABLE = {ANTHROPIC}


class LLMUnavailableError(RuntimeError):
    """Raised when no provider is configured."""


class LLMResponseError(RuntimeError):
    """Raised when the model's reply is not the JSON object we asked for."""


def active_provider() -> str:
    """The provider this process will use, or "" when none is configured.

    An explicit LLM_PROVIDER wins. Otherwise whichever key is present does,
    and Anthropic wins if both are — it is the only one that can read the
    documents.
    """
    settings = get_settings()

    forced = settings.llm_provider
    if forced:
        return forced

    if settings.anthropic_api_key:
        return ANTHROPIC
    if settings.deepseek_api_key:
        return DEEPSEEK
    return ""


def is_configured() -> bool:
    """True when a provider is selected and its key is present."""
    settings = get_settings()
    provider = active_provider()

    if provider == ANTHROPIC:
        return bool(settings.anthropic_api_key)
    if provider == DEEPSEEK:
        return bool(settings.deepseek_api_key)
    return False


def supports_documents() -> bool:
    """True when the active provider accepts image and PDF blocks.

    False sends the caller to its sample data rather than to a request the
    provider would reject.
    """
    return is_configured() and active_provider() in _DOCUMENT_CAPABLE


def source_label() -> str:
    """How a result produced by the active provider is labelled to the UI."""
    provider = active_provider()
    if provider == ANTHROPIC:
        # Kept as "claude" so existing dashboards and tests still read it.
        return "claude"
    return provider or "sample"


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
        raise LLMResponseError(
            f"The model did not return valid JSON: {text[:200]!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise LLMResponseError(
            f"Expected a JSON object, got {type(parsed).__name__}."
        )

    return parsed


def complete_json(
    *,
    system: str,
    content: list[dict[str, Any]],
) -> dict[str, Any]:
    """Send one message to the active provider and parse its reply as JSON.

    The clients are imported here rather than at module scope so that each
    provider's dependencies stay optional.
    """
    provider = active_provider()

    if provider == ANTHROPIC:
        from . import claude_client

        return claude_client.complete_json(system=system, content=content)

    if provider == DEEPSEEK:
        from . import deepseek_client

        return deepseek_client.complete_json(system=system, content=content)

    raise LLMUnavailableError(
        "No language model is configured; set ANTHROPIC_API_KEY or "
        "DEEPSEEK_API_KEY."
    )
