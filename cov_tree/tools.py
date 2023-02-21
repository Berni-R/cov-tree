from typing import Collection


def missed_lines_str(
        missed: Collection[int],
        executable: Collection[int] | None = None,
) -> str:
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
