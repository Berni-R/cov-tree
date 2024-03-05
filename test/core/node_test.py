from __future__ import annotations
import pytest
from typing import Collection
from coverage import Coverage  # type: ignore
from pytest_mock import MockFixture

from cov_tree.core.node import CovFile, CovModule, CovNode


def test_cov_file_default_constructor() -> None:
    node = CovFile('name')
    assert node.name == 'name'
    assert node.is_leaf
    assert node.children == ()
    assert node.parent is None
    assert node.is_root
    assert len(node) == 1
    assert node.depth == 0
    assert node.num_executable_lines == 0
    assert node.num_skipped_lines == 0
    assert node.num_missed_lines == 0
    assert node.missed_lines_str() == ''
    assert node.num_covered_lines == 0
    assert node.num_total_lines == 0
    assert node.coverage == 1
    assert repr(node) == '<CovFile "name" 100%>'
    assert list(node.iter_tree()) == [node]


def test_cov_file_constructor() -> None:
    node = CovFile(
        'file.py',
        executable_lines=[1, 2, 4, 5, 9, 10, 15, 16, 17],
        skipped_lines=[11],
        missed_lines=[2, 4, 5],
    )
    assert node.name == 'file.py'
    assert node.is_leaf
    assert node.children == ()
    assert node.parent is None
    assert node.is_root
    assert len(node) == 1
    assert node.depth == 0
    assert node.num_executable_lines == 9
    assert node.num_skipped_lines == 1
    assert node.num_missed_lines == 3
    assert node.missed_lines_str() == '2-5'
    assert node.num_covered_lines == 6
    assert node.num_total_lines == 10
    assert node.coverage == 1 - 3 / 9
    assert repr(node) == '<CovFile "file.py" 67%>'
    assert list(node.iter_tree()) == [node]

    with pytest.raises(RuntimeError):
        node.insert_child(CovFile('something'))


@pytest.mark.parametrize('executable_lines, skipped_lines, missed_lines', [
    ([1, 2, 3], [2], []),
    ([2, 3], [], [1]),
    ([1, 2, 4], [5], [3, 4]),
    ([1, 2, 4, 5, 9, 10, 11, 15, 16, 17], [11], [2, 4, 5]),
])
def test_cov_bad_file_constructor(
        executable_lines: Collection[int],
        skipped_lines: Collection[int],
        missed_lines: Collection[int],
) -> None:
    with pytest.raises(ValueError):
        CovFile(
            'file.py',
            executable_lines=executable_lines,
            skipped_lines=skipped_lines,
            missed_lines=missed_lines,
        )


def test_cov_file_from_cov(mocker: MockFixture) -> None:
    mocker.patch(
        'coverage.Coverage.analysis2',
        lambda _, morf: (
            morf, [1, 3, 6, 8, 9], [2, 4, 5], [6, 8], '6-8',
        ),
    )
    cov = Coverage(data_file=None)
    node = CovFile.from_coverage(cov, 'some/path')

    assert node.name == 'path'
    assert node.is_leaf
    assert node.children == ()
    assert node.parent is None
    assert node.is_root
    assert len(node) == 1
    assert node.depth == 0
    assert node.num_executable_lines == 5
    assert node.num_skipped_lines == 3
    assert node.num_missed_lines == 2
    assert node.missed_lines_str() == '6-8'
    assert node.num_covered_lines == 5 - 2
    assert node.num_total_lines == 8
    assert node.coverage == 1 - 2 / 5
    assert repr(node) == '<CovFile "path" 60%>'
    assert list(node.iter_tree()) == [node]


def test_cov_module_default_constructor() -> None:
    node = CovModule('module')
    assert node.name == 'module'
    assert node.is_leaf
    assert node.children == ()
    assert node.parent is None
    assert len(node) == 1
    assert node.num_executable_lines == 0
    assert node.num_skipped_lines == 0
    assert node.num_missed_lines == 0
    assert node.missed_lines_str() == ''
    assert node.num_covered_lines == 0
    assert node.num_total_lines == 0
    assert node.coverage == 1
    assert repr(node) == '<CovModule "module" 100%>'


