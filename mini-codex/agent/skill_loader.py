"""
skill_loader.py — Discovers and matches .github/skills/*/SKILL.md files to the
current agent goal.  Results are stored in state.artifacts["active_skills"] so the
agent loop, evaluator, and any downstream consumer can reference them.
"""
import os
import re
from typing import List, Dict, Any

# Skills root relative to this file: mini-codex/.github/skills/
_DEFAULT_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", ".github", "skills")
)

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_FIELD_RE = re.compile(r'^([\w-]+):\s*"?([^"\n]*)"?\s*$', re.MULTILINE)

# Known aish tool names that may appear in skill Procedure sections.
_KNOWN_TOOLS = {
    "repo_map", "ai_read", "fast_process", "fast_analyze", "fast_prepare",
    "fast_evaluate", "test_select", "cmd_run", "env_check", "lint_check",
    "friction_summarizer", "tool_audit", "toolmaker", "agent_audit",
    "agent_improver",
}


def _parse_frontmatter(text: str) -> Dict[str, str]:
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    return dict(_FIELD_RE.findall(m.group(1)))


def discover_skills(skills_dir: str = None) -> List[Dict[str, str]]:
    """Return one entry per SKILL.md found under skills_dir."""
    base = skills_dir or _DEFAULT_SKILLS_DIR
    if not os.path.isdir(base):
        return []
    results = []
    for folder in sorted(os.listdir(base)):
        path = os.path.join(base, folder, "SKILL.md")
        if not os.path.isfile(path):
            continue
        try:
            text = open(path, encoding="utf-8").read()
            meta = _parse_frontmatter(text)
            results.append(
                {
                    "name": meta.get("name", folder),
                    "description": meta.get("description", ""),
                    "folder": folder,
                    "path": path,
                    "_text": text,
                }
            )
        except Exception:
            pass
    return results


def _skill_words(skill: Dict) -> set:
    """
    Tokenise a skill's identifiers into individual words.
    Hyphens and underscores are treated as word separators so that
    'tool-audit-enhancer' contributes {'tool', 'audit', 'enhancer'}.
    """
    raw = f"{skill['folder']} {skill['name']} {skill['description']}"
    return set(re.sub(r"[^a-z0-9 ]", " ", raw.lower()).split())


def _score(goal_words: set, skill: Dict) -> int:
    return len(goal_words & _skill_words(skill))


def _parse_tool_hints(skill_text: str) -> List[str]:
    """Extract known aish tool names mentioned in the Procedure section."""
    proc_match = re.search(r"## Procedure\n(.*?)(?=\n##|\Z)", skill_text, re.DOTALL)
    if not proc_match:
        return []
    body = proc_match.group(1).lower()
    # Replace hyphens/underscores with spaces for token boundary matching
    body = body.replace("-", " ").replace("_", " ")
    return [t for t in _KNOWN_TOOLS if t.replace("_", " ") in body]


def match_skills(goal: str, skills: List[Dict], top_n: int = 5) -> List[Dict[str, str]]:
    """Return skills most relevant to goal, ranked by keyword overlap."""
    goal_words = set(re.sub(r"[^a-z0-9 ]", " ", goal.lower()).split())
    # Remove very short / stop words that would over-match
    goal_words -= {"the", "a", "an", "in", "of", "to", "for", "and", "or", "is", "it"}
    scored = [(s, _score(goal_words, s)) for s in skills]
    scored = [(s, sc) for s, sc in scored if sc > 0]
    scored.sort(key=lambda x: -x[1])
    return [s for s, _ in scored[:top_n]]


def load_skills_for_goal(
    goal: str, skills_dir: str = None, top_n: int = 5
) -> List[Dict[str, str]]:
    """
    Discover all skills and return the top_n most relevant to `goal`.
    Each entry has: name, description, tool_hints, content.
    """
    all_skills = discover_skills(skills_dir)
    matched = match_skills(goal, all_skills, top_n=top_n)
    return [
        {
            "name": s["name"],
            "description": s["description"],
            "tool_hints": _parse_tool_hints(s["_text"]),
            "content": s["_text"],
        }
        for s in matched
    ]


def get_skill_tool_hints(artifacts: Dict[str, Any]) -> List[str]:
    """
    Return a deduplicated, ordered list of tool names recommended by the
    currently active skills.  Call from the planner with state.artifacts.
    """
    seen: set = set()
    hints: List[str] = []
    for skill in artifacts.get("active_skills", []):
        for tool in skill.get("tool_hints", []):
            if tool not in seen:
                seen.add(tool)
                hints.append(tool)
    return hints
