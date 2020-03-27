import glob
import os.path

from sophie_bot import logger
from sophie_bot.config import get_config_key

NO_LOAD_COMPONENTS = get_config_key("disabled_components")


def list_all_components():
	components = []
	mod_paths = glob.glob(os.path.dirname(__file__) + "/*.py")
	all_components = [
		os.path.basename(f)[:-3]
		for f in mod_paths
		if os.path.isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
	]
	for component in all_components:
		if component not in DISABLED_COMPONENTS:
			components.append(component)

	return components


ALL_COMPONENTS = sorted(list(list_all_components()))

print(ALL_COMPONENTS)

logger.info("Components to load: %s", str(ALL_COMPONENTS))
__all__ = ALL_COMPONENTS + ["ALL_COMPONENTS"]
