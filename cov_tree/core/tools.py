from typing import Collection


def missed_lines_str(
        missed: Collection[int],
        executable: Collection[int] | None = None,
) -> str:
    """Given a collection of integers (missed lines), return a string that lists
    the missed intervals, respecting that the entirety of integers (all
    executable lines) might miss some integers (lines).

    Args:
        missed: The collection of the missedn lines.
        executable: A collection of all (executable and not skipped) lines. If
                    not given / None, it default to all integral numbers.

    Returns:
        A human reable string of the missed intervals.

    Example:
        >>> missed_lines_str([3, 4, 6], [1, 2, 3, 4, 6, 7])
        '3-6'
        >>> missed_lines_str([2, 6, 9, 10], [1, 2, 3, 4, 5, 6, 9, 10, 11])
        '2, 6-10'
    """
    if len(missed) == 0:
        return ''

    if executable is None:
        executable = range(min(missed), max(missed) + 1)
    else:
        executable = sorted(set(executable))

    intervals: list[list[int]] = []
    interv: list[int] | None = None
    for line in executable:
        if line in missed:
            if interv is None:
                interv = [line, line]
            else:
                interv[1] = line
        elif interv is not None:
            intervals.append(interv)
            interv = None
    if interv is not None:
        intervals.append(interv)

    return ', '.join(str(a) if a == b else f'{a}-{b}' for a, b in intervals)
