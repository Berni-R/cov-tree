import pytest
from coverage import Coverage  # type: ignore
from pytest_mock import MockFixture

from cov_tree.core.node import CovFile, CovModule


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
    assert list(node.iter_tree()) == [(node, ())]


def test_cov_file_constructor() -> None:
    node = CovFile(
        'file.py',
        executable_lines=[1, 2, 4, 5, 9, 10, 15, 16, 17],
        skipped_lines=[11],
        missed_lines=[2, 4, 5],
    )
    assert node.name == 'file.py'
    assert node.is_leaf
    assert node._children == dict()
    assert len(node) == 1
    assert node.num_executable_lines() == 9
    assert node.num_skipped_lines() == 1
    assert node.num_missed_lines() == 3
    assert node.num_covered_lines() == 6
    assert node.num_lines() == (9, 1, 3)
    assert node.coverage() == 1 - 3 / 9
    assert repr(node) == '<CovFile "file.py" 67%>'
    assert list(node.iter_tree()) == [(node, ())]


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
    assert node._children == dict()
    assert len(node) == 1
    assert node.num_executable_lines() == 5
    assert node.num_skipped_lines() == 3
    assert node.num_missed_lines() == 2
    assert node.num_covered_lines() == 5 - 2
    assert node.num_lines() == (5, 3, 2)
    assert node.coverage() == 1 - 2 / 5
    assert repr(node) == '<CovFile "path" 60%>'
    assert list(node.iter_tree()) == [(node, ())]


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
    mod_2 = CovFile('module_2.py', range(42), [], range(20, 24))
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

    assert root.num_lines() == (152, 11, 17)

    paths = {node.name: path for node, path in root.iter_tree()}
    assert paths == {
        'root': (),
        'module_1': ('module_1',),
        'module_2.py': ('module_2.py',),
        'module_3.py': ('module_1', 'module_3.py'),
        'module_4.py': ('module_1', 'module_4.py'),
        'module_5': ('module_1', 'module_5'),
        'module_6.py': ('module_1', 'module_5', 'module_6.py'),
    }
    cov = {
        node.name: round(node.coverage(), 2)
        for node, _ in root.iter_tree(lambda n: n.coverage() < 0.9)
    }
    assert cov == {
        'module_1': 0.88,
        'module_2.py': 0.9,
        'module_3.py': 0.83,
        'module_4.py': 0.83,
        'module_5': 0.94,
        # 'module_6.py': 0.94,  <- not descending into module_5
        'root': 0.89,
    }
