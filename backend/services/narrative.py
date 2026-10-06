"""
services/narrative.py — "What just happened?" year-end narratives.

Generates 2-4 short sentences explaining what the player did this year
and how it played out. Output is deterministic, template-driven, and
fast (no LLM, no new dependencies). The sentences are tagged with a
sentiment so the frontend can render them with appropriate icons/colors:

    [{"text": "Marketing was your strongest play — returned $1.40 per dollar.",
      "sentiment": "positive"},
     {"text": "R&D under-delivered at $0.60 per dollar.",
      "sentiment": "negative"},
     {"text": "Profit fell $230K versus last year.",
      "sentiment": "negative"}]

Rules
-----
The rules below are intentionally simple — they fire on clearly-defined
threshold crossings using fields the simulator already computes (no
recomputation), each rule produces at most one sentence. We pick the
~3 most informative rules to render so the panel stays scannable.

When adding rules:
  - keep one sentence per rule
  - prefer specific numbers ("$230K", "3.2 points") over vague language
  - use plain English — this is the pedagogical layer, not a dashboard
  - tag sentiment honestly (a $1K profit drop is "neutral", not "negative")

Sentiment legend:
  "positive" — green, up-arrow icon
  "negative" — red, down-arrow icon
  "neutral"  — gray, dot icon
  "warning"  — amber, flag icon (use sparingly — for competitor threats)
"""

from typing import Optional


# Currency thresholds are in the simulator's base units.

_PROFIT_DELTA_FLAT = 50_000      # below this, "stayed roughly flat"
_PROFIT_DELTA_BIG  = 500_000     # above this, qualifies as "surged" / "plunged"
_SHARE_DELTA_FLAT  = 0.5         # market-share percentage points
_SHARE_DELTA_BIG   = 3.0
_DEPT_RETURN_GREAT = 1.3         # $1.30 of value per $1 spent
_DEPT_RETURN_WEAK  = 0.8
_COMPETITOR_SHARE_LEAD = 2.0     # if a competitor outpaces user by this many pts

_MAX_SENTENCES = 6


def _fmt_num(val: float, sym: str = '$', suffix: str = 'K') -> str:
    """Format a numeric value into a short readable string.

    Mirrors the frontend's canonical `fmtCur` (components/allocate/shared.jsx
    and PerformanceTab.jsx) EXACTLY so narrative text matches every other
    currency value in the UI:

      • suffix 'K': round(value / 1_000) and append 'K'  — never switches to 'M'.
        (A previous version here divided by 1000 and appended 'M', which made
        the same raw value read as e.g. "$88,732M" in the recap while the rest
        of the UI showed "$88,732K" — the source of the K-vs-M mismatch.)
      • suffix 'L': lakh/crore formatting for the India scenarios.
      • otherwise: divide by 1e6 and append 'M'.
    """
    if val is None:
        return '—'
    abs_v = abs(val)
    neg = '-' if val < 0 else ''
    if suffix == 'K':
        return f"{neg}{sym}{round(abs_v / 1_000):,}K"
    if suffix == 'L':
        if abs_v >= 1e7:
            return f"{neg}{sym}{abs_v / 1e7:.1f}Cr"
        return f"{neg}{sym}{round(abs_v / 1e5):,}L"
    return f"{neg}{sym}{abs_v / 1e6:.2f}M"


# Each rule takes (year_result, prev_year_result, year_results_so_far) and returns {text, sentiment} or None.
# # prev_year_result is None in year 1.

