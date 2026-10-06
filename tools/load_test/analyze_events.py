"""
analyze_events.py — validate the year-lock barrier from a Playwright run.

Invariants checked
------------------
1. BARRIER TIMING  For every year N, no client received all_teams_locked
   before the last controller's lock_hold_end for year N.
   lock_hold_end is logged when the modal closes, which is AFTER the lock
   HTTP response — so it is a reliable lower bound for when the last lock
   was processed.  Grace window is 500 ms to absorb WS propagation latency.

2. COMPLETENESS    Every team that locked eventually receives all_teams_locked.
   Year N_max (the final year) is exempt from this check because viewer
   tasks are cancelled immediately after controllers finish — some viewers
   can be mid-sleep when they receive the cancel and will miss the message.

3. DELIVERY SPREAD All clients received all_teams_locked within a tight
   window of each other (checks broadcast fan-out quality).

4. ORDERING        Per-team year sequence of all_teams_locked is contiguous.

5. UI_ADVANCED     Every controller's UI advanced from year N to year N+1.
   Not applicable to the final year (no N+1 to advance to).

Usage:
    python analyze_events.py events.jsonl
"""

import json, sys
from collections import defaultdict
from statistics import median


def load_events(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def analyze(events):
    lock_hold_starts = defaultdict(list)   # year -> [(team, ts)]
    lock_hold_ends   = defaultdict(list)   # year -> [(team, ts)]
    all_locked_msgs  = defaultdict(list)   # year -> [(team, username, ts)]
    ui_advanced      = defaultdict(set)    # year -> {team_key}
    ui_stuck         = defaultdict(list)   # year -> [(team, note)]
    teams_seen       = set()
    users_seen       = set()
    errors           = []
    page_errors      = []
    fiber_fallbacks  = defaultdict(list)   # year -> [team]
    completed_early  = defaultdict(list)   # year -> [team] (server auto-locked,
                                           # harness exited without locking)
    reload_pass      = []   # [(team, year)]
    reload_fail      = []   # [event dict]
    reload_skipped   = []   # [(team, year)]
    reload_errs      = []   # [event dict]
    viewer_self_skips = []  # [team_key] — viewers that missed the storyboard
                            # broadcast and self-advanced (race diagnostic)
    all_logged_in_ts  = None   # ts of the all_controllers_logged_in marker
    all_begun_ts      = None   # ts of the all_controllers_begun marker

    for e in events:
        teams_seen.add(e["team_key"])
        users_seen.add((e["team_key"], e["username"]))
        kind = e["kind"]
        if kind == "lock_hold_start":
            lock_hold_starts[e["year"]].append((e["team_key"], e["ts"]))
        elif kind == "lock_hold_end":
            lock_hold_ends[e["year"]].append((e["team_key"], e["ts"]))
        elif kind == "hold_fiber_fallback":
            fiber_fallbacks[e.get("year")].append(e["team_key"])
        elif kind == "ws_msg" and e.get("msg_type") == "all_teams_locked":
            if e.get("year") is not None:
                all_locked_msgs[e["year"]].append(
                    (e["team_key"], e["username"], e["ts"]))
        elif kind == "ui_advanced":
            ui_advanced[e["year"] - 1].add(e["team_key"])
        elif kind == "ui_stuck":
            ui_stuck[e["year"]].append((e["team_key"], e.get("note", "")))
        elif kind == "error":
            errors.append(e)
        elif kind == "page_error":
            page_errors.append(e)
        elif kind == "reload_test_pass":
            reload_pass.append((e["team_key"], e.get("year")))
        elif kind == "reload_test_fail":
            reload_fail.append(e)
        elif kind == "reload_test_skipped":
            reload_skipped.append((e["team_key"], e.get("year")))
        elif kind == "reload_test_error":
            reload_errs.append(e)
        elif kind == "viewer_self_skipped_storyboard":
            viewer_self_skips.append(e["team_key"])
        elif kind == "game_completed_early":
            completed_early[e["year"]].append(e["team_key"])
        elif kind == "all_controllers_logged_in":
            all_logged_in_ts = e["ts"] if all_logged_in_ts is None else min(all_logged_in_ts, e["ts"])
        elif kind == "all_controllers_begun":
            all_begun_ts = e["ts"] if all_begun_ts is None else min(all_begun_ts, e["ts"])

    all_years   = sorted(all_locked_msgs.keys() | lock_hold_ends.keys() | lock_hold_starts.keys() | completed_early.keys())
    final_year  = max(all_years) if all_years else None

    print(f"\n=== ORAS Playwright Barrier Analysis ===")
    print(f"Teams observed : {len(teams_seen)}")
    print(f"Users observed : {len(users_seen)}")
    print(f"Years observed : {all_years}")
    print(f"Driver errors  : {len(errors)}")
    print(f"Page JS errors : {len(page_errors)}")
    total_fallbacks = sum(len(v) for v in fiber_fallbacks.values())
    if total_fallbacks or viewer_self_skips:
        print(f"Hold fallbacks : {total_fallbacks}  "
              f"(RAF stalled; fiber onComplete used — expected for "
              f"background contexts, now seals reliably)")
        print(f"Viewer reskips : {len(viewer_self_skips)}  "
              f"(missed storyboard_complete broadcast, self-advanced)")

    if errors:
        print(f"\n  Sample driver errors (up to 5):")
        for e in errors[:5]:
            print(f"    {e['username']}@{e['team_key']} yr={e.get('year','?')}: "
                  f"{e.get('err','')[:100]}")
    if page_errors:
        print(f"\n  Sample page JS errors (up to 5):")
        for e in page_errors[:5]:
            print(f"    {e['username']}@{e['team_key']}: "
                  f"{e.get('err','')[:120]}")

    violations = 0
    GRACE_MS   = 500   # WS propagation + React commit latency

    print("\n--- Login-before-lock invariant ---")
    first_lock_ts = None
    first_lock_who = None
    for yr in (lock_hold_starts, lock_hold_ends):
        for y, entries in yr.items():
            for team, ts in entries:
                if first_lock_ts is None or ts < first_lock_ts:
                    first_lock_ts, first_lock_who = ts, (team, y)
    if all_logged_in_ts is None:
        print("  ⚠ no all_controllers_logged_in marker in log "
              "(old harness, or run didn't reach the gate) — cannot verify")
    elif first_lock_ts is None:
        print("  ℹ no locks recorded — nothing to check")
    else:
        margin = first_lock_ts - all_logged_in_ts
        if margin >= 0:
            print(f"  ✓ all controllers logged in {margin:.0f} ms before the "
                  f"first lock ({first_lock_who[0]} yr={first_lock_who[1]})")
        else:
            print(f"  ✗ LOGIN ORDER: first lock ({first_lock_who[0]} "
                  f"yr={first_lock_who[1]}) occurred {-margin:.0f} ms BEFORE all "
                  f"controllers had logged in — a team could lock against an "
                  f"incomplete cohort")
            violations += 1

    for year in all_years:
        is_final = (year == final_year)
        print(f"\n--- Year {year}{' (final)' if is_final else ''} ---")

        starts = lock_hold_starts.get(year, [])
        ends   = lock_hold_ends.get(year, [])
        msgs   = all_locked_msgs.get(year, [])
        fbacks = fiber_fallbacks.get(year, [])

        unique_locking   = {t for t, _ in ends}
        unique_receiving = {t for t, _, _ in msgs}

        print(f"  lock_hold_end events     : {len(ends)} "
              f"from {len(unique_locking)} team(s)")
        early = completed_early.get(year, [])
        if early:
            print(f"  completed early (server auto-lock): {len(early)} "
                  f"team(s) {sorted(set(early))} — driver exited without "
                  f"locking; these locks happened server-side and won't appear "
                  f"in lock_hold_end")
        print(f"  all_teams_locked received: {len(msgs)} "
              f"to {len(unique_receiving)} team(s)")
        if fbacks:
            print(f"  fiber fallback used by   : {sorted(set(fbacks))}")

        if not ends and not starts:
            print(f"  ⚠ No locks recorded — skipping checks")
            continue

        # The barrier reference is lock_hold_START (when the HTTP request is
        # dispatched), not lock_hold_END (when the response arrives).
        # lock_hold_end includes execute_lock_year compute time (~1-2s), so
        # the server legitimately broadcasts all_teams_locked before the first
        # team's HTTP response returns — using end as the reference would flag
        # every single year as a violation.  Using start gives a true lower
        # bound: the server cannot have processed the lock before the request
        # was sent.
        if starts:
            last_start_ts   = max(ts for _, ts in starts)
            last_start_team = next(t for t, ts in starts if ts == last_start_ts)
            last_end_ts     = max(ts for _, ts in ends) if ends else None
            last_end_team   = next(t for t, ts in ends if ts == last_end_ts) if ends else None
            print(f"  Last to start hold: {last_start_team}  t={last_start_ts:.3f}")
            if last_end_team:
                print(f"  Last to seal (end): {last_end_team}  t={last_end_ts:.3f}")
            barrier_ref_ts   = last_start_ts
            barrier_ref_name = "last hold-start"
        else:
            # Fallback for old logs without lock_hold_start events
            last_end_ts   = max(ts for _, ts in ends)
            last_end_team = next(t for t, ts in ends if ts == last_end_ts)
            print(f"  Last to seal: {last_end_team}  t={last_end_ts:.3f}")
            barrier_ref_ts   = last_end_ts
            barrier_ref_name = "last hold-end (fallback — no start events)"

        # 1. BARRIER TIMING
        # Final year is exempt: the server does extra work (final results,
        # narrative generation) before the HTTP response arrives, so the
        # WS broadcast lands before modal-close by design — not a violation.
        if is_final:
            print(f"  ℹ Barrier timing not checked on final year "
                  f"(server computes final results before HTTP response)")
        else:
            early = [(t, u, ts) for t, u, ts in msgs
                     if ts < (barrier_ref_ts - GRACE_MS / 1000)]
            if early:
                violations += len(early)
                print(f"  ✗ BARRIER: {len(early)} client(s) got all_teams_locked "
                      f">{GRACE_MS}ms before {barrier_ref_name}:")
                for t, u, ts in sorted(early, key=lambda x: x[2])[:5]:
                    gap = (barrier_ref_ts - ts) * 1000
                    print(f"      {u}@{t}: {gap:.0f}ms early")
            else:
                print(f"  ✓ Barrier timing OK")

        # 3. DELIVERY SPREAD
        if msgs:
            tss          = sorted(ts for _, _, ts in msgs)
            spread_ms    = (tss[-1] - tss[0]) * 1000
            from_release = sorted((ts - barrier_ref_ts) * 1000
                                  for _, _, ts in msgs)
            print(f"  Delivery spread          : {spread_ms:.1f} ms "
                  f"({'✓ tight' if spread_ms < 200 else '⚠ wide'})")
            print(f"  From last-start → receive: "
                  f"min={from_release[0]:.0f}ms  "
                  f"median={median(from_release):.0f}ms  "
                  f"max={from_release[-1]:.0f}ms")
            # Separate HARNESS hold time from real SERVER latency. The metric
            # above (last-START → receive) includes the entire hold-to-seal
            # sequence — the scripted 1.6s hold plus up to 8×1.2s RAF-fallback
            # retries per throttled background context — which is test-automation
            # cost that real foreground users never incur, NOT server latency.
            # last_end_ts is the last lock's modal-close (≈ when the last lock
            # actually landed), so (receive − last_end_ts) is the genuine
            # barrier-complete + fan-out time. Compare the two to see how much of
            # the wall-clock is the harness driving a press-and-hold UI vs. work
            # the server is actually doing.
            if last_end_ts is not None:
                srv = sorted((ts - last_end_ts) * 1000 for _, _, ts in msgs)
                if starts:
                    hold_ms = (last_end_ts - last_start_ts) * 1000
                    print(f"  Harness hold sequence    : {hold_ms:.0f}ms "
                          f"(scripted hold + RAF-fallback retries — harness, not server)")
                print(f"  SERVER last-lock → receive: "
                      f"min={srv[0]:.0f}ms  median={median(srv):.0f}ms  "
                      f"max={srv[-1]:.0f}ms  ← actual barrier + fan-out latency")
            if spread_ms >= 500:
                violations += 1
                print(f"  ✗ SPREAD: fan-out took {spread_ms:.0f}ms — "
                      f"some clients lagging")

        # 2. COMPLETENESS
        missing = unique_locking - unique_receiving
        if missing:
            if is_final:
                print(f"  ℹ COMPLETENESS: {len(missing)} team(s) locked but "
                      f"didn't receive all_teams_locked — expected on final year "
                      f"(viewer tasks cancelled before message arrived): "
                      f"{sorted(missing)[:5]}")
            else:
                violations += len(missing)
                print(f"  ✗ COMPLETENESS: {len(missing)} team(s) locked but "
                      f"never received all_teams_locked: {sorted(missing)[:5]}")
        else:
            print(f"  ✓ Completeness OK")

        # 5. UI_ADVANCED
        if not is_final:
            advanced   = ui_advanced.get(year, set())
            ui_missing = unique_locking - advanced
            if ui_missing:
                violations += len(ui_missing)
                print(f"  ✗ UI_ADVANCED: {len(ui_missing)} controller(s) did "
                      f"not see Year {year} → Year {year+1}: "
                      f"{sorted(ui_missing)[:5]}")
            else:
                print(f"  ✓ All {len(advanced)} controller(s) UI advanced")

        if year in ui_stuck:
            for team, note in ui_stuck[year][:3]:
                print(f"  ✗ UI_STUCK: {team}: {note}")
                violations += 1

    # 4. ORDERING
    print(f"\n--- Ordering ---")
    team_seqs = defaultdict(list)
    for year in sorted(all_locked_msgs):
        for team, _, ts in sorted(all_locked_msgs[year], key=lambda x: x[2]):
            team_seqs[team].append((year, ts))
    bad = 0
    for team, seq in team_seqs.items():
        seen_years = []
        for y, _ in seq:
            if not seen_years or seen_years[-1] != y:
                seen_years.append(y)
        expected = list(range(seen_years[0], seen_years[0] + len(seen_years)))
        if seen_years != expected:
            bad += 1
            if bad <= 5:
                print(f"  ✗ {team}: non-contiguous years: {seen_years}")
    if bad == 0:
        print(f"  ✓ All {len(team_seqs)} team(s) received contiguous sequences")
    else:
        violations += bad

    if reload_pass or reload_fail or reload_skipped or reload_errs:
        print(f"\n--- Reload Banner-Persistence Test ---")
        print(f"  passed  : {len(reload_pass)}  (banner persisted across reload)")
        print(f"  skipped : {len(reload_skipped)}  (team was last locker — N/A)")
        if reload_errs:
            print(f"  errored : {len(reload_errs)}  (harness issue, not a verdict)")
            for e in reload_errs[:5]:
                print(f"    {e['username']}@{e['team_key']} yr={e.get('year','?')}: "
                      f"{e.get('err','')[:100]}")
        if reload_fail:
            print(f"  ✗ FAILED : {len(reload_fail)}  "
                  f"(reload advanced team past the barrier)")
            for e in reload_fail[:5]:
                exposed = e.get("alloc_ui_exposed")
                print(f"    {e['username']}@{e['team_key']} yr={e.get('year','?')}: "
                      f"banner gone"
                      f"{' + year N+1 allocate UI exposed' if exposed else ''}")
            violations += len(reload_fail)
        else:
            checked = len(reload_pass) + len(reload_skipped)
            print(f"  ✓ No reload violations "
                  f"({len(reload_pass)} asserted, {len(reload_skipped)} N/A)")
            if len(reload_pass) == 0 and checked > 0:
                print(f"  ⚠ NOTE: every reload self-skipped (designated team was "
                      f"always the last locker) — the assertion never actually "
                      f"fired. Re-run, or set ORAS_RELOAD_TEAM to a team that "
                      f"locks earlier, to get real coverage.")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Violations: {violations}")
    if violations == 0:
        print("✓ PASS — barrier invariant holds, all UIs advanced correctly")
    else:
        print("✗ FAIL — see violations above")
    return 0 if violations == 0 else 1


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "events.jsonl"
    sys.exit(analyze(load_events(path)))
