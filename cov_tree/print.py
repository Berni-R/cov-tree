from typing import Callable, Sequence
from termcolor import cprint

from .node import CovStats


_TREE_SET = {
    'fancy': ['    ', '│   ', '└── ', '├── '],
    'ascii': ['    ', '|   ', '`-- ', '|-- '],
    **{f'indent-{n}': ([' ' * n] * 4) for n in (1, 2, 3, 4)},
}


def get_available_tree_sets() -> list[str]:
    return list(_TREE_SET.keys())


def cov_color(
        coverage: float,
        thresholds: tuple[float, float, float] = (0.8, 0.8, 0.95),
) -> str | None:
    if coverage >= thresholds[2]:
        return 'green'
    elif coverage >= thresholds[1]:
        return 'yellow'
    elif coverage >= thresholds[0]:
        return None
    else:
        return 'red'


def _print_tree(
        node: CovStats,
        level_last: tuple[bool, ...],
        tree_width: int,
        show_module_stats: bool,
        cov_color: Callable[[float], str | None] | None,
        tree_set: Sequence[str],
        threshold: Callable[[CovStats], bool] | None,
) -> None:
    is_leaf_like = (
        len(node.children) == 0 or
        (threshold is not None and threshold(node))
    )

    tree = ''
    for last in level_last[:-1]:
        tree += tree_set[0] if last else tree_set[1]
    if level_last:
        tree += tree_set[2] if level_last[-1] else tree_set[3]

    print(tree, end='')
    kwargs = dict(
        color=cov_color(node.coverage()) if cov_color else None,
        attrs=['bold'] if len(node.children) else [],
        end='',
    )
    cprint(
        '{:{w}}  '.format(node.name, w=tree_width-len(tree)),
        **kwargs,  # type: ignore
    )
    if is_leaf_like or show_module_stats:
        cprint(
            '{:6,d}  {:6,d}  {:5.0%}'.format(
                node.num_lines, node.num_missed, node.coverage(),
            ),
            **kwargs,  # type: ignore
        )
    print()

    if not is_leaf_like:
        for child in node.children:
            last = child is node.children[-1]
            _print_tree(
                child,
                level_last=level_last+(last,),
                tree_width=tree_width,
                show_module_stats=show_module_stats,
                cov_color=cov_color,
                tree_set=tree_set,
                threshold=threshold,
            )


def _max_tree_width(tree: CovStats, tab: int = 4) -> int:
    return max(
        (tab + _max_tree_width(child, tab) for child in tree.children),
        default=len(tree.name),
    )


def print_tree(
        tree: CovStats,
        show_module_stats: bool = True,
        cov_color: Callable[[float], str | None] | None = None,
        tree_set: str = 'fancy',
        threshold: Callable[[CovStats], bool] | None = None,
) -> None:
    tree_set_ = _TREE_SET[tree_set]
    tab = len(tree_set_[0])
    tree_width = _max_tree_width(tree, tab)

    cprint('{:{w}}  {:>6s}  {:>6s}  {:>5s}'.format(
        '', 'Stmts', 'Miss', 'Cover', w=tree_width), attrs=['bold'])
    print()
    _print_tree(
        tree, tuple(),
        tree_width=tree_width,
        show_module_stats=show_module_stats,
        cov_color=cov_color,
        tree_set=tree_set_,
        threshold=threshold,
    )
