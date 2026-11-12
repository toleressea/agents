---
name: test
description: Test a change or reproduce a bug through configurable stages (static, unit, integration, smoke, e2e, or the repo's own), each bound to the repo's command, another skill, or plain instructions, per user, per repo, or per run. Use when asked to test, verify, or prove a change works, or when another skill needs a test step.
argument-hint: "[dry-run] [key=value ...] [what to test]"
shell: bash
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/bin/layers.py" *)
---

# /tol:test

Arguments: $ARGUMENTS

## Config

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/layers.py" tol test "${CLAUDE_SKILL_DIR}" "${CLAUDE_PROJECT_DIR}"`

If the block above is missing (another agent, or the command did not run), read
`config.toml` next to this file, then `~/.agents/config/tol/test.toml` and
`.agents/config/tol/test.toml` in the repo, and merge them as the convention says.

## Steps

1. **Target.** What to test: the arguments, else the uncommitted changes plus
   commits not on the default branch. For a bug, the target is a reproduction:
   the stage that reproduces it must fail before a fix and pass after.
2. **Stages.** Run each stage in `order` that is still in the effective config.
   - Run it inline, unless it is bound to a skill: then invoke that skill with the
     target and the stage's instructions.
   - Record `pass`, `fail`, or `none-found`, the command or method, and evidence.
   - Never mark a stage `pass` without output that shows it ran.
   - `fail_fast = true`: stop at the first `fail`.
3. **Fix.** `off`: skip. `ask`: offer fixes for the failures and wait.
   `apply`: fix, rerun the failed stage and every stage before it, up to `rounds` times.
4. **Report.** A table: stage, result, command or method, evidence. Then one line:
   `tests: pass` only if no stage failed, else `tests: fail` with the first failure.
