import importlib as _importlib
_module = _importlib.import_module("tools.network_observability.diagnostics.connectivity.transport_analysis.probes.tls_cert.tls_cert_probe.command")
globals().update({k: v for k, v in _module.__dict__.items() if not (k.startswith("__") and k.endswith("__"))})
