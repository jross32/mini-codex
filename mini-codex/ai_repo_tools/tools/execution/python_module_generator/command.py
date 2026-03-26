import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.module_generation.python_modules.generic_generators.builders.python_module_generator.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
