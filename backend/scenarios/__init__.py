"""Scenario registry.

Each scenario module registers a ScenarioDefinition for a (country, industry)
pair at import time. The admin selects one as the active scenario.

    from scenarios import get_scenario, set_active_scenario

    set_active_scenario("us", "ev")
    get_scenario().company.name
"""
import importlib
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from scenarios.base import ScenarioDefinition

_REGISTRY: Dict[Tuple[str, str], ScenarioDefinition] = {}
_active_scenario: Optional[ScenarioDefinition] = None

# Another server instance may change the scenario. When running on Firestore,
# get_active_scenario() re-checks the shared setting at most this often.
_REMOTE_POLL_TTL = 30.0
_last_remote_check_ts = 0.0
_last_remote_value: Optional[Tuple[str, str]] = None
_logger = logging.getLogger("scenarios")


def register_scenario(country: str, industry: str, scenario: ScenarioDefinition):
    _REGISTRY[(country.lower(), industry.lower())] = scenario


def get_scenario(country: str = None, industry: str = None) -> ScenarioDefinition:
    """Look up a scenario by (country, industry), or return the active one.

    Raises KeyError for an unknown pair. Without arguments, falls back to us/ev
    when no scenario has been activated.
    """
    if country and industry:
        key = (country.lower(), industry.lower())
        if key not in _REGISTRY:
            raise KeyError(f"No scenario registered for ({country}, {industry})")
        return _REGISTRY[key]

    if _active_scenario is not None:
        return _active_scenario
    if ("us", "ev") in _REGISTRY:
        return _REGISTRY[("us", "ev")]
    raise RuntimeError("No scenario registered.")


def set_active_scenario(country: str, industry: str):
    global _active_scenario, _last_remote_check_ts, _last_remote_value
    _active_scenario = get_scenario(country, industry)
    # Record this as the latest remote value so the next poll does not revert it.
    _last_remote_check_ts = time.time()
    _last_remote_value = (country.lower(), industry.lower())


def _maybe_refresh_from_remote() -> None:
    """Adopt a scenario change made by another instance (Firestore backend only)."""
    global _active_scenario, _last_remote_check_ts, _last_remote_value
    if os.environ.get('STORAGE_BACKEND', 'local').lower() != 'firestore':
        return
    now = time.time()
    if (now - _last_remote_check_ts) < _REMOTE_POLL_TTL:
        return
    _last_remote_check_ts = now

    try:
        from auth import get_store  # deferred: auth imports storage, which imports config
        observed = get_store().load_active_scenario()
        if not observed or observed == _last_remote_value:
            return
        try:
            _active_scenario = get_scenario(*observed)
        except KeyError:
            _logger.warning("Remote scenario %s/%s is not registered locally; ignoring.", *observed)
            return
        _last_remote_value = observed
        from config import refresh_cfg, refresh_derived
        refresh_cfg()
        refresh_derived()
        _logger.info("Scenario changed by another instance: now %s/%s", *observed)
    except Exception as e:
        _logger.debug("Remote scenario check skipped: %s", e)


def get_active_scenario() -> Optional[ScenarioDefinition]:
    """The active scenario, or None if none has been set."""
    _maybe_refresh_from_remote()
    return _active_scenario


def list_scenarios() -> List[dict]:
    return [
        {
            "country": country,
            "industry": industry,
            "scenario_id": s.scenario_id,
            "label": s.scenario_label,
            "country_name": s.locale.country_name,
            "currency": s.locale.currency_symbol,
        }
        for (country, industry), s in sorted(_REGISTRY.items())
    ]


_SCENARIO_MODULES = [
    f"scenarios.{country}_{industry}"
    for industry in ("ev", "pharma", "hydration")
    for country in ("us", "ca", "in", "uk")
]

for _module in _SCENARIO_MODULES:
    importlib.import_module(_module)
