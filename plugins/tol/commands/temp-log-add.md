---
description: Add temporary debug logs, tagged for one-step removal, to investigate the current problem
argument-hint: "[marker, default TEMPLOG]"
---

Add temporary debug logs to the files relevant to the problem under investigation. Every line you add carries one marker so `/tol:temp-log-remove` can find and delete all of them later.

## Marker

- Use `$ARGUMENTS` as the marker if given, else `TEMPLOG`.
- If the project has its own temp-log convention (a `Temp` log category, a project AGENTS.md rule), use that instead and say so.
- Put the marker in every added line: in the log call itself (a category or a message prefix like `[TEMPLOG]`), or as a trailing comment (`// TEMPLOG`). A throttle field or helper you add gets the marker comment too.

## Instructions

1. Identify the files relevant to the current problem from the conversation.
2. Use the project's existing logger. Add logs at:
   - entry of key methods, with key parameters
   - state changes, decision branches, and early returns (log why it returns)
   - before and after the operation under suspicion, including network or IPC calls
   - exception and error paths
3. In hot paths (per-frame updates, tight loops), throttle: log at most every few seconds, or only the first N iterations.
4. Log values, not just events: `ProcessDamage: target=<name>, amount=<n>, armor=<n>`, not `Processing damage`.
5. Report the marker and the files you touched.
