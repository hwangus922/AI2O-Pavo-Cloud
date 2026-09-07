"""Audit-trail writer.

Every state change and every decision writes a row here. A decision row always
carries the rule_id that produced it in after_state — this is what makes the
"no black box outputs" constraint checkable.
"""
from __future__ import annotations

from typing import Any, Optional

from .db import Repository


def record(
    repository: Repository,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_agent_id: str,
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Append one entry to the audit log."""
    return repository.insert_audit_log(
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor_agent_id": actor_agent_id,
            "before_state": before_state,
            "after_state": after_state,
        }
    )