def _rule_profit_movement(yr, prev, history, sym, suffix):
    """Profit direction year-over-year."""
    # On a poor-grade year, profit is reported as a neutral fact rather than a
    # celebration — a big profit alongside an F is misleading if framed as a win.
    poor = yr.get('grade') in ('D', 'F')
    if prev is None:
        # Year 1 — describe absolute profit instead of delta
        profit = yr.get('profit', 0)
        if profit > 0:
            if poor:
                return {"text": f"Net profit was {_fmt_num(profit, sym, suffix)} — but profit is only half the score.",
                        "sentiment": "neutral"}
            return {"text": f"Year 1 closed in the black — net profit of {_fmt_num(profit, sym, suffix)}.",
                    "sentiment": "positive"}
        elif profit < -_PROFIT_DELTA_FLAT:
            return {"text": f"Year 1 closed with a loss of {_fmt_num(abs(profit), sym, suffix)} — common during startup.",
                    "sentiment": "neutral"}
        return None

    delta = yr.get('profit', 0) - prev.get('profit', 0)
    abs_d = abs(delta)
    if abs_d < _PROFIT_DELTA_FLAT:
        return {"text": "Profit stayed roughly flat versus last year.",
                "sentiment": "neutral"}
    direction = "grew" if delta > 0 else "fell"
    qualifier = "surged" if delta > _PROFIT_DELTA_BIG else direction
    if delta < 0 and abs_d > _PROFIT_DELTA_BIG:
        qualifier = "plunged"
    # A profit rise on a failing year is still just a fact, not a win.
    sentiment = "neutral" if (delta > 0 and poor) else ("positive" if delta > 0 else "negative")
    return {"text": f"Profit {qualifier} {_fmt_num(abs_d, sym, suffix)} versus last year.",
            "sentiment": sentiment}


def _rule_share_movement(yr, prev, history, sym, suffix):
    """Market-share change year-over-year (already in percentage points)."""
    if prev is None:
        share = yr.get('market_share', 0)
        if share >= 20:
            return {"text": f"You ended Year 1 with {share:.1f}% market share — a strong opening position.",
                    "sentiment": "positive"}
        return None  # Year 1 absolute share is noisy; skip unless notable
    delta = yr.get('market_share', 0) - prev.get('market_share', 0)
    if abs(delta) < _SHARE_DELTA_FLAT:
        return None  # Skip — not informative
    cur_share = yr.get('market_share', 0)
    if delta > _SHARE_DELTA_BIG:
        return {"text": f"Market share jumped {delta:+.1f} points to {cur_share:.1f}%.",
                "sentiment": "positive"}
    if delta < -_SHARE_DELTA_BIG:
        return {"text": f"Market share dropped {abs(delta):.1f} points to {cur_share:.1f}%.",
                "sentiment": "negative"}
    return {"text": f"Market share moved {delta:+.1f} points to {cur_share:.1f}%.",
            "sentiment": "positive" if delta > 0 else "neutral"}


def _rule_strongest_department(yr, prev, history, sym, suffix):
    """Pick the department with the best $/$ return this year."""
    dept_returns = yr.get('dept_returns') or {}
    if not dept_returns:
        return None
    # dept_returns is {dept_name: return_per_dollar} per game_logic.py
    best = max(dept_returns.items(), key=lambda kv: kv[1] if isinstance(kv[1], (int, float)) else 0,
               default=None)
    if not best:
        return None
    name, ret = best
    if not isinstance(ret, (int, float)) or ret < _DEPT_RETURN_GREAT:
        return None
    return {"text": f"{name} was your strongest play — returned ${ret:.2f} per dollar spent.",
            "sentiment": "positive"}


def _rule_weakest_department(yr, prev, history, sym, suffix):
    """Pick the department with the worst $/$ return this year — but only
    flag it if the team actually spent meaningfully there. Calling out
    'R&D under-delivered' when the team spent $5K is unhelpful noise."""
    dept_returns = yr.get('dept_returns') or {}
    if not dept_returns:
        return None
    candidates = [(n, r) for n, r in dept_returns.items()
                  if isinstance(r, (int, float)) and r < _DEPT_RETURN_WEAK]
    if not candidates:
        return None
    name, ret = min(candidates, key=lambda kv: kv[1])
    return {"text": f"{name} under-delivered at ${ret:.2f} per dollar — worth a rethink.",
            "sentiment": "negative"}


