import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.contracts.interfaces.cross_project.generators.engine_contract_generator.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
