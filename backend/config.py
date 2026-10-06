"""Simulation config derived from the active scenario."""
from simulator import ScenarioConfig, DepartmentConfig

EVAL_SEED = 42


def _active_scenario():
    from scenarios import get_active_scenario
    return get_active_scenario()


def get_scenario_cfg() -> ScenarioConfig:
    """Build a ScenarioConfig from the active scenario (defaults if none is set)."""
    s = _active_scenario()
    if s is None:
        c = ScenarioConfig()
        c.profit_reinvestment_rate = 0.03
        return c

    f = s.financials
    depts = [
        DepartmentConfig(
            name=d.name, S_max=d.S_max, K=d.K, alpha=d.alpha,
            decay=d.decay, min_spend=d.min_spend, max_spend=d.max_spend,
            state_sensitivity=d.state_sensitivity, catch_up_rate=d.catch_up_rate,
            sweet_spot_frac=d.sweet_spot_frac,
        )
        for d in s.departments
    ]
    return ScenarioConfig(
        company_name=s.company.name,
        product_name=s.company.product_name,
        base_revenue=f.base_revenue,
        unit_price=s.company.unit_price,
        unit_cost=s.company.unit_cost,
        fixed_costs=f.fixed_costs,
        total_budget=f.total_budget,
        num_periods=f.num_periods,
        profit_reinvestment_rate=f.profit_reinvestment_rate,
        inflation_min=f.inflation_min,
        inflation_max=f.inflation_max,
        underuse_threshold=f.underuse_threshold,
        underuse_penalty_rate=f.underuse_penalty_rate,
        max_change_rate=f.max_change_rate,
        departments=depts,
        demand_noise_std=f.demand_noise_std,
        scenario_drift_std=f.scenario_drift_std,
        risk_penalty_lambda=f.risk_penalty_lambda,
        carryover_strength=1.0,
        num_eval_scenarios=f.num_eval_scenarios,
        state_decay=f.state_decay,
    )


def _vpi_bounds():
    s = _active_scenario()
    if s:
        f = s.financials
        return f.vpi_ras_floor, f.vpi_ras_ceiling, f.vpi_share_floor, f.vpi_share_ceiling
    return -65_000_000, 260_000_000, 8.0, 26.0


cfg = get_scenario_cfg()
NP = cfg.num_periods
ND = len(cfg.departments)
VPI_RAS_FLOOR, VPI_RAS_CEIL, VPI_SHARE_FLOOR, VPI_SHARE_CEIL = _vpi_bounds()


def refresh_cfg():
    """Rebuild `cfg` after the active scenario changes."""
    global cfg
    cfg = get_scenario_cfg()


def refresh_derived():
    """Refresh values derived from `cfg` and the active scenario. Call after `refresh_cfg`."""
    global NP, ND, VPI_RAS_FLOOR, VPI_RAS_CEIL, VPI_SHARE_FLOOR, VPI_SHARE_CEIL
    NP = cfg.num_periods
    ND = len(cfg.departments)
    VPI_RAS_FLOOR, VPI_RAS_CEIL, VPI_SHARE_FLOOR, VPI_SHARE_CEIL = _vpi_bounds()
