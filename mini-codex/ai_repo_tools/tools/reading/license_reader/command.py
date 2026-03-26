import importlib as _importlib
_module = _importlib.import_module("tools.content_extraction.reading.parsing.structured_access.summarization.license_reader.license_reader.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
