import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.configuration.validation.schema_rules.game_modes.game_type_schema_validator.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
