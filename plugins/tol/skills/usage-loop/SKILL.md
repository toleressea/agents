---
name: usage-loop
description: Use when a long or repeating agent run must stay inside Claude plan usage limits across several cswap-managed accounts, when another skill or prompt should keep running overnight or "until done" without hitting a 5-hour or weekly limit, or when the user sets usage caps such as "pause at 95% of the 5-hour limit" or "only use 60% of the weekly limit today". Also applies when /usage-loop is named inside another prompt.
argument-hint: [--five-cap PCT] [--week-cap PCT|ACCOUNT=PCT] [--model NAME] [--no-wait] -- <skill or prompt>
allowed-tools: Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/gate.py:*), Bash(cswap switch:*), Bash(sleep:*), Bash(git branch --show-current)
---

# Usage loop

Run another skill or prompt in a loop. Before each unit of work, ask the gate script whether usage allows it. Switch accounts, pause until a 5-hour reset, or stop at the weekly cap. Every pause writes a handoff doc, so work resumes cleanly even after context compaction.

## Arguments

| Flag | Default | Meaning |
|---|---|---|
| `--five-cap` | 95 | Per-account 5-hour cap. |
| `--week-cap` | 98 | Weekly cap. `ACCOUNT=PCT` sets one account's cap (cswap slot number, email, or alias). Accounts without their own cap use the plain `--week-cap PCT` value, or 98. |
| `--model` | none | Also count that model's own weekly limit (cswap `scoped` name, e.g. `Fable`, any case). Pass it when the session runs on that model. |
| `--no-wait` | off | Stop instead of pausing for a 5-hour reset. Use it to spend only the 5-hour windows that are open now. |

Caps are absolute usage levels, not an amount to spend. `--week-cap 60` on an account already at 50% leaves 10 points. The caps hold for the whole run, even across midnight.

### Two ways in

The inner task is the work this skill wraps. Find it from how you were invoked:

| Invocation | Inner task |
|---|---|
| `/usage-loop --week-cap 60 -- /some-skill <args>` | The text after `--`. Load that skill with the Skill tool, then run it under the loop. |
| `/some-skill <args> and use /usage-loop to keep it running tonight` | The other skill already loaded this turn, with the rest of the prompt as its arguments. Load usage-loop with the Skill tool, but do not load the other skill again. Its instructions stay in charge of the work. This skill only adds the gate, the handoff, and the waits. |

Skills with `disable-model-invocation: true` cannot be loaded with the Skill tool. Run them only the second way. If the text after `--` names one, say so and give the user the second form to type.

In a prose invocation, map cap wording to flags with the table below. Time words such as "tonight", "overnight", or "until done" map to no flag, so the defaults apply. If the inner skill has a run-length input (rounds, iterations, a count) and the user gave no value, set it to its unlimited value, so the caps end the run.

| Prose | Flags |
|---|---|
| "60% of the weekly limit", "take it to 60% weekly" | `--week-cap 60` |
| "account 2 to 70%" | `--week-cap 2=70` |
| "pause at 90% of the 5-hour" | `--five-cap 90` |
| "on Fable", or the session runs on Fable | `--model Fable` |
| "just this 5-hour window", "don't wait for a reset" | `--no-wait` |

Before the first unit, tell the user in one message:

- the flags, and each account's current 5-hour and weekly usage from the first gate output;
- a suggestion to lower the caps when units are long or run in parallel. The gate checks between units, so a unit started just under a cap ends above it. Do not change the caps yourself;
- when the run may go unattended, the allow rules from Permissions below.

## The gate

```bash
python3 -I ${CLAUDE_SKILL_DIR}/scripts/gate.py <the caps flags, verbatim>
```

It reads `cswap list --json` and prints a JSON `decision`. Act on it exactly:

| decision | Do |
|---|---|
| `go` | Run the next unit of work. |
| `switch` | `cswap switch <account>`, then run the next unit. |
| `pause` | Write the handoff, then wait `waitSeconds` (see Waiting). On wake, re-run the gate. `unreadable: true` means cswap could not read some accounts' usage. Stop after three such pauses in a row. |
| `stop` | Run the inner skill's own finishing steps that start no new agents (status, report). Then write the handoff, report, and end the run (see Ending). |

The gate is the only judge of usage. Do not estimate percentages, and do not skip a check because the last one was low. The gate runs only between units. After `pause` or `stop`, start no new unit, even "to finish this one thing".

