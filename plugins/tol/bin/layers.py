"""Resolve a composable skill's config layers and print them for injection.

usage: layers.py <plugin> <skill> <skill dir> <project dir>

Prints the convention text, then the merged config as flat `key = value  # source`
lines. Always exits 0, because a failing `!` injection aborts the whole skill.
Problems are printed as `CONFIG ERROR:` lines, and the skill stops on them.
"""

import json
import sys
import tomllib
from pathlib import Path

OFF = "off"
BINDING = {"skill", "instructions", "args"}  # any slot may set these


def load(path):
    if not path.is_file():
        return None, None
    try:
        with open(path, "rb") as f:
            return tomllib.load(f), None
    except (OSError, tomllib.TOMLDecodeError) as e:
        return None, f"{path}: {e}"


def merge(base, layer, source, sources, extensible, errors, prefix=""):
    """Deep-merge layer into base in place. Tables merge, everything else replaces."""
    for key, value in layer.items():
        path = f"{prefix}{key}"
        free = key in BINDING or any(prefix.startswith(e + ".") for e in extensible)
        if key not in base and not free:
            errors.append(f"{source}: unknown key `{path}`")
            continue
        if value == OFF and isinstance(
            base.get(key), dict
        ):  # "off" is a plain value for scalars
            base.pop(key)
            for k in [k for k in sources if k == path or k.startswith(path + ".")]:
                del sources[k]
            sources[path] = f"{source} (off)"
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value, source, sources, extensible, errors, path + ".")
        else:
            base[key] = value
            for k in [k for k in sources if k.startswith(path + ".")]:
                del sources[k]
            mark(value, path, source, sources)


def mark(value, path, source, sources):
    if isinstance(value, dict):
        for k, v in value.items():
            mark(v, f"{path}.{k}", source, sources)
    else:
        sources[path] = source


def flatten(table, prefix=""):
    for key, value in table.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            yield from flatten(value, path + ".")
        elif value != "":  # an empty string unsets a binding field
            yield path, value


def resolve(plugin, skill, skill_dir, project_dir, home=None):
    home = Path(home or Path.home())
    layers = [
        ("shipped", Path(skill_dir) / "config.toml"),
        ("user", home / ".agents" / "config" / plugin / f"{skill}.toml"),
        ("repo", Path(project_dir) / ".agents" / "config" / plugin / f"{skill}.toml"),
    ]
    errors, sources, config, used = [], {}, {}, []
    for name, path in layers:
        data, err = load(path)
        if err:
            errors.append(err)
        if data is None:
            continue
        used.append(f"{name}: {path}")
        if name == "shipped":
            config = data
            mark(data, "", name, sources)
            sources = {k.lstrip("."): v for k, v in sources.items()}
        else:
            merge(
                config, data, name, sources, set(config.get("extensible", [])), errors
            )
    if not used or not used[0].startswith("shipped"):
        errors.append(f"shipped config missing: {layers[0][1]}")
    return config, sources, used, errors


def render(config, sources, used, errors):
    out = ["layers read:"] + [f"  {u}" for u in used]
    out += [f"CONFIG ERROR: {e}" for e in errors]
    out.append("")
    out.append("resolved config:")
    for path, value in flatten({k: v for k, v in config.items() if k != "extensible"}):
        out.append(f"{path} = {json.dumps(value)}  # {sources.get(path, '?')}")
    offs = sorted(k for k, v in sources.items() if v.endswith("(off)"))
    out += [f"{k} = off  # {sources[k]}" for k in offs]
    return "\n".join(out)


def main(argv):
    if len(argv) != 5:
        print(
            "CONFIG ERROR: usage: layers.py <plugin> <skill> <skill dir> <project dir>"
        )
        return
    convention = (
        Path(__file__).resolve().parent.parent / "conventions" / "composable.md"
    )
    if convention.is_file():
        print(convention.read_text(encoding="utf-8"))
    print("```")
    print(render(*resolve(*argv[1:5])))
    print("```")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        main(sys.argv)
    except Exception as e:  # noqa: BLE001  # never abort the skill; make the failure visible instead
        print(f"CONFIG ERROR: layers.py crashed: {e!r}")
