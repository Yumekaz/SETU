"""Anti-flapping guard for pending recommendations."""

from __future__ import annotations

from app.models.generated import Recommendation, Status
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.orchestrate import recommendation_trigger_risk


def should_supersede_pending(
    new_trigger_risk: float,
    pending: Recommendation | None,
    config: OrchestratorConfig,
    *,
    force: bool = False,
) -> bool:
    """Return True when a new recommendation may replace a pending one."""
    if force:
        return True
    if pending is None or pending.status != Status.pending_approval:
        return True
    prior_risk = recommendation_trigger_risk(pending, config)
    return abs(new_trigger_risk - prior_risk) >= config.hysteresis_risk_delta
