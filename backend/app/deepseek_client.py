"""DeepSeek client.

DeepSeek serves an OpenAI-compatible chat-completions endpoint, so this is a
plain HTTP call over the httpx already in the dependency list — no extra SDK.

It is a **text-only** API: the hosted models take no image or PDF input. The
two callers that carry a file (the insurance card and the Evidence of
Coverage) check `llm.supports_documents()` and never reach this module, so a
non-text block arriving here is a routing bug and is reported as one.
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings
from .llm import LLMResponseError, LLMUnavailableError, extract_json_object

# Generous: an appeal letter is the longest thing asked of it, and a cold
# start on a reasoning model is slow.
TIMEOUT_SECONDS = 120.0

MAX_TOKENS = 4096


def is_configured() -> bool:
    """True when a DeepSeek key is present."""
    return bool(get_settings().deepseek_api_key)


def flatten_content(content: list[dict[str, Any]]) -> str:
    """Collapse the content blocks into the single text prompt DeepSeek takes.

    Anything that is not a text block is refused rather than dropped: silently
    discarding a card image would produce a confident answer about a document
    the model never saw.
    """
    parts: list[str] = []

    for block in content:
        kind = block.get("type")
        if kind != "text":
            raise LLMResponseError(
                f"DeepSeek accepts text only, so a {kind!r} block cannot be "
                "sent. Use Anthropic for document parsing."
            )
        text = str(block.get("text") or "").strip()
        if text:
            parts.append(text)

    return "\n\n".join(parts)


def complete_json(
    *,
    system: str,
    content: list[dict[str, Any]],
) -> dict[str, Any]:
    """Send one message to DeepSeek and parse its reply as a JSON object."""
    settings = get_settings()

    if not settings.deepseek_api_key:
        raise LLMUnavailableError("DEEPSEEK_API_KEY is not set; cannot call DeepSeek.")

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": flatten_content(content)},
        ],
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }

    try:
        response = httpx.post(
            f"{settings.deepseek_base_url}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            timeout=TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise LLMResponseError(f"DeepSeek request failed: {exc}") from exc

    if response.status_code != 200:
        # The body carries the reason (bad key, no credit, unknown model);
        # surface it, trimmed, rather than just the status.
        detail = response.text.strip()[:300] or "no error body"
        raise LLMResponseError(
            f"DeepSeek returned HTTP {response.status_code}: {detail}"
        )

    try:
        body = response.json()
    except ValueError as exc:
        raise LLMResponseError(
            f"DeepSeek returned a non-JSON body: {response.text[:200]!r}"
        ) from exc

    choices = body.get("choices") or []
    if not choices:
        raise LLMResponseError("DeepSeek returned no choices.")

    choice = choices[0]

    if choice.get("finish_reason") == "content_filter":
        raise LLMResponseError("DeepSeek declined to process this request.")

    message = choice.get("message") or {}
    text = str(message.get("content") or "").strip()

    if not text:
        raise LLMResponseError("DeepSeek returned an empty message.")

    return extract_json_object(text)
