from datetime import UTC, datetime

from gate import decide, parse_caps, unmatched_keys

NOW = datetime(2026, 10, 29, 0, 0, tzinfo=UTC)


def acct(
    n,
    five,
    week,
    active=False,
    five_reset="2026-10-29T01:00:00+00:00",
    week_reset="2026-11-01T23:00:00+00:00",
    fable=None,
    status="ok",
):
    u = {
        "fiveHour": {"pct": five, "resetsAt": five_reset},
        "sevenDay": {"pct": week, "resetsAt": week_reset},
        "scoped": [],
    }
    if fable is not None:
        u["scoped"].append({"name": "Fable", "pct": fable, "resetsAt": week_reset})
    return {
        "number": n,
        "email": f"u{n}@x",
        "active": active,
        "usageStatus": status,
        "usage": u,
    }


def run(accts, five=95, week=("100",), models=(), no_wait=False):
    base, per = parse_caps(list(week), 100.0)
    return decide({"accounts": accts}, five, base, per, set(models), NOW, no_wait)


def test_go_switch_and_pause_on_five_hour_caps():
    assert run([acct(1, 50, 20, active=True), acct(2, 0, 0)])["decision"] == "go"
    r = run([acct(1, 96, 20, active=True), acct(2, 10, 30)])
    assert (r["decision"], r["account"]) == ("switch", 2), r
    r = run(
        [
            acct(1, 96, 20, active=True, five_reset="2026-10-29T02:00:00+00:00"),
            acct(2, 95, 30, five_reset="2026-10-29T01:00:00+00:00"),
        ]
    )
    assert (r["decision"], r["account"], r["waitSeconds"]) == (
        "pause",
        2,
        3600 + 120,
    ), r


def test_weekly_caps_and_per_account_overrides():
    # Account 1 at 61% is out under a 60% weekly cap even though its 5h window is fine.
    r = run([acct(1, 10, 61, active=True), acct(2, 96, 40)], week=("60",))
    assert (r["decision"], r["account"]) == ("pause", 2), r
    assert run([acct(1, 10, 61, active=True)], week=("60", "1=70"))["decision"] == "go"
    r = run([acct(1, 10, 61, active=True), acct(2, 10, 60)], week=("60",))
    assert r["decision"] == "stop", r
    # A 5h-capped account past its weekly cap must not trigger a pause.
    assert run([acct(1, 99, 65, active=True)], week=("60",))["decision"] == "stop"


def test_model_weekly_limit_counts_only_when_requested():
    assert run([acct(1, 10, 20, active=True, fable=99)])["decision"] == "go"
    assert (
        run([acct(1, 10, 20, active=True, fable=100)], models=("Fable",))["decision"]
        == "stop"
    )
    assert (
        run([acct(1, 10, 20, active=True, fable=100)], models=("fable",))["decision"]
        == "stop"
    )


def test_unreadable_usage_pauses_for_retry():
    r = run([acct(1, 10, 20, active=True, status="error")])
    assert (r["decision"], r["waitSeconds"], r["unreadable"]) == ("pause", 900, True), r
    r = run(
        [acct(1, 10, 20, active=True, status="token_expired"), acct(2, 10, 65)],
        week=("60",),
    )
    assert (r["decision"], r["waitSeconds"]) == ("pause", 900), r
    r = run(
        [acct(1, 10, 20, status="unavailable"), acct(2, 96, 20, active=True)]
    )  # reset in 1h > 15 min
    assert (r["decision"], r["waitSeconds"]) == ("pause", 900), r
    r = run(
        [
            acct(1, 10, 20, status="unavailable"),
            acct(2, 96, 20, active=True, five_reset="2026-10-29T00:05:00+00:00"),
        ]
    )
    assert (r["decision"], r["account"], r["waitSeconds"]) == ("pause", 2, 300 + 120), r
    nullpct = acct(1, 10, 20, active=True)
    nullpct["usage"]["fiveHour"]["pct"] = None
    assert run([nullpct])["accounts"][0]["state"] == "unknown"


def test_missing_windows_disabled_accounts_and_reset_times():
    bare = {"number": 1, "active": True, "usageStatus": "ok", "usage": {}}
    assert run([bare])["decision"] == "go"
    assert (
        run([{**acct(1, 10, 20, active=True), "disabled": True}, acct(2, 10, 20)])[
            "decision"
        ]
        == "switch"
    )
    r = run([acct(1, 96, 20, active=True, five_reset="2026-10-29T01:00:00.5Z")])
    assert r["waitSeconds"] == 3600 + 120, r
    r = run([acct(1, 96, 20, active=True, five_reset="2026-10-28T23:00:00+00:00")])
    assert r["waitSeconds"] == 600, r
    r = run([acct(1, 96, 20, active=True, five_reset=None)], five=0)
    assert (r["decision"], r["waitSeconds"]) == ("pause", 600), r


def test_override_keys_match_number_email_or_alias():
    aliased = {**acct(2, 10, 65, active=True), "alias": "work"}
    assert run([aliased], week=("60", "work=70"))["decision"] == "go"
    assert run([aliased], week=("60", "u2@x=70"))["decision"] == "go"
    assert unmatched_keys({"accounts": [aliased]}, {"wrok": 70.0, "2": 70.0}) == [
        "wrok"
    ]


def test_no_wait_stops_instead_of_pausing():
    assert run([acct(1, 96, 20, active=True)], no_wait=True)["decision"] == "stop"
    assert (
        run([acct(1, 96, 20, active=True), acct(2, 10, 20)], no_wait=True)["decision"]
        == "switch"
    )
