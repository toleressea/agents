## Composable skill convention

This skill is configured in layers. The block below is the resolved result of the
shipped, user, and repo layers, already merged by `bin/layers.py`. Do not re-merge it.

1. If any line starts with `CONFIG ERROR`, stop. Show the errors and the file to fix.
2. Apply the invocation layer yourself, on top of the resolved config:
   - `key.path=value` tokens set that key (`lenses.security=off`, `verify.rounds=2`).
   - `off` removes an entry. An empty string unsets a binding field.
   - Free text changes a config key only when it names that slot or key ("turn off
     the docs lens", "verify twice"). Anything else is a behavior note: list it on its
     own line and leave every key at its resolved value.
   - `dry-run` is not config: it means stop after step 3.
3. Print the effective config before any work: one line per key with its source
   (`shipped`, `user`, `repo`, `invocation`). Free-text requests get their own line.
4. A slot binding has `skill`, `instructions`, or both.
   - `skill` only: invoke that skill for the slot.
   - `instructions` only: do the slot yourself, following them.
   - both: invoke the skill, and pass the instructions to steer it.
   - A bound skill that is not installed stops the run. Never fall back silently.
5. The slot contract (input, done-when, output) is in the shipped config comments
   and in this skill's steps. A skill that does not know the contract still gets
   the slot's needs in its arguments, and you extract the output from what it returns.
6. This skill owns loops (`rounds`) and the hand-off between slots. A block never
   calls the next slot.
