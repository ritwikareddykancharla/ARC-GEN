"""Direct scene-coordinate programs; no augmentation-normalization wrappers.

These reviewed rewrites express the transformed operation itself. Other
families require a reviewed native-coordinate variant before augmented SFT.
"""

def direct_source(task_id, d4, palette):
    if task_id == 'f18ec8cc':
        # A quarter turn changes vertical strips into horizontal strips; a
        # reflection/reversal changes which end strip moves to the other end.
        # Inspect and move strips in the visible coordinates, never normalize.
        horizontal = d4 % 2 == 1
        from_start = d4 in (0, 1, 6, 7)
        source = '''from collections import Counter

def solve(demonstrations, grid):
    lines = LINES
    colours = []
    for line in lines:
        colour, count = Counter(line).most_common(1)[0]
        if count * 2 <= len(line):
            raise ValueError("Each strip needs a strict majority colour")
        colours.append(colour)
    CUT
    MOVE
'''
        source = source.replace('LINES', 'grid' if horizontal else 'list(zip(*grid))')
        if from_start:
            source = source.replace('CUT', '''cut = 1
    while cut < len(colours) and colours[cut] == colours[0]:
        cut += 1''')
        else:
            source = source.replace('CUT', '''cut = len(colours) - 1
    while cut > 0 and colours[cut - 1] == colours[-1]:
        cut -= 1''')
        source = source.replace('MOVE',
            'return [list(row) for row in grid[cut:] + grid[:cut]]' if horizontal
            else 'return [list(row[cut:]) + list(row[:cut]) for row in grid]')
        return source
    if task_id == '00576224':
        # After a quarter turn, the mirrored middle row-band becomes a column-band.
        if d4 % 2:
            return '''def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    out = [[0] * (3 * width) for _ in range(3 * height)]
    for band_y in range(3):
        for band_x in range(3):
            for row in range(height):
                source_row = height - 1 - row if band_x == 1 else row
                for col in range(width):
                    out[band_y * height + row][band_x * width + col] = grid[source_row][col]
    return out
'''
        return '''def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    out = [[0] * (3 * width) for _ in range(3 * height)]
    for band_y in range(3):
        for band_x in range(3):
            for row in range(height):
                for col in range(width):
                    source_col = width - 1 - col if band_y == 1 else col
                    out[band_y * height + row][band_x * width + col] = grid[row][source_col]
    return out
'''
    if task_id == '0692e18c':
        return '''def solve(demonstrations, grid):
    background = BACKGROUND
    height, width = len(grid), len(grid[0])
    colours = {cell for row in grid for cell in row if cell != background}
    if len(colours) != 1:
        raise ValueError("Expected exactly one foreground colour")
    colour = next(iter(colours))
    out = [[background] * (width * width) for _ in range(height * height)]
    for block_row in range(height):
        for block_col in range(width):
            if grid[block_row][block_col] == background:
                continue
            for row in range(height):
                for col in range(width):
                    if grid[row][col] == background:
                        out[block_row * height + row][block_col * width + col] = colour
    return out
'''.replace('BACKGROUND', repr(palette[0]))
    if task_id == '00dbd492':
        # Connectivity/size semantics commute with D4. Only colour roles change.
        from .program_targets import native_program
        import ast
        source, _ = native_program(task_id)
        class Colours(ast.NodeTransformer):
            def visit_Dict(self, node):
                if [getattr(k,'value',None) for k in node.keys] == [5,7,9] and [getattr(v,'value',None) for v in node.values] == [8,4,3]:
                    node.values = [ast.Constant(palette[c]) for c in (8,4,3)]
                return self.generic_visit(node)
            def visit_FunctionDef(self, node):
                if node.name == '_native_solve':node.name = 'solve'
                return self.generic_visit(node)
        tree=Colours().visit(ast.parse(source));ast.fix_missing_locations(tree)
        return ast.unparse(tree)+'\n'
    return None
