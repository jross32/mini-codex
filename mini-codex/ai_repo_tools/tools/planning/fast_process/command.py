import importlib as _importlib
_module = _importlib.import_module("tools.workflow_design.planning.decision_support.task_structuring.routing.fast_process.fast_process.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
