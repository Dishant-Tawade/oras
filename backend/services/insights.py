"""
services/insights.py — End-of-session per-team insights.

Computed once when Year 5 locks, attached to each team's
game_state['final_insights']. The FinalInsights React component renders
this directly. Pure function, no I/O, deterministic — runs in the
simulation executor as part of the barrier-complete code path so it
adds no user-visible latency.

Privacy / fairness
------------------
The "compared to top teams" stats are computed against the top quartile
of ALL teams that completed the simulation. Other teams are not named —
only aggregate percentages. A team in the top quartile sees themselves
compared to "top-quartile teams" (a set they are part of), so the
comparison reads neutrally rather than as flattering.

The output schema (so the frontend has a stable contract):

  {
    "ranking": {
      "place": 14, "of": 60,          # 1-indexed, lower = better
      "percentile": 77,               # 100 - (place-1)/of * 100, integer
      "quartile": "Q2",               # "Q1" (top) | "Q2" | "Q3" | "Q4"
    },
    "trajectory": [                   # 5 entries, one per year
      {
        "year": 1,
        "dominant_dept": "Marketing", # the dept that got the most spend
        "vpi": 720,
        "vpi_delta": null,            # null on year 1; delta vs Y-1 thereafter
        "strategic_shift": false,     # true if dominant_dept changed from prior year
      },
      ...
    ],
    "strengths": [                    # 0-2 short strings
      "Marketing — consistently top quartile across Years 2-5"
    ],
    "gaps": [                         # 0-2 short strings
      "R&D — bottom quartile from Year 3 onward"
    ],
    "vs_top_quartile": [              # 0-3 short strings, anonymous comparison
      "You under-allocated to R&D by 14% vs top-quartile teams"
    ],
    "headline": "..."                 # one-sentence summary
  }
"""

from typing import Optional


# Tunables
_QUARTILE_TOP_PCT = 0.25    # top 25% considered "top quartile"
_QUARTILE_BOT_PCT = 0.25    # bottom 25%
_PERSISTENT_YEARS = 3       # rule needs at least this many years to call out
_VS_TOP_THRESHOLD_PCT = 8   # ignore vs-top-quartile diffs smaller than this


def _allocation_totals_from_gs(gs: dict) -> dict:
    """Fallback: read allocations from gs['locked_allocations'] (list-of-lists
    by year, ordered same as dept names) when individual yr_results don't
    carry a dict. Returns {dept_name: total}."""
    locked = gs.get('locked_allocations') or []
    if not locked:
        return {}
    # Map indices to department names via config; empty if unavailable.
    try:
        import config as _cfg
        dept_names = [d.name for d in _cfg.cfg.departments]
    except Exception:
        return {}
    totals: dict = {n: 0.0 for n in dept_names}
    for year_allocs in locked:
        for i, amt in enumerate(year_allocs):
            if i < len(dept_names):
                try:
                    totals[dept_names[i]] += float(amt)
                except (TypeError, ValueError):
                    pass
    return totals


def _dominant_dept_per_year(gs: dict) -> list:
    """Returns one dept name per year — the one with the largest allocation
    in that year. Robust against missing config/data; returns [] on failure."""
    locked = gs.get('locked_allocations') or []
    if not locked:
        return []
    try:
        import config as _cfg
        dept_names = [d.name for d in _cfg.cfg.departments]
    except Exception:
        return []
    out = []
    for year_allocs in locked:
        if not year_allocs:
            out.append(None)
            continue
        best_i = max(range(min(len(year_allocs), len(dept_names))),
                     key=lambda i: year_allocs[i])
        out.append(dept_names[best_i])
    return out


def _team_final_vpi(gs: dict) -> Optional[float]:
    """Best available "how did this team finish" score.

    Prefers final_vpi (Monte Carlo average) → falls back to Year 5 VPI →
    falls back to the last available year_result['vpi']. None if nothing is
    available (rare — would indicate a malformed state)."""
    fv = gs.get('final_vpi')
    if isinstance(fv, dict) and 'vpi' in fv:
        return float(fv['vpi'])
    if isinstance(fv, (int, float)):
        return float(fv)
    yr = gs.get('year_results') or []
    for r in reversed(yr):
        if r.get('vpi') is not None:
            return float(r['vpi'])
    return None


def _quartile_label(rank_1based: int, total: int) -> str:
    """Q1 (top) to Q4 (bottom). rank=1 is best."""
    if total <= 0:
        return 'Q?'
    p = (rank_1based - 1) / total
    if p < 0.25: return 'Q1'
    if p < 0.50: return 'Q2'
    if p < 0.75: return 'Q3'
    return 'Q4'


