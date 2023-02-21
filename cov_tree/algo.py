from typing import Iterable, Callable

from .node import Path, CovStats


def iterate(
    tree: CovStats,
    leaf_only: bool = False,
    threshold: Callable[[CovStats], bool] | None = None,
    prev_path: Path = tuple(),
) -> Iterable[tuple[Path, 'CovStats']]:
    is_leaf_like = (
        len(tree.children) == 0 or
        (threshold is not None and threshold(tree))
    )

    if is_leaf_like or not leaf_only:
        yield list(prev_path), tree

    if not is_leaf_like:
        for child in tree.children:
            path = [*prev_path, child.name]
            yield from iterate(child, leaf_only, threshold, path)


def max_depth(tree: CovStats) -> int:
    return max((1 + max_depth(child) for child in tree.children), default=0)


def follow_path(
    tree: CovStats,
    path: Path,
    create: bool = False,
) -> CovStats:
    """Follow the given path with the tree and return the corresponding node.

    Args:
        tree:
        path:
        create:

    Returns:
        The node ...

    Raises:
        ValueError: if the path does not lead to a node and create was False.
    """
    current = tree
    for name in path:
        child = current.get_child(name)
        if child is None:
            if create:
                child = CovStats(name)
                current.children.append(child)
            else:
                raise ValueError(
                    f'could not find child "{name}" for "{current.name}"'
                )
        current = child
    return current
