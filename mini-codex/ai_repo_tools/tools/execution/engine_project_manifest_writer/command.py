import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.reporting.manifests.project_metadata.writers.engine_project_manifest_writer.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
