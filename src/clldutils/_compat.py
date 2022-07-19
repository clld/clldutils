try:
    from importlib.metadata import entry_points
except ModuleNotFoundError:  # pragma: no cover
    from importlib_metadata import entry_points


def get_entrypoints(group):
    eps = entry_points()
    return eps.select(group=group) if hasattr(eps, 'select') else eps.get(group, [])
