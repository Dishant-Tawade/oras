"""Performance index (VPI) computation and leaderboard entries.
"""
import numpy as np

import config as _config_module
from config import NP
from simulator import compute_competitor_trajectory, compute_market_shares
from game_state import get_team_gs


# Clip both norms to [0, 1] so outliers cannot push VPI outside its range.

def vpi_grade(s: float) -> str:
    if s >= 850: return 'S'
    if s >= 700: return 'A'
    if s >= 550: return 'B'
    if s >= 400: return 'C'
    if s >= 250: return 'D'
    return 'F'


def compute_final_vpi(team_gs: dict, mode: str) -> dict | None:
    """
    Canonical VPI computation using evaluate() — identical to the evaluation
    section. Uses EVAL_SEED Monte Carlo (30 scenarios) for RAS, so the score
    is independent of the noise draw that occurred during gameplay.

    This is the single source of truth for VPI. Both the leaderboard and the
    final evaluation section call this function.

    CONCURRENCY NOTE
    ────────────────
    This function used to mutate _config_module.cfg (num_periods and
    carryover_strength) as part of its work, then restore the originals.
    That was unsafe under thread concurrency: at the year-5 barrier fire,
    up to 60 teams call this function simultaneously from the sim_executor
    pool, and every thread stomped on the shared global cfg.  Specifically
    carryover_strength was never restored at all (buggy set without revert),
    and num_periods interleaving could cause a thread to simulate with the
    wrong number of years if another thread's num_periods write landed
    between this thread's read and the evaluate() call.

    Fix: build a per-call ScenarioConfig copy with dataclasses.replace and
    hand it to the simulator.  No global state is touched.
    """
    results   = team_gs.get('year_results', [])
    locked    = team_gs.get('locked_allocations', [])
    locked_sd = team_gs.get('locked_subdecisions', [])
    n = len(results)
    if n == 0:
        return None

    from simulator import (
        ResourceAllocationSimulator, generate_competitors,
        NewsEvent as _NE,
    )
    from config import EVAL_SEED
    import dataclasses as _dc

    plan = np.array(locked[:n])

    # Shallow copy so concurrent calls never mutate the shared config.
    _base_cfg = _config_module.cfg
    local_cfg = _dc.replace(
        _base_cfg,
        num_periods=n,
        carryover_strength=1.0,
    )

    # RAS via Monte Carlo evaluate (same as evaluation section)
    se = ResourceAllocationSimulator(local_cfg)

    pnews_data = team_gs.get('player_news', [])
    player_news = [
        _NE(year=e['year'], headline=e['headline'], detail=e['detail'],
            revenue_impact=e.get('revenue_impact', 1.0),
            profit_impact=e.get('profit_impact', 0),
            sentiment=e.get('sentiment', 'neutral'),
            target=e.get('target', ''),
            dept_pressure=e.get('dept_pressure', ''),
            dept_k_mult=e.get('dept_k_mult', 1.0),
            dept_smax_mult=e.get('dept_smax_mult', 1.0))
        for e in pnews_data
    ] if pnews_data else []

    multi     = se.evaluate(plan, seed_base=EVAL_SEED,
                            sub_decisions_by_year=locked_sd[:n],
                            player_news=player_news)
    avg_p     = multi['avg_annual_profit']
    std_p     = multi['std_annual_profit']
    ras       = avg_p - (2.0 - local_cfg.risk_penalty_lambda) * std_p

    # Market share
    user_revs = [r['total_revenue'] for r in results[:n]]
    competitors_list, _ = generate_competitors(NP, team_gs['play_seed'])
    comp_trajs = [
        compute_competitor_trajectory(comp, n, mode, locked[:n], seed=42 + ci,
                                      user_sub_decisions=locked_sd[:n])
        for ci, comp in enumerate(competitors_list)
    ]
    mkt   = compute_market_shares(
        user_revs, comp_trajs,
        user_allocations=locked[:n],
        user_sub_decisions=locked_sd[:n],
        total_budget=local_cfg.total_budget,
        game_seed=team_gs.get('play_seed', None),
    )
    share = float(np.mean(mkt[0]['shares'])) if mkt else 0.0

    # Clip both norms to [0, 1] so outliers cannot push VPI outside its range.
    ras_norm_raw   = (ras - _config_module.VPI_RAS_FLOOR)   / (_config_module.VPI_RAS_CEIL   - _config_module.VPI_RAS_FLOOR)
    share_norm_raw = (share - _config_module.VPI_SHARE_FLOOR) / (_config_module.VPI_SHARE_CEIL - _config_module.VPI_SHARE_FLOOR)
    ras_norm   = max(0.0, min(1.0, ras_norm_raw))
    share_norm = max(0.0, min(1.0, share_norm_raw))
    vpi        = round((0.50 * ras_norm + 0.50 * share_norm) * 1000)

    profits = [r['profit'] for r in results[:n]]
    return {
        'vpi':        vpi,
        'grade':      vpi_grade(vpi),
        'year':       n,
        'cum_profit': sum(profits),
        'avg_profit': avg_p,
        'std_profit': std_p,
        'ras':        ras,
        'avg_share':  share,
    }


