from pathlib import Path
import re

ROOT = Path(r"c:\Users\justi\Desktop\Coding Projects\mini-codex")
GS = ROOT / "ai_repo_tools" / "tools" / "game_systems"
MAIN = ROOT / "ai_repo_tools" / "main.py"


def subcategory(name: str) -> str:
    if name.startswith("shop_"):
        return "shops"
    if name.startswith("monster_"):
        return "monsters"
    if name.startswith("character_"):
        return "character"
    if name.startswith("combat_"):
        return "combat"
    if name.startswith("rest_"):
        return "rest"
    if name.startswith("saveload_"):
        return "saveload"
    if name.startswith("ui_"):
        return "ui"
    if name.startswith("rpg_"):
        return "builders"
    if name in {"game_orchestrator", "v2_branch_probe_tool"}:
        return "orchestration"
    return "core"


def is_tool_dir(p: Path) -> bool:
    return p.is_dir() and (p / "command.py").exists() and (p / "__init__.py").exists()


# 1) Move direct tool dirs under subsystem subfolders
moved = []
kept = []
for child in GS.iterdir():
    if child.name == "__pycache__":
        continue
    if child.is_dir() and not is_tool_dir(child):
        # likely existing subcategory folder
        continue
    if is_tool_dir(child):
        sub = subcategory(child.name)
        target_parent = GS / sub
        target_parent.mkdir(parents=True, exist_ok=True)
        target = target_parent / child.name
        if target.exists():
            kept.append((child.name, sub))
            continue
        child.rename(target)
        moved.append((child.name, sub))

# 2) Build index of all tools now under subcategories
name_to_sub = {}
for subdir in GS.iterdir():
    if not subdir.is_dir() or subdir.name == "__pycache__":
        continue
    for maybe_tool in subdir.iterdir():
        if is_tool_dir(maybe_tool):
            name_to_sub[maybe_tool.name] = subdir.name

# 3) Regenerate each subcategory __init__.py
for sub in sorted({v for v in name_to_sub.values()}):
    sub_path = GS / sub
    tool_names = sorted(
        [p.name for p in sub_path.iterdir() if is_tool_dir(p)]
    )
    lines = [f"# game_systems.{sub} tools", ""]
    for t in tool_names:
        lines.append(f"from .{t} import cmd_{t}")
    lines.append("")
    lines.append("__all__ = [")
    for t in tool_names:
        lines.append(f"    'cmd_{t}',")
    lines.append("]")
    lines.append("")
    (sub_path / "__init__.py").write_text("\n".join(lines), encoding="utf-8")

# 4) Regenerate top-level game_systems __init__.py
subcats = sorted({v for v in name_to_sub.values()})
lines = [
    '"""Game systems tool namespace with subsystem categories."""',
    "",
]
for sub in subcats:
    lines.append(f"from . import {sub}")
lines.append("")
lines.append("__all__ = [")
for sub in subcats:
    lines.append(f"    '{sub}',")
lines.append("]")
lines.append("")
(GS / "__init__.py").write_text("\n".join(lines), encoding="utf-8")

# 5) Rewrite imports in main.py
main_txt = MAIN.read_text(encoding="utf-8")
for name, sub in sorted(name_to_sub.items()):
    old = f"from tools.game_systems.{name} import cmd_{name}"
    new = f"from tools.game_systems.{sub}.{name} import cmd_{name}"
    main_txt = main_txt.replace(old, new)
MAIN.write_text(main_txt, encoding="utf-8")

print(f"MOVED={len(moved)}")
print(f"TOTAL_TOOLS={len(name_to_sub)}")
print(f"SUBCATEGORIES={','.join(subcats)}")
