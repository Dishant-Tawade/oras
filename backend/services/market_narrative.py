"""
services/market_narrative.py — "What happened in the market?" section.

Generates per-competitor insights that players CANNOT infer from the
visible UI alone. Grounded entirely in sim outputs stored in year_result:
  - competitor_ai[name].allocations / alloc_shifts / sub_decisions
  - competitor_ai[name].dominant_segment
  - market_shares[name] (current) vs prev year's market_shares
  - segment_likability[seg][name]
  - competitor_profits[name]

Rules:
  - One insight per competitor, max 2-3 sentences
  - Never generic — every sentence references a specific number or choice
  - Sentiment: positive (green) = competitor is weakening relative to player
                warning (amber) = competitor is growing threat
                neutral (gray)  = factual, neither threatening nor comforting
"""

from typing import Optional


def _fmt_num(val, sym='$', suffix='K'):
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


_SEGMENT_LABELS = {
    'budget':      'budget-conscious families',
    'tech':        'tech enthusiasts',
    'performance': 'performance buyers',
    'fleet':       'fleet operators',
}

_DEPT_LABELS = {
    'R&D':        'R&D',
    'Sales':      'Sales',
    'Operations': 'Operations',
    'Marketing':  'Marketing',
}


def _seg_label(key: str) -> str:
    return _SEGMENT_LABELS.get(key, key)


def _dept_label(key: str) -> str:
    return _DEPT_LABELS.get(key, key)


def _share_delta(comp_name: str, yr: dict, prev: Optional[dict]) -> Optional[float]:
    """Return competitor's share change vs prior year, or None if unavailable."""
    cur_shares  = yr.get('market_shares') or {}
    prev_shares = (prev.get('market_shares') or {}) if prev else {}
    cur  = cur_shares.get(comp_name)
    prv  = prev_shares.get(comp_name)
    if cur is None:
        return None
    if prv is None:
        return None
    return cur - prv


