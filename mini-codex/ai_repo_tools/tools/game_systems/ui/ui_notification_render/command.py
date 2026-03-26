import importlib as _importlib
_module = _importlib.import_module("tools.interactive_systems.gameplay.systems.mechanics.specializations.ui_notification.ui_notification_render.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
