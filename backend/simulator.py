"""Core simulation engine: department return curves, synergies and bottlenecks, market share,
news events and the competitor AI. Scenario content is supplied by the active scenario.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple


def _active_scenario():
    """The active scenario, or None."""
    try:
        from scenarios import get_active_scenario
        return get_active_scenario()
    except Exception:
        return None


def get_consumer_segments() -> dict:
    return _active_scenario().segments_dict()


def get_sub_decisions() -> dict:
    return _active_scenario().sub_decisions_dict()


def get_dept_background() -> dict:
    return _active_scenario().dept_background_dict()


def get_company_name() -> str:
    return _active_scenario().company.name


def get_news_pool() -> list:
    s = _active_scenario()
    return s.competitor_news_pool if s.competitor_news_pool else _NEWS_POOL


def get_dept_news_pool() -> list:
    s = _active_scenario()
    return s.dept_news_pool if s.dept_news_pool else _DEPT_NEWS_POOL

def get_general_news_pool() -> list:
    s = _active_scenario()
    return s.general_news_pool if s.general_news_pool else _GENERAL_NEWS_POOL

def get_competitor_defs() -> list:
    """Return competitor definitions from scenario."""
    return _active_scenario().competitor_defs_list()

def get_bottleneck_config() -> dict:
    """Return bottleneck/synergy config from scenario."""
    s = _active_scenario()
    return {
        'cap_dept_idx': s.bottleneck_cap_dept_idx,
        'capped_dept_idx': s.bottleneck_capped_dept_idx,
        'cap_fraction': s.bottleneck_cap_fraction,
        'overcap_ratio': getattr(s, 'bottleneck_overcap_ratio', 1.5),
        'overcap_floor': getattr(s, 'bottleneck_overcap_floor', 0.6),
        'delayed_dept_idx': s.delayed_return_dept_idx,
        'brand_equity_depts': s.brand_equity_depts,
    }

@dataclass
class DepartmentConfig:
    name: str
    S_max: float
    K: float
    alpha: float
    decay: float
    min_spend: float
    max_spend: float
    state_sensitivity: float = 0.1
    catch_up_rate: float = 0.3
    sweet_spot_frac: float = 0.75 


@dataclass
class NewsEvent:
    year: int
    headline: str
    detail: str
    revenue_impact: float
    profit_impact: float
    sentiment: str
    target: str = ""
    # department-specific pressure
    dept_pressure: str = ""        # dept name affected (empty = general)
    dept_k_mult: float = 1.0      # temporary K multiplier (>1 = harder)
    dept_smax_mult: float = 1.0   # temporary S_max multiplier (<1 = weaker)


@dataclass
class CompetitorCompany:
    name: str
    industry: str
    location: str
    founded: str
    description: str
    base_revenue: List[float] = field(default_factory=list)
    base_profit: List[float] = field(default_factory=list)
    news_events: List[NewsEvent] = field(default_factory=list)


@dataclass
class ScenarioConfig:
    company_name: str = ""
    product_name: str = ""
    base_revenue: float = 40_000_000       # Year 0 context: NOT added to sim
    unit_price: float = 42_000.0
    unit_cost: float = 28_000.0
    fixed_costs: float = 95_000_000
    total_budget: float = 60_000_000
    num_periods: int = 5
    profit_reinvestment_rate: float = 0.20
    inflation_min: float = 0.06
    inflation_max: float = 0.15
    underuse_threshold: float = 0.15
    underuse_penalty_rate: float = 2.5
    max_change_rate: float = 0.30        
    departments: list = field(default_factory=list)
    demand_noise_std: float = 0.08
    scenario_drift_std: float = 0.03
    risk_penalty_lambda: float = 1.5
    carryover_strength: float = 1.0
    num_eval_scenarios: int = 30
    state_decay: float = 0.5

    def __post_init__(self):
        if not self.departments:
            self.departments = self._default_departments()

    def _default_departments(self):
        return [
            DepartmentConfig("R&D", S_max=80_000_000, K=16_000_000, alpha=1.3,
                             decay=0.6, min_spend=3_000_000, max_spend=30_000_000,
                             state_sensitivity=0.12, catch_up_rate=0.25,
                             sweet_spot_frac=0.70),
            DepartmentConfig("Sales", S_max=60_000_000, K=14_000_000, alpha=0.9,
                             decay=0.15, min_spend=5_000_000, max_spend=30_000_000,
                             state_sensitivity=0.05, catch_up_rate=0.35,
                             sweet_spot_frac=0.80),
            DepartmentConfig("Operations", S_max=80_000_000, K=9_000_000, alpha=0.85,
                             decay=0.55, min_spend=4_000_000, max_spend=25_000_000,
                             state_sensitivity=0.12, catch_up_rate=0.30,
                             sweet_spot_frac=0.80),
            DepartmentConfig("Marketing", S_max=80_000_000, K=10_000_000, alpha=1.05,
                             decay=0.40, min_spend=3_000_000, max_spend=25_000_000,
                             state_sensitivity=0.10, catch_up_rate=0.30,
                             sweet_spot_frac=0.65),
        ]


# Per-department sub-decision modifier

def compute_dept_subdecision_modifiers(
    sub_decisions_by_year: List[Dict[str, str]],
    year_idx: int,
    dept_names: List[str],
    track_log: Optional[list] = None,
) -> Dict[str, Dict]:
    """
    For each department, compute the sub-decision's impact on its own curve
    and any synergy bonuses it grants to other departments.

    Diminishing synergy returns: if the same sub-decision is chosen in
    consecutive years, cross-department synergy bonuses decay by 30% per
    repeat.  Own-department curve modifiers (smax_mult, k_mult) are NOT
    diminished; only the synergy bonuses to OTHER departments decay.

    Returns dict: {dept_name: {'smax_mult': float, 'k_mult': float}}

    Optional `track_log`: if a list is passed, the function appends one
    entry per synergy bonus it applies:
        {'source':          str — dept that emitted the bonus
         'source_choice':   str — sub-decision key (e.g. 'Innovate')
         'target':          str — dept that received the bonus
         'raw_bonus':       float — bonus before decay (0.10 = +10%)
         'streak':          int — # of consecutive prior years with same choice
         'decay_factor':    float — multiplier applied to raw_bonus (1.0 = full,
                                    0.7 = first repeat, ... floor 0.4)
         'effective_bonus': float — raw_bonus * decay_factor (what hit the curve)}
    This is INSTRUMENTATION ONLY — simulation outputs are unchanged whether
    or not track_log is passed.  Existing callers that pass nothing see no
    behaviour change.
    """
    if year_idx >= len(sub_decisions_by_year):
        return {d: {'smax_mult': 1.0, 'k_mult': 1.0} for d in dept_names}

    year_decisions = sub_decisions_by_year[year_idx]
    if not year_decisions:
        return {d: {'smax_mult': 1.0, 'k_mult': 1.0} for d in dept_names}

    mods = {d: {'smax_mult': 1.0, 'k_mult': 1.0} for d in dept_names}

    # Count consecutive repeats per department (how many prior years in a row
    # was this same sub-decision chosen?)
    repeat_counts: Dict[str, int] = {}
    for dept_name, option_key in year_decisions.items():
        streak = 0
        for prior_idx in range(year_idx - 1, -1, -1):
            if prior_idx >= len(sub_decisions_by_year):
                break
            prior = sub_decisions_by_year[prior_idx]
            if prior.get(dept_name) == option_key:
                streak += 1
            else:
                break
        repeat_counts[dept_name] = streak

    _sd = get_sub_decisions()
    for dept_name, option_key in year_decisions.items():
        if dept_name not in _sd:
            continue
        opts = _sd[dept_name]["options"]
        if option_key not in opts:
            continue
        opt = opts[option_key]

        # Own department curve modification: no diminishing returns
        mods[dept_name]['smax_mult'] *= opt.get('smax_mult', 1.0)
        mods[dept_name]['k_mult'] *= opt.get('k_mult', 1.0)

        # Synergy bonuses to OTHER departments: decay 30% per consecutive repeat
        streak = repeat_counts.get(dept_name, 0)
        synergy_decay = max(0.4, 1.0 - 0.30 * streak)  # floor at 40% of original

        for target_dept, smax_bonus in opt.get('synergy', {}).items():
            if target_dept in mods:
                # Apply decay only to the synergy bonus portion
                effective_bonus = smax_bonus * synergy_decay
                mods[target_dept]['smax_mult'] *= (1.0 + effective_bonus)

                # Optional instrumentation — append for callers that want it
                if track_log is not None:
                    track_log.append({
                        'source':          dept_name,
                        'source_choice':   option_key,
                        'target':          target_dept,
                        'raw_bonus':       float(smax_bonus),
                        'streak':          int(streak),
                        'decay_factor':    float(synergy_decay),
                        'effective_bonus': float(effective_bonus),
                    })

    return mods


def compute_subdecision_multiplier(
    sub_decisions_by_year: List[Dict[str, str]], year_idx: int
) -> float:
    """Segment-weighted consumer fit score (for UI display + market share)."""
    if year_idx >= len(sub_decisions_by_year):
        return 1.0
    year_decisions = sub_decisions_by_year[year_idx]
    if not year_decisions:
        return 1.0

    _cs = get_consumer_segments()
    _sd = get_sub_decisions()
    segments = list(_cs.keys())
    segment_weights = np.array([_cs[s]["market_weight"] for s in segments])
    segment_scores = np.ones(len(segments))
    dept_count = 0

    for dept_name, option_key in year_decisions.items():
        if dept_name not in _sd:
            continue
        dept_opts = _sd[dept_name]["options"]
        if option_key not in dept_opts:
            continue
        mults = dept_opts[option_key]["segment_multipliers"]
        for i, seg in enumerate(segments):
            segment_scores[i] *= mults.get(seg, 1.0)
        dept_count += 1

    if dept_count == 0:
        return 1.0
    segment_scores = segment_scores ** (1.0 / dept_count)
    return float(np.dot(segment_weights, segment_scores))


# Empty defaults; news comes from the active scenario's news module.

_NEWS_POOL = []
_DEPT_NEWS_POOL = []
_GENERAL_NEWS_POOL = []


# News Generation

def generate_news_events(companies: list, num_periods: int, seed: int) -> List[NewsEvent]:
    rng = np.random.RandomState(seed)
    all_events = []

    _pool = get_news_pool()
    pool_by_sentiment = {
        'positive': [e for e in _pool if e[4] == 'positive'],
        'negative': [e for e in _pool if e[4] == 'negative'],
        'neutral':  [e for e in _pool if e[4] == 'neutral'],
    }
    sentiment_choices = ['positive', 'negative', 'neutral']
    sentiment_weights = np.array([50, 50, 15], dtype=float)
    sentiment_weights /= sentiment_weights.sum()

    for yr in range(1, num_periods + 1):
        n_events = rng.randint(1, 4)
        affected = rng.choice(len(companies), size=n_events, replace=True)

        for comp_idx in affected:
            comp = companies[comp_idx]
            sentiment = rng.choice(sentiment_choices, p=sentiment_weights)
            bucket = pool_by_sentiment[sentiment]
            tmpl_idx = rng.randint(0, len(bucket))
            headline_t, detail_t, rev_range, prof_range, _ = bucket[tmpl_idx]

            rev_impact = rng.uniform(*rev_range)
            prof_impact = rng.uniform(*prof_range)

            event = NewsEvent(
                year=yr,
                headline=headline_t.replace("{{company}}", comp.name),
                detail=detail_t,
                revenue_impact=round(rev_impact, 3),
                profit_impact=round(prof_impact),
                sentiment=sentiment,
                target=comp.name,
            )
            all_events.append(event)

    return all_events


def generate_player_news_events(num_periods: int, seed: int) -> List[NewsEvent]:
    """Generate 6 visible news events per year:
     - 2 department-targeted (modify specific department's K and S_max)
     - 2 general company-wide (revenue multiplier + flat profit impact)
     - 2 competitor/market news (informational only, no gameplay effect)

    Department and general events affect the simulation.
    Competitor news is display-only. It shows what's happening in the
    broader market to create immersion, but has no mechanical impact.
    """
    rng = np.random.RandomState(seed + 200)
    events = []

    _company = get_company_name()
    _dept_pool = get_dept_news_pool()
    _gen_pool = get_general_news_pool()
    _comp_pool = get_news_pool()

    for yr in range(1, num_periods + 1):
        # 2 department events (no duplicate departments in same year)
        used_depts = set()
        attempts = 0
        dept_count = 0
        while dept_count < 2 and attempts < 20:
            attempts += 1
            idx = rng.randint(0, len(_dept_pool))
            tmpl = _dept_pool[idx]
            headline, detail, dept, k_mult, smax_mult, sentiment = tmpl

            if dept in used_depts:
                continue
            used_depts.add(dept)
            dept_count += 1

            # Add randomness to pressure magnitude
            k_noise = rng.uniform(0.9, 1.1)
            s_noise = rng.uniform(0.9, 1.1)
            actual_k = 1.0 + (k_mult - 1.0) * k_noise
            actual_s = 1.0 + (smax_mult - 1.0) * s_noise

            event = NewsEvent(
                year=yr,
                headline=headline.replace("{{company}}", _company),
                detail=detail,
                revenue_impact=1.0,
                profit_impact=0,
                sentiment=sentiment,
                target=_company,
                dept_pressure=dept,
                dept_k_mult=round(actual_k, 3),
                dept_smax_mult=round(actual_s, 3),
            )
            events.append(event)

        # 2 general (company-wide) events
        used_general = set()
        for _ in range(2):
            idx = rng.randint(0, len(_gen_pool))
            while idx in used_general:
                idx = rng.randint(0, len(_gen_pool))
            used_general.add(idx)

            tmpl = _gen_pool[idx]
            headline, detail, rev_range, prof_range, sentiment = tmpl

            rev_mult = rng.uniform(*rev_range)
            prof_impact = rng.uniform(*prof_range)

            event = NewsEvent(
                year=yr,
                headline=headline.replace("{{company}}", _company),
                detail=detail,
                revenue_impact=round(rev_mult, 3),
                profit_impact=round(prof_impact),
                sentiment=sentiment,
                target=_company,
                dept_pressure="",      # empty = company-wide
                dept_k_mult=1.0,
                dept_smax_mult=1.0,
            )
            events.append(event)

        # 2 competitor/market news (display-only, no gameplay effect)
        used_comp = set()
        for _ in range(2):
            idx = rng.randint(0, len(_comp_pool))
            while idx in used_comp:
                idx = rng.randint(0, len(_comp_pool))
            used_comp.add(idx)

            tmpl = _comp_pool[idx]
            headline, detail, rev_range, prof_range, sentiment = tmpl

            # Pick a random competitor name for the headline
            s = _active_scenario()
            comp_name = s.competitors[rng.randint(0, len(s.competitors))].name

            event = NewsEvent(
                year=yr,
                headline=headline.replace("{{company}}", comp_name),
                detail=detail,
                revenue_impact=1.0,   # No effect on player
                profit_impact=0,      # No effect on player
                sentiment=sentiment,
                target=comp_name,     # Marks this as competitor news
                dept_pressure="__market__",  # Special marker for UI rendering
                dept_k_mult=1.0,
                dept_smax_mult=1.0,
            )
            events.append(event)

    return events


def generate_competitor_ai_news(
    ai_states: Dict[str, List],
    num_periods: int,
    seed: int,
) -> Tuple[List[NewsEvent], Dict[str, Dict[int, dict]]]:
    """Generate news events from competitor AI actions and pre-scripted
    competitor-affecting events.

    Returns:
        (display_events, competitor_effects_by_year)

        display_events: List[NewsEvent]: news headlines for the player to see,
            generated from what competitors actually did. These replace the old
            static competitor news pool.

        competitor_effects_by_year: {comp_name: {year_idx: effects_dict}}
            Pre-scripted effects that should be applied to competitor decisions.
            Keyed by 0-indexed year. effects_dict has keys like:
                "allocation_shift": {"dept_name": delta_fraction}
                "force_sub_decision": {"dept_name": "option_key"}
                "budget_mult": float
    """
    rng = np.random.RandomState(seed + 500)
    s = _active_scenario()
    if not s:
        return [], {}

    display_events = []
    comp_effects = {}  # {comp_name: {yr: effects_dict}}

    # Dynamic news templates based on competitor actions
    action_templates = {
        'heavy_rd': [
            ("{name} Reportedly Doubles Down on R&D: Industry Sources",
             "Analysts note increased patent filings and engineering hires."),
            ("{name} Unveils Ambitious Technology Roadmap at Investor Day",
             "Multi-year R&D investment plan exceeds industry expectations."),
        ],
        'heavy_marketing': [
            ("{name} Launches Aggressive Brand Campaign Across Major Markets",
             "Marketing spend surge signals intent to capture mindshare."),
            ("{name} Signs Celebrity Endorsement Deal Worth Millions",
             "Brand awareness push targets younger demographics."),
        ],
        'perf_sub': [
            ("{name} Reveals Next-Gen Performance Platform at Auto Show",
             "New powertrain architecture promises class-leading acceleration."),
        ],
        'software_sub': [
            ("{name} Announces Major Software Update with AI Features",
             "OTA update brings autonomous driving improvements to existing fleet."),
        ],
        'cost_sub': [
            ("{name} Cuts Starting Price by $3,000 on Entry Model",
             "Cost reduction initiative enables more competitive pricing."),
        ],
        'range_sub': [
            ("{name} Claims Battery Breakthrough - 400+ Mile Range Target",
             "New cell chemistry promises significant range improvement."),
        ],
        'fleet_sub': [
            ("{name} Wins Major Government Fleet Contract",
             "Multi-year deal to supply electric vehicles to federal agencies."),
        ],
    }

    # Pre-scripted competitor-affecting events (happen at specific years)
    # These create dramatic moments and force competitors to deviate from plan.
    prescripted = [
        # Year 2: Tariff hits BrightDrive
        (1, "BrightDrive Motors", {
            "headline": "US Announces 35% Tariff on Chinese EV Imports",
            "detail": "BrightDrive faces margin pressure; may need to localize production.",
            "sentiment": "negative",
            "effects": {"budget_mult": 0.85, "allocation_shift": {"Operations": 0.10, "Marketing": -0.05, "Sales": -0.05}},
        }),
        # Year 3: Apex union issues
        (2, "Apex Legacy Auto (EV Division)", {
            "headline": "Apex Legacy Auto Workers Vote to Strike Over EV Transition Terms",
            "detail": "Production halted at main assembly plant; resolution expected within months.",
            "sentiment": "negative",
            "effects": {"budget_mult": 0.90, "allocation_shift": {"Operations": 0.12, "R&D": -0.06, "Marketing": -0.06}},
        }),
        # Year 4: Halo gets tech partnership
        (3, "Halo Electric", {
            "headline": "Halo Electric Partners with Major Tech Firm on Autonomous Driving",
            "detail": "Strategic partnership brings Silicon Valley AI expertise to European engineering.",
            "sentiment": "positive",
            "effects": {"allocation_shift": {"R&D": 0.08, "Sales": -0.04, "Operations": -0.04},
                        "force_sub_decision": {"R&D": "software"}},
        }),
        # Year 4: BrightDrive gets investment
        (3, "BrightDrive Motors", {
            "headline": "BrightDrive Secures $500M Investment from Sovereign Wealth Fund",
            "detail": "Funding to accelerate Western market expansion and local manufacturing.",
            "sentiment": "positive",
            "effects": {"budget_mult": 1.15},
        }),
    ]

    # Register pre-scripted effects
    for yr_idx, comp_name, event_data in prescripted:
        if comp_name not in comp_effects:
            comp_effects[comp_name] = {}
        comp_effects[comp_name][yr_idx] = event_data.get('effects', {})

        # Also create display event
        display_events.append(NewsEvent(
            year=yr_idx + 1,
            headline=event_data['headline'],
            detail=event_data['detail'],
            revenue_impact=1.0,
            profit_impact=0,
            sentiment=event_data['sentiment'],
            target=comp_name,
            dept_pressure="__market__",
        ))

    # Generate dynamic news from AI actions (post-hoc, after simulation)
    for comp_name, states in ai_states.items():
        for yr_idx, state in enumerate(states):
            if rng.random() > 0.4:  # 60% chance of news per competitor per year
                continue

            # Determine what's noteworthy about this year's actions
            rd_alloc = state.allocations[0] if state.allocations else 0
            mktg_alloc = state.allocations[3] if len(state.allocations) > 3 else 0
            rd_sub = state.sub_decisions.get("R&D", "")
            sales_sub = state.sub_decisions.get("Sales", "")

            personality = next((c.personality for c in s.competitors if c.name == comp_name), None)
            if not personality:
                continue

            rd_frac = rd_alloc / personality.total_budget if personality.total_budget > 0 else 0
            mktg_frac = mktg_alloc / personality.total_budget if personality.total_budget > 0 else 0

            # Pick template based on most noteworthy action
            if rd_frac > 0.35:
                templates = action_templates['heavy_rd']
            elif mktg_frac > 0.30:
                templates = action_templates['heavy_marketing']
            elif rd_sub == 'performance':
                templates = action_templates['perf_sub']
            elif rd_sub == 'software':
                templates = action_templates['software_sub']
            elif rd_sub == 'cost':
                templates = action_templates['cost_sub']
            elif rd_sub == 'range':
                templates = action_templates['range_sub']
            elif sales_sub == 'fleet':
                templates = action_templates['fleet_sub']
            else:
                continue

            tmpl = templates[rng.randint(0, len(templates))]
            headline = tmpl[0].format(name=comp_name)
            detail = tmpl[1]

            display_events.append(NewsEvent(
                year=yr_idx + 1,
                headline=headline,
                detail=detail,
                revenue_impact=1.0,
                profit_impact=0,
                sentiment="neutral",
                target=comp_name,
                dept_pressure="__market__",
            ))

    return display_events, comp_effects


# Competitor Generation

def generate_competitors(num_periods: int = 5, seed: int = 999) -> tuple:
    rng = np.random.RandomState(seed)

    # Build competitor list from scenario
    _comp_defs = get_competitor_defs()
    companies = [
        CompetitorCompany(
            name=cd['name'], industry=cd['industry'],
            location=cd['location'], founded=cd['founded'],
            description=cd['description'],
        )
        for cd in _comp_defs
    ]
    profiles = {cd['name']: (cd['base_revenue'], cd['growth_rate'], cd['margin'])
                for cd in _comp_defs}

    # Generate competitor news events
    news_seed = seed + 42
    all_news = generate_news_events(companies, num_periods, news_seed)

    for comp in companies:
        comp.news_events = [e for e in all_news if e.target == comp.name]

    for comp in companies:
        base_rev, growth, margin = profiles[comp.name]
        rev = base_rev
        revenues, profits = [], []
        for yr in range(num_periods):
            yr_growth = growth + rng.uniform(-0.02, 0.2)
            rev *= (1 + yr_growth)
            yr_margin = margin + rng.uniform(-0.05, 0.05)
            profit = rev * yr_margin

            for event in comp.news_events:
                if event.year == yr + 1:
                    rev *= event.revenue_impact
                    profit += event.profit_impact

            revenues.append(round(rev))
            profits.append(round(profit))

        comp.base_revenue = revenues
        comp.base_profit = profits

    return companies, all_news


def compute_competitor_trajectory(competitor, num_periods, mode='course',
                                   user_allocations=None, seed=42,
                                   user_sub_decisions=None):
    rng = np.random.RandomState(seed)
    revenues = list(competitor.base_revenue[:num_periods])
    profits = list(competitor.base_profit[:num_periods])

    # Always apply volatility and user-pressure (not just competition mode)
    for yr in range(min(len(revenues), num_periods)):
        # Base volatility: competitors have unpredictable swings
        vol_mult = rng.uniform(0.5, 1.5)
        revenues[yr] = int(revenues[yr] * vol_mult)
        profits[yr] = int(profits[yr] * vol_mult)

    if mode == 'competition':
        _pool = get_news_pool()
        pool_by_sentiment = {
            'positive': [e for e in _pool if e[4] == 'positive'],
            'negative': [e for e in _pool if e[4] == 'negative'],
            'neutral':  [e for e in _pool if e[4] == 'neutral'],
        }
        sentiment_choices = ['positive', 'negative', 'neutral']
        sentiment_weights = np.array([50, 50, 15], dtype=float)
        sentiment_weights /= sentiment_weights.sum()

        for yr in range(min(len(revenues), num_periods)):
            n_extra = rng.randint(0, 3)
            for _ in range(n_extra):
                sentiment = rng.choice(sentiment_choices, p=sentiment_weights)
                bucket = pool_by_sentiment[sentiment]
                tmpl = bucket[rng.randint(0, len(bucket))]
                rev_mult = rng.uniform(*tmpl[2])
                prof_add = rng.uniform(*tmpl[3])
                revenues[yr] = int(revenues[yr] * rev_mult)
                profits[yr] = int(profits[yr] * rev_mult + prof_add)

    # Competitors adapt to user spending: heavy user investment forces competitors
    # to respond (spending war), reducing their margins but sometimes boosting revenue
    if user_allocations:
        # Get budget from scenario for intensity calculation
        _s = _active_scenario()
        _budget = _s.financials.total_budget if _s else 60_000_000
        for yr in range(min(len(user_allocations), num_periods)):
            user_spend = sum(user_allocations[yr])
            intensity = user_spend / _budget

            # Revenue pressure: strong user spend steals market, but competitors fight back
            if intensity > 1.0:
                # User overspending: competitors lose some revenue but adapt aggressively
                rev_pressure = 1.0 - 0.10 * (intensity - 1.0)
                margin_squeeze = 0.85 + rng.uniform(0, 0.10)  # they cut margins to compete
                revenues[yr] = int(revenues[yr] * rev_pressure * rng.uniform(0.92, 1.08))
                profits[yr] = int(revenues[yr] * margin_squeeze * 0.10)
            elif intensity > 0.7:
                # Moderate user spend: competitors maintain with some noise
                noise = rng.uniform(0.93, 1.07)
                revenues[yr] = int(revenues[yr] * noise)
                profits[yr] = int(profits[yr] * noise)
            else:
                # User underspending: competitors capitalise and grow faster
                boost = 1.0 + 0.12 * (0.7 - intensity)
                revenues[yr] = int(revenues[yr] * boost * rng.uniform(0.96, 1.04))
                profits[yr] = int(profits[yr] * boost * rng.uniform(0.96, 1.04))

    # The main competitor pivots toward a segment the player has dominated for 2+ years.
    if user_sub_decisions and len(user_sub_decisions) >= 2:
        _cs = get_consumer_segments()
        _sd = get_sub_decisions()
        segment_keys = list(_cs.keys())

        # Measure player's segment concentration: which segment has the highest
        # cumulative multiplier across all locked sub-decisions?
        seg_scores = {k: 0.0 for k in segment_keys}
        for yr_idx, yr_sd in enumerate(user_sub_decisions):
            for dept_name, opt_key in yr_sd.items():
                if dept_name not in _sd:
                    continue
                dept_opts = _sd[dept_name].get('options', {})
                if opt_key not in dept_opts:
                    continue
                seg_mults = dept_opts[opt_key].get('segment_multipliers', {})
                for seg_key in segment_keys:
                    m = seg_mults.get(seg_key, 1.0)
                    seg_scores[seg_key] += (m - 1.0)  # accumulate deltas above baseline

        # Identify the player's dominant segment (highest positive score)
        dominant_seg = max(seg_scores, key=seg_scores.get)
        dominance_strength = seg_scores[dominant_seg]

        # Only react if dominance is meaningful (player committed to a segment)
        if dominance_strength > 0.5:
            # Response intensity depends on the competitor's seed: aggressive (seed%3==0), moderate (==1), passive.
            response_start = min(2, len(revenues) - 1)  # react from Year 3 onward
            competitor_personality = seed % 3
            if competitor_personality == 0:
                # Aggressive: directly challenges the dominant segment, +12–18% revenue
                response_mult = 1.0 + rng.uniform(0.12, 0.18) * min(dominance_strength, 2.0)
            elif competitor_personality == 1:
                # Moderate: moderate counter, +7–12%
                response_mult = 1.0 + rng.uniform(0.07, 0.12) * min(dominance_strength, 2.0)
            else:
                # Passive: minor reaction, +3–7%
                response_mult = 1.0 + rng.uniform(0.03, 0.07) * min(dominance_strength, 2.0)

            for yr in range(response_start, len(revenues)):
                revenues[yr] = int(revenues[yr] * response_mult)
                profits[yr] = int(profits[yr] * response_mult * rng.uniform(0.90, 1.05))

    active_events = [e for e in competitor.news_events if e.year <= num_periods]
    return {'name': competitor.name, 'revenues': revenues, 'profits': profits,
            'news_events': active_events}


# Market Share Model: Likability × Reach

def _compute_market_share_data(
    user_revenues: List[float],
    competitor_trajectories: list,
    user_allocations: list = None,
    user_sub_decisions: list = None,
    total_budget: float = 60_000_000,
    game_seed: int = None,
) -> dict:
    """
    Internal function that computes all market share data and per-component breakdowns.

    presence = product_appeal × reach
      product_appeal (60%) = segment-weighted likability score [0–100], normalised to [0,1]
      reach (40%)          = sub_decision segment multipliers × brand_boost

    Applied symmetrically to player and all competitors.
    Competitors use base_reach from their CompetitorDef; player reach comes from
    sub-decisions and accumulated brand equity spend.

    Returns a dict with:
      'shares'     : List[dict] - [{name, shares: [yr0, yr1, ...]}, ...]
      'components' : List[dict] - per-year breakdown for the player
                     [{yr, appeal, reach, brand_boost, presence}, ...]
    """
    num_years = len(user_revenues)
    _company = get_company_name()
    _cs = get_consumer_segments()
    _sd = get_sub_decisions()
    _bc = get_bottleneck_config()
    s = _active_scenario()

    all_names = [f"{_company} (You)"] + [t['name'] for t in competitor_trajectories]
    segments = list(_cs.keys())
    seg_market_weights = np.array([_cs[seg]['market_weight'] for seg in segments])

    # Compute player and competitor specs
    locked_allocs = user_allocations or []
    locked_sd     = user_sub_decisions or []

    player_specs = compute_player_product_specs(locked_allocs, locked_sd, num_years)

    # Use CompetitorDef objects directly (not the dict version from competitor_defs_list)
    comp_defs = s.competitors  # List[CompetitorDef]
    comp_names = [t['name'] for t in competitor_trajectories]

    has_ai = any(
        next((c for c in comp_defs if c.name == cn), None) is not None
        and getattr(next((c for c in comp_defs if c.name == cn), None), 'personality', None) is not None
        for cn in comp_names
    )

    ai_states = {}
    if has_ai:
        # Use game_seed for per-session determinism, fall back to name-based hash
        traj_seed = game_seed if game_seed is not None else (hash(tuple(comp_names)) % 100000)

        # Generate pre-scripted news effects that alter competitor behavior
        _, news_effects = generate_competitor_ai_news({}, num_years, traj_seed)

        ai_states = simulate_all_competitors(
            num_years, locked_allocs, locked_sd, seed=traj_seed,
            news_effects_by_year=news_effects,
        )

    # Build competitor specs: use AI-computed specs if available, else legacy
    comp_specs_list = []
    comp_ai_reach = {}   # {comp_name: [reach_yr0, reach_yr1, ...]}
    for ci, comp_name in enumerate(comp_names):
        comp_def = next((c for c in comp_defs if c.name == comp_name), None)

        if comp_name in ai_states:
            # AI system: extract specs per year from simulated states
            states = ai_states[comp_name]
            ai_spec_dict = {}
            for ps in s.product_specs:
                ai_spec_dict[ps.key] = [st.specs.get(ps.key, ps.base_value) for st in states]
            comp_specs_list.append(ai_spec_dict)
            comp_ai_reach[comp_name] = [st.reach for st in states]
        else:
            comp_traj = competitor_trajectories[ci]
            comp_specs = compute_competitor_product_specs(
                [comp_def] if comp_def else [],
                [comp_traj],
                num_years,
            )
            comp_specs_list.append(comp_specs[0] if comp_specs else {})

    # Compute likability for player and competitors
    # Returns {seg_key: [{prod_name: score, ...}, ...per yr]}
    all_likability = compute_segment_likability(
        player_specs, comp_specs_list, comp_names, num_years
    )

    # Brand boost for player: cumulative marketing/brand spend
    brand_depts = _bc.get('brand_equity_depts', [(3, 1.0), (0, 0.5)])
    cumulative_brand = 0.0
    BRAND_BOOST_MAX = 0.20  # brand equity adds up to +20% on reach (1.0 → 1.2)
    BRAND_REF = total_budget * 1.2  # reference: 1.2 years of full brand spend = max boost

    # Build per-year presence scores
    player_presences = []
    comp_presences   = [[] for _ in comp_names]
    components       = []  # diagnostic breakdown for the player
    comp_reach_boost = [1.0] * len(comp_names)

    # Legacy path only: perturb each competitor's reach per (competitor, year) by about +-5%, seeded by
    # # game_seed, so teams with identical play still get different shares and the leaderboard has no ties.
    comp_reach_noise = [[1.0] * num_years for _ in comp_names]
    if not has_ai and game_seed is not None and len(comp_names) > 0:
        _noise_rng = np.random.RandomState(int(game_seed) & 0x7fffffff)
        for ci in range(len(comp_names)):
            for yr in range(num_years):
                comp_reach_noise[ci][yr] = float(_noise_rng.uniform(0.92, 1.08))

    for yr in range(num_years):

        # Player: product appeal (segment-weighted likability, normalised)
        player_appeal_scores = []
        for seg in segments:
            yr_scores = all_likability.get(seg, [{}] * num_years)
            player_score = yr_scores[yr].get(_company, 0.0) if yr < len(yr_scores) else 0.0
            player_appeal_scores.append(player_score / 100.0)  # normalise to [0,1]
        player_appeal = float(np.dot(seg_market_weights, player_appeal_scores))

        # Player: reach = sub-decision multipliers × brand boost
        seg_reach = np.ones(len(segments))
        if locked_sd and yr < len(locked_sd):
            sd = locked_sd[yr]
            for dept_name, opt_key in sd.items():
                if dept_name in _sd and opt_key in _sd[dept_name]["options"]:
                    mults = _sd[dept_name]["options"][opt_key]["segment_multipliers"]
                    for i, seg in enumerate(segments):
                        seg_reach[i] *= mults.get(seg, 1.0)
        # Cap per-segment reach at 1.8x so aligned sub-decisions cannot stack without limit.
        SEGMENT_REACH_CAP = 1.8
        SEGMENT_REACH_FLOOR = 0.4
        seg_reach = np.clip(seg_reach, SEGMENT_REACH_FLOOR, SEGMENT_REACH_CAP)
        reach_score = float(np.dot(seg_market_weights, seg_reach))

        # Brand boost: cumulative spend on brand equity departments
        if locked_allocs and yr < len(locked_allocs):
            alloc = locked_allocs[yr]
            brand_spend = sum(
                alloc[idx] * w for idx, w in brand_depts if idx < len(alloc)
            )
            cumulative_brand += brand_spend
        brand_boost = 1.0 + min(cumulative_brand / BRAND_REF, 1.0) * BRAND_BOOST_MAX

        # Low spend on brand/sales/ops scales player reach down (1.0 at full spend, about 0.4 at minimal).
        SPEND_SCALE_MIN = 0.15  # floor: even zero spend gives 15% of base reach
        SPEND_SCALE_REF = total_budget  # reference: spending full budget = 1.0
        if locked_allocs and yr < len(locked_allocs):
            yr_alloc = locked_allocs[yr]
            yr_total_spend = sum(yr_alloc)
            spend_scale = SPEND_SCALE_MIN + (1.0 - SPEND_SCALE_MIN) * min(yr_total_spend / SPEND_SCALE_REF, 1.0)
        else:
            spend_scale = SPEND_SCALE_MIN

        player_reach = reach_score * brand_boost * spend_scale

        # The player is a new entrant: base reach starts at a fraction of full potential.
        PLAYER_STARTUP_REACH = 0.55
        player_reach *= PLAYER_STARTUP_REACH

        # Player presence
        player_presence = player_appeal * player_reach   # multiplicative: reach amplifies appeal, can't substitute for it
        player_presences.append(player_presence)

        components.append({
            'yr':         yr + 1,
            'appeal':     round(player_appeal * 100, 1),   # back to 0–100 for display
            'reach':      round(reach_score, 3),
            'brand_boost':round(brand_boost, 3),
            'presence':   round(player_presence, 4),
        })

        # Competitors: use AI reach if available, else legacy base_reach
        for ci, comp_name in enumerate(comp_names):
            comp_def = next((c for c in comp_defs if c.name == comp_name), None)

            if comp_name in comp_ai_reach:
                # AI system: reach computed from sub-decisions + brand equity.
                # Already per-team via simulate_all_competitors(seed=game_seed).
                comp_reach = comp_ai_reach[comp_name][yr] if yr < len(comp_ai_reach[comp_name]) else 1.0
            else:
                comp_reach = (
                    (getattr(comp_def, 'base_reach', 1.0) if comp_def else 1.0)
                    * comp_reach_boost[ci]
                    * comp_reach_noise[ci][yr]
                )

            comp_appeal_scores = []
            for seg in segments:
                yr_scores = all_likability.get(seg, [{}] * num_years)
                c_score = yr_scores[yr].get(comp_name, 0.0) if yr < len(yr_scores) else 0.0
                comp_appeal_scores.append(c_score / 100.0)
            comp_appeal = float(np.dot(seg_market_weights, comp_appeal_scores))

            comp_presence = comp_appeal * comp_reach   # multiplicative: reach amplifies appeal, can't substitute for it
            comp_presences[ci].append(comp_presence)

        # Competitor responsiveness: if player share > 25%, boost competitor reach
        if yr < num_years - 1:
            total_p_this_yr = player_presences[yr] + sum(cp[yr] for cp in comp_presences)
            player_share_this_yr = (player_presences[yr] / total_p_this_yr * 100) if total_p_this_yr > 0 else 0
            if player_share_this_yr > 25:
                for ci in range(len(comp_names)):
                    comp_reach_boost[ci] = min(comp_reach_boost[ci] * 1.03, 1.15)

    # Convert presences to market shares via softmax
    result_shares = []
    for i, name in enumerate(all_names):
        yr_shares = []
        for yr in range(num_years):
            my_p = player_presences[yr] if i == 0 else comp_presences[i - 1][yr]
            total_p = player_presences[yr] + sum(cp[yr] for cp in comp_presences)
            share = (my_p / total_p * 100) if total_p > 0 else 0.0
            yr_shares.append(round(share, 1))
        result_shares.append({'name': name, 'shares': yr_shares})

    return {'shares': result_shares, 'components': components}


def compute_market_shares(
    user_revenues: List[float],
    competitor_trajectories: list,
    user_allocations: list = None,
    user_sub_decisions: list = None,
    total_budget: float = 60_000_000,
    game_seed: int = None,
) -> List[dict]:
    """
    Public API: returns [{name, shares: [yr0, yr1, ...]}, ...].
    Signature unchanged from v5; all existing callers work without modification.
    game_seed: optional per-game seed for competitor AI determinism.
    """
    return _compute_market_share_data(
        user_revenues, competitor_trajectories,
        user_allocations, user_sub_decisions, total_budget, game_seed,
    )['shares']


# Pure functions over game state; nothing here is persisted.

def compute_player_product_specs(
    locked_allocations: list,
    locked_subdecisions: list,
    num_years: int,
) -> Dict[str, List[float]]:
    """Compute the player's product specs per year.

    Returns {spec_key: [value_yr1, value_yr2, ...]} for each spec defined
    in the active scenario.

    The computation mirrors the main simulation engine: R&D spend (and its
    sub-decision bonuses) are applied with a ONE-YEAR LAG: exactly as
    rd_pending works in ResourceAllocationSimulator.run().  Concretely:

      Year 1 spec delta = base_growth only  (no R&D effect yet)
      Year 2 spec delta = base_growth
                        + (yr-1 R&D spend / dept_budget_ref) * spend_sensitivity
                        + sub_decision_bonuses[yr-1 chosen option]

    Non-R&D rules (if any future specs use other departments) are applied
    in the current year without a lag, matching engine behaviour.
    """
    s = _active_scenario()
    if not s or not s.product_specs:
        return {}

    specs = {ps.key: ps.base_value for ps in s.product_specs}
    rules_by_spec = {}
    for rule in s.spec_evolution_rules:
        rules_by_spec[rule.spec_key] = rule

    dept_names = [d.name for d in s.departments]
    result = {key: [] for key in specs}

    for yr in range(num_years):
        for ps in s.product_specs:
            rule = rules_by_spec.get(ps.key)
            if not rule:
                # No evolution rule: value stays static
                result[ps.key].append(specs[ps.key])
                continue

            prev = specs[ps.key]
            delta = rule.base_growth

            # R&D takes effect one year late; other departments apply immediately.
            is_rd_rule = (rule.dept_name == "R&D")
            effect_yr = yr - 1 if is_rd_rule else yr

            # Add spend-driven improvement
            if effect_yr >= 0 and effect_yr < len(locked_allocations):
                alloc = locked_allocations[effect_yr]
                dept_idx = next((i for i, dn in enumerate(dept_names) if dn == rule.dept_name), None)
                if dept_idx is not None and dept_idx < len(alloc):
                    spend_ratio = alloc[dept_idx] / rule.dept_budget_ref
                    delta += spend_ratio * rule.spend_sensitivity

            # Add sub-decision bonus (same lag as spend)
            if effect_yr >= 0 and effect_yr < len(locked_subdecisions):
                sd = locked_subdecisions[effect_yr]
                chosen = sd.get(rule.dept_name, '')
                bonus = rule.sub_decision_bonuses.get(chosen, 0.0)
                delta += bonus

            new_val = max(rule.min_value, min(rule.max_value, prev + delta))
            specs[ps.key] = new_val
            result[ps.key].append(round(new_val, 2))

    return result


def compute_competitor_product_specs(
    competitors: list,
    competitor_trajectories: list,
    num_years: int,
) -> List[Dict[str, List[float]]]:
    """Compute product specs per year for each competitor.

    Returns a list (one per competitor) of {spec_key: [val_yr1, val_yr2, ...]}.

    Competitors evolve based on their revenue trajectory (as a proxy for
    R&D investment) and their per-spec growth rates from the scenario.
    If the scenario doesn't define competitor specs, they're auto-generated
    from the player's base specs with slight offsets.
    """
    s = _active_scenario()
    if not s or not s.product_specs:
        return [{} for _ in competitors]

    comp_defs = s.competitor_defs_list()
    comp_def_map = {cd['name']: cd for cd in comp_defs}

    all_comp_specs = []
    for ci, comp in enumerate(competitors):
        cd = comp_def_map.get(comp.name, {})
        base_specs = cd.get('base_specs', {})
        growth_rates = cd.get('spec_growth_rates', {})

        # If no specs defined for this competitor, derive from player base
        if not base_specs:
            for ps in s.product_specs:
                # Offset: competitor starts ±15% from player base
                import hashlib
                h = int(hashlib.md5(f"{comp.name}:{ps.key}".encode()).hexdigest()[:8], 16)
                offset = ((h % 30) - 15) / 100.0  # -15% to +15%
                base_specs[ps.key] = ps.base_value * (1.0 + offset)

        # If no growth rates, derive from competitor's overall growth rate
        if not growth_rates:
            comp_growth = cd.get('growth_rate', 0.05)
            for ps in s.product_specs:
                # Find the matching evolution rule to get a sense of scale
                rule = next((r for r in s.spec_evolution_rules if r.spec_key == ps.key), None)
                if rule:
                    # Competitor grows at a fraction of max player growth
                    max_player_growth = rule.base_growth + rule.spend_sensitivity
                    growth_rates[ps.key] = max_player_growth * (0.3 + comp_growth * 3)
                else:
                    growth_rates[ps.key] = 0.0

        specs = dict(base_specs)
        comp_result = {ps.key: [] for ps in s.product_specs}

        for yr in range(num_years):
            for ps in s.product_specs:
                gr = growth_rates.get(ps.key, 0.0)
                rule = next((r for r in s.spec_evolution_rules if r.spec_key == ps.key), None)
                if rule:
                    new_val = max(rule.min_value, min(rule.max_value, specs[ps.key] + gr))
                else:
                    new_val = specs[ps.key] + gr
                specs[ps.key] = new_val
                comp_result[ps.key].append(round(new_val, 2))

        all_comp_specs.append(comp_result)

    return all_comp_specs


# Competitors with a `personality` are simulated as NPC players using the same spec-evolution and reach math.

@dataclass
class CompetitorYearState:
    """The simulated state of one competitor for one year."""
    allocations: List[float]             # [R&D, Sales, Ops, Marketing] spend
    sub_decisions: Dict[str, str]        # {"R&D": "software", "Sales": "direct", ...}
    specs: Dict[str, float]              # {"range": 320, "battery": 85, "accel": 3.2}
    reach: float                         # scalar reach score (segment-weighted)
    brand_equity: float                  # cumulative brand spend
    brand_boost: float                   # 1.0 + boost from brand equity


def simulate_competitor_decisions(
    personality,
    dept_names: List[str],
    year: int,
    seed: int,
    market_state: Optional[dict] = None,
    news_effects: Optional[dict] = None,
) -> Tuple[List[float], Dict[str, str]]:
    """Decide allocations and sub-decisions for one competitor for one year.

    Returns (allocations_list, sub_decisions_dict).

    news_effects (optional): effects on this competitor. Optional keys: allocation_shift
    ({dept: delta_fraction}), force_sub_decision ({dept: option_key}), budget_mult (0.92 = 8% cut).
        Keys: "allocation_shift", "force_sub_decision", "budget_mult"
    """
    rng = np.random.RandomState(seed + year * 1000)

    # Base allocations
    budget = personality.total_budget

    # Apply news-driven budget modification
    if news_effects and 'budget_mult' in news_effects:
        budget *= news_effects['budget_mult']

    allocs = {}
    for dept in dept_names:
        base_weight = personality.base_allocation_weights.get(dept, 1.0 / len(dept_names))
        # Apply noise
        noise = rng.uniform(1.0 - personality.noise_factor, 1.0 + personality.noise_factor)
        allocs[dept] = base_weight * noise
    # Normalise
    total_w = sum(allocs.values())
    allocs = {d: (w / total_w) * budget for d, w in allocs.items()}

    # Apply news-driven allocation shifts
    if news_effects and 'allocation_shift' in news_effects:
        for dept, delta_frac in news_effects['allocation_shift'].items():
            if dept in allocs:
                allocs[dept] += delta_frac * budget
                allocs[dept] = max(0, allocs[dept])
        # Re-normalise to budget
        total = sum(allocs.values())
        if total > 0:
            allocs = {d: (v / total) * budget for d, v in allocs.items()}

    # Adaptation (if market state available and competitor is strategic)
    if market_state and personality.strategic_iq > 0 and year >= 1:
        _apply_competitor_adaptation(allocs, personality, market_state, dept_names, rng)

    # Enforce min/max spend from scenario
    s = _active_scenario()
    if s:
        for i, dept in enumerate(dept_names):
            if i < len(s.departments):
                dp = s.departments[i]
                allocs[dept] = max(dp.min_spend, min(dp.max_spend, allocs[dept]))
        # Re-normalise to budget after clamping
        total = sum(allocs.values())
        if total > 0:
            allocs = {d: (v / total) * budget for d, v in allocs.items()}

    alloc_list = [allocs.get(d, 0.0) for d in dept_names]

    # Sub-decision choices
    sub_decisions = {}
    for dept in dept_names:
        # Check for news-forced sub-decision
        if news_effects and 'force_sub_decision' in news_effects:
            forced = news_effects['force_sub_decision'].get(dept)
            if forced:
                sub_decisions[dept] = forced
                continue

        prefs = personality.sub_decision_prefs.get(dept, [])
        if not prefs:
            # No preference defined: use scenario default
            if s and dept in s.sub_decisions:
                sub_decisions[dept] = s.sub_decisions[dept].default
            continue
        # Weighted random choice
        options = [p[0] for p in prefs]
        weights = np.array([p[1] for p in prefs], dtype=float)
        weights /= weights.sum()
        sub_decisions[dept] = rng.choice(options, p=weights)

    return alloc_list, sub_decisions


def _apply_competitor_adaptation(
    allocs: Dict[str, float],
    personality,
    market_state: dict,
    dept_names: List[str],
    rng,
):
    """Shift competitor allocations based on market conditions.

    Modifies `allocs` dict in place.
    """
    iq = personality.strategic_iq
    strength = iq * 0.15  # max 15% budget shift for smartest competitor

    player_seg = market_state.get('player_segment_shares', {})
    comp_seg = market_state.get('comp_segment_shares', {})
    player_growth = market_state.get('player_share_growth', 0.0)

    # Detect segment threats: player likability exceeds this competitor's by >10 points
    threatened_segments = []
    for seg_key in player_seg:
        diff = player_seg.get(seg_key, 0) - comp_seg.get(seg_key, 0)
        if diff > 10:
            threatened_segments.append(seg_key)

    # Detect overall share threat
    share_threat = player_growth > 5.0

    budget = personality.total_budget

    if threatened_segments:
        # Shift toward R&D to improve product competitiveness
        rd_boost = strength * 0.5 * budget
        allocs["R&D"] = allocs.get("R&D", 0) + rd_boost
        # Pull from the department with lowest weight
        min_dept = min(dept_names, key=lambda d: personality.base_allocation_weights.get(d, 0.25))
        allocs[min_dept] = max(0, allocs.get(min_dept, 0) - rd_boost)

    if share_threat:
        # Defensive: boost Marketing to protect brand
        mktg_boost = strength * 0.3 * budget
        allocs["Marketing"] = allocs.get("Marketing", 0) + mktg_boost
        # Pull from Operations
        allocs["Operations"] = max(0, allocs.get("Operations", 0) - mktg_boost * 0.5)
        allocs["Sales"] = max(0, allocs.get("Sales", 0) - mktg_boost * 0.5)


def simulate_all_competitors(
    num_years: int,
    locked_player_allocs: list = None,
    locked_player_sd: list = None,
    seed: int = 42,
    news_effects_by_year: Optional[Dict[str, Dict[int, dict]]] = None,
) -> Dict[str, List[CompetitorYearState]]:
    """Simulate all competitors for all years.

    Returns {competitor_name: [CompetitorYearState_yr0, ..., CompetitorYearState_yr4]}.

    This is the main entry point for the competitor AI system. It replaces
    both compute_competitor_product_specs() and the fixed base_reach logic
    in _compute_market_share_data() for scenarios with personality-based competitors.
    """
    s = _active_scenario()
    if not s:
        return {}

    dept_names = [d.name for d in s.departments]
    _sd = s.sub_decisions_dict()
    segments = list(s.segments_dict().keys())
    seg_market_weights = np.array([seg.market_weight for seg in s.segments])
    _bc = get_bottleneck_config()
    brand_depts = _bc.get('brand_equity_depts', [(3, 1.0), (0, 0.5)])

    # Pre-compute player specs for adaptation context
    player_allocs = locked_player_allocs or []
    player_sd = locked_player_sd or []
    player_specs = compute_player_product_specs(player_allocs, player_sd, num_years)

    # Helper: compute raw appeal for one entity's specs in one segment for one year
    hib = {ps.key: ps.higher_is_better for ps in s.product_specs}
    OVER_IDEAL_ASYMPTOTE = 0.05

    def _raw_appeal(spec_vals: Dict[str, float], seg_key: str) -> float:
        """Compute raw appeal [0,1] for a set of spec values in one segment."""
        prefs = s.segment_spec_preferences.get(seg_key, [])
        total_weight = 0.0
        weighted_sat = 0.0
        for pref in prefs:
            val = spec_vals.get(pref.spec_key)
            if val is None:
                continue
            ideal = pref.ideal_value
            tol = pref.tolerance
            spec_hib = hib.get(pref.spec_key, True)
            if spec_hib:
                shortfall = ideal - val
                if shortfall > 0:
                    sat = max(0.0, 1.0 - shortfall / tol) if tol > 0 else 0.0
                else:
                    surplus = val - ideal
                    sat = 1.0 - OVER_IDEAL_ASYMPTOTE * (1.0 - np.exp(-surplus / tol)) if tol > 0 else 1.0
            else:
                excess = val - ideal
                if excess > 0:
                    sat = max(0.0, 1.0 - excess / tol) if tol > 0 else 0.0
                else:
                    saving = ideal - val
                    sat = 1.0 - OVER_IDEAL_ASYMPTOTE * (1.0 - np.exp(-saving / tol)) if tol > 0 else 1.0
            weighted_sat += sat * pref.weight
            total_weight += pref.weight
        return (weighted_sat / total_weight) if total_weight > 0 else 0.5

    # Track previous-year market data for adaptation
    prev_player_seg_appeal = {}   # {seg_key: raw_appeal}
    prev_comp_seg_appeal = {}     # {comp_name: {seg_key: raw_appeal}}
    prev_player_total_presence = 0.0
    prev_total_presence = 0.0

    result = {}

    # First pass: initialise all competitor state trackers
    comp_trackers = {}
    for ci, comp_def in enumerate(s.competitors):
        personality = comp_def.personality
        if not personality:
            continue
        comp_trackers[comp_def.name] = {
            'def': comp_def,
            'personality': personality,
            'seed': seed + ci * 7919,
            'specs': dict(comp_def.starting_specs or comp_def.base_specs or
                          {ps.key: ps.base_value for ps in s.product_specs}),
            'cumulative_brand': personality.starting_brand_equity,
            'prev_rd_alloc': 0.0,
            'prev_rd_sub': '',
            'states': [],
        }

    # Year-by-year simulation
    for yr in range(num_years):

        # Compute player's current-year spec values for adaptation
        player_yr_specs = {}
        for ps in s.product_specs:
            vals = player_specs.get(ps.key, [])
            player_yr_specs[ps.key] = vals[yr] if yr < len(vals) else ps.base_value

        # Compute player's raw appeal per segment
        player_seg_appeal = {}
        for seg_key in segments:
            player_seg_appeal[seg_key] = _raw_appeal(player_yr_specs, seg_key)

        # Simulate each competitor for this year
        for comp_name, tracker in comp_trackers.items():
            personality = tracker['personality']
            comp_seed = tracker['seed']
            specs = tracker['specs']

            # Build market state from previous year
            market_state = None
            if yr >= 1:
                prev_p_seg = prev_player_seg_appeal
                prev_c_seg = prev_comp_seg_appeal.get(comp_name, {})

                # Convert raw appeals to 0-100 scale for comparison
                p_seg_100 = {k: v * 100 for k, v in prev_p_seg.items()}
                c_seg_100 = {k: v * 100 for k, v in prev_c_seg.items()}

                # Estimate player share growth from presence tracking
                player_share_growth = 0.0
                if prev_total_presence > 0 and prev_player_total_presence > 0:
                    # Rough share estimate from previous year
                    player_share_growth = 5.0  # default moderate growth signal

                market_state = {
                    'player_segment_shares': p_seg_100,
                    'comp_segment_shares': c_seg_100,
                    'player_share_growth': player_share_growth,
                    'year': yr,
                }

            # Get news effects for this competitor and year
            yr_news_effects = None
            if news_effects_by_year and comp_name in news_effects_by_year:
                yr_news_effects = news_effects_by_year[comp_name].get(yr, None)

            # Decide allocations and sub-decisions
            alloc_list, sub_decisions = simulate_competitor_decisions(
                personality, dept_names, yr, comp_seed, market_state, yr_news_effects
            )

            # Evolve specs using same SpecEvolutionRule as player
            prev_rd_alloc = tracker['prev_rd_alloc']
            prev_rd_sub = tracker['prev_rd_sub']

            for ps in s.product_specs:
                rule = next((r for r in s.spec_evolution_rules if r.spec_key == ps.key), None)
                if not rule:
                    continue

                delta = rule.base_growth
                is_rd_rule = (rule.dept_name == "R&D")

                if is_rd_rule and yr >= 1:
                    dept_idx = next((i for i, dn in enumerate(dept_names) if dn == "R&D"), None)
                    if dept_idx is not None:
                        spend_ratio = prev_rd_alloc / rule.dept_budget_ref
                        delta += spend_ratio * rule.spend_sensitivity
                    bonus = rule.sub_decision_bonuses.get(prev_rd_sub, 0.0)
                    delta += bonus
                elif not is_rd_rule:
                    dept_idx = next((i for i, dn in enumerate(dept_names) if dn == rule.dept_name), None)
                    if dept_idx is not None and dept_idx < len(alloc_list):
                        spend_ratio = alloc_list[dept_idx] / rule.dept_budget_ref
                        delta += spend_ratio * rule.spend_sensitivity
                    chosen = sub_decisions.get(rule.dept_name, '')
                    bonus = rule.sub_decision_bonuses.get(chosen, 0.0)
                    delta += bonus

                new_val = max(rule.min_value, min(rule.max_value, specs[ps.key] + delta))
                specs[ps.key] = new_val

            # Compute reach from sub-decisions + brand equity
            seg_reach = np.ones(len(segments))
            for dept_name, opt_key in sub_decisions.items():
                if dept_name in _sd and opt_key in _sd[dept_name]["options"]:
                    mults = _sd[dept_name]["options"][opt_key]["segment_multipliers"]
                    for i, seg in enumerate(segments):
                        seg_reach[i] *= mults.get(seg, 1.0)
            # Cap per-segment reach at 1.8x so aligned sub-decisions cannot stack without limit.
            SEGMENT_REACH_CAP = 1.8
            SEGMENT_REACH_FLOOR = 0.4
            seg_reach = np.clip(seg_reach, SEGMENT_REACH_FLOOR, SEGMENT_REACH_CAP)
            reach_score = float(np.dot(seg_market_weights, seg_reach))

            # Brand boost
            cumulative_brand = tracker['cumulative_brand']
            BRAND_BOOST_MAX = 0.20
            BRAND_REF = personality.total_budget * 1.2
            brand_spend = sum(
                alloc_list[idx] * w for idx, w in brand_depts if idx < len(alloc_list)
            )
            cumulative_brand += brand_spend
            brand_boost = 1.0 + min(cumulative_brand / BRAND_REF, 1.0) * BRAND_BOOST_MAX
            tracker['cumulative_brand'] = cumulative_brand

            # Spend scale
            SPEND_SCALE_MIN = 0.15
            yr_total_spend = sum(alloc_list)
            spend_scale = SPEND_SCALE_MIN + (1.0 - SPEND_SCALE_MIN) * min(
                yr_total_spend / personality.total_budget, 1.0
            )

            final_reach = reach_score * brand_boost * spend_scale

            # Budget-based reach scaling
            BUDGET_REACH_REF = 60_000_000
            budget_reach_scale = (personality.total_budget / BUDGET_REACH_REF) ** 0.5
            final_reach *= budget_reach_scale

            # Store state
            tracker['states'].append(CompetitorYearState(
                allocations=list(alloc_list),
                sub_decisions=dict(sub_decisions),
                specs={k: round(v, 2) for k, v in specs.items()},
                reach=round(final_reach, 4),
                brand_equity=cumulative_brand,
                brand_boost=round(brand_boost, 4),
            ))

            # Save R&D state for next year's lag
            rd_idx = next((i for i, d in enumerate(dept_names) if d == "R&D"), 0)
            tracker['prev_rd_alloc'] = alloc_list[rd_idx] if rd_idx < len(alloc_list) else 0.0
            tracker['prev_rd_sub'] = sub_decisions.get("R&D", "")

            # Track this competitor's segment appeal for next year's adaptation
            comp_yr_seg_appeal = {}
            for seg_key in segments:
                comp_yr_seg_appeal[seg_key] = _raw_appeal(specs, seg_key)
            prev_comp_seg_appeal[comp_name] = comp_yr_seg_appeal

        # Update previous-year player appeal for next iteration
        prev_player_seg_appeal = player_seg_appeal

    # Collect results
    for comp_name, tracker in comp_trackers.items():
        result[comp_name] = tracker['states']

    return result


def compute_segment_likability(
    player_specs: Dict[str, List[float]],
    competitor_specs: List[Dict[str, List[float]]],
    competitor_names: List[str],
    num_years: int,
) -> Dict[str, List[Dict[str, float]]]:
    """Compute likability scores (0-100) per segment per product per year.

    Returns:
        {segment_key: [
            {product_name: score, ...}  # year 1
            ...
        ]}

    Scores SUM TO 100 per segment per year: exactly like a market-share
    split among all products for that segment's buyers.  A product with no
    differentiation in a 5-product field would sit at 20; a clear leader
    can approach 100.

    Two-stage computation:

    Stage 1: raw appeal (plateau satisfaction)
      For each spec the segment values:
       : higher_is_better spec - full score (1.0) if actual >= ideal,
          linear drop-off below ideal, gentle excess penalty above ideal.
       : lower_is_better spec (e.g. accel) - full score if actual <= ideal,
          linear drop-off above, gentle bonus penalty below.
      raw_appeal = weighted_average(sat_i * weight_i)  in [0, 1]

    Stage 2: softmax rescaling
      softmax_share_i = exp(k * raw_i) / sum_j(exp(k * raw_j))   k=6
      likability_i    = softmax_share_i * 100
      Scores naturally lie in [0, 100] and always sum to 100.
    """
    s = _active_scenario()
    if not s or not s.product_specs or not s.segment_spec_preferences:
        return {}

    company_name = s.company.name
    all_product_names = [company_name] + competitor_names
    all_specs = [player_specs] + competitor_specs
    segments = s.segments_dict()

    # higher_is_better flag per spec key
    hib = {ps.key: ps.higher_is_better for ps in s.product_specs}

    # Softmax sharpness: k=3.5 flattens winner-takes-all dynamic while
    # keeping meaningful differentiation between products (was k=5).
    SOFTMAX_K = 3.5
    OVER_IDEAL_ASYMPTOTE = 0.05

    result = {}
    for seg_key, prefs in s.segment_spec_preferences.items():
        if seg_key not in segments:
            continue
        yearly_scores = []
        for yr in range(num_years):
            # Stage 1: raw appeal per product
            raw_appeals = {}
            for pi, pname in enumerate(all_product_names):
                p_specs = all_specs[pi]
                total_weight = 0.0
                weighted_sat = 0.0
                for pref in prefs:
                    if pref.spec_key not in p_specs:
                        continue
                    vals = p_specs[pref.spec_key]
                    if yr >= len(vals):
                        continue
                    actual = vals[yr]
                    tol    = pref.tolerance
                    ideal  = pref.ideal_value
                    spec_hib = hib.get(pref.spec_key, True)

                    if spec_hib:
                        shortfall = ideal - actual
                        if shortfall > 0:
                            # Below ideal: linear decay to 0
                            sat = max(0.0, 1.0 - shortfall / tol) if tol > 0 else 0.0
                        else:
                            # Above ideal: soft asymptotic plateau: sat → (1: OVER_IDEAL_ASYMPTOTE)
                            # More is always better, just with diminishing returns past ideal.
                            surplus = actual - ideal
                            sat = 1.0 - OVER_IDEAL_ASYMPTOTE * (1.0 - np.exp(-surplus / tol)) if tol > 0 else 1.0
                    else:
                        excess = actual - ideal
                        if excess > 0:
                            # Worse than ideal: linear decay to 0
                            sat = max(0.0, 1.0 - excess / tol) if tol > 0 else 0.0
                        else:
                            # Better than ideal: soft asymptotic plateau
                            saving = ideal - actual
                            sat = 1.0 - OVER_IDEAL_ASYMPTOTE * (1.0 - np.exp(-saving / tol)) if tol > 0 else 1.0

                    weighted_sat += sat * pref.weight
                    total_weight += pref.weight

                raw_appeals[pname] = (weighted_sat / total_weight) if total_weight > 0 else 0.5

            # Stage 2: softmax -> scores that sum to 100
            appeals = np.array([raw_appeals[pname] for pname in all_product_names])
            exp_k = np.exp(SOFTMAX_K * (appeals - appeals.max()))  # numerically stable
            softmax_shares = exp_k / exp_k.sum()
            competitive_scores = softmax_shares * 100  # sums to 100

            yr_scores = {}
            for pi, pname in enumerate(all_product_names):
                yr_scores[pname] = round(float(competitive_scores[pi]), 1)
            yearly_scores.append(yr_scores)
        result[seg_key] = yearly_scores

    return result


class ResourceAllocationSimulator:

    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.num_depts = len(config.departments)

    def hill_response(self, spend, dept, state=0.0,
                      smax_override=None, k_override=None):
        """Hill function with optional sub-decision / event overrides."""
        if spend <= 0:
            return 0.0
        S_max = smax_override if smax_override is not None else dept.S_max
        K = k_override if k_override is not None else dept.K

        acc = 1.0 + dept.state_sensitivity * state
        catch = 1.0 + dept.catch_up_rate / (1.0 + state)
        eff_smax = S_max * acc * catch
        sa = spend ** dept.alpha
        ka = K ** dept.alpha
        return eff_smax * sa / (ka + sa)

    def compute_adstock(self, current_spend, prev_adstock, dept):
        decay = min(dept.decay * self.config.carryover_strength, 0.95)
        return current_spend + decay * prev_adstock

    def update_state(self, current_state, allocations):
        new = np.zeros(self.num_depts)
        for i, dept in enumerate(self.config.departments):
            new[i] = self.config.state_decay * current_state[i] + allocations[i] / dept.K
        return new

    def compute_underuse_penalty(self, spend, budget, max_allocatable=None):
        """Compute underuse penalty against the effectively-spendable budget.

        When department ±30% caps make it structurally impossible to spend the
        full budget, teams should not be penalised for the unallocatable portion.
        max_allocatable is the sum of all department ceiling values for this year;
        the penalty baseline is min(budget, max_allocatable) so that only
        genuinely allocatable unused budget counts against the team.
        """
        if budget <= 0:
            return 0.0
        effective_budget = min(budget, max_allocatable) if max_allocatable and max_allocatable > 0 else budget
        if effective_budget <= 0:
            return 0.0
        unused = 1.0 - spend / effective_budget
        if unused <= self.config.underuse_threshold:
            return 0.0
        excess = unused - self.config.underuse_threshold
        return self.config.underuse_penalty_rate * (excess ** 2) * effective_budget

    def compute_overspend_penalty(self, spend, dept):
        """Diminishing returns for overspending past the sweet spot.
        Returns a multiplier 0-1 applied to the department's raw return."""
        sweet_spot = dept.max_spend * dept.sweet_spot_frac
        if spend <= sweet_spot:
            return 1.0
        # Beyond sweet spot: returns decay quadratically
        overshoot = (spend - sweet_spot) / (dept.max_spend - sweet_spot + 1)
        penalty = max(0.4, 1.0 - 0.6 * overshoot ** 1.5)
        return penalty

    def simulate(self, plan, noise_seed=None, scenario_perturbation=None,
                 initial_budget=None, inflation_seed=None,
                 cumulative_inflation=1.0,
                 sub_decisions_by_year: Optional[List[Dict[str, str]]] = None,
                 player_news: Optional[List[NewsEvent]] = None,
                 max_allocatable_by_year: Optional[List[Optional[float]]] = None):
        """
        Run the simulation.
        """
        rng = np.random.RandomState(noise_seed)
        inf_rng = np.random.RandomState(
            inflation_seed if inflation_seed is not None else
            (noise_seed + 7 if noise_seed else 42))
        T = plan.shape[0] if hasattr(plan, "shape") else self.config.num_periods
        D = self.num_depts

        adstocks = np.zeros(D)
        state = np.ones(D) * 0.5
        if scenario_perturbation is None:
            scenario_perturbation = np.ones(D)

        current_budget = initial_budget or self.config.total_budget
        current_fixed_costs = self.config.fixed_costs * cumulative_inflation
        cum_infl = cumulative_inflation

        pending_rd_return = 0.0
        dept_names = [d.name for d in self.config.departments]
        rd_index = next((i for i, d in enumerate(self.config.departments) if d.name == "R&D"), None)
        ops_index = next((i for i, d in enumerate(self.config.departments) if d.name == "Operations"), None)
        sales_index = next((i for i, d in enumerate(self.config.departments) if d.name == "Sales"), None)
        _bc = get_bottleneck_config()   # bottleneck + overcap config for this scenario

        results = {
            'periods': [], 'revenue_by_dept': np.zeros((T, D)),
            'total_revenue': np.zeros(T), 'total_spend': np.zeros(T),
            'profit': np.zeros(T), 'raw_profit': np.zeros(T),
            'underuse_penalty': np.zeros(T), 'available_budget': np.zeros(T),
            'fixed_costs': np.zeros(T), 'inflation_rate': np.zeros(T),
            'cumulative_inflation': np.zeros(T),
            'state_history': np.zeros((T + 1, D)),
            'adstock_history': np.zeros((T + 1, D)),
            'rd_pending': np.zeros(T),
            'subdecision_multiplier': np.ones(T),
            # extras
            'dept_smax_used': np.zeros((T, D)),
            'dept_k_used': np.zeros((T, D)),
            'ops_cap': np.zeros(T),
            'sales_raw': np.zeros(T),
            'sales_capped': np.zeros(T),
            'overspend_penalty': np.zeros((T, D)),
            'overcap_penalty': np.ones(T),   # symmetric over-capacity multiplier
            'dept_news': [[] for _ in range(T)],
            'general_news': [[] for _ in range(T)],
            'market_news': [[] for _ in range(T)],
            # Per-year log of synergy bonuses that fired; read by services/narrative.py, does not affect results.
            'synergies': [[] for _ in range(T)],
        }
        results['state_history'][0] = state.copy()
        results['adstock_history'][0] = adstocks.copy()

        for t in range(T):
            results['available_budget'][t] = current_budget
            results['fixed_costs'][t] = current_fixed_costs
            results['cumulative_inflation'][t] = cum_infl

            # Passing the synergy log records which bonuses fired; results are unchanged.
            sd_mods = compute_dept_subdecision_modifiers(
                sub_decisions_by_year if sub_decisions_by_year else [],
                t, dept_names,
                track_log=results['synergies'][t])

            # Also compute the legacy segment multiplier for display
            sd_mult = compute_subdecision_multiplier(
                sub_decisions_by_year if sub_decisions_by_year else [], t)
            results['subdecision_multiplier'][t] = sd_mult

            # Department-targeted + general + market news event processing
            dept_event_mods = {d: {'k_mult': 1.0, 'smax_mult': 1.0} for d in dept_names}
            general_rev_mult = 1.0
            general_prof_impact = 0.0
            if player_news:
                for event in player_news:
                    if event.year == t + 1:
                        if event.dept_pressure == '__market__':
                            # Competitor/market news: display only, no gameplay effect
                            results['market_news'][t].append(event)
                        elif event.dept_pressure:
                            # Department-specific event: modifies that dept's return curve
                            dp = event.dept_pressure
                            if dp in dept_event_mods:
                                dept_event_mods[dp]['k_mult'] *= event.dept_k_mult
                                dept_event_mods[dp]['smax_mult'] *= event.dept_smax_mult
                                results['dept_news'][t].append(event)
                        else:
                            # General (company-wide) event: multiplies total revenue + flat profit
                            general_rev_mult *= event.revenue_impact
                            general_prof_impact += event.profit_impact
                            results['general_news'][t].append(event)

            period_revenue = 0.0
            period_spend = plan[t].sum()
            dept_raw_returns = np.zeros(D)

            for d, dept in enumerate(self.config.departments):
                spend = plan[t, d]
                adstocks[d] = self.compute_adstock(spend, adstocks[d], dept)

                # Compute effective S_max and K with sub-decision + event modifiers
                dn = dept.name
                eff_smax = dept.S_max * sd_mods[dn]['smax_mult'] * dept_event_mods[dn]['smax_mult']
                eff_k = dept.K * sd_mods[dn]['k_mult'] * dept_event_mods[dn]['k_mult']
                results['dept_smax_used'][t, d] = eff_smax
                results['dept_k_used'][t, d] = eff_k

                raw_return = self.hill_response(adstocks[d], dept, state[d],
                                                 smax_override=eff_smax,
                                                 k_override=eff_k)
                raw_return *= scenario_perturbation[d]
                noise = rng.lognormal(0, self.config.demand_noise_std)
                noisy_return = raw_return * noise

                # Overspend penalty
                overspend_mult = self.compute_overspend_penalty(spend, dept)
                results['overspend_penalty'][t, d] = overspend_mult
                noisy_return *= overspend_mult

                dept_raw_returns[d] = noisy_return

                if d == rd_index:
                    results['revenue_by_dept'][t, d] = 0.0
                    results['rd_pending'][t] = noisy_return
                else:
                    results['revenue_by_dept'][t, d] = noisy_return

            # Operations bottleneck caps Sales
            if ops_index is not None and sales_index is not None:
                ops_return = dept_raw_returns[ops_index]
                sales_return = dept_raw_returns[sales_index]
                # Operations capacity = ops return * cap_fraction
                # This ensures Ops must be well-funded to support Sales
                ops_capacity = ops_return * _bc['cap_fraction']
                results['ops_cap'][t] = ops_capacity
                results['sales_raw'][t] = sales_return

                if sales_return > ops_capacity:
                    # Cap sales at operations capacity
                    capped_sales = ops_capacity
                    results['sales_capped'][t] = capped_sales
                    results['revenue_by_dept'][t, sales_index] = capped_sales
                else:
                    results['sales_capped'][t] = sales_return
                    results['revenue_by_dept'][t, sales_index] = sales_return

                # Excess Ops capacity relative to Sales is wasted (mirrors the bottleneck cap).
                overcap_ratio = _bc.get('overcap_ratio', 1.5)
                overcap_floor = _bc.get('overcap_floor', 0.6)
                if sales_return > 0 and ops_return > sales_return * overcap_ratio:
                    # How far past the acceptable ratio are we?
                    overshoot = (ops_return / (sales_return * overcap_ratio)) - 1.0
                    # Quadratic decay matching overspend penalty style
                    overcap_mult = max(overcap_floor, 1.0 - 0.4 * overshoot ** 1.5)
                    ops_penalised = ops_return * overcap_mult
                    dept_raw_returns[ops_index] = ops_penalised
                    results['revenue_by_dept'][t, ops_index] = ops_penalised
                    # Recalculate ops_capacity with penalised value
                    ops_capacity = ops_penalised * _bc['cap_fraction']
                    results['ops_cap'][t] = ops_capacity
                    # Re-apply bottleneck cap with updated ops capacity
                    if sales_return > ops_capacity:
                        results['sales_capped'][t] = ops_capacity
                        results['revenue_by_dept'][t, sales_index] = ops_capacity
                results['overcap_penalty'][t] = dept_raw_returns[ops_index] / ops_return if ops_return > 0 else 1.0

            # Sum non-R&D department returns for period revenue
            for d in range(D):
                if d != rd_index:
                    period_revenue += results['revenue_by_dept'][t, d]

            # Lagged R&D return from previous period
            period_revenue += pending_rd_return
            if rd_index is not None and t > 0:
                results['revenue_by_dept'][t, rd_index] = pending_rd_return

            pending_rd_return = results['rd_pending'][t]

            # Total revenue: purely from department returns, no base
            total_revenue = period_revenue

            # Apply general (company-wide) news event effects
            total_revenue *= general_rev_mult

            _max_alloc_t = (max_allocatable_by_year[t]
                             if max_allocatable_by_year and t < len(max_allocatable_by_year)
                             else None)
            underuse_pen = self.compute_underuse_penalty(period_spend, current_budget, _max_alloc_t)
            raw_profit = total_revenue - period_spend - current_fixed_costs
            profit = raw_profit - underuse_pen + general_prof_impact

            results['total_revenue'][t] = total_revenue
            results['total_spend'][t] = period_spend
            results['raw_profit'][t] = raw_profit
            results['underuse_penalty'][t] = underuse_pen
            results['profit'][t] = profit

            state = self.update_state(state, plan[t])
            results['state_history'][t + 1] = state.copy()
            results['adstock_history'][t + 1] = adstocks.copy()
            results['periods'].append({
                'period': t + 1, 'total_revenue': total_revenue, 'profit': profit,
            })

            reinvestment = profit * self.config.profit_reinvestment_rate
            reinvestment = np.ceil(reinvestment / 100) * 100 if reinvestment >= 0 else np.floor(reinvestment / 100) * 100
            current_budget = current_budget + reinvestment
            current_budget = max(current_budget, self.config.total_budget * 0.5)  # floor: never below 50% of starting

            inflation = inf_rng.uniform(self.config.inflation_min, self.config.inflation_max)
            results['inflation_rate'][t] = inflation
            current_fixed_costs *= (1 + inflation)
            cum_infl *= (1 + inflation)

        results['cumulative_profit'] = results['profit'].sum()
        results['avg_profit'] = results['profit'].mean()
        results['std_profit'] = results['profit'].std()
        results['risk_adjusted_score'] = (
            results['avg_profit'] - (2.0 - self.config.risk_penalty_lambda) * results['std_profit'])
        return results

    def evaluate(self, plan, seed_base=42,
                 sub_decisions_by_year: Optional[List[Dict[str, str]]] = None,
                 player_news: Optional[List[NewsEvent]] = None):
        rng = np.random.RandomState(seed_base)
        scenario_results = []
        for _ in range(self.config.num_eval_scenarios):
            pert = rng.lognormal(0, self.config.scenario_drift_std, size=self.num_depts)
            ns = rng.randint(0, 2**31)
            scenario_results.append(self.simulate(
                plan, noise_seed=ns, scenario_perturbation=pert,
                sub_decisions_by_year=sub_decisions_by_year,
                player_news=player_news,
            ))

        all_cum = [r['cumulative_profit'] for r in scenario_results]
        all_avg = [r['avg_profit'] for r in scenario_results]
        avg_p = np.mean(all_avg)
        std_p = np.std(all_avg)

        return {
            'valid': True, 'avg_cumulative_profit': np.mean(all_cum),
            'avg_annual_profit': avg_p, 'std_annual_profit': std_p,
            'risk_adjusted_score': avg_p - (2.0 - self.config.risk_penalty_lambda) * std_p,
            'best_scenario_profit': max(all_cum), 'worst_scenario_profit': min(all_cum),
            'scenario_results': scenario_results,
        }
