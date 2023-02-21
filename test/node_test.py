import pytest
from coverage import Coverage  # type: ignore
from pytest_mock import MockFixture

from cov_tree.node import CovFile, CovModule


def test_cov_file_default_constructor() -> None:
    node = CovFile('name')
    assert node.name == 'name'
    assert node.is_leaf
    assert node._children == dict()
    assert len(node) == 1
    assert node.num_executable_lines() == 0
    assert node.num_skipped_lines() == 0
    assert node.num_missed_lines() == 0
    assert node.num_covered_lines() == 0
    assert node.num_lines() == (0, 0, 0)
    assert node.coverage() == 1
    assert repr(node) == '<CovFile "name" 100%>'


def test_cov_file_constructor() -> None:
    node = CovFile(
        'file.py',
        executable_lines=[1, 2, 4, 5, 9, 10, 11, 15, 16, 17],
        skipped_lines=[11],
        missed_lines=[2, 4, 5],
    )
    assert node.name == 'file.py'
    assert node.is_leaf
    assert node._children == dict()
    assert len(node) == 1
    assert node.num_executable_lines() == 10
    assert node.num_skipped_lines() == 1
    assert node.num_missed_lines() == 3
    assert node.num_covered_lines() == 6
    assert node.num_lines() == (10, 1, 3)
    assert node.coverage() == 7/10
    assert node.coverage(exclude_skipped=True) == 6/9
    assert repr(node) == '<CovFile "file.py" 70%>'


def test_cov_file_from_cov(mocker: MockFixture) -> None:
    mocker.patch(
        'coverage.Coverage.analysis2',
        lambda self, morf: (
            morf, [1, 2, 3, 4, 5, 6, 7, 8, 9], [2], [4, 5, 6], '4-6',
        ),
    )
    cov = Coverage(data_file=None)
    mod = CovFile.from_coverage(cov, 'some/path')

    assert mod.name == 'path'
    assert mod.num_children == 0


def test_cov_module_default_constructor() -> None:
    node = CovModule('module')
    assert node.name == 'module'
    assert node.is_leaf
    assert node._children == dict()
    assert len(node) == 1
    assert node.num_executable_lines() == 0
    assert node.num_skipped_lines() == 0
    assert node.num_missed_lines() == 0
    assert node.num_covered_lines() == 0
    assert node.num_lines() == (0, 0, 0)
    assert node.coverage() == 1
    assert repr(node) == '<CovModule "module" 100%>'


def test_cov_module() -> None:
    root = CovModule('root')
    mod_1 = CovModule('module_1')
    mod_2 = CovFile('module_2.py', range(100), [], [])
    for mod in (mod_1, mod_2):
        root.insert_child(mod)
    mod_3 = CovFile('module_3.py', range(30), [], range(5, 10))
    mod_4 = CovFile('module_4.py', range(30), [21], [12, 13, 14, 20, 22])
    for mod in (mod_3, mod_4):
        mod_1.insert_child(mod)
    mod_6 = CovFile('module_6.py', range(50), range(20, 30), [42, 43, 53])
    root.insert_child(mod_6, [mod_1.name, 'module_5'])

    with pytest.raises(RuntimeError):
        root.insert_child(mod_6, [mod_1.name, 'module_5'])

    assert root.name == 'root'
    assert root.num_children == 2
    for child, expected in zip(root.children, [mod_1, mod_2]):
        assert child is expected
    for child, name in zip(root.children, root.children_names):
        assert child.name == name
    assert len(root) == 7
    assert root.get_child('module_2.py') is mod_2
    assert root['module_1'] is mod_1
    assert mod_1.num_children == 3
    assert len(root['module_1']) == 5
    assert root.follow_path(['module_1', 'module_4.py']) is mod_4

    assert root.num_lines() == (210, 11, 13)
