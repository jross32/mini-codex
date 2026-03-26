import importlib as _importlib
_module = _importlib.import_module("tools.workflow_design.planning.decision_support.task_structuring.routing.migration_risk.migration_risk_planner.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
