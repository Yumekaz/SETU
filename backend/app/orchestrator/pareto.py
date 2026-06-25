"""Pareto dominance and frontier sorting (Appendix C)."""

from __future__ import annotations

from app.models.generated import Option


def _objectives(option: Option) -> tuple[float, float, float]:
    return (option.cost_score, option.time_score, option.risk_score)


def dominates(a: Option, b: Option) -> bool:
    """A dominates B if no worse on all objectives and strictly better on at least one."""
    objs_a = _objectives(a)
    objs_b = _objectives(b)
    no_worse = all(x <= y for x, y in zip(objs_a, objs_b, strict=True))
    strictly_better = any(x < y for x, y in zip(objs_a, objs_b, strict=True))
    return no_worse and strictly_better


def mark_pareto_optimal(options: list[Option]) -> list[Option]:
    """Return new Option list with is_pareto_optimal flags set."""
    marked: list[Option] = []
    for i, opt in enumerate(options):
        is_optimal = True
        for j, other in enumerate(options):
            if i != j and dominates(other, opt):
                is_optimal = False
                break
        marked.append(
            Option(
                option_id=opt.option_id,
                description=opt.description,
                cost_score=opt.cost_score,
                time_score=opt.time_score,
                risk_score=opt.risk_score,
                is_pareto_optimal=is_optimal,
            )
        )
    return marked


def sort_frontier(options: list[Option]) -> list[Option]:
    """Sort Pareto-optimal options: risk_score asc, then time_score asc."""
    frontier = [o for o in options if o.is_pareto_optimal]
    dominated = [o for o in options if not o.is_pareto_optimal]
    frontier_sorted = sorted(frontier, key=lambda o: (o.risk_score, o.time_score))
    dominated_sorted = sorted(dominated, key=lambda o: (o.risk_score, o.time_score))
    return frontier_sorted + dominated_sorted
