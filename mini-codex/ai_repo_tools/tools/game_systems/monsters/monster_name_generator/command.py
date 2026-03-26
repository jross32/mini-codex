import importlib as _importlib
_module = _importlib.import_module("tools.interactive_systems.gameplay.systems.mechanics.specializations.monster_name.monster_name_generator.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
