---
name: policy-mutation-boundary-marker
description: "Use when implementing or improving policy-mutation-boundary-marker workflows in mini-codex."
argument-hint: "Describe the goal, target files, constraints, and validation expectations"
user-invocable: true
---

# policy-mutation-boundary-marker

## Purpose
- Declare read-only and side-effect boundaries for tool actions.

## When to Use
- The task maps to this capability area in mini-codex.
- You need a repeatable, policy-aware workflow instead of ad-hoc edits.

## Procedure
1. Clarify target scope and affected modules.
2. Run toolkit-first analysis and planning through AISH-compatible paths.
3. Implement minimal safe changes consistent with role and policy constraints.
4. Validate with deterministic checks and module-based Python execution where applicable.
5. Report outcomes, metrics, and any fallback rationale.

## Completion Checks
- Changes align with capability matrix intent and safety policy.
- Validation executed for affected paths.
- Performance reporting included when performance is discussed.
