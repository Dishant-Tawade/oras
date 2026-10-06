"""Game logic behind the lock-year flow: validation, year execution, scoring and slider constraints.
"""

import math
import functools
import numpy as np
import config as _config_module
from config import NP, ND
from simulator import (
    ResourceAllocationSimulator, generate_competitors,
    NewsEvent as _NE, get_company_name,
    compute_competitor_trajectory, compute_market_shares,
    compute_player_product_specs, compute_competitor_product_specs,
    compute_segment_likability, simulate_all_competitors,
)
from game_state import (
    set_team_gs,
    teams_blocking_year,
)


# Competitor results depend only on (play_seed, num_years, mode); cache them across teams (per process).

@functools.lru_cache(maxsize=32)
def _cached_competitors(play_seed: int, num_periods: int):
    """Return (competitors_list, all_news) — cached by (seed, num_periods)."""
    return generate_competitors(num_periods, play_seed)


@functools.lru_cache(maxsize=256)
def _cached_competitor_trajectory(comp_name: str, play_seed: int,
                                   num_years: int, mode: str,
                                   alloc_key: tuple, sd_key: tuple,
                                   ci: int):
    """
    Return competitor trajectory for one competitor — cached by all inputs.

    alloc_key and sd_key are tuples (hashable) derived from the team's locked
    allocations and sub-decisions respectively.  Because competitor trajectories
    depend on user spend intensity (they react to player pressure), we must
    include the allocations in the cache key.  Using a tuple makes them hashable.
    """
    competitors_list, _ = _cached_competitors(play_seed, num_years)
    comp = next(c for c in competitors_list if c.name == comp_name)
    user_allocs = [list(a) for a in alloc_key] if alloc_key else None
    user_sds    = [dict(sd) for sd in sd_key]  if sd_key    else None
    return compute_competitor_trajectory(
        comp, num_years, mode,
        user_allocations=user_allocs,
        seed=42 + ci,
        user_sub_decisions=user_sds,
    )


def validate_lock_year(allocations: list[float], subdecisions: dict[str, str],
                       gs: dict, team_key: str) -> tuple[dict | None, dict]:
    """
    Validate a lock-year request.

    Returns a (error, resolved_subdecisions) tuple:
      - error is None on success, or a dict {"error": str, ...} on failure
      - resolved_subdecisions is a NEW dict with any missing or
        '_placeholder' entries filled in from the previous year's locked
        choices. Callers should use this returned dict for the actual
        lock, not the input dict.

    Previously this function mutated the input `subdecisions` dict in
    place. That was harmless for the current FastAPI caller (Pydantic
    builds a fresh dict per request) but made the function's contract
    confusing: a function named "validate" shouldn't have write side
    effects on its arguments. Returning the resolved value explicitly
    keeps the validator pure and lets future callers compose it freely.
    """
    bgt = gs.get('available_budget', _config_module.cfg.total_budget)
    if sum(allocations) > bgt * 1.001:
        return {"error": "Over budget: reduce allocations"}, dict(subdecisions)

    # Validate subdecisions — build a new dict, don't mutate the caller's.
    resolved = dict(subdecisions)
    dept_names = [d.name for d in _config_module.cfg.departments]
    prev_locked_sd = gs.get('locked_subdecisions', [])
    prev_sd_dict = prev_locked_sd[-1] if prev_locked_sd else {}

    for dept_name in dept_names:
        val = resolved.get(dept_name, '')
        if not val or val == '_placeholder':
            if dept_name in prev_sd_dict and prev_sd_dict[dept_name] != '_placeholder':
                resolved[dept_name] = prev_sd_dict[dept_name]
            else:
                return ({"error": "Select a strategy for every department before locking"},
                        resolved)

    # Check blocking
    blocking = teams_blocking_year(gs['current_year'], team_key)
    if blocking:
        return ({"error": f"Waiting for {len(blocking)} team(s) to catch up",
                 "blocking": blocking},
                resolved)

    return None, resolved


def execute_lock_year(allocations: list[float], subdecisions: dict[str, str],
                      gs: dict, team_key: str,
                      carryover: float = 0.5) -> dict:
    """
    Run the simulation for one year and return the updated game state + year result.

    Returns:
        {
            "game_state": { ... new game state ... },
            "year_result": { ... this year's results ... },
            "year": int,
            "completed": bool,
            "waiting_for_others": bool,
        }
    """
    # Record this lock's inputs, then compute the year.
    alloc = list(allocations)
    locked = gs['locked_allocations']
    locked.append(alloc)
    locked_sd = gs.get('locked_subdecisions', [])
    locked_sd.append(dict(subdecisions))
    gs['locked_subdecisions'] = locked_sd   # ensure stored for the compute step

    out = compute_year_for_team(gs, team_key, carryover)
    set_team_gs(team_key, out['game_state'])
    return out