def build_sample_tree() -> tuple[CovModule, list[CovNode]]:
    root = CovModule('root')

    mod_1 = CovModule('module_1')
    mod_2 = CovFile('module_2.py', range(42), [], range(20, 24))
    for mod in (mod_1, mod_2):
        root.insert_child(mod)

    mod_3 = CovFile('module_3.py', range(30), [], range(5, 10))
    mod_4 = CovFile(
        'module_4.py',
        set(range(30)) - {21},
        [21],
        [12, 13, 14, 20, 22],
    )
    for mod in (mod_3, mod_4):
        mod_1.insert_child(mod)

    mod_6 = CovFile(
        'module_6.py',
        set(range(55)) - set(range(20, 30)),
        range(20, 30),
        [42, 43, 53],
    )
    root.insert_child(mod_6, [mod_1.name, 'module_5'])

    return root, [mod_1, mod_2, mod_3, mod_4, mod_6]


def test_cov_module_basics() -> None:
    root, [mod_1, mod_2, mod_3, mod_4, mod_6] = build_sample_tree()

    assert root.name == 'root'
    assert root.parent is None
    assert root.is_root
    assert root.depth == 0
    assert root.num_children == 2
    for child, expected in zip(root.children, [mod_1, mod_2]):
        assert child is expected
        assert child.parent is root
        assert child.root is root
        assert not child.is_root
        assert child.depth == 1
    for child, name in zip(root.children, root.children_names):
        assert child.name == name
        assert child.parent is root
        assert child.root is root
        assert not child.is_root
        assert child.depth == 1
    assert len(root) == 7
    assert root.get_child('module_2.py') is mod_2
    assert root['module_1'] is mod_1
    assert mod_1.num_children == 3
    assert len(root['module_1']) == 5

    for child in mod_1.children:
        assert child.parent is mod_1
        assert child.root is root
        assert not child.is_root
        assert child.depth == 2

    assert root.num_total_lines == 146 + 11


def test_cov_module_bad_inserts() -> None:
    root, [mod_1, mod_2, mod_3, mod_4, mod_6] = build_sample_tree()

    with pytest.raises(RuntimeError):
        root.insert_child(mod_6, [mod_1.name, 'module_5'])

    with pytest.raises(RuntimeError):
        mod_4.insert_child(mod_3)

    with pytest.raises(RuntimeError):
        root.insert_child(mod_2, [mod_2.name])


def test_cov_module_iter() -> None:
    root, _ = build_sample_tree()

    paths = {node.name: node.path for node in root.iter_tree()}
    assert paths == {
        'root': ('root',),
        'module_1': ('root', 'module_1',),
        'module_2.py': ('root', 'module_2.py',),
        'module_3.py': ('root', 'module_1', 'module_3.py'),
        'module_4.py': ('root', 'module_1', 'module_4.py'),
        'module_5': ('root', 'module_1', 'module_5'),
        'module_6.py': ('root', 'module_1', 'module_5', 'module_6.py'),
    }


def test_cov_module_iter_filter() -> None:
    root, _ = build_sample_tree()

    cov = {
        node.name: round(node.coverage, 2)
        for node in root.iter_tree(lambda n: n.coverage < 0.9)
    }
    assert cov == {
        'module_1': 0.88,
        'module_2.py': 0.9,
        'module_3.py': 0.83,
        'module_4.py': 0.83,
        'module_5': 0.93,
        # 'module_6.py': 0.9x,  <- not descending into module_5, b/c of coverage
        'root': 0.88,
    }


def test_cov_module_missed_lines() -> None:
    root, _ = build_sample_tree()

    cov = {node.name: node.missed_lines_str() for node in root.iter_tree()}
    assert cov == {
        'module_1': '[module_3.py: 5-9], [module_4.py: 12-14, 20-22], '
                    '[module_5: [module_6.py: 42-43, 53]]',
        'module_2.py': '20-23',
        'module_3.py': '5-9',
        'module_4.py': '12-14, 20-22',
        'module_5': '[module_6.py: 42-43, 53]',
        'module_6.py': '42-43, 53',
        'root': '[module_1: [module_3.py: 5-9], [module_4.py: 12-14, 20-22], '
                '[module_5: [module_6.py: 42-43, 53]]], [module_2.py: 20-23]',
    }

    cov = {
        node.name: node.missed_lines_str(False)
        for node in root.iter_tree()
    }
    assert cov == {
        'module_1': '',
        'module_2.py': '20-23',
        'module_3.py': '5-9',
        'module_4.py': '12-14, 20-22',
        'module_5': '',
        'module_6.py': '42-43, 53',
        'root': '',
    }