def _rule_competitor_pressure(yr, prev, history, sym, suffix):
    """Flag if a single competitor materially outpaced the user in share."""
    if prev is None:
        return None
    cur_shares = yr.get('market_shares') or {}
    prev_shares = prev.get('market_shares') or {}
    if not cur_shares or not prev_shares:
        return None
    # Report only the single biggest mover.
    biggest_gain = None
    biggest_gain_name = None
    for name, share in cur_shares.items():
        prev_s = prev_shares.get(name)
        if prev_s is None:
            continue
        delta = share - prev_s
        if biggest_gain is None or delta > biggest_gain:
            biggest_gain = delta
            biggest_gain_name = name
    if biggest_gain is None or biggest_gain < _COMPETITOR_SHARE_LEAD:
        return None
    # Only flag if the competitor's gain exceeds the user's share movement
    user_share_delta = yr.get('market_share', 0) - prev.get('market_share', 0)
    if biggest_gain <= user_share_delta + 0.5:
        return None
    return {"text": f"{biggest_gain_name} is pulling ahead — gained {biggest_gain:+.1f} points of share this year.",
            "sentiment": "warning"}


def _rule_strategic_momentum(yr, prev, history, sym, suffix):
    """Recognize a high-VPI run vs the team's own history."""
    cur_vpi = yr.get('vpi')
    if cur_vpi is None or not history:
        return None
    prev_vpis = [h.get('vpi') for h in history[:-1] if h.get('vpi') is not None]
    if not prev_vpis:
        return None
    best_prev = max(prev_vpis)
    if cur_vpi > best_prev:
        return {"text": f"VPI {int(cur_vpi)} — your highest score yet this game.",
                "sentiment": "positive"}
    return None


def _rule_underuse_penalty(yr, prev, history, sym, suffix):
    """Call out if the team left budget on the table and paid a penalty."""
    penalty = yr.get('underuse_penalty', 0)
    if penalty is None or penalty < 1000:
        return None
    return {"text": f"You left budget unused — that triggered a {_fmt_num(penalty, sym, suffix)} underuse penalty.",
            "sentiment": "negative"}


def _rule_thin_margin(yr, prev, history, sym, suffix):
    """Flag thin profit margins relative to revenue."""
    revenue = yr.get('total_revenue', 0)
    profit  = yr.get('profit', 0)
    if not revenue or revenue <= 0:
        return None
    margin = (profit / revenue) * 100
    # Loss case is already covered by _rule_profit_movement; only flag the
    # in-between "thin but positive" range here so we don't duplicate.
    if profit <= 0 or margin >= 5:
        return None
    return {"text": f"Margin was thin at {margin:.1f}% — costs ate most of the revenue this year.",
            "sentiment": "warning"}


def _rule_ops_sales_imbalance(yr, prev, history, sym, suffix, gs):
    """Detect a meaningful imbalance between Operations and Sales spend.

    Skipped when _rule_bottleneck_fired already covered the mechanic with
    actual revenue numbers — no need to duplicate with a spend-ratio warning.
    """
    # Forward warning only; skipped when _rule_bottleneck_fired already explained a real loss.
    if yr.get('bottleneck_fired'):
        return None
    if gs is None:
        return None
    locked = gs.get('locked_allocations') or []
    if not locked:
        return None
    try:
        import config as _cfg
        dept_names = [d.name for d in _cfg.cfg.departments]
    except Exception:
        return None
    latest = locked[-1] if locked else []
    if len(latest) < len(dept_names):
        return None
    try:
        ops_i   = dept_names.index('Operations')
        sales_i = dept_names.index('Sales')
    except ValueError:
        return None
    ops   = float(latest[ops_i]   or 0)
    sales = float(latest[sales_i] or 0)
    if ops <= 0 or sales <= 0:
        return None
    ratio = ops / sales
    if ratio < 0.5:
        return {"text": (
            f"Operations ({_fmt_num(ops, sym, suffix)}) was less than half of Sales "
            f"({_fmt_num(sales, sym, suffix)}). Operations sets the ceiling on what Sales "
            f"can actually deliver — if this gap widens, unmet demand will cost you revenue."
        ), "sentiment": "warning"}
    if ratio > 2.2:
        return {"text": (
            f"Operations ({_fmt_num(ops, sym, suffix)}) was more than double Sales "
            f"({_fmt_num(sales, sym, suffix)}) — excess capacity sits idle when Sales "
            f"isn't generating enough demand to fill it."
        ), "sentiment": "warning"}
    return None

