---
name: unity-cli
description: Drive the running Unity Editor from the terminal via the Unity CLI and the com.unity.pipeline package. Read the console, enter or exit Play mode, inspect and edit the open scene, GameObjects, components, prefabs, scripts, assets, materials and animation, run tests, take screenshots, and build. Use whenever you need live Editor state or to perform Editor actions rather than inferring from source alone. Requires the Unity Editor open with the project.
---

# Driving Unity from the terminal (Unity CLI)

The Unity CLI (`unity`) talks to the running Editor through the **`com.unity.pipeline`** package, which exposes a local HTTP/JSON server inside the Editor. It is the supported way to see and act on live Editor state (console errors, Play mode, scene contents, tests, screenshots) without a human clicking.

## Prerequisites

- **The Editor is open on this project.** If it isn't, every command fails. Check with `unity status`. It prints the port, project path, Editor version and PID when connected, e.g. `7800  ready  <project path>  6000.3.26f1  8000`.
- `unity` must be on PATH. On Windows, `winget install --id Unity.CLI -e` puts it at `"$env:LOCALAPPDATA\Microsoft\WindowsApps\unity.exe"`. Call it by that full path if PATH hasn't picked it up yet.

## Command shape

```
unity status                        # connected Editor(s): port, project, version, PID
unity command                       # list every available command
unity list                          # same, as a Name / Group / Description table
unity command <name> [args...]      # run one command
unity command <name> --help         # args + return type for one command
```

Output is a table whose `Result` column is JSON. Parse it, don't eyeball it.

## The commands you'll actually use

**Observe (read-only)**
- `console`: captured Editor console output (tail, level filtering). `console_status` for counts only.
- `editor_status`: play mode, compiling, domain reload, project path
- `get_scene_hierarchy`: GameObject tree of the open scene, with `instanceId` / `hierarchyPath` handles
- `find_gameobjects`: find by name, tag, component or hierarchy path
- `get_component_properties`, `get_serialized_fields`: read component state
- `get_performance_stats`, `list_open_scenes`, `get_selection`
- `find_assets`, `read_text_file`, `get_import_settings`

**Act (Editor state)**
- `editor_play` / `editor_stop` / `editor_pause`: Play mode. **Always `editor_stop` when done.**
- `create_gameobject` / `create_gameobjects`, `delete_gameobject`, `set_transform`, `set_parent`, `rename_gameobject`, `set_active`, `set_tag`, `set_layer`
- `add_component` / `remove_component`, `set_component_properties`, `set_serialized_field`
- `create_script`, `attach_script`, `write_text_file`
- `create_prefab`, `instantiate_prefab`, `save_prefab_contents`, `apply_prefab_overrides`
- `save_scene` / `save_all`, `open_scene`, `create_scene`

**Verify**
- `recompile`, then poll `recompile_status`
- `list_tests`, then `save_all`, then `run_tests`, then poll `test_status`. Always `save_all` first: with a scene left unsaved, the test runner opens a modal save dialog and every CLI call times out. `run_tests` runs EditMode and PlayMode by default (`--mode all|editor|playmode`).
- `screenshot`, `capture_game_view`, `capture_scene_view`
- `menu`: run an Editor menu item by path
- `eval` / `eval_file`: run C# in the Editor without a domain reload (Roslyn)

**Async pattern:** long operations return immediately. Kick off, then poll the matching `*_status` (`build_status`, `test_status`, `recompile_status`, `*_bake_status`, `package_status`, `audit_status`).

## Project verbs and running players

- A project can add its own commands as `[CliCommand]` statics. `unity command --tag <tag>` lists the ones with that tag. They exist in the Editor and in development builds only.
- A development build runs its own server: `unity command --runtime-path <build folder> <verb>`. Players have a smaller built-in set than the Editor: **no `wait_for`, no `screenshot` / `capture_game_view`**, and `eval` sees game types only through reflection. Poll a project verb for state, and give the project its own screenshot verb if it needs one.
- `build` from a build profile (`--profileName "<profile>"`) also needs `--options '["Development"]'` on 6000.3, or the pipeline does not bake its server config and the player never answers.
- `capture_game_view --save_path` resolves a relative path under `Assets/`. Always pass an absolute path outside the repo.

## Windows / PowerShell gotcha: `eval` quoting

Inner double quotes get mangled between PowerShell, the CLI and the server, so `eval` code containing string literals arrives broken. Either avoid quotes (`unity command eval --code 'Debug.Log(42);'`) or, for anything real, write a `.cs` file and use `eval_file`.

## Guardrails

- Destructive commands require `confirm=true` (`delete_asset`, `clear_*`, `package_remove`, `switch_build_target`, and others). Prefer `dry_run=true` first.
- Never leave the Editor in Play mode. Finish with `editor_stop`.
- A new script's type does not exist until a recompile completes: call `recompile`, poll `recompile_status`, then `attach_script`.
- **Always pass `--result-only`.** The default envelope can report `success: true` for a call that actually failed: `run_tests` with an invalid `--filter_type` returns `0/0 passed`, which reads as a green run. Valid filter types are `testName`, `assembly`, `category`. There is no regex option.
- **On `EDITOR_TIMEOUT`**, find out why before retrying: a modal dialog in the Editor, a compile or test run in progress, or a blocked CLI queue. Tell the operator about a dialog. Do not wait out a long timeout on one.
- Asset refresh (regenerating `.meta` files after writing assets) is `menu --path "Assets/Refresh"`.

## Typical loop

```
unity command editor_play
sleep 5
unity command console        # read runtime errors
unity command editor_stop
```
