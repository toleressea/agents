"""Usage gate for long agent runs across cswap-managed Claude accounts.

Reads `cswap list --json` and prints one JSON decision:
  go     - the active account is under its caps; keep working
  switch - the active account is capped, another is not; run `cswap switch <account>`
  pause  - every account is capped, at least one only by its 5-hour cap; wait until resumeAt
           (with --no-wait this is a stop instead). Also a 15-minute pause when usage is unreadable.
  stop   - every account hit its weekly cap (or has no readable usage); end the run

Usage:
  python3 -I gate.py [--five-cap 95] [--week-cap 60] [--week-cap 2=70] [--model Fable] [--no-wait]

Exit 2: a --week-cap ACCOUNT=PCT key matches no account.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime

RESUME_BUFFER_SECONDS = 120  # cswap readings lag the real reset by a little
UNREADABLE_WAIT_SECONDS = 900
STALE_RESET_WAIT_SECONDS = (
    600  # reset time missing or past: the reading is stale, so retry later
)
DEFAULT_WEEK_CAP = 98.0  # leaves room for the last unit before the hard weekly limit


def parse_caps(values: list[str], default: float) -> tuple[float, dict[str, float]]:
    base, per_account = default, {}
    for v in values or []:
        if "=" in v:
            key, pct = v.split("=", 1)
            per_account[key.strip()] = float(pct)
        else:
            base = float(v)
    return base, per_account


def cap_for(acct: dict, base: float, per_account: dict[str, float]) -> float:
    for key in (str(acct.get("number")), acct.get("email"), acct.get("alias")):
        if key in per_account:
            return per_account[key]
    return base


def ts(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def decide(
    data: dict,
    five_cap: float,
    week_base: float,
    week_per: dict[str, float],
    models: set[str],
    now: datetime,
    no_wait: bool = False,
) -> dict:
    models = {
        m.casefold() for m in models
    }  # cswap matches model names case-insensitively
    rows = []
    for a in data.get("accounts", []):
        if a.get("disabled"):
            continue
        row = {
            "account": a["number"],
            "email": a.get("email"),
            "active": bool(a.get("active")),
        }
        u = a.get("usage") or {}
        five_win = u.get("fiveHour") or {}
        weekly = [u.get("sevenDay") or {}] + [
            w
            for w in u.get("scoped") or []
            if (w.get("name") or "").casefold() in models
        ]
        # A null pct is no reading at all; counting it as 0% could run an account past its limit.
        if a.get("usageStatus") != "ok" or any(
            w.get("pct", 0.0) is None for w in [five_win, *weekly]
        ):
            rows.append(
                {**row, "state": "unknown", "usageStatus": a.get("usageStatus")}
            )
            continue
        five = five_win.get("pct", 0.0)
        week = max(w.get("pct", 0.0) for w in weekly)
        week_cap = cap_for(a, week_base, week_per)
        row.update(
            five=five,
            fiveCap=five_cap,
            week=week,
            weekCap=week_cap,
            fiveResetsAt=five_win.get("resetsAt"),
            weekResetsAt=min(
                (
                    w["resetsAt"]
                    for w in weekly
                    if w.get("pct", 0.0) >= week_cap and w.get("resetsAt")
                ),
                key=ts,
                default=None,
            ),
        )
        row["state"] = (
            "week-capped"
            if week >= week_cap
            else "five-capped"
            if five >= five_cap
            else "ok"
        )
        rows.append(row)

    def out(decision: str, reason: str, **extra) -> dict:
        return {"decision": decision, "reason": reason, **extra, "accounts": rows}

    ok = [r for r in rows if r["state"] == "ok"]
    active = next((r for r in ok if r["active"]), None)
    if active:
        return out("go", "active account is under its caps", account=active["account"])
    if ok:
        best = max(
            ok, key=lambda r: min(r["fiveCap"] - r["five"], r["weekCap"] - r["week"])
        )
        return out(
            "switch",
            "active account is capped; another account has headroom",
            account=best["account"],
        )

    unknown = [r for r in rows if r["state"] == "unknown"]

    def wait_for(r: dict) -> int:
        reset = ts(r.get("fiveResetsAt"))
        if reset is None or reset <= now:
            return STALE_RESET_WAIT_SECONDS
        return int((reset - now).total_seconds()) + RESUME_BUFFER_SECONDS

    five_capped = [] if no_wait else [r for r in rows if r["state"] == "five-capped"]
    waits = [(wait_for(r), r) for r in five_capped]
    if unknown:
        # cswap retries unreadable accounts itself, so a read failure is a short pause, not the end.
        waits.append((UNREADABLE_WAIT_SECONDS, None))
    if waits:
        wait, first = min(waits, key=lambda w: w[0])
        if first is None:
            return out(
                "pause",
                "usage unreadable for some accounts and no account is under its caps; retry soon",
                unreadable=True,
                waitSeconds=wait,
            )
        return out(
            "pause",
            "all accounts capped; earliest 5-hour reset frees one",
            account=first["account"],
            resumeAt=first["fiveResetsAt"],
            waitSeconds=wait,
        )
    if no_wait and any(r["state"] == "five-capped" for r in rows):
        return out("stop", "all accounts capped and --no-wait is set")
    return out("stop", "every account reached its weekly cap for this run")


def unmatched_keys(data: dict, week_per: dict[str, float]) -> list[str]:
    known = {
        str(k)
        for a in data.get("accounts", [])
        for k in (a.get("number"), a.get("email"), a.get("alias"))
        if k
    }
    return sorted(set(week_per) - known)


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--five-cap", type=float, default=95.0)
    p.add_argument(
        "--week-cap",
        action="append",
        metavar="PCT|ACCOUNT=PCT",
        help="weekly cap; repeat with ACCOUNT=PCT (slot number, email, or alias) per account",
    )
    p.add_argument(
        "--model",
        action="append",
        default=[],
        help="also count this model's weekly limit (cswap 'scoped' name, e.g. Fable)",
    )
    p.add_argument(
        "--no-wait",
        action="store_true",
        help="stop instead of pausing for a 5-hour reset",
    )
    args = p.parse_args()
    raw = subprocess.run(
        ["cswap", "list", "--json"], capture_output=True, text=True, check=True
    ).stdout
    data = json.loads(raw)
    week_base, week_per = parse_caps(args.week_cap, DEFAULT_WEEK_CAP)
    if bad := unmatched_keys(data, week_per):
        print(f"--week-cap names no cswap account: {', '.join(bad)}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            decide(
                data,
                args.five_cap,
                week_base,
                week_per,
                set(args.model),
                datetime.now(UTC),
                args.no_wait,
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
