from typing import Callable, Sequence
from typing import Protocol, Any
from termcolor import cprint

from .core import CovNode


class SupportsWrite(Protocol):
    def write(self, str_: str, /) -> Any | None:
        ...


_TREE_SET = {
    'fancy': ['    ', '│   ', '└── ', '├── '],
    'ascii': ['    ', '|   ', '`-- ', '|-- '],
    **{f'indent-{n}': ([' ' * n] * 4) for n in (1, 2, 3, 4)},
}


def get_available_tree_sets() -> list[str]:
    return list(_TREE_SET.keys())


def cov_color(
        coverage: float,
        thresholds: tuple[float, float, float] = (0.8, 0.8, 0.97),
) -> str | None:
    thresholds = tuple(sorted(thresholds))  # type: ignore
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
        descend: Callable[[CovNode], bool] | None,
        file: SupportsWrite | None = None,
        no_ansi_escape: bool = False,
) -> None:
    print_: Callable[..., None]
    kwargs: dict[str, Any] = dict(
        end='',
        file=file,
    )
    if no_ansi_escape:
        print_ = print
    else:
        print_ = cprint
        kwargs.update(dict(
            color=cov_color(node.coverage) if cov_color else None,
            attrs=['bold'] if len(node.children) else [],
        ))

    do_descend = descend is None or descend(node)
    is_leaf_like = len(node.children) == 0 or not do_descend

    tree = ''
    for last in level_last[:-1]:
        tree += tree_set[0] if last else tree_set[1]
    if level_last:
        tree += tree_set[2] if level_last[-1] else tree_set[3]

    print_(tree, end='', file=file)
    print_(
        '{:{w}}'.format(node.name, w=tree_width-len(tree)),
        **kwargs,  # type: ignore
    )
    if is_leaf_like or show_module_stats:
        print_(
            f'  {node.num_executable_lines:6,d}'
            f'  {node.num_missed_lines:6,d}'
            f'  {node.coverage:5.0%}',
            **kwargs,  # type: ignore
        )
        if show_missing:
            print_(
                f'  {node.missed_lines_str(not do_descend)}',
                **kwargs,  # type: ignore
            )
    print_('', file=file)

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
                descend=descend,
                file=file,
                no_ansi_escape=no_ansi_escape,
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
        descend: Callable[[CovNode], bool] | None = None,
        file: SupportsWrite | None = None,
        no_ansi_escape: bool = False,
) -> None:
    tree_set_ = _TREE_SET[tree_set]
    tab = len(tree_set_[0])
    tree_width = _max_tree_width(tree, tab)

    print_: Callable[..., None]
    if no_ansi_escape:
        print_ = print
        args = dict()
    else:
        print_ = cprint
        args = dict(attrs=['bold'])

    print_(
        '{:{w}}  {:>6s}  {:>6s}  {:>5s}'.format(
            '', 'Stmts', 'Miss', 'Cover', w=tree_width),
        end='', file=file, **args
    )
    if show_missing:
        print_('  Missing', end='', file=file, **args)
    print_('', file=file)

    print_('-' * (tree_width + 2 + 6 + 2 + 6 + 2 + 5), end='', file=file)
    if show_missing:
        print_('---------', end='', file=file)
    print_('', file=file)

    _print_tree(
        tree, tuple(),
        tree_width=tree_width,
        show_missing=show_missing,
        show_module_stats=show_module_stats,
        cov_color=cov_color,
        tree_set=tree_set_,
        descend=descend,
        file=file,
        no_ansi_escape=no_ansi_escape,
    )

    print_('-' * (tree_width + 2 + 6 + 2 + 6 + 2 + 5), end='', file=file)
    if show_missing:
        print_('---------', end='', file=file)
    print_('', file=file)
    print_(
        '{:{w}}  {:6,d}  {:6,d}  {:5.0%}'.format(
            'TOTAL',
            tree.num_executable_lines,
            tree.num_missed_lines,
            tree.coverage, w=tree_width),
        file=file,
    )
