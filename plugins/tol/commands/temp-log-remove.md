---
description: Remove every temporary debug log added by /tol:temp-log-add
argument-hint: "[marker, default TEMPLOG]"
---

Remove every temporary debug log tagged with the marker.

1. Marker: `$ARGUMENTS` if given, else `TEMPLOG` (or the project's own temp-log convention, if `/tol:temp-log-add` used one).
2. Find every occurrence: `git grep -n '<marker>'`. Include untracked files: `git grep -n --untracked '<marker>'`.
3. In each file, remove the tagged log calls and any throttle fields or helpers added for them. Remove an import or `using` only if nothing else uses it now.
4. Run `git grep '<marker>'` again. It must return nothing.
5. Report the files changed and the number of lines removed.
