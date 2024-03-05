from __future__ import annotations
import pytest
from typing import Collection

from cov_tree.core.tools import missed_lines_str


@pytest.mark.parametrize('lines, omega, string', [
    ([], None, ''),
    ([42], None, '42'),
    ([3, 11], None, '3, 11'),
    ([3, 11], range(15), '3, 11'),
    ([13, 11], range(10, 15), '11, 13'),
    ([3, 4], [1, 2, 3, 4, 5, 6], '3-4'),
    ([1, 2], [1, 2, 3, 4], '1-2'),
    ([3, 4, 6], [1, 2, 3, 4, 6, 7], '3-6'),
    ([3, 4, 6, 9, 10], [1, 2, 3, 4, 6, 7, 8, 9, 10], '3-6, 9-10'),
    ([5, 6, 7, 8], None, '5-8'),
    (
        [12, 17, 18, 20, 21, 22, 23, 27],
        [1, 3, 6, 12, 17, 18, 20, 21, 22, 23, 26, 27],
        '12-23, 27',
    ),
    ([5, 6, 7, 8, 21, 22, 23], None, '5-8, 21-23'),
    ([5, 7, 8, 21, 22, 23], None, '5, 7-8, 21-23'),
    ((5, 7, 8, 21, 22, 23), None, '5, 7-8, 21-23'),
    ({5, 7, 8, 21, 22, 23}, None, '5, 7-8, 21-23'),
    ([5, 7, 8, 21, 21, 22, 23], None, '5, 7-8, 21-23'),
    ([7, 8, 21, 21, 22], [7, 8, 8, 9, 11, 12, 21, 22, 22, 23], '7-8, 21-22'),
])
def test_line_list_to_human_str(
        lines: Collection[int],
        omega: Collection[int] | None,
        string: str,
) -> None:
    assert missed_lines_str(lines, omega) == string
