from pytest_mock import MockFixture
from typing import Collection

from cov_tree.core.node import CovFile
from cov_tree.core.builder import build_cov_tree


MOCK_TREE: dict[str, dict[str, Collection[int]]] = {
    '/path/to/folder/root/mod1/file1.py': {
        'executable_lines': set(range(20)) - {11, 12, 19},
        'skipped_lines': [11, 12, 19],
        'missed_lines': [1, 7, 8, 9, 15, 16, 17],
    },
    '/path/to/folder/root/mod1/file2.py': {
        'executable_lines': range(10),
        'skipped_lines': [],
        'missed_lines': [8, 9],
    },
    '/path/to/folder/root/mod2.py': {
        'executable_lines': set(range(15)) - {12, 13},
        'skipped_lines': [12, 13],
        'missed_lines': [1, 2, 3],
    },
}


def test_build_cov_tree(mocker: MockFixture) -> None:
    mocker.patch('coverage.Coverage.combine')
    mocker.patch(
        'coverage.CoverageData.measured_files',
        lambda _: MOCK_TREE.keys(),
    )
    mocker.patch(
        'cov_tree.core.node.CovFile.from_coverage',
        lambda _, path, name: CovFile(name, **MOCK_TREE[path]),  # type: ignore
    )

    base, tree = build_cov_tree()
    assert base == '/path/to/folder'

    assert tree.name == 'root'
    assert len(tree) == 5
    assert tree.get_child('mod2.py').num_skipped_lines() == 2
    cov = {
        node.name: round(node.coverage(), 2)
        for node, _ in tree.iter_tree()
    }
    assert cov == {
        'file1.py': 0.59,
        'file2.py': 0.8,
        'mod1': 0.67,
        'mod2.py': 0.77,
        'root': 0.7,
    }

    base, tree = build_cov_tree(drop_ext=True)
    names = {node.name for node, _ in tree.iter_tree()}
    assert names == set('file1 file2 mod1 mod2 root'.split())
