from __future__ import annotations
import sys
if sys.version_info >= (3, 10):
    from typing import TypeAlias  # pragma: no cover
else:
    from typing_extensions import TypeAlias  # pragma: no cover
    if sys.version_info < (3, 9):  # pragma: no cover
        from typing import Tuple
from typing import Sequence, Collection, Iterator, Callable
from abc import ABC, abstractproperty, abstractmethod
import os
from coverage import Coverage  # type: ignore
from coverage.types import TMorf  # type: ignore

from .tools import missed_lines_str


if sys.version_info >= (3, 9):
    Path: TypeAlias = tuple[str, ...]
else:
    Path: TypeAlias = Tuple[str, ...]
"""A convenience type alias for a tree path, i.e. a tuple of node names."""

PathLike: TypeAlias = Sequence[str]
"""A convenience type alias for a tree path-like type,
i.e. a sequence of node names. It can, but does not need to be a
:class:`~Path`."""


class CovNode(ABC):
    """A general node (i.e. a directory or file) of a module structure."""
    def __init__(self, name: str) -> None:
        self._name = name
        self._children: dict[str, 'CovNode'] = dict()
        self._parent: 'CovNode | None' = None
        super().__init__()

    @property
    def name(self) -> str:
        """The (file-/directory-)name of this node."""
        return self._name

    @property
    def is_leaf(self) -> bool:
        """Whether this is a leaf node, i.e. an ordinary file."""
        return not self._children

    @property
    def parent(self) -> 'CovNode | None':
        """A reference to the parent node. None, if this is the root."""
        return self._parent

    @property
    def root(self) -> 'CovNode':
        """A reference to the root node of the tree."""
        if self._parent is None:
            return self
        return self._parent.root

    @property
    def is_root(self) -> bool:
        """Whether this is the root node of this tree.

        This is quivalent to ``self.root == self``."""
        return self._parent is None

    @abstractproperty
    def num_executable_lines(self) -> int:
        """The number of executable code lines. This does *not* include skipped
        lines."""
        ...

    @abstractproperty
    def num_skipped_lines(self) -> int:
        """The number of lines skipped by ``coverage``."""
        ...

    @abstractproperty
    def num_missed_lines(self) -> int:
        """The number of not covered lines:
        ``num_executable_lines - num_covered_lines``."""
        ...

    @property
    def num_total_lines(self) -> int:
        """The total number of lines, i.e.
        ``self.num_executable_lines + self.num_skipped_lines``."""
        return self.num_executable_lines + self.num_skipped_lines

    @property
    def num_covered_lines(self) -> int:
        """The number of covered lines:
        ``num_executable_lines - num_missed_lines``."""
        return self.num_executable_lines - self.num_missed_lines

    @abstractmethod
    def missed_lines_str(self, recursive: bool = True) -> str:
        """The line numbers of the missed lines in a human readable from.

        Args:
            recursive: If this is True for a module, return the lines of the
                       sub-module / files therein, otherwise just return ''.

        Returns:
            A string like '1-7, 11, 15-16' for files and something similar to
            '[file1.py: 3-5], [[file2.py: 5], [file4.py: 9-12, 15-20]]'.
        """
        ...

    @property
    def coverage(self) -> float:
        """The coverage. If there are no line, it defaults to 100%.

        It calculates ``1 - num_missed_lines / num_executable_lines``.
        """
        num_exec = self.num_executable_lines
        if num_exec == 0:
            return 1.0

        return 1 - self.num_missed_lines / num_exec

    def get_child(self, name: str) -> 'CovNode':
        """The the child with the given name."""
        return self._children[name]

    def __getitem__(self, name: str) -> 'CovNode':
        return self._children[name]

    def iter_tree(
            self,
            descend: Callable[['CovNode'], bool] | None = None,
    ) -> Iterator['CovNode']:
        """Iterator over all node (leaf or not and self) in this tree.

        Args:
            descend: An optional callable that takes a node. If there turn value
                     is True, descend into this node, otherwise do not yield its
                     children.

        Yields:
            All the nodes in this tree.
        """
        yield self

        if descend is None or descend(self):
            for child in self._children.values():
                yield from child.iter_tree(descend)

    def insert_child(
            self,
            node: 'CovNode',
            at_path: PathLike = tuple(),
    ) -> None:
        """Insert a new node into this tree.

        Args:
            node: The node to insert.
            at_path: If the path is None, place the new node as a child.
                     Otherwise follow the given path and then place the node
                     there as a child.
        """
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
        """To number of (direct) children."""
        return len(self._children)

    @property
    def children(self) -> tuple['CovNode', ...]:
        """A tuple to the (direct) children."""
        return tuple(self._children.values())

    @property
    def children_names(self) -> tuple[str, ...]:
        """A tuple with the names of the children. This is equivalent to
        ``tuple(child.name for child in self)``."""
        return tuple(self._children.keys())

    @property
    def depth(self) -> int:
        """The depth of this node in the tree
        (which implies that the root always has depth 0)."""
        return 0 if self._parent is None else (self._parent.depth + 1)

    @property
    def path(self) -> Path:
        """The path in the tree to this node. The path is sequence of node names
        (and of type :class:`~Path`)."""
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
        """Create a leaf node from a coverage report and its path.

        Args:
            cov: A :class:`coverage.Coverage` object with the data.
            path: The path as in the :class:`Coverage` object for which we want
                  to create the node.
            name: The name this node will have. It default to the filename
                  (without the directory) given by :obj:`path`.

        Returns:
            A new instance of :class:`~CovNode` with the data as given by the
            :obj:`cov` for :obj:`path`.
        """
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
        if not recursive:
            return ''

        missed: list[str] = []
        for child in self._children.values():
            child_miss = child.missed_lines_str(recursive)
            if child_miss:
                missed.append(f'[{child._name}: {child_miss}]')
        return ', '.join(missed)
