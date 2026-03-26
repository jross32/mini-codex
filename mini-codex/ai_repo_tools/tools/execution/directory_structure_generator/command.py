import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.structure_generation.filesystem_layouts.directory_materializers.builders.directory_structure_generator.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
