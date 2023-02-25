from cov_tree import (
    CovNode, build_cov_tree, print_tree, cov_color, get_available_tree_sets,
)
from argparse import ArgumentParser


def main() -> int:
    argparser = get_arg_parser()
    args = argparser.parse_args()

    color = cov_color if args.color else None
    if args.threshold is None:
        descend = None
    else:
        def func(n: CovNode) -> bool:
            return n.coverage < args.threshold / 100
        descend = func

    try:
        _, tree = build_cov_tree(args.coverage_file)
        print_tree(
            tree,
            show_missing=args.show_missing,
            show_module_stats=args.summarize,
            cov_color=color,
            tree_set=args.set,
            descend=descend,
        )
    except Exception as e:
        print(e)
        return 1

    return 0


def get_arg_parser() -> ArgumentParser:
    argparser = ArgumentParser(
        'cov-tree [coverage-file]',
    )
    argparser.add_argument(
        'coverage_file',
        nargs='?', default='.coverage',
        help='The path to the coverage report file to print.',
    )
    argparser.add_argument(
        '-t', '--threshold', required=False, default=None, type=float,
        help='If the coverage is at least this high (measured in percent), '
        'collapse the folder / sub-module into a single line.',
    )
    argparser.add_argument(
        '-m', '--show-missing', action='store_true',
        help='Show the missing lines.',
    )
    argparser.add_argument(
        '-s', '--summarize', action='store_true',
        help='Show per sub-module summaries.',
    )
    argparser.add_argument(
        '--set', default='fancy',
        choices=get_available_tree_sets(),
        help='Choose a set of characters for printing the tree.',
    )
    argparser.add_argument(
        '-c', '--color', action='store_true', default=False,
        help='Colorise the output by the coverage.',
    )
    argparser.add_argument(
        '--no-color', action='store_false', dest='color',
        help='Turn off coloring. (If both, --no-color and --color are given, '
        'the ooption use last is relevant.)',
    )

    return argparser
