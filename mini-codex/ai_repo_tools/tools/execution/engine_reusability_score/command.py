import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.evaluation.reuse_scoring.cross_project_quality.scorers.engine_reusability_score.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