def compute_year_for_team(gs: dict, team_key: str,
                          carryover: float = 0.5) -> dict:
    """Pure per-team year computation.

    Assumes gs['locked_allocations'] and gs['locked_subdecisions'] ALREADY
    include this year's inputs (recorded at lock time). Runs the simulation,
    builds the year_result and the updated game state, and returns them —
    WITHOUT persisting (the caller persists). execute_lock_year() calls this
    inline; the deferred-compute barrier path calls it for every team once the
    year's barrier is reached. Because each team's year-N compute reads only its
    OWN prior-year results (for the market-share revenue history), the result is
    identical whether computed at lock time or deferred to the barrier.

    Returns: {game_state, year_result, year, completed, waiting_for_others}
    """
    cur = gs['current_year']
    locked = gs['locked_allocations']
    locked_sd = gs.get('locked_subdecisions', [])
    subdecisions = locked_sd[-1] if locked_sd else {}

    plan = np.array(locked)
    _config_module.cfg.carryover_strength = carryover
    sim_play = ResourceAllocationSimulator(_config_module.cfg)
    orig_np = _config_module.cfg.num_periods
    _config_module.cfg.num_periods = len(locked)

    # Build player news events
    pnews_data = gs.get('player_news', [])
    _company = get_company_name()
    player_news = [
        _NE(year=e['year'], headline=e['headline'], detail=e['detail'],
            # Defaults keep game states saved before these fields existed working (news stays inert).
            revenue_impact=e.get('revenue_impact', 1.0),
            profit_impact=e.get('profit_impact', 0),
            sentiment=e['sentiment'],
            target=_company, dept_pressure=e.get('dept_pressure', ''),
            dept_k_mult=e.get('dept_k_mult', 1.0),
            dept_smax_mult=e.get('dept_smax_mult', 1.0))
        for e in pnews_data
    ]

    # Only the current year is capped precisely; earlier years use no cap (already penalised when live).
    _alloc_gs = dict(gs)
    _alloc_gs['locked_allocations'] = locked[:-1]  # state *before* this lock
    _ba = get_budget_allocatability(_alloc_gs)
    max_allocatable_by_year = [None] * (len(locked) - 1) + [_ba['max_allocatable']]

    result = sim_play.simulate(
        plan, noise_seed=gs['play_seed'],
        cumulative_inflation=gs.get('cumulative_inflation', 1.0),
        sub_decisions_by_year=locked_sd,
        player_news=player_news,
        max_allocatable_by_year=max_allocatable_by_year,
    )
    _config_module.cfg.num_periods = orig_np

    yi = len(locked) - 1
    # Pre-compute department indices needed by narrative and R&D projection
    dept_names_list = [d.name for d in _config_module.cfg.departments]
    rd_index = next((i for i, n in enumerate(dept_names_list) if n == 'R&D'), None)
    dept_returns = [float(result['revenue_by_dept'][yi, d]) for d in range(ND)]
    dept_state = [float(result['state_history'][yi + 1, d]) for d in range(ND)]

    year_result = {
        'total_revenue': float(result['total_revenue'][yi]),
        'profit': float(result['profit'][yi]),
        'total_spend': float(result['total_spend'][yi]),
        'underuse_penalty': float(result['underuse_penalty'][yi]),
        'max_allocatable': _ba['max_allocatable'],
        'unallocatable_budget': _ba['unallocatable'],
        'available_budget': float(result['available_budget'][yi]),
        'fixed_costs': float(result['fixed_costs'][yi]),
        'inflation_rate': float(result['inflation_rate'][yi]),
        'dept_returns': dept_returns,
        'dept_state': dept_state,
        'subdecision_multiplier': float(result['subdecision_multiplier'][yi]),
        'subdecisions': dict(subdecisions),
        'ops_cap': float(result['ops_cap'][yi]),
        'sales_raw': float(result['sales_raw'][yi]),
        'sales_capped': float(result['sales_capped'][yi]),
        'overspend_penalties': [float(result['overspend_penalty'][yi, d]) for d in range(ND)],
        # Synergy log for this year; narrative rules use it for pairing callouts.
        'synergies': list(result.get('synergies', [[]])[yi]) if yi < len(result.get('synergies', [])) else [],
        # Pre-computed bottleneck booleans for the narrative rules.
        'bottleneck_fired':  bool(result['sales_raw'][yi] > result['ops_cap'][yi] > 0),
        'overcap_penalty':   float(result['overcap_penalty'][yi]),
        'dept_news': [{'headline': e.headline, 'dept': e.dept_pressure,
                       'sentiment': e.sentiment, 'k_mult': e.dept_k_mult,
                       'smax_mult': e.dept_smax_mult}
                      for e in result['dept_news'][yi]],
        'general_news': [{'headline': e.headline, 'detail': e.detail,
                          'sentiment': e.sentiment, 'revenue_impact': e.revenue_impact,
                          'profit_impact': e.profit_impact}
                         for e in result['general_news'][yi]],
        'market_news': [{'headline': e.headline, 'detail': e.detail,
                         'sentiment': e.sentiment, 'target': e.target}
                        for e in result['market_news'][yi]],
    }

    # Competitor trajectories & market share
    try:
        mode = gs.get('mode', 'competition')
        play_seed = gs.get('play_seed', 42)
        n = len(locked)  # years locked so far (including this one)

        # Use cached competitor list — same seed always produces same result.
        competitors_list, _ = _cached_competitors(play_seed, NP)

        # Build hashable cache keys for allocations and sub-decisions so that
        # teams with identical spend patterns share trajectory results.
        alloc_key = tuple(tuple(a) for a in locked[:n])
        sd_key    = tuple(tuple(sorted(sd.items())) for sd in locked_sd[:n])

        comp_trajs = [
            _cached_competitor_trajectory(
                comp.name, play_seed, n, mode,
                alloc_key, sd_key, ci,
            )
            for ci, comp in enumerate(competitors_list)
        ]

        # Market share for all years up to now — we only need the last year's share
        user_revs = [
            *(r['total_revenue'] for r in gs.get('year_results', [])),
            year_result['total_revenue'],
        ]
        mkt = compute_market_shares(
            user_revs, comp_trajs,
            user_allocations=locked[:n],
            user_sub_decisions=locked_sd[:n],
            total_budget=_config_module.cfg.total_budget,
            game_seed=play_seed,
        )

        # mkt = [{name, shares: [yr0, yr1, ...]}, ...]
        # shares[0] = player, shares[1..] = competitors
        year_result['market_share'] = float(mkt[0]['shares'][yi]) if mkt else 0.0
        year_result['market_shares'] = {
            entry['name']: float(entry['shares'][yi])
            for entry in mkt
        }
        year_result['competitor_profits'] = {
            comp.name: float(comp_trajs[ci]['profits'][yi])
            for ci, comp in enumerate(competitors_list)
            if yi < len(comp_trajs[ci]['profits'])
        }
        year_result['competitor_revenues'] = {
            comp.name: float(comp_trajs[ci]['revenues'][yi])
            for ci, comp in enumerate(competitors_list)
            if yi < len(comp_trajs[ci]['revenues'])
        }

        # Competitor AI states — allocations, sub-decisions, dominant segment
        try:
            from scenarios import get_active_scenario as _gas
            _s = _gas()
            _has_ai = _s and any(
                getattr(comp_obj, 'personality', None) is not None
                for comp_obj in _s.competitors
            )
            if _has_ai:
                from simulator import generate_competitor_ai_news
                _, _news_fx = generate_competitor_ai_news({}, n, play_seed)
                ai_states = simulate_all_competitors(
                    n, locked[:n], locked_sd[:n],
                    seed=play_seed,
                    news_effects_by_year=_news_fx,
                )
                _dnames = [d.name for d in _config_module.cfg.departments]
                comp_ai_data = {}
                for comp_obj in competitors_list:
                    states = ai_states.get(comp_obj.name)
                    if not states or yi >= len(states):
                        continue
                    st      = states[yi]
                    st_prev = states[yi - 1] if yi > 0 else None
                    alloc_dict = {_dnames[i]: round(float(st.allocations[i])) for i in range(len(_dnames)) if i < len(st.allocations)}
                    alloc_prev = {_dnames[i]: round(float(st_prev.allocations[i])) for i in range(len(_dnames)) if i < len(st_prev.allocations)} if st_prev else {}
                    alloc_shifts = {d: alloc_dict.get(d, 0) - alloc_prev.get(d, 0) for d in alloc_dict} if alloc_prev else {}
                    biggest_shift_dept = max(alloc_shifts, key=lambda d: abs(alloc_shifts[d]), default=None) if alloc_shifts else None
                    # Dominant segment: where this competitor scores highest in likability
                    seg_lik = year_result.get('segment_likability', {})
                    dom_seg = max(seg_lik.keys(), key=lambda seg: seg_lik[seg].get(comp_obj.name, 0), default=None) if seg_lik else None
                    comp_ai_data[comp_obj.name] = {
                        'allocations':          alloc_dict,
                        'alloc_prev':           alloc_prev,
                        'alloc_shifts':         alloc_shifts,
                        'biggest_shift_dept':   biggest_shift_dept,
                        'biggest_shift_amount': alloc_shifts.get(biggest_shift_dept, 0) if biggest_shift_dept else 0,
                        'sub_decisions':        dict(st.sub_decisions),
                        'dominant_segment':     dom_seg,
                        'reach':                round(float(st.reach), 4),
                        'brand_boost':          round(float(st.brand_boost), 4),
                    }
                year_result['competitor_ai'] = comp_ai_data
            else:
                year_result['competitor_ai'] = {}
        except Exception as _ai_e:
            import logging as _logai
            _logai.getLogger('game_logic').warning(f'Competitor AI state extraction failed: {_ai_e}')
            year_result['competitor_ai'] = {}

        # R&D forward projection
        try:
            rd_pending_arr = result.get('rd_pending')
            if rd_pending_arr is not None and rd_index is not None and yi < len(rd_pending_arr):
                year_result['rd_next_year_projection'] = round(float(rd_pending_arr[yi]))
            else:
                year_result['rd_next_year_projection'] = 0
        except Exception:
            year_result['rd_next_year_projection'] = 0

        # Product spec evolution
        try:
            player_specs = compute_player_product_specs(locked[:n], locked_sd[:n], n)
            # Convert to per-year dict: {spec_key: value_this_year}
            year_result['product_specs'] = {
                k: float(v[yi]) for k, v in player_specs.items() if yi < len(v)
            }
        except Exception:
            year_result['product_specs'] = {}

        # Segment likability
        try:
            comp_specs = compute_competitor_product_specs(
                competitors_list,
                [{'name': c.name, 'revenues': comp_trajs[ci]['revenues'],
                  'profits': comp_trajs[ci]['profits']}
                 for ci, c in enumerate(competitors_list)],
                n,
            )
            comp_names = [c.name for c in competitors_list]
            likability_all = compute_segment_likability(player_specs, comp_specs, comp_names, n)
            # Extract this year's slice: {seg: {name: score}}
            year_result['segment_likability'] = {
                seg: entries[yi]
                for seg, entries in likability_all.items()
                if yi < len(entries)
            }
        except Exception:
            year_result['segment_likability'] = {}

    except Exception as _e:
        import logging as _log
        _log.getLogger('game_logic').warning(f'Competitor/market share computation failed: {_e}')
        year_result['market_share'] = 0.0
        year_result['market_shares'] = {}
        year_result['competitor_profits'] = {}
        year_result['competitor_revenues'] = {}
        year_result['product_specs'] = {}
        year_result['segment_likability'] = {}

    # Compute next year's budget
    profit = result['profit'][yi]
    reinvest = profit * _config_module.cfg.profit_reinvestment_rate
    reinvest = (math.ceil(reinvest / 100) * 100 if reinvest >= 0
                else math.floor(reinvest / 100) * 100)
    next_bgt = max(gs.get('available_budget', _config_module.cfg.total_budget) + reinvest,
                   _config_module.cfg.total_budget * 0.5)
    infl = result['inflation_rate'][yi]
    next_costs = result['fixed_costs'][yi] * (1 + infl)
    cum_infl = gs.get('cumulative_inflation', 1.0) * (1 + infl)

    is_comp = gs.get('mode', 'competition') == 'competition'
    waiting = False
    if is_comp:
        try:
            from game_state import get_all_team_keys
            roster = get_all_team_keys()
            # Multi-team: show the waiting overlay until the barrier clears it.
            if len(roster) > 1:
                waiting = True
            # else: truly a solo run (only one team in users.json) — no wait
        except Exception:
            # Roster read failed — fail SAFE (block and let the barrier
            # / watchdog sort it out) rather than fail OPEN (race ahead).
            waiting = True

    yr = gs.get('year_results', [])
    yr.append(year_result)

    new_gs = {
        'current_year': cur + 1,
        'locked_allocations': locked,
        'year_results': yr,
        'play_seed': gs['play_seed'],
        'completed': (cur >= NP),
        'mode': gs.get('mode', 'competition'),
        'available_budget': next_bgt,
        'current_fixed_costs': next_costs,
        'cumulative_inflation': cum_infl,
        'locked_subdecisions': locked_sd,
        'player_news': gs.get('player_news', []),
        'waiting_for_others': waiting,
        'simulation_started': True,
        # Preserve simulation_begun so late-joining viewers can skip storyboard
        'simulation_begun': gs.get('simulation_begun', False),
    }

    # VPI from the profit and share computed above; floors and ceilings come from the scenario.
    try:
        from leaderboard import vpi_grade
        import config as _cfg_mod
        profit    = year_result.get('profit', 0)
        avg_share = year_result.get('market_share', 0)

        ras = float(profit)  # single deterministic run, std=0
        ras_floor, ras_ceil = _cfg_mod.VPI_RAS_FLOOR, _cfg_mod.VPI_RAS_CEIL
        sh_floor,  sh_ceil  = _cfg_mod.VPI_SHARE_FLOOR, _cfg_mod.VPI_SHARE_CEIL

        ras_norm   = (ras - ras_floor)     / (ras_ceil - ras_floor)   if ras_ceil  != ras_floor  else 0
        share_norm = (avg_share - sh_floor) / (sh_ceil  - sh_floor)   if sh_ceil   != sh_floor   else 0
        vpi   = round((0.50 * ras_norm + 0.50 * share_norm) * 1000)
        grade = vpi_grade(vpi)

        yr[-1]['vpi']           = vpi
        yr[-1]['grade']         = grade
        yr[-1]['ras']           = round(ras)
        yr[-1]['avg_share_vpi'] = avg_share
        # Each half of the VPI (0-500), so the recap can say which one dragged the score down.
        yr[-1]['profit_score']  = round(max(0.0, min(1.0, ras_norm))   * 500)
        yr[-1]['share_score']   = round(max(0.0, min(1.0, share_norm)) * 500)
        new_gs['year_results']  = yr
    except Exception as _ve:
        import logging as _l
        _l.getLogger('game_logic').warning(f'VPI compute failed for {team_key}: {_ve}')

    # Generate market narrative ("What happened in the market?")
    try:
        from services.market_narrative import generate_market_narrative
        from scenarios import get_active_scenario as _gas2
        _s2 = _gas2()
        _sc2 = {
            'currency_symbol': getattr(getattr(_s2, 'locale', None), 'currency_symbol', '$') if _s2 else '$',
            'small_number_suffix': getattr(getattr(_s2, 'locale', None), 'small_number_suffix', 'K') if _s2 else 'K',
        }
        market_narrative = generate_market_narrative(
            year_result=yr[-1],
            history=yr,
            scenario_info=_sc2,
        )
        if market_narrative:
            yr[-1]['market_narrative'] = market_narrative
            new_gs['year_results'] = yr
    except Exception as _mn_e:
        import logging as _lmn
        _lmn.getLogger('game_logic').warning(f'Market narrative failed for {team_key}: {_mn_e}')

    # Attach the recap narrative; a failure here must not block the lock.
    try:
        from services.narrative import generate_year_narrative
        from scenarios import get_active_scenario
        s = get_active_scenario()
        sc_info = {
            'currency_symbol': getattr(getattr(s, 'locale', None), 'currency_symbol', '$') if s else '$',
            'small_number_suffix': getattr(getattr(s, 'locale', None), 'small_number_suffix', 'K') if s else 'K',
        }
        narrative = generate_year_narrative(
            year_result=yr[-1],
            history=yr,
            scenario_info=sc_info,
            gs=new_gs,
        )
        if narrative:
            yr[-1]['narrative'] = narrative
            new_gs['year_results'] = yr
    except Exception as _ne:
        import logging as _l2
        _l2.getLogger('game_logic').warning(f'Narrative generation failed for {team_key}: {_ne}')

    # Compute the final VPI (Monte Carlo) inline and store it with the state.
    if cur >= NP:
        try:
            from leaderboard import compute_final_vpi
            final_vpi = compute_final_vpi(new_gs, new_gs.get('mode', 'competition'))
            if final_vpi:
                new_gs['final_vpi'] = final_vpi
        except Exception as _fv_err:
            import logging as _l3
            _l3.getLogger('game_logic').warning(
                f'final_vpi synchronous compute failed for {team_key}: {_fv_err}'
            )

    # Does not persist; callers save the result.
    return {
        "game_state": new_gs,
        "year_result": year_result,
        "year": cur,
        "completed": cur >= NP,
        "waiting_for_others": waiting,
    }


