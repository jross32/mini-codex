# Stderr Self-Correction Hook v0 (Safe Scaffold)

## Goal
Provide suggestion-first assistance when a command fails, without autonomous command execution.

## Safe v0 Shape
- Input: captured stderr text plus failing command string.
- Classify: map stderr to a lightweight category.
- Suggest: emit one investigation suggestion and ask for user confirmation.
- No auto-fix loop.
- No recursive shell automation.

## Current Scaffold
- Script: `ai_repo_tools/stderr_hook_v0.py`
- Output: JSON payload with:
  - `category`
  - `title`
  - `suggested_action`
  - `suggested_command`
  - `prompt`
  - `mode: suggestion-first`
  - `auto_execute: false`

## Integration Path (Later)
- Caller captures stderr when a command fails.
- Caller invokes this helper.
- UI/agent shows suggestion and asks user whether to run follow-up command.
- Follow-up command only runs on explicit user approval.

## Out of Scope
- Autonomous retries.
- Auto-editing files from stderr without user consent.
- Chained self-healing loops.
