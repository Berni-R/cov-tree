from typing import Callable, Sequence
from termcolor import cprint

from .node import CovNode


_TREE_SET = {
    'fancy': ['    ', '│   ', '└── ', '├── '],
    'ascii': ['    ', '|   ', '`-- ', '|-- '],
    **{f'indent-{n}': ([' ' * n] * 4) for n in (1, 2, 3, 4)},
}


def get_available_tree_sets() -> list[str]:
    return list(_TREE_SET.keys())


def cov_color(
        coverage: float,
        thresholds: tuple[float, float, float] = (0.5, 0.5, 0.95),
) -> str | None:
    if coverage >= thresholds[2]:
        return 'light_green'
    elif coverage >= thresholds[1]:
        return 'yellow'
    elif coverage >= thresholds[0]:
        return None
    else:
        return 'light_red'


def _print_tree(
        node: CovNode,
        level_last: tuple[bool, ...],
        tree_width: int,
        show_missing: bool,
        show_module_stats: bool,
        cov_color: Callable[[float], str | None] | None,
        tree_set: Sequence[str],
        threshold: Callable[[CovNode], bool] | None,
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
        '{:{w}}'.format(node.name, w=tree_width-len(tree)),
        **kwargs,  # type: ignore
    )
    if is_leaf_like or show_module_stats:
        cprint(
            f'  {node.num_executable_lines():6,d}'
            f'  {node.num_missed_lines():6,d}'
            f'  {node.coverage():5.0%}',
            **kwargs,  # type: ignore
        )
        if show_missing:
            cprint(
                f'  {node.missed_lines_str()}',
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
                show_missing=show_missing,
                show_module_stats=show_module_stats,
                cov_color=cov_color,
                tree_set=tree_set,
                threshold=threshold,
            )


def _max_tree_width(tree: CovNode, tab: int = 4) -> int:
    return max(
        (tab + _max_tree_width(child, tab) for child in tree.children),
        default=len(tree.name),
    )


def print_tree(
        tree: CovNode,
        show_missing: bool = False,
        show_module_stats: bool = True,
        cov_color: Callable[[float], str | None] | None = None,
        tree_set: str = 'fancy',
        threshold: Callable[[CovNode], bool] | None = None,
) -> None:
    tree_set_ = _TREE_SET[tree_set]
    tab = len(tree_set_[0])
    tree_width = _max_tree_width(tree, tab)

    cprint('{:{w}}  {:>6s}  {:>6s}  {:>5s}'.format(
        '', 'Stmts', 'Miss', 'Cover', w=tree_width), attrs=['bold'], end='')
    if show_missing:
        cprint('  Missing', attrs=['bold'], end='')
    print()
    print()
    _print_tree(
        tree, tuple(),
        tree_width=tree_width,
        show_missing=show_missing,
        show_module_stats=show_module_stats,
        cov_color=cov_color,
        tree_set=tree_set_,
        threshold=threshold,
    )
