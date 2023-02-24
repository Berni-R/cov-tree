from typing import Sequence, TypeAlias, Collection, Iterator, Callable
from abc import ABC, abstractproperty, abstractmethod
import os
from coverage import Coverage  # type: ignore
from coverage.types import TMorf  # type: ignore

from .tools import missed_lines_str


Path: TypeAlias = tuple[str, ...]
"""A convenience type alias for a tree path, i.e. a tuple of node names."""

PathLike: TypeAlias = Sequence[str]
"""A convenience type alias for a tree path-like type,
i.e. a sequence of node names."""


class CovNode(ABC):
    def __init__(self, name: str) -> None:
        self._name = name
        self._children: dict[str, 'CovNode'] = dict()
        self._parent: 'CovNode | None' = None
        super().__init__()

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_leaf(self) -> bool:
        return not self._children

    @property
    def parent(self) -> 'CovNode | None':
        return self._parent

    @property
    def root(self) -> 'CovNode':
        if self._parent is None:
            return self
        return self._parent.root

    @property
    def is_root(self) -> bool:
        return self._parent is None

    @abstractproperty
    def num_executable_lines(self) -> int:
        ...

    @abstractproperty
    def num_skipped_lines(self) -> int:
        ...

    @abstractproperty
    def num_missed_lines(self) -> int:
        ...

    @abstractmethod
    def missed_lines_str(self, recursive: bool = True) -> str:
        ...

    @property
    def coverage(self) -> float:
        """The coverage. If there are no line, it defaults to 100%.

        Returns:
            The fraction of covered lines as a float in the interval [0, 1].
        """
        num_exec = self.num_executable_lines
        if num_exec == 0:
            return 1.0

        return 1 - self.num_missed_lines / num_exec

    @property
    def num_lines(self) -> tuple[int, int, int]:
        return (
            self.num_executable_lines,
            self.num_skipped_lines,
            self.num_missed_lines,
        )

    @property
    def num_covered_lines(self) -> int:
        return self.num_executable_lines - self.num_missed_lines

    def get_child(self, name: str) -> 'CovNode':
        """The the child with the given name."""
        return self._children[name]

    def __getitem__(self, name: str) -> 'CovNode':
        return self._children[name]

    def iter_tree(
            self,
            descend: Callable[['CovNode'], bool] | None = None,
    ) -> Iterator['CovNode']:
        yield self

        if descend is None or descend(self):
            for child in self._children.values():
                yield from child.iter_tree(descend)

    def insert_child(
            self,
            node: 'CovNode',
            at_path: PathLike = tuple(),
    ) -> None:
        if at_path:
            at_path = tuple(at_path)
            module = at_path[0]
            if module not in self._children:
                self._children[module] = CovModule(module)
                self._children[module]._parent = self
            child = self._children[module]
            child.insert_child(node, at_path[1:])
        else:
            if node._name in self._children:
                raise RuntimeError(f'Module "{self._name}" already has a child '
                                   f'named "{node._name}"')
            self._children[node._name] = node
            node._parent = self

    @property
    def num_children(self) -> int:
        return len(self._children)

    @property
    def children(self) -> tuple['CovNode', ...]:
        return tuple(self._children.values())

    @property
    def children_names(self) -> tuple[str, ...]:
        return tuple(self._children.keys())

    @property
    def depth(self) -> int:
        return 0 if self._parent is None else (self._parent.depth + 1)

    @property
    def path(self) -> Path:
        if self._parent is None:
            return (self._name,)
        return self._parent.path + (self._name,)

    def __repr__(self) -> str:
        cov = self.coverage
        return f'<{type(self).__name__} "{self._name}" {cov:.0%}>'

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
            strict: bool = True,
    ) -> None:
        super().__init__(name)

        self.executable_lines = set(executable_lines)
        self.skipped_lines = set(skipped_lines)
        self.missed_lines = set(missed_lines)

        if strict:
            if set(missed_lines) - set(executable_lines):
                off = set(missed_lines) - set(executable_lines)
                raise ValueError(
                    f'Some missed lines that are not executable: {off}'
                )
            if set(skipped_lines) & set(executable_lines):
                off = set(skipped_lines) & set(executable_lines)
                raise ValueError(
                    f'Some skipped lines that are executable: {off}'
                )

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

    @property
    def num_executable_lines(self) -> int:
        return len(self.executable_lines)

    @property
    def num_skipped_lines(self) -> int:
        return len(self.skipped_lines)

    @property
    def num_missed_lines(self) -> int:
        return len(self.missed_lines)

    def missed_lines_str(self, recursive: bool = True) -> str:
        return missed_lines_str(self.missed_lines, self.executable_lines)

    def insert_child(self, child: 'CovNode', path: PathLike = tuple()) -> None:
        raise RuntimeError('Cannot insert a child to a file node!')


class CovModule(CovNode):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @property
    def num_executable_lines(self) -> int:
        return sum(
            child.num_executable_lines for child in self._children.values()
        )

    @property
    def num_skipped_lines(self) -> int:
        return sum(
            child.num_skipped_lines for child in self._children.values()
        )

    @property
    def num_missed_lines(self) -> int:
        return sum(
            child.num_missed_lines for child in self._children.values()
        )

    def missed_lines_str(self, recursive: bool = True) -> str:
        if recursive <= 0:
            return ''

        missed: list[str] = []
        for child in self._children.values():
            child_miss = child.missed_lines_str(recursive)
            if child_miss:
                missed.append(f'[{child._name}: {child_miss}]')
        return ', '.join(missed)
