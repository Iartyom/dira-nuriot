"""Adapter registry and aggregator for external sources (madlan, yad2).
Each adapter module should expose a function `fetch(query)` that returns a list of deal-like dicts
or raises/returns an empty list on failure. Adapter implementations should save raw responses
into updates/ for provenance.
"""
import pkgutil
import importlib
import traceback


def _discover_adapters():
    adapters = []
    package = __name__
    for _, name, ispkg in pkgutil.iter_modules(__path__):
        if not ispkg:
            try:
                mod = importlib.import_module(f"{package}.{name}")
                if hasattr(mod, "fetch"):
                    adapters.append((name, mod))
            except Exception:
                # ignore broken adapters
                traceback.print_exc()
    return adapters


def fetch_all(query):
    """Call all available adapters and return a flat list of items.
    Each returned item will gain a `_source` key with the adapter name for provenance.
    """
    results = []
    for name, mod in _discover_adapters():
        try:
            items = mod.fetch(query)
            if items:
                for it in items:
                    if isinstance(it, dict):
                        it.setdefault("_source", name)
                    results.append(it)
        except Exception:
            # adapter failure should not stop the pipeline
            traceback.print_exc()
    return results
