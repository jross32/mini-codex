import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.analysis.dependency_maps.module_relationships.builders.engine_dependency_map_builder.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
