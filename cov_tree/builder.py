import os
import coverage  # type: ignore

from .node import CovStats
from .algo import follow_path


def _populate(node: CovStats) -> None:
    if len(node.children) == 0:
        return

    node.num_lines = 0
    node.num_skipped = 0
    node.num_missed = 0
    for child in node.children:
        _populate(child)
        node.num_lines += child.num_lines
        node.num_skipped += child.num_skipped
        node.num_missed += child.num_missed


def build_cov_tree(
        cov_file: str = ".coverage",
        drop_ext: bool = False,
) -> tuple[str, CovStats]:
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
    root = CovStats(name="<root>")
    for path in sorted(cov_data.measured_files()):
        path_list = os.path.normpath(path).split(os.sep)
        if drop_ext:
            path_list[-1] = os.path.splitext(path_list[-1])[0]
        leaf = follow_path(root, path_list, create=True)
        _, executable_lines, skipped_lines, missed_lines, _ = (
            cov.analysis2(path)
        )
        leaf.num_lines = len(executable_lines)
        leaf.num_skipped = len(skipped_lines)
        leaf.num_missed = len(missed_lines)
        leaf.missed_lines = missed_lines
    _populate(root)

    # clean the linear tree until the first splitting node
    # ... but remember the path to this new root node
    base = []
    while len(root.children) == 1:
        base.append(root.name)
        root = root.children[0]

    return os.sep.join(base[1:]), root