def _rule_repeated_strategy(yr, prev, history, sym, suffix, gs):
    """Flag when a department has held the same sub-decision year over year.
    Synergy in the simulator decays ~30% when the same choice is repeated,
    so this is genuinely actionable.

    Skipped when the top synergy rule above already covered the decay
    mechanic in detail — no need to repeat the same lesson twice in one
    panel.
    """
    if gs is None:
        return None
    # Skipped when _rule_top_synergy already explains the decay.
    synergies = yr.get('synergies') or []
    top_is_held = any(
        s.get('streak', 0) > 0
        and s.get('decay_factor', 1.0) < 0.95
        and s.get('effective_bonus', 0) >= 0.04
        for s in synergies
    )
    if top_is_held:
        return None

    locked_sd = gs.get('locked_subdecisions') or []
    if len(locked_sd) < 2:
        return None
    cur_sd  = locked_sd[-1] or {}
    prev_sd = locked_sd[-2] or {}
    if not cur_sd or not prev_sd:
        return None
    repeats = [d for d, choice in cur_sd.items()
               if choice and choice != '_placeholder' and prev_sd.get(d) == choice]
    if not repeats:
        return None
    if len(repeats) == 1:
        return {"text": f"Repeated last year's {repeats[0]} strategy — synergy decays ~30% on a hold.",
                "sentiment": "warning"}
    return {"text": f"Repeated {len(repeats)} strategies from last year ({', '.join(repeats)}) — synergy decays ~30% on each hold.",
            "sentiment": "warning"}


def _rule_rd_underinvestment(yr, prev, history, sym, suffix, gs):
    """Flag when R&D received less than 10% of total spend. Doesn't bite
    this year — but pipeline strength compounds, so this is a forward
    warning the player can act on in the next allocation.
    Ported from the previous AlertsCard, which used the same threshold."""
    if gs is None:
        return None
    locked = gs.get('locked_allocations') or []
    if not locked:
        return None
    try:
        import config as _cfg
        dept_names = [d.name for d in _cfg.cfg.departments]
    except Exception:
        return None
    latest = locked[-1] if locked else []
    if len(latest) < len(dept_names):
        return None
    try:
        rd_i = dept_names.index('R&D')
    except ValueError:
        return None
    total = sum(float(x or 0) for x in latest)
    if total <= 0:
        return None
    rd_pct = float(latest[rd_i] or 0) / total * 100
    if rd_pct >= 10:
        return None
    return {"text": f"R&D was {rd_pct:.0f}% of spend — your pipeline may thin out next year.",
            "sentiment": "warning"}


# Verdict and score diagnostics, so poor years lead with what went wrong.

def _rule_grade_verdict(yr, prev, history, sym, suffix):
    """Lead sentence stating, honestly, where the score landed. Sentiment is
    tied to the grade — a poor grade gets a negative verdict, full stop, so
    the recap opens with the truth instead of a cherry-picked positive."""
    vpi   = yr.get('vpi')
    grade = yr.get('grade')
    if vpi is None or grade is None:
        return None
    if grade in ('S', 'A'):
        return {"text": f"Strong year — VPI {vpi} (grade {grade}). The strategy is working.",
                "sentiment": "positive"}
    if grade == 'B':
        return {"text": f"Solid year — VPI {vpi} (grade {grade}). Credible, with room to climb.",
                "sentiment": "positive"}
    if grade == 'C':
        return {"text": f"Middling year — VPI {vpi} (grade {grade}). Profitable or present, but not both enough.",
                "sentiment": "neutral"}
    if grade == 'D':
        return {"text": f"Underperforming year — VPI {vpi} (grade {grade}). The current approach isn't paying off.",
                "sentiment": "negative"}
    # F
    return {"text": f"Poor year — VPI {vpi} (grade {grade}). Something is fundamentally off in the strategy.",
            "sentiment": "negative"}


