import os
import coverage  # type: ignore

from .node import CovNode, CovModule, CovFile


def build_cov_tree(
        cov_file: str = ".coverage",
        drop_ext: bool = False,
) -> tuple[str, CovNode]:
    """Build a coverage tree from a coverage file.

    Args:
        cov_file: The path to the coverage file created by `coverage`.
                  This typically is `.coverage`.
        drop_ext: Drop file extenstions for the node names (e.g. use 'module'
                  for the file 'module.py').

    Returns:
        A tuple of the path to the root node and the root node of the tree.
    """
    # read the coverage file
    cov = coverage.Coverage(data_file=None)
    cov.combine([cov_file], strict=True, keep=True)
    cov_data = cov.get_data()

    # build the tree
    root: CovNode = CovModule(name="<root>")
    for path in sorted(cov_data.measured_files()):
        path_list = os.path.normpath(path).split(os.sep)
        if drop_ext:
            path_list[-1] = os.path.splitext(path_list[-1])[0]
        leaf = CovFile.from_coverage(cov, path, path_list[-1])
        root.insert_child(leaf, path_list[:-1])

    # clean the linear tree until the first splitting node
    # ... but remember the path to this new root node
    base = []
    while root.num_children == 1:
        base.append(root.name)
        name = root.children_names[0]
        root = root.get_child(name)

    return os.sep.join(base[1:]), root
