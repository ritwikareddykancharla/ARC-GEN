"""Reviewed bijective colour alignment for broader constructor domains.

These families use background=0 in the native program, while RE-ARC samples
the background. Align that role before the shared episode palette is sampled.
This changes neither geometry nor the constructor's input/output relation.
Output colours 4 (enclosed-region fill), 8 (diagonal halo) and 3 (line fill)
and 2 (square-hole fill) are preserved. Line endpoints are aligned to native cyan for 253bf280.
"""

from collections import Counter

ROLE_ALIGNED = frozenset(("00d62c1b", "025d127b", "10fcaaa3", "1e0a9b12",
                          "2013d3e2", "253bf280", "44d8ac46"))


def align_pair(task_id, pair):
    if task_id not in ROLE_ALIGNED:
        return pair, list(range(10))
    counts = Counter(c for row in pair["input"] for c in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Colour-role alignment requires a unique modal background")
    background = counts[0][0]
    reserved = {"00d62c1b": 4, "10fcaaa3": 8, "253bf280": 3, "44d8ac46": 2}.get(task_id)
    if background == reserved:
        raise ValueError("Background collides with the family's output marker")
    palette = list(range(10))
    palette[0], palette[background] = background, 0
    if task_id == "253bf280":
        if len(counts) != 2 or counts[1][0] == reserved:
            raise ValueError("Line connection requires one foreground colour distinct from fill")
        # RE-ARC randomizes the endpoint colour; the native target uses cyan.
        # Complete a bijection while leaving background and green fill fixed.
        foreground = counts[1][0]
        source_of_cyan = palette.index(8)
        palette[foreground], palette[source_of_cyan] = 8, palette[foreground]
    aligned = {k: [[palette[c] for c in row] for row in pair[k]]
               for k in ("input", "output")}
    return aligned, palette