def _rule_score_imbalance(yr, prev, history, sym, suffix):
    """Explain WHICH half of the VPI dragged the score down.

    VPI = 50% risk-adjusted profitability + 50% market share, each worth up
    to 500 points. When one half is healthy and the other is near zero, the
    player often misreads the result ("but I made huge profit!"). This rule
    names the gap explicitly. Only fires when the two halves clearly diverge,
    so it stays quiet on balanced outcomes.
    """
    p = yr.get('profit_score')
    s = yr.get('share_score')
    if p is None or s is None:
        return None
    gap = abs(p - s)
    # Need a meaningful divergence AND at least one weak half to be worth saying.
    if gap < 150:
        return None
    weak = min(p, s)
    if weak >= 250:
        return None  # both halves are decent — no diagnostic needed

    if p > s:
        # Profitable but losing on share — the screenshot's exact failure.
        return {"text": (f"Your score is lopsided: profitability scored {p}/500 but market share "
                         f"only {s}/500. VPI weights them equally — profit alone can't carry the grade."),
                "sentiment": "negative"}
    else:
        # Winning share but bleeding money.
        return {"text": (f"Your score is lopsided: market share scored {s}/500 but profitability "
                         f"only {p}/500. VPI weights them equally — share bought with losses won't carry the grade."),
                "sentiment": "negative"}


def _rule_rd_projection(yr, prev, history, sym, suffix, gs):
    """Tell players what their current R&D spend will return next year.
    R&D is the only department whose return is lagged one year — players
    have no other way to know what this year's R&D investment will produce.
    Only fires when the projection is meaningful (> $0) and there is a
    next year to benefit from it. Skipped on Year 5 (no next year).
    """
    projection = yr.get('rd_next_year_projection', 0)
    if not projection or projection <= 0:
        return None
    year_n = len(history)
    if year_n >= 5:
        return None  # last year — no next year to project into
    return {
        "text": (
            f"Your Year {year_n} R&D investment is queued to return "
            f"~{_fmt_num(projection, sym, suffix)} next year — "
            f"R&D revenue always lands one year after the spend."
        ),
        "sentiment": "neutral",
    }


def _rule_profit_high_share_low(yr, prev, history, sym, suffix):
    """Flag when profit is strong but market share is mediocre.
    Players often optimise for profit because it's the most visible number,
    but VPI weights market share equally. This rule names the gap explicitly
    so players understand why a profitable year can still produce a weak grade.
    Only fires when the divergence is clear enough to be actionable.
    """
    profit  = yr.get('profit', 0)
    share   = yr.get('market_share', 0)
    revenue = yr.get('total_revenue', 0)
    if revenue <= 0:
        return None
    margin = (profit / revenue) * 100
    # Profit threshold: margin > 15% = genuinely healthy
    # Share threshold: < 12% = clearly losing on the market half of VPI
    if margin < 15 or share >= 12:
        return None
    return {
        "text": (
            f"You ran efficiently ({margin:.0f}% margin) but only held {share:.1f}% market share. "
            f"VPI weights profitability and share equally — profit alone can't carry the grade."
        ),
        "sentiment": "warning",
    }


def _rule_share_high_profit_low(yr, prev, history, sym, suffix):
    """Flag when market share is strong but profit is thin or negative.
    Winning share by over-investing is a real strategic trap — the player
    is buying customers at a cost that the revenue can't justify.
    """
    profit  = yr.get('profit', 0)
    share   = yr.get('market_share', 0)
    revenue = yr.get('total_revenue', 0)
    if revenue <= 0:
        return None
    margin = (profit / revenue) * 100 if revenue > 0 else 0
    # Share threshold: > 20% = genuinely competitive
    # Profit threshold: margin < 5% = thin or negative
    if share < 20 or margin >= 5:
        return None
    return {
        "text": (
            f"You held {share:.1f}% market share but margin was only {margin:.0f}%. "
            f"You're winning customers but not converting that into returns — "
            f"your cost structure may need rebalancing."
        ),
        "sentiment": "warning",
    }


# Read the per-year `synergies` log. Holding a sub-decision across years decays its pairing bonus by 30% per repeat.

def _synergy_dept_pretty(name: str) -> str:
    """Render a department key for prose (R&D stays uppercased)."""
    return name if name in ('R&D',) else str(name)


def _rank_synergies(yr):
    """Return this year's synergy entries sorted by effective magnitude, desc.

    Filters out empty/zero entries. Entries are dicts as logged by the
    simulator; tolerate missing keys defensively since the log is
    instrumentation and its shape could drift.
    """
    raw = yr.get('synergies') or []
    cleaned = []
    for s in raw:
        if not isinstance(s, dict):
            continue
        eff = s.get('effective_bonus')
        if eff is None or abs(float(eff)) < 0.005:  # < 0.5% — not worth a line
            continue
        cleaned.append(s)
    cleaned.sort(key=lambda s: abs(float(s.get('effective_bonus', 0))), reverse=True)
    return cleaned