def get_competitors_data(play_seed: int) -> tuple[list, list]:
    """Generate competitor data for briefing/market tabs."""
    competitors, all_news = generate_competitors(NP, play_seed)
    comp_list = []
    for c in competitors:
        comp_list.append({
            'name': c.name,
            'display_label': getattr(c, 'display_label', ''),
            'description': getattr(c, 'description', ''),
            'location': getattr(c, 'location', ''),
            'founded': getattr(c, 'founded', ''),
            'industry': getattr(c, 'industry', ''),
            'spending_tendency': getattr(c, 'personality', None) and getattr(c.personality, 'spending_tendency', '') or '',
            'budget': int(getattr(getattr(c, 'personality', None), 'total_budget', 0)),
            'margin': getattr(c, 'margin', 0.0),
            'base_revenue': [int(r) for r in c.base_revenue] if hasattr(c, 'base_revenue') else [],
            'base_profit': [int(p) for p in c.base_profit] if hasattr(c, 'base_profit') else [],
            'news_events': [
                {'headline': n.headline, 'detail': getattr(n, 'detail', ''),
                 'sentiment': n.sentiment, 'target': getattr(n, 'target', c.name)}
                for n in (c.news_events or [])
            ] if hasattr(c, 'news_events') and c.news_events else [],
        })
    # Serialize all_news — flat list of NewsEvent objects
    news_list = []
    for n in all_news:
        news_list.append({
            'headline': n.headline,
            'detail': getattr(n, 'detail', ''),
            'sentiment': n.sentiment,
            'target': getattr(n, 'target', ''),
            'year': getattr(n, 'year', 0),
        })
    return comp_list, news_list


