import glob
import os.path


def list_all_filters():
	mod_paths = glob.glob(os.path.dirname(__file__) + "/*.py")
	all_filters = [
		os.path.basename(f)[:-3]
		for f in mod_paths
		if os.path.isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
	]

	return all_filters


ALL_FILTERS = sorted(list(list_all_filters()))

__all__ = ALL_FILTERS + ["ALL_FILTERS"]
