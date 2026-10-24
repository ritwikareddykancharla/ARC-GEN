"""Reviewed bijective colour alignment for broader constructor domains.

These families use background=0 in the native program, while RE-ARC samples
the background. Align that role before the shared episode palette is sampled.
This changes neither geometry nor the constructor's input/output relation.

Each entry in ``ROLE_SPECS`` was reviewed against the RE-ARC generator and the
saved direct program (see ``reports/diversity-v1/role-certificates``):

* ``fixed``: colours the RE-ARC constructor hard-codes with the same meaning as
  the native program (output markers, anchors, seed legends). They must stay
  fixed points of the mapping and may never be the background or foreground.
* ``foreground``: the native colour of a single free foreground role, or None
  when the program does not name that role. The foreground is the unique input
  colour that is neither background nor fixed.
* ``input_colours``: exact number of input colours the role assignment needs.

The background is the strict modal input colour. Ties, collisions with fixed
colours and missing/ambiguous foregrounds raise ValueError; callers count them
as rejected proposals. Only input grids determine the mapping.
"""

from collections import Counter

ROLE_SPECS = {
    # First batch (reviewed in cf79bbc).
    "00d62c1b": {"fixed": (4,)},             # enclosed-region fill
    "025d127b": {},
    "10fcaaa3": {"fixed": (8,)},             # diagonal halo
    "1e0a9b12": {},
    "2013d3e2": {},
    "253bf280": {"fixed": (3,), "foreground": 8, "input_colours": 2},  # line fill; endpoints
    "44d8ac46": {"fixed": (2,)},             # square-hole fill
    # Second batch: background-only programs (other colours are read generically).
    "0a938d79": {},                          # alternating stripes from two seeds
    "25ff71a9": {},                          # shift one cell down
    "4347f46a": {},                          # hollow rectangles
    "46f33fce": {},                          # 4x upscale of sparse lattice
    "7468f01a": {},                          # crop and mirror
    # Second batch: background plus constructor-fixed marker colours.
    "0ca9ddb6": {"fixed": (1, 2, 4, 6, 7, 8)},  # seed legend and stamp colours
    "1caeab9d": {"fixed": (1,)},             # anchor; movers are read generically
    "31aa019c": {"fixed": (2,)},             # ring around the unique pixel
    "50cb2852": {"fixed": (8,)},             # rectangle interior fill
    "60b61512": {"fixed": (7,)},             # bounding-box fill
    # Second batch: background, one named foreground and fixed markers.
    "3aa6fb7a": {"fixed": (1,), "foreground": 8, "input_colours": 2},
    "4258a5f9": {"fixed": (1,), "foreground": 5, "input_colours": 2},
    "6d75e8bb": {"fixed": (2,), "foreground": 8, "input_colours": 2},
    "6e82a1ae": {"fixed": (1, 2, 3), "foreground": 5, "input_colours": 2},
    "56dc2b01": {"fixed": (2, 8), "foreground": 3, "input_colours": 3},  # bar, marker; shape
}

ROLE_ALIGNED = frozenset(ROLE_SPECS)


def _swap_target(palette, source, target):
    """Send ``source`` to ``target`` and whoever mapped there to source's old image."""
    holder = palette.index(target)
    palette[source], palette[holder] = target, palette[source]


def align_pair(task_id, pair):
    spec = ROLE_SPECS.get(task_id)
    if spec is None:
        return pair, list(range(10))
    counts = Counter(c for row in pair["input"] for c in row).most_common()
    if len(counts) < 2 or counts[0][1] == counts[1][1]:
        raise ValueError("Colour-role alignment requires a unique modal background")
    fixed = set(spec.get("fixed", ()))
    background = counts[0][0]
    if background in fixed:
        raise ValueError("Background collides with the family's output marker")
    if "input_colours" in spec and len(counts) != spec["input_colours"]:
        raise ValueError("Unexpected number of input colours for this role assignment")
    palette = list(range(10))
    _swap_target(palette, background, 0)
    target = spec.get("foreground")
    if target is not None:
        free = [c for c, _ in counts if c != background and c not in fixed]
        if len(free) != 1:
            raise ValueError("Foreground role requires one colour distinct from fixed markers")
        # RE-ARC randomizes this colour; the native program names it explicitly.
        _swap_target(palette, free[0], target)
    if palette[background] != 0 or any(palette[c] != c for c in fixed):
        raise ValueError("Alignment would move a fixed colour role")
    aligned = {k: [[palette[c] for c in row] for row in pair[k]]
               for k in ("input", "output")}
    return aligned, palette
