from typing import Sequence, TypeAlias, Collection
from abc import ABC, abstractmethod
import os
from coverage import Coverage
from coverage.types import TMorf


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
    def missed_lines_str(self) -> str:
        ...

    def coverage(self, exclude_skipped: bool = False) -> float:
        """The coverage. If there are no line, it defaults to 100%.

        Args:
            exclude_skipped: Exclude the skipped lines from the total.

        Returns:
            The fraction of covered lines as a float in the interval [0, 1].
        """
        num_exec, num_skipped, num_missed = self.num_lines()
        if num_exec == 0:
            return 1.0

        if exclude_skipped:
            total = num_exec - num_skipped
            num_covered = num_exec - num_skipped - num_missed
        else:
            total = num_exec
            num_covered = num_exec - num_missed

        return num_covered / total

    def num_lines(self) -> tuple[int, int, int]:
        return (
            self.num_executable_lines(),
            self.num_skipped_lines(),
            self.num_missed_lines(),
        )

    def num_covered_lines(self) -> int:
        num_exec, num_skipped, num_missed = self.num_lines()
        return num_exec - num_skipped - num_missed

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
        cov = self.coverage(exclude_skipped=False)
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
            missed_lines_str: str = '',
    ) -> None:
        super().__init__(name)

        self.executable_lines = list(executable_lines)
        self.skipped_lines = list(skipped_lines)
        self.missed_lines = list(missed_lines)
        # TODO: this could become inconsistent!!!
        self._missed_lines_str = missed_lines_str

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
        return cls(
            name=name,
            executable_lines=executable_lines,
            skipped_lines=skipped_lines,
            missed_lines=missed_lines,
            missed_lines_str=miss_str,
        )

    def num_executable_lines(self) -> int:
        return len(self.executable_lines)

    def num_skipped_lines(self) -> int:
        return len(self.skipped_lines)

    def num_missed_lines(self) -> int:
        return len(self.missed_lines)

    def missed_lines_str(self) -> str:
        return self._missed_lines_str

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

    def missed_lines_str(self) -> str:
        return ''
