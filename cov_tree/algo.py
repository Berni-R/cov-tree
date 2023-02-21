from typing import Iterable, Callable

from .node import Path, CovNode


def iterate(
    tree: CovNode,
    leaf_only: bool = False,
    threshold: Callable[[CovNode], bool] | None = None,
    prev_path: Path = tuple(),
) -> Iterable[tuple[Path, CovNode]]:
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


def max_depth(tree: CovNode) -> int:
    return max((1 + max_depth(child) for child in tree.children), default=0)
