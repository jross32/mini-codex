import importlib as _importlib
_module = _importlib.import_module("tools.quality_assurance.evaluation.measurement.risk_analysis.scoring.test_density.test_density_score.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
