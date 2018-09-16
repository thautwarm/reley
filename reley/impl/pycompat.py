import sys
from .reley_import import find_reley_module_spec


class ReleyFinder:
    @classmethod
    def find_spec(cls, fullname: str, paths, target=None):

        return find_reley_module_spec(fullname)


sys.meta_path.append(ReleyFinder)