If the gate exits with code 2, a `--week-cap` key names no account. Stop and report its error. On any other failure (cswap error, non-zero exit), treat it as `pause` with a 15-minute wait. Stop after three failures in a row.

## Loop

1. Parse the caps and the inner task. Look in `~/.agents/usage-loop/` for a handoff whose "Inner task" line matches this task. If one exists, read it and resume from its "Next step".
2. Run the gate.
3. On `go` or after `switch`, do one unit of the inner task.
   - If the inner skill defines its own unit (a round, a ticket), that is the unit. A started unit runs all its steps, including verification. When that unit can run for hours (a ticket through review and test), also run the gate before each agent dispatch inside it, and dispatch nothing new after a `pause`.
   - Otherwise a unit is the smallest step that leaves clean state: one failing test, one subagent dispatch, one commit.
   - Bookkeeping steps (ledger writes, reading reports, status checks) are not units and need no gate. A wait on the user is not a usage pause. Follow the inner skill's own rule for it.
   - Subagents already running cannot be paused. On `pause` or `stop`, wait for running subagents to return, record their results, then write the handoff.
4. Repeat from step 2 until the inner task reports done, or the gate says `stop`.
5. When the inner task is done, delete the handoff and give the final summary with the last gate output. Done wins when the gate says `stop` at the same time. Then end the run (see Ending).

## Handoff

Path: `~/.agents/usage-loop/<slug>.md`, where the slug is the inner skill's name plus its main argument, in kebab case (for example `review-auth-refactor`). Write it before the first unit, and overwrite it after every unit and on every pause or stop. A session can die between pauses, so the handoff must always be current. It is a resume point, not a log.

If the inner skill keeps its own run state (a ledger or run file), update that state the way the inner skill says to. Then make the handoff's "Done" section a path to that state file, and set "Next step" to the inner skill's own resume step. Do not copy the inner state into the handoff.

```markdown
# <slug>
Resume with: <exact prompt to type in a new session: the original prompt, or the inner skill's own resume form>
- Inner task: <exact skill or prompt, with args>
- Caps: <exact gate flags>
- Gate: <decision, reason, resumeAt> as of <UTC time>
- Repo / branch: <repo>, <branch>, uncommitted: <yes/no, which files>
## Done
<units finished, with PR/ticket/commit refs>
## Next step
<the one unit to run on resume, concrete enough to start without re-reading the conversation>
## Open questions
<anything blocked on the user>
```

Leave partial edits in the working tree, uncommitted. List each partial file in the handoff with what is left to do. Do not revert, stash, commit, or push to tidy up. Commit or push only if the inner task or the user already allows it.

The caps are the user's decision. A deadline or a nearly-uncapped account is not a reason to raise them. Report the pause with `resumeAt`, and say which flag the user would change to go further.

## Waiting

Pick by mode:

- **Inside `/loop` dynamic mode:** `ScheduleWakeup` with `delaySeconds = min(waitSeconds, 3600)` and the same `/loop` prompt.
- **Otherwise, including `claude -p`:** a background Bash `sleep` with `run_in_background: true` and `timeout: 7200000`, sleeping `min(waitSeconds, 7000)` seconds. Its exit re-invokes you, and `claude -p` waits for it before exiting. A foreground `sleep` is blocked.
- **No background tasks (`claude --bare -p`):** write the handoff with `resumeAt` and exit. An outside runner restarts the task.

Each wake costs one short turn. Do nothing in it except run the gate and act on the result. The gate recomputes `waitSeconds` from the clock, so an early wake just waits again.

A background sleep and background subagents end with the session, including a restart of the Claude Code process. Nothing wakes the run after that: the user, or an outside runner, resumes it with the handoff's "Resume with" line.

On resume, re-read the handoff and run `git branch --show-current`. If the branch differs from the handoff, stop and ask. Otherwise run the gate before any work.

## Ending

- In `/loop` dynamic mode, call `ScheduleWakeup` with `stop: true`. Ending a turn without it schedules a fallback wakeup about 20 minutes later.
- If the `PushNotification` tool is available, send one on `stop`.

## Permissions

The `allowed-tools` grant covers only the turn that loads this skill. Later wakes can hit a permission prompt, and an unattended run stalls on it until someone answers. Unless the session runs in a mode that approves these commands already, the user needs these allow rules in their Claude Code settings:

```json
"Bash(python3 -I */usage-loop/scripts/gate.py *)",
"Bash(cswap switch *)",
"Bash(sleep *)",
"Bash(git branch --show-current)"
```

