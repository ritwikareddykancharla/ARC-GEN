"""Direct scene-coordinate programs; no augmentation-normalization wrappers.

These reviewed rewrites express the transformed operation itself. Other
families require a reviewed native-coordinate variant before augmented SFT.
"""

def direct_source(task_id, d4, palette):
    if task_id == 'f0100645':
        return '''from collections import Counter

def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    if len({row[0] for row in grid}) == 1 and len({row[-1] for row in grid}) == 1 and grid[0][0] != grid[0][-1]:
        walls = [(grid[0][-1], 0, 1), (grid[0][0], 0, -1)]
        border = {(row, col) for row in range(height) for col in (0, width - 1)}
    elif len(set(grid[0])) == 1 and len(set(grid[-1])) == 1 and grid[0][0] != grid[-1][0]:
        walls = [(grid[-1][0], 1, 0), (grid[0][0], -1, 0)]
        border = {(row, col) for row in (0, height - 1) for col in range(width)}
    else:
        raise ValueError("Expected two differently coloured opposite walls")
    out = [row[:] for row in grid]
    for colour, dy, dx in walls:
        remaining = {(row, col) for row in range(height) for col in range(width)
                     if grid[row][col] == colour and (row, col) not in border}
        objects = []
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            cells = [start]
            for row, col in cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        point = (row + dr, col + dc)
                        if point in remaining:
                            remaining.remove(point)
                            cells.append(point)
            objects.append(cells)
        objects.sort(key=lambda cells: -max(row * dy + col * dx for row, col in cells))
        for cells in objects:
            for row, col in cells:
                out[row][col] = background
            shift = 0
            while all(0 <= row + (shift + 1) * dy < height
                      and 0 <= col + (shift + 1) * dx < width
                      and out[row + (shift + 1) * dy][col + (shift + 1) * dx] == background
                      for row, col in cells):
                shift += 1
            for row, col in cells:
                out[row + shift * dy][col + shift * dx] = colour
    return out
'''
    if task_id in ('27a28665', '9110e3c5', 'd4469b4b'):
        # These are demonstration-defined legends, not fixed answer tables.
        # A valid generated episode must demonstrate the query's legend key.
        if task_id == '27a28665':
            key_body = 'return tuple(tuple(cell != background for cell in row) for row in grid)'
        elif task_id == '9110e3c5':
            key_body = '''counts = Counter(cell for row in grid for cell in row if cell != background)
    if not counts:
        raise ValueError("Missing foreground")
    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError("Ambiguous dominant colour")
    return ranked[0][0]'''
        else:
            key_body = '''colours = {cell for row in grid for cell in row if cell != background}
    if len(colours) != 1:
        raise ValueError("Expected one ink colour")
    return next(iter(colours))'''
        return '''from collections import Counter

def legend_key(grid):
    background = BACKGROUND
    KEY_BODY

def solve(demonstrations, grid):
    key = legend_key(grid)
    matches = [pair["output"] for pair in demonstrations if legend_key(pair["input"]) == key]
    if not matches:
        raise ValueError("Query legend entry is absent from the demonstrations")
    if any(output != matches[0] for output in matches[1:]):
        raise ValueError("Contradictory demonstrated legend")
    return [row[:] for row in matches[0]]
'''.replace('BACKGROUND', repr(palette[0])).replace('KEY_BODY', key_body)
    if task_id in ('a6f40cea', 'e12f9a14', 'f560132c', 'd6542281'):
        # These solvers recover their colour roles and geometry from visible
        # cells. Their reviewed domains support D4/palette changes directly.
        import ast
        from .program_targets import native_program
        source, _ = native_program(task_id)
        class EntryPoint(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                if node.name == '_native_solve':
                    node.name = 'solve'
                return self.generic_visit(node)
        tree = EntryPoint().visit(ast.parse(source))
        ast.fix_missing_locations(tree)
        return ast.unparse(tree) + '\n'
    if task_id == 'b74ca5d1':
        # Corner identity and glyph-local geometry are visible after any D4
        # transform. Infer colour roles, rather than undoing a permutation.
        return '''from collections import Counter

def solve(demonstrations, grid):
    height, width = len(grid), len(grid[0])
    counts = Counter(cell for row in grid for cell in row)
    background = counts.most_common(1)[0][0]
    corners = [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)]
    legend = {}
    protected = set()
    for row, col in corners:
        colour = grid[row][col]
        if colour != background:
            if colour in legend:
                raise ValueError("Corner colours must be distinct")
            legend[colour] = (row, col)
            protected.add((row, col))
    bodies = {}
    markers = []
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour in legend and (row, col) not in protected:
                markers.append((row, col, colour))
            elif colour != background and colour not in legend:
                bodies.setdefault(colour, []).append((row, col))
    objects = []
    for body_colour, cells in bodies.items():
        top = min(row for row, col in cells)
        bottom = max(row for row, col in cells)
        left = min(col for row, col in cells)
        right = max(col for row, col in cells)
        compatible = [(row, col, colour) for row, col, colour in markers
                      if max(bottom, row) - min(top, row) < 5
                      and max(right, col) - min(left, col) < 5]
        if len(compatible) != 1:
            raise ValueError("Each glyph needs one unambiguous marker")
        row, col, marker_colour = compatible[0]
        objects.append((body_colour, marker_colour, cells, (row, col)))
    out = [row[:] for row in grid]
    for body_colour, marker_colour, cells, marker in objects:
        for row, col in cells:
            out[row][col] = marker_colour
        out[marker[0]][marker[1]] = body_colour
    for body_colour, marker_colour, cells, marker in objects:
        silhouette = cells + [marker]
        top = min(row for row, col in silhouette)
        bottom = max(row for row, col in silhouette)
        left = min(col for row, col in silhouette)
        right = max(col for row, col in silhouette)
        corner_row, corner_col = legend[marker_colour]
        offset_row = 0 if corner_row == 0 else height - (bottom - top + 1)
        offset_col = 0 if corner_col == 0 else width - (right - left + 1)
        for row, col in silhouette:
            target = (offset_row + row - top, offset_col + col - left)
            if target not in protected:
                out[target[0]][target[1]] = marker_colour
    return out
'''
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
            def visit_Call(self, node):
                # A size-7 box may occupy 25/49 cells, so modal colour is
                # the outline rather than the background. This family's
                # background role is known and follows palette augmentation.
                if isinstance(node.func, ast.Name) and node.func.id == 'background':
                    return ast.copy_location(ast.Constant(palette[0]), node)
                return self.generic_visit(node)
            def visit_Dict(self, node):
                if [getattr(k,'value',None) for k in node.keys] == [5,7,9] and [getattr(v,'value',None) for v in node.values] == [8,4,3]:
                    node.values = [ast.Constant(palette[c]) for c in (8,4,3)]
                return self.generic_visit(node)
            def visit_FunctionDef(self, node):
                if node.name == '_native_solve':node.name = 'solve'
                return self.generic_visit(node)
        tree=Colours().visit(ast.parse(source));ast.fix_missing_locations(tree)
        return ast.unparse(tree)+'\n'
    from .direct_certificates import certified_source, certified_factory_source
    return certified_factory_source(task_id, d4, palette) or certified_source(task_id)
