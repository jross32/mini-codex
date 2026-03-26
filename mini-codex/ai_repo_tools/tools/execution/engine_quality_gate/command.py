import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.validation.quality_gates.engine_outputs.reviewers.engine_quality_gate.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
