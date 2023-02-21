from typing import Sequence, TypeAlias, Collection, Iterator, Callable
from abc import ABC, abstractmethod
import os
from coverage import Coverage  # type: ignore
from coverage.types import TMorf  # type: ignore

from .tools import missed_lines_str


Path: TypeAlias = Sequence[str]
"""A convenience type alias for a three path, i.e. a sequence of node names."""


class CovNode(ABC):
    def __init__(self, name: str) -> None:
        self._name = name
        self._children: dict[str, 'CovNode'] = dict()
        super().__init__()

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_leaf(self) -> bool:
        return not self._children

    @abstractmethod
    def num_executable_lines(self) -> int:
        ...

    @abstractmethod
    def num_skipped_lines(self) -> int:
        ...

    @abstractmethod
    def num_missed_lines(self) -> int:
        ...

    @abstractmethod
    def missed_lines_str(self, recursive: bool = True) -> str:
        ...

    def coverage(self) -> float:
        """The coverage. If there are no line, it defaults to 100%.

        Returns:
            The fraction of covered lines as a float in the interval [0, 1].
        """
        num_exec = self.num_executable_lines()
        if num_exec == 0:
            return 1.0

        return 1 - self.num_missed_lines() / num_exec

    def num_lines(self) -> tuple[int, int, int]:
        return (
            self.num_executable_lines(),
            self.num_skipped_lines(),
            self.num_missed_lines(),
        )

    def num_covered_lines(self) -> int:
        return self.num_executable_lines() - self.num_missed_lines()

    def get_child(self, name: str) -> 'CovNode':
        """The the child with the given name."""
        return self._children[name]

    def __getitem__(self, name: str) -> 'CovNode':
        return self._children[name]

    def follow_path(self, path: Path) -> 'CovNode':
        node = self
        for name in path:
            node = node._children[name]
        return node

    def iter_tree(
            self,
            descend: Callable[['CovNode'], bool] | None = None,
            _curr_path: Path = tuple(),
    ) -> Iterator[tuple['CovNode', Path]]:
        yield self, _curr_path

        if descend is None or descend(self):
            curr_path = tuple(_curr_path)
            for child in self._children.values():
                yield from child.iter_tree(descend, curr_path + (child.name,))

    def insert_child(self, child: 'CovNode', path: Path = tuple()) -> None:
        node = self
        for name in path:
            if name not in node._children:
                node._children[name] = CovModule(name)
            node = node._children[name]

        if child.name in node._children:
            raise RuntimeError(f'Module "{node.name}" already has a child '
                               f'named "{child.name}"')
        node._children[child.name] = child

    @property
    def num_children(self) -> int:
        return len(self._children)

    @property
    def children(self) -> tuple['CovNode', ...]:
        return tuple(self._children.values())

    @property
    def children_names(self) -> tuple[str, ...]:
        return tuple(self._children.keys())

    def __repr__(self) -> str:
        cov = self.coverage()
        return f'<{type(self).__name__} "{self.name}" {cov:.0%}>'

    def __len__(self) -> int:
        cnt = 1
        for child in self._children.values():
            cnt += len(child)
        return cnt


class CovFile(CovNode):
    def __init__(
            self,
            name: str,
            executable_lines: Collection[int] = tuple(),
            skipped_lines: Collection[int] = tuple(),
            missed_lines: Collection[int] = tuple(),
    ) -> None:
        super().__init__(name)

        self.executable_lines = list(executable_lines)
        self.skipped_lines = list(skipped_lines)
        self.missed_lines = list(missed_lines)

    @classmethod
    def from_coverage(
            cls,
            cov: Coverage,
            path: TMorf,
            name: str | None = None,
    ) -> 'CovFile':
        filename, executable_lines, skipped_lines, missed_lines, miss_str = (
            cov.analysis2(path)
        )
        if name is None:
            _, name = os.path.split(filename)
        node = cls(
            name=name,
            executable_lines=executable_lines,
            skipped_lines=skipped_lines,
            missed_lines=missed_lines,
        )
        assert miss_str == node.missed_lines_str()
        return node

    def num_executable_lines(self) -> int:
        return len(self.executable_lines)

    def num_skipped_lines(self) -> int:
        return len(self.skipped_lines)

    def num_missed_lines(self) -> int:
        return len(self.missed_lines)

    def missed_lines_str(self, recursive: bool = True) -> str:
        return missed_lines_str(self.missed_lines, self.executable_lines)

    def insert_child(self, child: 'CovNode', path: Path = tuple()) -> None:
        raise RuntimeError('Cannot insert a child to a file node!')


class CovModule(CovNode):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def num_executable_lines(self) -> int:
        return sum(
            child.num_executable_lines() for child in self._children.values()
        )

    def num_skipped_lines(self) -> int:
        return sum(
            child.num_skipped_lines() for child in self._children.values()
        )

    def num_missed_lines(self) -> int:
        return sum(
            child.num_missed_lines() for child in self._children.values()
        )

    def missed_lines_str(self, recursive: bool = True) -> str:
        if recursive <= 0:
            return ''

        missed: list[str] = []
        for child in self._children.values():
            child_miss = child.missed_lines_str(recursive)
            if child_miss:
                missed.append(f'[{child.name}: {child_miss}]')
        return ', '.join(missed)
