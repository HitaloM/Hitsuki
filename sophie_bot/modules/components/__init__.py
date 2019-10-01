from os.path import dirname, basename, isfile
import glob

from sophie_bot import CONFIG, logger

NO_LOAD_COMPONENTS = CONFIG["Advanced"]["not_load_this_components"]


def list_all_components():
    components = []
    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_components = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]
    for component in all_components:
        if component not in NO_LOAD_COMPONENTS:
            components.append(component)

    return components


ALL_COMPONENTS = sorted(list(list_all_components()))

print(ALL_COMPONENTS)

logger.info("Components to load: %s", str(ALL_COMPONENTS))
__all__ = ALL_COMPONENTS + ["ALL_COMPONENTS"]
