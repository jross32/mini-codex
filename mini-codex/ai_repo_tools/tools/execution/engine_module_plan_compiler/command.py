import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.planning.module_plans.python_layouts.compilers.engine_module_plan_compiler.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