def _synergy_sentence(s) -> Optional[dict]:
    """Turn one synergy log entry into a {text, sentiment} sentence.

    Two framings:
      • Fresh pairing (streak 0): celebrate the boost the source choice gave
        the target department.
      • Decayed pairing (streak ≥ 1): explain that holding the same choice
        eroded the bonus — the dysynergy the player should learn from.
    """
    source  = _synergy_dept_pretty(s.get('source', ''))
    choice  = s.get('source_choice', '')
    target  = _synergy_dept_pretty(s.get('target', ''))
    raw     = float(s.get('raw_bonus', 0)) * 100
    eff     = float(s.get('effective_bonus', 0)) * 100
    streak  = int(s.get('streak', 0))
    if not source or not target or not choice:
        return None

    if streak >= 1 and eff < raw - 0.05:
        # Decayed — the "dysynergy" lesson.
        return {
            "text": (
                f"Holding {source}'s {choice} for {streak + 1} years straight decayed its "
                f"synergy into {target} — that bonus faded from +{raw:.0f}% to +{eff:.0f}%. "
                f"Rotating strategies keeps pairings fresh."
            ),
            "sentiment": "warning",
        }
    # Fresh, full-strength pairing.
    return {
        "text": (
            f"Your {source} {choice} call fed {target} a +{eff:.0f}% boost — that pairing "
            f"is working for you."
        ),
        "sentiment": "positive",
    }


def _rule_top_synergy(yr, prev, history, sym, suffix):
    """Headline the single most impactful strategy pairing this year."""
    ranked = _rank_synergies(yr)
    if not ranked:
        return None
    return _synergy_sentence(ranked[0])


def _rule_secondary_synergy(yr, prev, history, sym, suffix):
    """Call out the second-most impactful pairing, if it's meaningfully
    distinct from the top one (different target department)."""
    ranked = _rank_synergies(yr)
    if len(ranked) < 2:
        return None
    top, second = ranked[0], ranked[1]
    # Skip if it would just echo the headline's target — keeps the recap
    # from spending two of its ~6 slots on the same department.
    if second.get('target') == top.get('target'):
        return None
    return _synergy_sentence(second)


# Capacity / overspend diagnostics

def _rule_overcap_penalty(yr, prev, history, sym, suffix):
    """Flag spend that ran past a department's hard cap and was wasted.

    `overcap_penalty` is the value lost to spending beyond what a department
    could productively absorb this year. Distinct from the underuse penalty
    (left money unspent) — this is the opposite mistake: money poured into a
    department past the point it could convert.
    """
    pen = yr.get('overcap_penalty', 0)
    if pen is None or float(pen) < 1000:
        return None
    return {
        "text": (
            f"You pushed {_fmt_num(pen, sym, suffix)} past a department's effective ceiling — "
            f"spend beyond what it can absorb in a year doesn't convert. Redistributing that "
            f"budget would lift your return."
        ),
        "sentiment": "negative",
    }


def _rule_bottleneck_fired(yr, prev, history, sym, suffix):
    """Explain an Operations→Sales capacity choke with real lost units.

    The simulator flags `bottleneck_fired` when raw Sales demand exceeded the
    Operations-set delivery ceiling (`ops_cap`), so `sales_capped` < `sales_raw`.
    The gap is demand the team generated but couldn't fulfil — the clearest
    teachable moment in the ops/sales coupling.
    """
    if not yr.get('bottleneck_fired'):
        return None
    raw    = float(yr.get('sales_raw', 0) or 0)
    capped = float(yr.get('sales_capped', 0) or 0)
    cap    = float(yr.get('ops_cap', 0) or 0)
    lost   = raw - capped
    if lost <= 0:
        return None
    return {
        "text": (
            f"Sales generated more demand than Operations could deliver — output was capped at "
            f"{_fmt_num(cap, sym, suffix)} and you left roughly {_fmt_num(lost, sym, suffix)} of "
            f"demand unfulfilled. Operations sets the ceiling on what Sales can convert."
        ),
        "sentiment": "negative",
    }


