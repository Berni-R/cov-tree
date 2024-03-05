from __future__ import annotations
import pytest

from cov_tree.cmdline import get_arg_parser, main
from cov_tree import __version__


DEF_ARGS = {
    'coverage_file': '.coverage',
    'threshold': None,
    'show_missing': False,
    'summarize': False,
    'set': 'ascii',
    'color': False,
}


def test_args() -> None:
    parser = get_arg_parser()
    args = parser.parse_args(args=[])

    assert set(name for name, _ in args._get_kwargs()) == {
        'coverage_file', 'threshold', 'show_missing', 'summarize', 'set',
        'color',
    }

    assert args.coverage_file == '.coverage'


def test_main() -> None:
    # mock build_cov_tree and print_tree
    pass


def test_main_version(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit):
        main(['-v'])
    captured = capsys.readouterr()
    assert __version__ in captured.out
    assert captured.err == ""
