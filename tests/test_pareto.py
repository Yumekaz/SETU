"""Pareto dominance and tie-break tests."""

from __future__ import annotations

from app.models.generated import Option
from app.orchestrator.pareto import dominates, mark_pareto_optimal, sort_frontier


def _opt(oid: str, cost: float, time: float, risk: float) -> Option:
    return Option(
        option_id=oid,
        description=oid,
        cost_score=cost,
        time_score=time,
        risk_score=risk,
        is_pareto_optimal=False,
    )


def test_dominates_strict_on_one_objective() -> None:
    a = _opt("a", 0.2, 0.5, 0.5)
    b = _opt("b", 0.3, 0.5, 0.5)
    assert dominates(a, b)
    assert not dominates(b, a)


def test_mutually_non_dominated_both_pareto() -> None:
    a = _opt("a", 0.2, 0.8, 0.5)
    b = _opt("b", 0.6, 0.3, 0.5)
    marked = mark_pareto_optimal([a, b])
    assert all(o.is_pareto_optimal for o in marked)


def test_dominated_option_not_pareto() -> None:
    a = _opt("a", 0.2, 0.2, 0.2)
    b = _opt("b", 0.5, 0.5, 0.5)
    marked = mark_pareto_optimal([a, b])
    by_id = {o.option_id: o for o in marked}
    assert by_id["a"].is_pareto_optimal
    assert not by_id["b"].is_pareto_optimal


def test_tie_break_risk_then_time() -> None:
    a = _opt("a", 0.3, 0.5, 0.4)
    b = _opt("b", 0.2, 0.9, 0.2)
    marked = mark_pareto_optimal([a, b])
    frontier = sort_frontier(marked)
    pareto_only = [o for o in frontier if o.is_pareto_optimal]
    assert pareto_only[0].option_id == "b"
    assert pareto_only[1].option_id == "a"
