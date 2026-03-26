import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.materialization.module_execution.python_layouts.writers.engine_module_materializer.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
