from typing import Sequence, TypeAlias
from dataclasses import dataclass, field


Path: TypeAlias = Sequence[str]


@dataclass(eq=False, slots=True, repr=False)
class CovStats:
    name: str
    children: list['CovStats'] = field(default_factory=list)
    num_lines: int = 0
    num_skipped: int = 0
    num_missed: int = 0
    missed_lines: list[int] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return not len(self.children)

    @property
    def lines(self) -> tuple[int, int, int]:
        return self.num_lines, self.num_skipped, self.num_missed

    @property
    def num_covered(self) -> int:
        return self.num_lines - self.num_skipped - self.num_missed

    def coverage(self, exclude_skipped: bool = True) -> float:
        if self.num_lines == 0:
            return 1.0

        if exclude_skipped:
            total = self.num_lines - self.num_skipped
        else:
            total = self.num_lines

        return self.num_covered / total

    def get_child(self, name: str) -> 'CovStats | None':
        for child in self.children:
            if child.name == name:
                return child
        return None

    def __repr__(self) -> str:
        cov = self.coverage(exclude_skipped=True)
        return f'<{type(self).__name__} "{self.name}" {cov:.0%}>'

    def __len__(self) -> int:
        cnt = 1
        for child in self.children:
            cnt += len(child)
        return cnt
