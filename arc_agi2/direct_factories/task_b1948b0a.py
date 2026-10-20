def build_program(d4, palette):
    src = int(palette[6])
    dst = int(palette[2])
    lines = []
    lines.append('SRC = %d' % src)
    lines.append('DST = %d' % dst)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    # Pointwise recolour: the (palette-mapped) background colour SRC becomes DST.')
    lines.append('    # The rule acts cell by cell, so it is the same in every D4 frame.')
    lines.append('    # Every other colour, including the scattered pixels, is kept as it is.')
    lines.append('    out = []')
    lines.append('    for row in grid:')
    lines.append('        out.append([DST if int(v) == SRC else int(v) for v in row])')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
