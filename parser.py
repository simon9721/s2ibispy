# Compatibility shim for moved parser module
# Re-exports S2IParser from legacy.parser so existing imports continue to work
try:
    from legacy.parser import S2IParser  # type: ignore
except Exception:
    # Provide a helpful ImportError if the legacy module isn't present
    raise ImportError("Could not import 'S2IParser' from 'legacy.parser'. Ensure 'legacy/parser.py' exists and is importable.")

__all__ = ["S2IParser"]
