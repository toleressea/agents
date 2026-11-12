---
name: watch-session
description: Watch another Claude Code session by its session ID while it works. Follows its transcript live, verifies what it claims, collects findings (problems, wasted effort, skill gaps, good patterns) on a live dark-mode page, then recommends fixes and waits for the operator's approval before implementing them. Use when the operator gives a session ID and asks to watch, monitor or review a running or finished session.
argument-hint: "<session id> [what to watch for]"
---

# /watch-session

Watch a session the operator names, find what goes wrong or could go better, and fix nothing until the operator approves. You observe; the watched session does the work.

## Start

1. Find the transcript: `~/.claude/projects/*/<session id>.jsonl` (a worktree session lives under its own project folder). Its agents' transcripts are in `<session id>/subagents/agent-<id>.jsonl` next to it.
2. Catch up first: read the first user message (the task) and the tail, and tell the operator in a few lines what the session is doing and where it stands.
3. Watch folder: `~/.agents/watch/<session id>/`. Copy `assets/findings.html` there, write `findings.json` (below), and serve the folder detached so it outlives the harness's time limit for background tasks:
   - Windows (PowerShell): `Start-Process python -ArgumentList '-I','-m','http.server','<free port>','--bind','127.0.0.1','--directory','<watch folder>' -WindowStyle Hidden -PassThru`
   - macOS / Linux: `nohup python3 -I -m http.server <free port> --bind 127.0.0.1 --directory '<watch folder>' >/dev/null 2>&1 & echo $!`

   Give the operator `http://127.0.0.1:<port>/findings.html` and the PID. Stop it at the end with `Stop-Process -Id <pid>` or `kill <pid>`.
4. Start the Monitor tool on `python -I -u <this skill>/scripts/watch.py <transcript> <watch folder> [state.json]` (`python3` on macOS / Linux) with the longest timeout. Pass the run's `state.json` when the session runs `/orchestrate`, so phase changes show. Re-arm the monitor each time it expires, and restart it after a fix to the script.

## While it runs

- **Verify before you report.** A session's status messages are its own view and can be stale or wrong. Check claims against the agent transcripts, `git log` / `git branch --contains`, the files, and live state. Read-only git only.
- **Record each finding at once** in `findings.json`, with the event's real time from the transcript, never an estimate. Say each new finding in chat in a sentence or two.
- **Correct yourself in place.** When later evidence changes a finding, rewrite it on the page and say so, rather than adding a contradicting one.
- Record good patterns too (positive findings), so a fix doesn't remove what works.
- Stay quiet on routine events. Speak when something goes wrong, a phase changes, or the operator needs to act now (for example, their uncommitted work is at risk).
- Never message, steer or edit the watched session or its files unless the operator asks. Their dry run is the evidence.

## When it ends

1. Stop the monitor. Mark the page title "run finished".
2. Give a short summary of the result, then walk the findings with the operator one topic at a time, most serious first, each with a recommended fix.
3. **Wait for the operator's approval before implementing anything.** They may cut, change or add fixes.
4. Implement the approved fixes as discrete commits, under the repo's own gates (its AGENTS.md or CLAUDE.md), and set each finding's `status` to its commit.

## findings.json

```json
{
  "title": "what is being watched",
  "session": "<session id>",
  "run": "optional run name",
  "status": "optional, e.g. run finished",
  "findings": [
    {"n": 1, "area": "short tag", "seen": "18:54 UTC", "title": "", "detail": "what happened, with evidence",
     "fix": "recommended fix", "status": "open | fixed <sha> | positive, no change"}
  ]
}
```

Edit it with Python's `json` module and write it whole. The page reloads it every 2 s and shows the newest first, with a green outline on findings added since the page loaded.

🤖 Generated with stochastic optimism by clankers 🤖
