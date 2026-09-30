#!/usr/bin/env python3
"""Install this skill's Codex roles into a Moneyfesting i18n worktree."""

import argparse
import os
import re
import subprocess
import tempfile
import tomllib
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / ".codex/agents"
MODEL_EFFORTS = {
    "gpt-6-astra": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "gpt-6-sol": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "gpt-6-luna": {"low", "medium", "high", "xhigh", "max"},
    "gpt-5.6-sol": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "gpt-5.6-terra": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "gpt-5.6-luna": {"low", "medium", "high", "xhigh", "max"},
    "gpt-5.5": {"low", "medium", "high"},
}


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git could not inspect the target")
    return result.stdout.strip()


def check_worktree(root):
    if not root.is_dir() or root.is_symlink() or root.absolute() != root.resolve():
        raise ValueError("--app-root must be a real worktree directory, not a symlink")
    if Path(git(root, "rev-parse", "--show-toplevel")) != root:
        raise ValueError("--app-root must name the worktree root")
    lines = git(root, "worktree", "list", "--porcelain").splitlines()
    primary = Path(next(line[9:] for line in lines if line.startswith("worktree "))).resolve()
    common_dir = Path(git(root, "rev-parse", "--path-format=absolute",
                          "--git-common-dir")).resolve()
    if primary.name != "Moneyfesting" or common_dir != primary / ".git":
        raise ValueError("target is not a Moneyfesting linked worktree")
    if root.parent != primary.parent / "Moneyfesting-wt" or root == primary:
        raise ValueError("target must be Moneyfesting-wt/<topic>, away from the main checkout")
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not re.fullmatch(r"i18n/[^/]+(?:/[^/]+)*", branch):
        raise ValueError("target branch must start with i18n/")


def source_roles():
    paths = sorted(SOURCE.glob("*.toml"))
    if len(paths) != 9:
        raise ValueError(f"expected nine source roles, found {len(paths)}")
    roles = {}
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"source role is a symlink: {path.name}")
        data = path.read_bytes()
        role = tomllib.loads(data.decode("utf-8"))
        for field in ("name", "description", "developer_instructions"):
            if not isinstance(role.get(field), str) or not role[field].strip():
                raise ValueError(f"{path.name}: {field} must be nonempty text")
        if role["name"] != path.stem or role["name"] in roles:
            raise ValueError(f"{path.name}: role name must match its unique filename")
        model = role.get("model")
        effort = role.get("model_reasoning_effort")
        if (not isinstance(model, str) or not isinstance(effort, str)
                or effort not in MODEL_EFFORTS.get(model, set())):
            raise ValueError(f"{path.name}: unsupported model or reasoning effort")
        if role.get("sandbox_mode") != "read-only":
            raise ValueError(f"{path.name}: sandbox_mode must be read-only")
        roles[role["name"]] = data
    return roles


def check_destination(root, roles):
    codex = root / ".codex"
    destination = codex / "agents"
    for directory in (codex, destination):
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise ValueError(f"unsafe destination directory: {directory}")
    states = {}
    for name, data in roles.items():
        path = destination / f"{name}.toml"
        if path.is_symlink():
            raise ValueError(f"unsafe destination symlink: {path}")
        if not path.exists():
            states[name] = "new"
        elif path.is_file() and path.read_bytes() == data:
            states[name] = "unchanged"
        else:
            states[name] = "conflicting"
    known_files = {f"{name}.toml" for name in roles}
    unrelated = (sorted(path.name for path in destination.iterdir()
                        if path.name not in known_files) if destination.exists() else [])
    return destination, states, unrelated


def install(destination, roles, states):
    destination.mkdir(parents=True, exist_ok=True)
    for name, state in states.items():
        if state != "new":
            continue
        path = destination / f"{name}.toml"
        with tempfile.NamedTemporaryFile(dir=destination, prefix=".agent-",
                                         delete=False) as temporary:
            temporary.write(roles[name])
            temporary_name = temporary.name
        try:
            os.link(temporary_name, path)
        finally:
            os.unlink(temporary_name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True, help="Moneyfesting i18n worktree")
    parser.add_argument("--apply", action="store_true", help="install absent roles after preflight")
    args = parser.parse_args()
    try:
        root = args.app_root.expanduser().absolute()
        check_worktree(root)
        roles = source_roles()
        destination, states, unrelated = check_destination(root, roles)
        for name, state in states.items():
            print(f"{state}: {name}.toml")
        for name in unrelated:
            print(f"unrelated (preserved): {name}")
        if "conflicting" in states.values():
            raise ValueError("existing role differs; resolve conflicts before applying")
        if args.apply:
            install(destination, roles, states)
            print("installed absent roles")
        else:
            print("preflight only; use --apply to install")
    except (OSError, ValueError, StopIteration, UnicodeError, tomllib.TOMLDecodeError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
