def build_program(d4, palette):
    d4 = int(d4)
    yes = int(palette[1])
    no = int(palette[7])
    # The original rule checks for left-right (column-reversal) mirror symmetry.
    # A horizontal flip (d4>=4) keeps that axis. An odd number of clockwise
    # rotations turns it into top-bottom (row-reversal) symmetry in visible coordinates.
    vertical_axis = (d4 % 4) in (1, 3)
    if vertical_axis:
        check = "g[::-1, :]"
        axis_note = "top-bottom mirror (rows reversed)"
    else:
        check = "g[:, ::-1]"
        axis_note = "left-right mirror (columns reversed)"
    lines = []
    lines.append("import numpy as np")
    lines.append("")
    lines.append("YES_COLOUR = %d" % yes)
    lines.append("NO_COLOUR = %d" % no)
    lines.append("")
    lines.append("def solve(demonstrations, grid):")
    lines.append("    g = np.array(grid, dtype=int)")
    lines.append("    # Compare the grid with its %s." % axis_note)
    lines.append("    mirrored = %s" % check)
    lines.append("    symmetric = bool(np.array_equal(g, mirrored))")
    lines.append("    return [[YES_COLOUR if symmetric else NO_COLOUR]]")
    return "\n".join(lines) + "\n"