def compute_latest_year_vpi(team_gs: dict, mode: str) -> dict | None:
    """
    Compute VPI for the latest locked year only (not a rolling average).
    Used by the player-facing leaderboard so players see their current year score.
    """
    results   = team_gs.get('year_results', [])
    locked    = team_gs.get('locked_allocations', [])
    locked_sd = team_gs.get('locked_subdecisions', [])
    n = len(results)
    if n == 0:
        return None

    from simulator import (
        ResourceAllocationSimulator, generate_competitors,
        NewsEvent as _NE,
    )
    from config import EVAL_SEED
    import dataclasses as _dc

    # Evaluate using only the allocations up to and including this year,
    # but score only on the latest year's profit and share.
    plan = np.array(locked[:n])

    # Shallow copy so concurrent calls never mutate the shared config.
    _base_cfg = _config_module.cfg
    local_cfg = _dc.replace(
        _base_cfg,
        num_periods=n,
        carryover_strength=1.0,
        num_eval_scenarios=1,   # cheap single-run — this is the player card estimate
    )
    se = ResourceAllocationSimulator(local_cfg)

    pnews_data = team_gs.get('player_news', [])
    player_news = [
        _NE(year=e['year'], headline=e['headline'], detail=e['detail'],
            revenue_impact=e.get('revenue_impact', 1.0),
            profit_impact=e.get('profit_impact', 0),
            sentiment=e.get('sentiment', 'neutral'),
            target=e.get('target', ''),
            dept_pressure=e.get('dept_pressure', ''),
            dept_k_mult=e.get('dept_k_mult', 1.0),
            dept_smax_mult=e.get('dept_smax_mult', 1.0))
        for e in pnews_data
    ] if pnews_data else []

    # Use 1 scenario only — the player performance card is an estimate,
    # not the authoritative leaderboard score. 30 runs happen at year 5 only.
    multi = se.evaluate(plan, seed_base=EVAL_SEED,
                        sub_decisions_by_year=locked_sd[:n],
                        player_news=player_news)

    # Use only the latest year's profit from each scenario run
    latest_yr_profits = [r['profit'][n - 1]
                         for r in multi['scenario_results']]
    avg_p = float(np.mean(latest_yr_profits))
    std_p = float(np.std(latest_yr_profits)) if n > 1 else 0.0
    ras   = avg_p - (2.0 - local_cfg.risk_penalty_lambda) * std_p

    # Market share for this year only
    competitors_list, _ = generate_competitors(NP, team_gs['play_seed'])
    comp_trajs = [
        compute_competitor_trajectory(comp, n, mode, locked[:n], seed=42 + ci,
                                      user_sub_decisions=locked_sd[:n])
        for ci, comp in enumerate(competitors_list)
    ]
    # Take only the latest year's share from the full trajectory
    mkt   = compute_market_shares(
        [r['total_revenue'] for r in results[:n]], comp_trajs,
        user_allocations=locked[:n],
        user_sub_decisions=locked_sd[:n],
        total_budget=local_cfg.total_budget,
        game_seed=team_gs.get('play_seed', None),
    )
    # shares is a list of per-year values — take the last one
    share = float(mkt[0]['shares'][n - 1]) if mkt and mkt[0]['shares'] else 0.0

    # Clip norms to [0, 1] so extreme outliers can't produce negative VPI
    ras_norm_raw   = (ras - _config_module.VPI_RAS_FLOOR)   / (_config_module.VPI_RAS_CEIL   - _config_module.VPI_RAS_FLOOR)
    share_norm_raw = (share - _config_module.VPI_SHARE_FLOOR) / (_config_module.VPI_SHARE_CEIL - _config_module.VPI_SHARE_FLOOR)
    ras_norm   = max(0.0, min(1.0, ras_norm_raw))
    share_norm = max(0.0, min(1.0, share_norm_raw))
    vpi        = round((0.50 * ras_norm + 0.50 * share_norm) * 1000)

    profits = [r['profit'] for r in results[:n]]
    return {
        'vpi':        vpi,
        'grade':      vpi_grade(vpi),
        'year':       n,
        'cum_profit': sum(profits),
        'avg_profit': avg_p,
        'std_profit': std_p,
        'ras':        ras,
        'avg_share':  share,
    }


# Leaderboard — data and UI separated

def compute_leaderboard_entries(this_team: str,
                                   all_game_states: dict | None = None) -> list:
    """
    Build leaderboard from pre-computed VPI already stored in each team's
    year_results — no NumPy simulation required.

    execute_lock_year stores vpi, grade, ras, avg_share_vpi in every
    year_result entry. Reading those values is a pure dict lookup — ~1000×
    faster than re-running evaluate() for each team.

    all_game_states: optional dict of {team_key: game_state} to avoid
    reading Firestore N times when the caller already has the states.
    """
    entries = []
    team_keys = list({u['team_key'] for u in _store_ref().load_users()}) if all_game_states is None else list(all_game_states.keys())
    for tk in team_keys:
        if all_game_states is not None:
            tgs = all_game_states.get(tk)
        else:
            tgs = get_team_gs(tk)
        if not tgs:
            continue
        results = tgs.get('year_results', [])
        if not results:
            continue
        last = results[-1]
        vpi   = last.get('vpi')
        grade = last.get('grade')
        if vpi is None:
            mode = tgs.get('mode', 'competition')
            vpi_data = compute_latest_year_vpi(tgs, mode)
            if vpi_data:
                entries.append({'team': tk, 'is_you': tk == this_team, **vpi_data})
            continue
        entries.append({
            'team':       tk,
            'is_you':     tk == this_team,
            'vpi':        vpi,
            'grade':      grade or vpi_grade(vpi),
            'year':       len(results),
            'cum_profit': sum(r.get('profit', 0) for r in results),
            'avg_profit': last.get('profit', 0),
            'std_profit': 0.0,
            'ras':        last.get('ras', 0),
            'avg_share':  last.get('avg_share_vpi', last.get('market_share', 0)),
        })
    entries.sort(key=lambda e: e['vpi'], reverse=True)
    return entries


def _store_ref():
    from auth import get_store
    return get_store()