def get_slider_constraints(gs: dict) -> list[dict]:
    """
    Compute slider min/max/default for each department given current game state.
    Sent to frontend so React can render sliders with correct bounds.

    Each constraint dict includes the usual min/max/default/step fields.
    The list itself carries two extra attributes accessible via the helper
    get_budget_allocatability(gs):
      - sum_of_maxima:  sum of all dept 'max' values — the most the team
                        can possibly spend given the ±30% change-rate caps
      - unallocatable:  max(0, budget - sum_of_maxima) — the portion of the
                        promised budget that is structurally unreachable this
                        year; teams must not be penalised for this amount
    """
    locked = gs.get('locked_allocations', [])
    prev = locked[-1] if locked else None
    cum_infl = gs.get('cumulative_inflation', 1.0)

    constraints = []
    for d, dept in enumerate(_config_module.cfg.departments):
        adj_min = _round1k(_round100_up(dept.min_spend * cum_infl))
        lo, hi = adj_min, _round1k(dept.max_spend)
        if prev:
            lo = max(lo, _round1k(_round100_up(prev[d] * (1 - _config_module.cfg.max_change_rate))))
            hi = min(hi, _round1k(int(prev[d] * (1 + _config_module.cfg.max_change_rate) / 100) * 100))
        hi = max(hi, lo)

        constraints.append({
            'dept_name': dept.name,
            'min': lo,
            'max': hi,
            'default': lo,
            'step': _config_module.cfg.slider_step if hasattr(_config_module.cfg, 'slider_step') else 100000,
        })

    return constraints


def get_budget_allocatability(gs: dict) -> dict:
    """
    Return the max-allocatable budget and unallocatable gap for a game state.

    Used by:
      - execute_lock_year: to pass max_allocatable_by_year into the simulator
        so the underuse penalty only fires on genuinely spendable budget
      - API responses: so the frontend can display the structural gap clearly
    """
    constraints = get_slider_constraints(gs)
    budget = gs.get('available_budget', _config_module.cfg.total_budget)
    sum_of_maxima = sum(c['max'] for c in constraints)
    unallocatable = max(0.0, budget - sum_of_maxima)
    return {
        'sum_of_maxima': sum_of_maxima,
        'unallocatable': unallocatable,
        'max_allocatable': sum_of_maxima,
    }


def _round1k(v):
    return round(v / 1000) * 1000

def _round100_up(v):
    import math as _m
    return _m.ceil(v / 100) * 100
