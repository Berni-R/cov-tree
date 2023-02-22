import pytest

from io import StringIO
from contextlib import redirect_stdout
import re

from cov_tree.print import _TREE_SET, get_available_tree_sets, cov_color
from cov_tree.print import print_tree
from cov_tree.core import CovFile, CovModule, CovNode


@pytest.mark.parametrize('tree_set', _TREE_SET.values())
def test_tree_sets(tree_set: list[str]) -> None:
    assert len(tree_set) == 4
    assert len({len(x) for x in tree_set})


def test_get_available_tree_sets() -> None:
    assert 'ascii' in get_available_tree_sets()
    assert 'fancy' in get_available_tree_sets()


@pytest.mark.parametrize('cov, th, color', [
    (0.9, (0.5, 0.6, 0.95), 'yellow'),
    (0.9, (0.5, 0.6, 0.85), 'light_green'),
    (0.55, (0.5, 0.6, 0.85), None),
    (0.0, (0.5, 0.6, 0.85), 'light_red'),
    (0.05, (0.0, 0.2, 0.8), None),
    (0.3, (0.0, 0.2, 0.8), 'yellow'),
])
def test_cov_color(
    cov: float, th: tuple[float, float, float], color: str | None,
) -> None:
    assert cov_color(cov, th) == color


@pytest.fixture
def sample_tree() -> CovNode:
    root = CovModule('module')

    root.insert_child(CovFile('__init__.py', {1, 2, 4, 7}, {}, {}))
    root.insert_child(CovFile('version.py', {1}, {}, {}))

    mod: CovNode
    for mod in (
        CovFile('__init__.py', {1, 2}, {}, {}),
        CovFile('file1.py', range(42), {}, range(20, 24)),
        CovFile('file2.py', set(range(60)) - {3, 4, 44}, {3, 4, 44},
                range(30, 33)),
    ):
        root.insert_child(mod, ['submodule_1'])

    for mod in (
        CovFile('__init__.py', {1, 2}, {}, {}),
        CovFile('file1.py', range(33), {}, {1, 2, 3, 8} | set(range(20, 25))),
        CovFile('file2.py', set(range(50)) - {22, 33}, {22, 33},
                range(10, 15)),
        CovFile('file3.py', range(33), {}, {3, 4, 5, 13, 20, 21, 22, 23}),
        CovModule('subsubmodule'),
    ):
        root.insert_child(mod, ['submodule_2'])

    for mod in (
        CovFile('__init__.py', {}, {}, {}),
        CovFile('file1.py', range(20), {}, {}),
        CovFile('file2.py', set(range(20)) - {3, 4}, {3, 4}, {11, 12, 18}),
    ):
        root.insert_child(mod, ['submodule_2', 'subsubmodule'])

    root.insert_child(CovFile('file3.py', range(10), {}, {}))

    return root


EXPECT_TREE_MISSING = """\
                          Stmts    Miss  Cover  Missing

module                      270      32    88%  
├── __init__.py               4       0   100%  
├── version.py                1       0   100%  
├── submodule_1             101       7    93%  
│   ├── __init__.py           2       0   100%  
│   ├── file1.py             42       4    90%  20-23
│   └── file2.py             57       3    95%  30-32
├── submodule_2             154      25    84%  
│   ├── __init__.py           2       0   100%  
│   ├── file1.py             33       9    73%  1-3, 8, 20-24
│   ├── file2.py             48       5    90%  10-14
│   ├── file3.py             33       8    76%  3-5, 13, 20-23
│   └── subsubmodule         38       3    92%  
│       ├── __init__.py       0       0   100%  
│       ├── file1.py         20       0   100%  
│       └── file2.py         18       3    83%  11-12, 18
└── file3.py                 10       0   100%  
"""
EXPECT_TREE = """\
                          Stmts    Miss  Cover

module                      270      32    88%
├── __init__.py               4       0   100%
├── version.py                1       0   100%
├── submodule_1             101       7    93%
│   ├── __init__.py           2       0   100%
│   ├── file1.py             42       4    90%
│   └── file2.py             57       3    95%
├── submodule_2             154      25    84%
│   ├── __init__.py           2       0   100%
│   ├── file1.py             33       9    73%
│   ├── file2.py             48       5    90%
│   ├── file3.py             33       8    76%
│   └── subsubmodule         38       3    92%
│       ├── __init__.py       0       0   100%
│       ├── file1.py         20       0   100%
│       └── file2.py         18       3    83%
└── file3.py                 10       0   100%
"""
EXPECT_TREE_NO_MOD = """\
                          Stmts    Miss  Cover

module                 
├── __init__.py               4       0   100%
├── version.py                1       0   100%
├── submodule_1        
│   ├── __init__.py           2       0   100%
│   ├── file1.py             42       4    90%
│   └── file2.py             57       3    95%
├── submodule_2        
│   ├── __init__.py           2       0   100%
│   ├── file1.py             33       9    73%
│   ├── file2.py             48       5    90%
│   ├── file3.py             33       8    76%
│   └── subsubmodule   
│       ├── __init__.py       0       0   100%
│       ├── file1.py         20       0   100%
│       └── file2.py         18       3    83%
└── file3.py                 10       0   100%
"""


ANSI_ESC_RE = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)


def clean_ansi_esc(text: str) -> str:
    return ANSI_ESC_RE.sub('', text)


def test_print_stdout(sample_tree: CovNode) -> None:
    with StringIO() as string_io:
        with redirect_stdout(string_io):
            print_tree(sample_tree, no_ansi_escape=True)
        output = string_io.getvalue()
    assert output == EXPECT_TREE


@pytest.mark.parametrize('missing', [True, False])
@pytest.mark.parametrize('ansi_esc', [True, False])
@pytest.mark.parametrize('mod_stats', [True, False])
def test_print_params(
        sample_tree: CovNode,
        missing: bool,
        ansi_esc: bool,
        mod_stats: bool,
) -> None:
    with StringIO() as string_io:
        print_tree(
            sample_tree, file=string_io,
            no_ansi_escape=ansi_esc,
            show_missing=missing,
            show_module_stats=mod_stats,
        )
        output = string_io.getvalue()

    if missing:
        if not mod_stats:
            return  # not testing this combinations
        expect = EXPECT_TREE_MISSING
    else:
        expect = EXPECT_TREE if mod_stats else EXPECT_TREE_NO_MOD

    if not ansi_esc:
        output = clean_ansi_esc(output)

    assert output == expect


EXPECT_TREE_COLLAPSED = """\
                          Stmts    Miss  Cover  Missing

module                      270      32    88%  
├── __init__.py               4       0   100%  
├── version.py                1       0   100%  
├── submodule_1             101       7    93%  [file1.py: 20-23], \
[file2.py: 30-32]
├── submodule_2             154      25    84%  
│   ├── __init__.py           2       0   100%  
│   ├── file1.py             33       9    73%  1-3, 8, 20-24
│   ├── file2.py             48       5    90%  10-14
│   ├── file3.py             33       8    76%  3-5, 13, 20-23
│   └── subsubmodule         38       3    92%  [file2.py: 11-12, 18]
└── file3.py                 10       0   100%  
"""


def test_print_collapsed(sample_tree: CovNode) -> None:
    with StringIO() as string_io:
        print_tree(
            sample_tree, file=string_io,
            no_ansi_escape=True,
            show_missing=True,
            show_module_stats=True,
            descend=lambda n: n.coverage() < 0.9,
        )
        output = string_io.getvalue()

    assert output == EXPECT_TREE_COLLAPSED
