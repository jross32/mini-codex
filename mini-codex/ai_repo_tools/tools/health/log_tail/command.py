import importlib as _importlib
_module = _importlib.import_module("tools.operational_health.validation.checks.environment_review.signals.log_tail.log_tail.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