def compute_player_insights(team_key: str,
                            team_gs: dict,
                            all_team_states: dict) -> dict:
    """Generate insights for `team_key` using their state plus all teams'.

    Returns the dict described in the module docstring. Defensive against
    missing fields — bad input produces an empty/partial insights dict
    rather than raising.

    `all_team_states` is {team_key: gs} for all teams in this session.
    The caller should already have loaded these as part of the broadcast
    path (the existing _load_and_clear_all in game_router does this).
    """
    yr_results = team_gs.get('year_results') or []
    out: dict = {
        'ranking': None,
        'trajectory': [],
        'strengths': [],
        'gaps': [],
        'vs_top_quartile': [],
        'headline': '',
    }

    # Ranking
    teams_with_score = []
    for tk, gs in all_team_states.items():
        v = _team_final_vpi(gs)
        if v is not None:
            teams_with_score.append((tk, v))
    teams_with_score.sort(key=lambda kv: kv[1], reverse=True)  # high VPI = better
    total = len(teams_with_score)
    my_score = _team_final_vpi(team_gs)
    if my_score is not None and total > 0:
        # Find our place. Ties broken by team_key for determinism.
        # rank: 1-based position; place 1 = best
        place = next(
            (i + 1 for i, (tk, _) in enumerate(teams_with_score) if tk == team_key),
            None,
        )
        if place is None:
            place = total  # shouldn't happen, but be safe
        percentile = int(100 - (place - 1) / total * 100) if total > 1 else 100
        out['ranking'] = {
            'place':      place,
            'of':         total,
            'percentile': percentile,
            'quartile':   _quartile_label(place, total),
        }

    # Trajectory: one row per year
    dom_per_year = _dominant_dept_per_year(team_gs)
    for i, yr in enumerate(yr_results):
        prev_dom = dom_per_year[i - 1] if i > 0 and i - 1 < len(dom_per_year) else None
        cur_dom  = dom_per_year[i] if i < len(dom_per_year) else None
        vpi = yr.get('vpi')
        prev_vpi = yr_results[i - 1].get('vpi') if i > 0 else None
        out['trajectory'].append({
            'year':              i + 1,
            'dominant_dept':     cur_dom,
            'vpi':               int(vpi) if vpi is not None else None,
            'vpi_delta':         int(vpi - prev_vpi) if (vpi is not None and prev_vpi is not None) else None,
            'strategic_shift':   bool(prev_dom and cur_dom and prev_dom != cur_dom),
        })

    # A department in the top (bottom) quartile of the team's own returns for >= _PERSISTENT_YEARS years is a strength (gap).
    dept_ranks = {}      # dept_name → list of "top"/"mid"/"bottom" per year
    for yr in yr_results:
        returns = yr.get('dept_returns') or {}
        if not returns:
            continue
        sorted_depts = sorted(returns.items(),
                              key=lambda kv: kv[1] if isinstance(kv[1], (int, float)) else 0,
                              reverse=True)
        n = len(sorted_depts)
        for i, (name, _) in enumerate(sorted_depts):
            tag = 'top' if i < max(1, n // 4) else ('bottom' if i >= n - max(1, n // 4) else 'mid')
            dept_ranks.setdefault(name, []).append(tag)
    for name, tags in dept_ranks.items():
        top_count    = tags.count('top')
        bottom_count = tags.count('bottom')
        if top_count >= _PERSISTENT_YEARS:
            out['strengths'].append(
                f"{name} — consistently strong returns ({top_count} of {len(tags)} years in your top quartile)."
            )
        if bottom_count >= _PERSISTENT_YEARS:
            out['gaps'].append(
                f"{name} — recurring underperformance ({bottom_count} of {len(tags)} years in your bottom quartile)."
            )

    # Cap to 2 each
    out['strengths'] = out['strengths'][:2]
    out['gaps']      = out['gaps'][:2]

    # vs_top_quartile: aggregate spend comparison
    if total >= 4:  # need at least 4 teams for a meaningful quartile
        top_q_count = max(1, int(total * _QUARTILE_TOP_PCT))
        top_q_keys = [tk for tk, _ in teams_with_score[:top_q_count]]
        # Skip if this team IS top quartile — comparing to yourself is weird
        if team_key not in top_q_keys:
            # Build avg allocation per dept across top quartile
            top_totals_by_team = [
                _allocation_totals_from_gs(all_team_states[tk])
                for tk in top_q_keys if tk in all_team_states
            ]
            if top_totals_by_team:
                # Avg across top-quartile teams
                all_depts = set()
                for t in top_totals_by_team:
                    all_depts.update(t.keys())
                avg_top = {
                    d: sum(t.get(d, 0) for t in top_totals_by_team) / len(top_totals_by_team)
                    for d in all_depts
                }
                my_totals = _allocation_totals_from_gs(team_gs)
                # Compare on a percentage-of-total basis (controls for
                # teams with different total budgets due to reinvestment)
                my_total_spend = sum(my_totals.values()) or 1
                top_total_spend = sum(avg_top.values()) or 1
                for dept in all_depts:
                    my_pct  = my_totals.get(dept, 0) / my_total_spend * 100
                    top_pct = avg_top.get(dept, 0)   / top_total_spend * 100
                    diff = my_pct - top_pct
                    if abs(diff) < _VS_TOP_THRESHOLD_PCT:
                        continue
                    if diff < 0:
                        out['vs_top_quartile'].append(
                            f"You under-allocated to {dept} by {abs(diff):.0f}% vs top-quartile teams."
                        )
                    else:
                        out['vs_top_quartile'].append(
                            f"You over-allocated to {dept} by {diff:.0f}% vs top-quartile teams."
                        )
                # Cap and sort by magnitude (biggest differences first)
                out['vs_top_quartile'] = sorted(
                    out['vs_top_quartile'],
                    key=lambda s: float(s.split('by ')[1].split('%')[0]) if 'by ' in s else 0,
                    reverse=True,
                )[:3]

    # Headline: one sentence summarizing the result
    if out['ranking']:
        place = out['ranking']['place']
        of    = out['ranking']['of']
        q     = out['ranking']['quartile']
        if q == 'Q1':
            out['headline'] = f"Strong finish — you placed {place} of {of}, top quartile."
        elif q == 'Q2':
            out['headline'] = f"Solid showing — {place} of {of} puts you in the second quartile."
        elif q == 'Q3':
            out['headline'] = f"You finished {place} of {of} — room to climb."
        else:
            out['headline'] = f"You finished {place} of {of} — a steep learning curve to review."
    elif my_score is not None:
        out['headline'] = f"Final VPI {int(my_score)}."

    return out