def _build_competitor_insight(
    comp_name: str,
    yr: dict,
    prev: Optional[dict],
    sym: str,
    suffix: str,
) -> Optional[dict]:
    """
    Build one insight dict for a single competitor.
    Returns {name, text, sentiment, detail} or None if nothing notable.
    """
    ai = (yr.get('competitor_ai') or {}).get(comp_name)
    cur_shares  = yr.get('market_shares') or {}
    seg_lik     = yr.get('segment_likability') or {}
    comp_profit = (yr.get('competitor_profits') or {}).get(comp_name)

    cur_share  = cur_shares.get(comp_name)
    share_delta = _share_delta(comp_name, yr, prev)

    sentences = []
    sentiment = 'neutral'

    # 1. Share movement with cause
    if cur_share is not None and share_delta is not None:
        abs_d = abs(share_delta)
        if abs_d >= 1.0:
            direction = "gained" if share_delta > 0 else "lost"
            sentences.append(
                f"{'▲' if share_delta > 0 else '▼'} {direction} {abs_d:.1f} pts of share, "
                f"now at {cur_share:.1f}%."
            )
            if share_delta > 2.0:
                sentiment = 'warning'
            elif share_delta < -2.0:
                sentiment = 'positive'
        elif cur_share is not None:
            sentences.append(f"Share held steady at {cur_share:.1f}%.")

    # 2. What they focused their budget on (from AI state)
    if ai:
        shifts = ai.get('alloc_shifts') or {}
        allocs = ai.get('allocations') or {}
        biggest_dept = ai.get('biggest_shift_dept')
        biggest_amt  = ai.get('biggest_shift_amount', 0)

        if biggest_dept and abs(biggest_amt) >= 1_000_000:
            direction = "increased" if biggest_amt > 0 else "cut"
            pct = abs(biggest_amt) / max(allocs.get(biggest_dept, 1), 1) * 100
            sentences.append(
                f"They {direction} {_dept_label(biggest_dept)} spend "
                f"by {_fmt_num(abs(biggest_amt), sym, suffix)} "
                f"({pct:.0f}%) vs last year."
            )
        elif allocs and not shifts:
            # Year 1 — just describe their biggest spend area
            top_dept = max(allocs, key=lambda d: allocs.get(d, 0), default=None)
            if top_dept:
                sentences.append(
                    f"Their heaviest investment was in {_dept_label(top_dept)} "
                    f"({_fmt_num(allocs.get(top_dept, 0), sym, suffix)})."
                )

        # 3. Strategic sub-decision
        sub_decisions = ai.get('sub_decisions') or {}
        if sub_decisions:
            # Find the sub-decision for their dominant spend department
            top_sd_dept = max(allocs, key=lambda d: allocs.get(d, 0), default=None) if allocs else None
            if top_sd_dept and top_sd_dept in sub_decisions:
                choice = sub_decisions[top_sd_dept]
                # Look up readable label from scenario config
                try:
                    from simulator import get_sub_decisions
                    sd_cfg = get_sub_decisions()
                    opt = sd_cfg.get(top_sd_dept, {}).get('options', {}).get(choice, {})
                    choice_label = opt.get('label', choice.replace('_', ' ').title()) if isinstance(opt, dict) else choice.replace('_', ' ').title()
                except Exception:
                    choice_label = choice.replace('_', ' ').title()
                sentences.append(
                    f"Their {_dept_label(top_sd_dept)} strategy: \"{choice_label}\"."
                )

        # 4. Dominant segment focus
        dom_seg = ai.get('dominant_segment')
        if dom_seg and seg_lik:
            dom_score = seg_lik.get(dom_seg, {}).get(comp_name, 0)
            comp_names_set = set((yr.get('competitor_profits') or {}).keys())
            player_seg_score = None
            for entity, score in seg_lik.get(dom_seg, {}).items():
                if entity not in comp_names_set:
                    player_seg_score = score
                    break
            if dom_score >= 50:
                seg_str = f"scoring {dom_score:.0f}/100 there"
                if player_seg_score is not None:
                    gap = dom_score - player_seg_score
                    if gap > 10:
                        seg_str += f" vs your {player_seg_score:.0f}/100"
                        if sentiment == 'neutral':
                            sentiment = 'warning'
                sentences.append(
                    f"Their strongest segment is {_seg_label(dom_seg)} — {seg_str}."
                )

    # 5. Profit context
    if comp_profit is not None and prev:
        prev_profit = (prev.get('competitor_profits') or {}).get(comp_name)
        if prev_profit is not None:
            delta = comp_profit - prev_profit
            abs_d = abs(delta)
            if abs_d >= 5_000_000:
                direction = "up" if delta > 0 else "down"
                sentences.append(
                    f"Profit {direction} {_fmt_num(abs_d, sym, suffix)} vs last year "
                    f"(now {_fmt_num(comp_profit, sym, suffix)})."
                )

    if not sentences:
        return None

    return {
        'name':      comp_name,
        'text':      ' '.join(sentences),
        'sentiment': sentiment,
    }


def generate_market_narrative(
    year_result: dict,
    history: list,
    scenario_info: Optional[dict] = None,
) -> list:
    """
    Produce one insight per competitor for the "What happened in the market?"
    section of the Market tab.

    Returns list of {name, text, sentiment} dicts, one per competitor
    for which meaningful data is available. Empty list if no data.
    """
    prev = history[-2] if len(history) >= 2 else None
    sym    = (scenario_info or {}).get('currency_symbol', '$')
    suffix = (scenario_info or {}).get('small_number_suffix', 'K')

    comp_profits = year_result.get('competitor_profits') or {}
    if not comp_profits:
        return []

    insights = []
    for comp_name in comp_profits:
        insight = _build_competitor_insight(comp_name, year_result, prev, sym, suffix)
        if insight:
            insights.append(insight)

    # Sort: biggest threats (warning) first, then neutral, then positive
    order = {'warning': 0, 'neutral': 1, 'positive': 2}
    insights.sort(key=lambda x: order.get(x['sentiment'], 1))
    return insights