def generate_year_narrative(year_result: dict,
                            history: list,
                            scenario_info: Optional[dict] = None,
                            gs: Optional[dict] = None) -> list:
    """Produce 2–4 sentences describing this year's outcome.

    Args:
      year_result:   the year_result dict that game_logic.execute_lock_year
                     just produced (includes vpi, grade, dept_returns,
                     market_share, market_shares, profit, underuse_penalty).
      history:       list of all year_results so far INCLUDING this year.
                     history[-1] is `year_result`; history[-2] is the prior
                     year (or empty list if Year 1).
      scenario_info: optional dict with currency_symbol / small_number_suffix.
                     Defaults to '$' / 'K' if absent.
      gs:            optional full game state. Rules that need locked
                     allocations or subdecisions (ops/sales imbalance,
                     repeated strategy) require this. Rules that don't
                     need it work with just year_result and history.

    Returns: list of {text, sentiment} dicts, length 1–4. May be empty if
    no rule fired (shouldn't happen in practice — every year has at least
    profit movement or a strongest-department call).
    """
    import inspect

    prev = history[-2] if len(history) >= 2 else None
    sym    = (scenario_info or {}).get('currency_symbol', '$')
    suffix = (scenario_info or {}).get('small_number_suffix', 'K')

    grade = year_result.get('grade')
    poor_year = grade in ('C', 'D', 'F')

    # Poor years lead with the verdict and diagnostics; good years lead with the financial headline.
    diagnostic_rules = [
        _rule_score_imbalance,       # which half tanked the score
        _rule_underuse_penalty,      # left budget on the table
        _rule_overcap_penalty,       # overspent past a cap
        _rule_bottleneck_fired,      # ops/sales capacity choke
        _rule_weakest_department,    # worst $/$ return
        _rule_thin_margin,           # costs ate revenue
        _rule_ops_sales_imbalance,   # structural imbalance
        _rule_rd_underinvestment,    # pipeline warning
        _rule_competitor_pressure,   # rival outpacing
        _rule_repeated_strategy,     # stale strategy
        _rule_profit_high_share_low, # efficient but losing share
        _rule_share_high_profit_low, # winning share but bleeding money
    ]
    positive_rules = [
        _rule_top_synergy,
        _rule_strongest_department,
        _rule_strategic_momentum,
        _rule_secondary_synergy,
        _rule_rd_projection,         # R&D forward projection
    ]
    movement_rules = [
        _rule_profit_movement,
        _rule_share_movement,
    ]

    if poor_year:
        # Verdict → why it failed (diagnostics) → the raw numbers → any
        # positives that still fit.
        rules = [_rule_grade_verdict] + diagnostic_rules + movement_rules + positive_rules
    else:
        # Verdict → headline numbers → positives → remaining diagnostics.
        rules = ([_rule_grade_verdict] + movement_rules + positive_rules + diagnostic_rules)

    sentences = []
    seen_text = set()
    for rule in rules:
        try:
            # Rules may take `gs` as a sixth argument; detected by parameter count so errors inside a rule still propagate.
            n_params = len(inspect.signature(rule).parameters)
            if n_params >= 6:
                result = rule(year_result, prev, history, sym, suffix, gs)
            else:
                result = rule(year_result, prev, history, sym, suffix)
            if result and result.get('text') and result['text'] not in seen_text:
                sentences.append(result)
                seen_text.add(result['text'])
        except Exception:
            continue
        if len(sentences) >= _MAX_SENTENCES:
            break

    # On a poor year, make sure the verdict and score-imbalance diagnostic come first.
    if poor_year and sentences:
        has_negative = any(s.get('sentiment') in ('negative', 'warning') for s in sentences)
        if not has_negative:
            forced = []
            for r in (_rule_grade_verdict, _rule_score_imbalance):
                res = r(year_result, prev, history, sym, suffix)
                if res and res.get('text') and res['text'] not in {s['text'] for s in forced}:
                    forced.append(res)
            # Keep a couple of the original lines for context, drop to fit.
            sentences = (forced + [s for s in sentences if s['text'] not in {f['text'] for f in forced}])[:_MAX_SENTENCES]

    return sentences
