def build_program(d4, palette):
    # Original fixed colour pairing from the generator: colormap[c] is the target of c.
    colormap = (0, 5, 6, 4, 3, 1, 2, 7, 9, 8)
    table = {}
    for c in range(10):
        src = int(palette[c])
        dst = int(palette[colormap[c]])
        table[src] = dst
    lines = []
    lines.append('# Pointwise colour substitution; geometry (stripe orientation) is untouched.')
    lines.append('# d4 = %d does not alter the mechanism: each cell is recoloured by its own colour.' % int(d4))
    lines.append('TABLE = ' + repr(table))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    out = []')
    lines.append('    for row in grid:')
    lines.append('        new_row = []')
    lines.append('        for v in row:')
    lines.append('            v = int(v)')
    lines.append('            new_row.append(TABLE.get(v, v))')
    lines.append('        out.append(new_row)')
    lines.append('    return out')
    lines.append('')
    return '\n'.join(lines)
