import importlib as _importlib
_module = _importlib.import_module("tools.project_generation.multi_project.configuration.templates.module_templates.catalogs.engine_template_catalog_loader.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
