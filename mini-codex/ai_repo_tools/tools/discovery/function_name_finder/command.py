import importlib as _importlib
_module = _importlib.import_module("tools.repository_intelligence.discovery.scanning.pattern_analysis.signals.function_name.function_name_finder.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
