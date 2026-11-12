---
name: review
description: Review a code change through configurable lenses (correctness, tests, simplicity, security, docs, or the repo's own), verify each finding, and report. Each lens can be bound to another review skill or to plain instructions, per user, per repo, or per run. Use when asked to review a diff, a branch, or uncommitted changes, or when another skill needs a review step.
argument-hint: "[dry-run] [key=value ...] [free text]"
shell: bash
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/bin/layers.py" *)
---

# /tol:review

Arguments: $ARGUMENTS

## Config

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/layers.py" tol review "${CLAUDE_SKILL_DIR}" "${CLAUDE_PROJECT_DIR}"`

If the block above is missing (another agent, or the command did not run), read
`config.toml` next to this file, then `~/.agents/config/tol/review.toml` and
`.agents/config/tol/review.toml` in the repo, and merge them as the convention says.

## Steps

1. **Scope.** Build the diff the `scope` slot describes. If it is empty, say so and stop.
2. **Lenses.** Run every lens in the effective config.
   - `parallel = true`: one subagent per lens, all in one message. Give each the
     diff (or how to get it), the lens binding, and the output format below.
   - `parallel = false`: run the lenses in order yourself.
   - Each lens returns findings: `file:line | severity | claim | evidence`.
     A lens with no findings says `none`.
3. **Verify.** For each round in `verify.rounds`, give every finding to a fresh
   agent bound to the `verify` slot. It reads the code and returns
   `confirmed` or `rejected` with its reason. Drop rejected findings. Merge duplicates
   across lenses and keep the lens names.
4. **Report.** Follow the `report` slot. Name the lens of each finding, and list
   rejected findings in one short line each so the user sees what was dropped.
5. **Fix.** `off`: stop. `ask`: offer to fix the confirmed findings and wait.
   `apply`: fix them, then show the diff.
