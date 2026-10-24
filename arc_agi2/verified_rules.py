"""Reviewed rule verifiers for demonstrated failures of archived programs.

The original reference packets are immutable. Overrides are explicit and
separately documented, not silent edits to teacher reasoning or benchmark data.
"""
from collections import Counter
from itertools import permutations


def panel_chain(grid):
    """Use all equal-sized panels in the unique complete contact chain.

    The saved 78332cb0 program chooses the first matching panel greedily.
    A reordered version of canonical train[2] disproves that implementation:
    a repeated contact requires consuming the bar before taking the exit.
    This verifier enumerates full panel permutations (at most six panels).
    It does not import constructor code, latent order, or expected output.
    """
    from .runtime import grid as check_grid
    a = check_grid(grid)
    H, W = len(a), len(a[0])
    counts = Counter(v for row in a for v in row)
    ranking = counts.most_common()
    if len(ranking) < 2 or ranking[0][1] == ranking[1][1]:
        raise ValueError('Panel background must be unambiguous')
    bg = ranking[0][0]
    row_lines = [(i, row[0]) for i, row in enumerate(a) if len(set(row)) == 1]
    col_lines = [(i, col[0]) for i, col in enumerate(zip(*a)) if len(set(col)) == 1]
    line_counts = Counter(c for _, c in row_lines+col_lines if c != bg)
    leaders = line_counts.most_common()
    if not leaders or (len(leaders) > 1 and leaders[0][1] == leaders[1][1]):
        raise ValueError('Panel divider colour must be unambiguous')
    divider = leaders[0][0]

    def spans(cuts, extent):
        borders = [-1] + sorted(cuts) + [extent]
        return [(left+1, right) for left, right in zip(borders, borders[1:])
                if right > left+1]

    ys = spans([i for i,c in row_lines if c == divider], H)
    xs = spans([i for i,c in col_lines if c == divider], W)
    panels = [[row[x0:x1] for row in a[y0:y1]]
              for y0,y1 in ys for x0,x1 in xs]
    if not 2 <= len(panels) <= 6:
        raise ValueError('Supported chain has two to six panels')
    h,w = len(panels[0]), len(panels[0][0])
    if any(len(p) != h or any(len(row) != w for row in p) for p in panels):
        raise ValueError('Panels must have equal dimensions')
    if any(len({v for row in p for v in row if v != bg}) != 1 for p in panels):
        raise ValueError('Each panel must hold one monochrome shape')

    solutions = []
    for vertical in (True,False):
        ends, starts = [], []
        valid = True
        for p in panels:
            entry = p[0] if vertical else [row[0] for row in p]
            exit = p[-1] if vertical else [row[-1] for row in p]
            cross = ([row[0] for row in p]+[row[-1] for row in p]
                     if vertical else p[0]+p[-1])
            ent = tuple(i for i,v in enumerate(entry) if v != bg)
            ext = tuple(i for i,v in enumerate(exit) if v != bg)
            if len(ent)>1 or len(ext)>1 or any(v != bg for v in cross):
                valid = False
                break
            starts.append(ent); ends.append(ext)
        if not valid:
            continue
        if sum(not e for e in starts) != 1 or sum(not e for e in ends) != 1:
            continue
        for order in permutations(range(len(panels))):
            if starts[order[0]] or ends[order[-1]]:
                continue
            if all(ends[left] and ends[left] == starts[right]
                   for left,right in zip(order,order[1:])):
                solutions.append((vertical,order))
    if len(solutions) != 1:
        raise ValueError('Panels do not form a unique complete chain')
    vertical,order = solutions[0]
    selected = [panels[i] for i in order]
    if vertical:
        result = []
        for i,p in enumerate(selected):
            if i:result.append([divider]*w)
            result.extend([row[:] for row in p])
    else:
        result = [[] for _ in range(h)]
        for i,p in enumerate(selected):
            for y in range(h):
                if i:result[y].append(divider)
                result[y].extend(p[y])
    return check_grid(result)


def cropped_mirror_patch(grid):
    """Recover a rectangle masked in an N-wide crop of an (N+2)-wide mosaic.

    The canonical N=30 gives mirror coordinate 31. Smaller even sizes are
    labelled synthetic extensions of the same two-cell crop geometry.
    Visible cells in each horizontal/vertical reflection orbit must agree.
    A transpose-orbit fallback preserves the weak cue used by the original
    first demonstration. No constructor, hidden quadrant or target is read.
    """
    from .runtime import grid as check_grid
    a = check_grid(grid)
    n = len(a)
    if n != len(a[0]) or n % 2 or not 12 <= n <= 30:
        raise ValueError('Expected an even square crop of side 12..30')
    mask = {(r,c) for r,row in enumerate(a) for c,v in enumerate(row) if v == 7}
    if not mask:
        raise ValueError('Missing mask rectangle')
    r0,r1 = min(r for r,c in mask),max(r for r,c in mask)
    c0,c1 = min(c for r,c in mask),max(c for r,c in mask)
    if len(mask) != (r1-r0+1)*(c1-c0+1):
        raise ValueError('Mask must be one complete rectangle')
    axis = n+1
    def key(r,c):
        return min(r,axis-r),min(c,axis-c)
    visible = {}
    for r,row in enumerate(a):
        for c,value in enumerate(row):
            if value == 7:
                continue
            orbit = key(r,c)
            if orbit in visible and visible[orbit] != value:
                raise ValueError('Visible reflection partners disagree')
            visible[orbit] = value
    output = []
    for r in range(r0,r1+1):
        row = []
        for c in range(c0,c1+1):
            orbit = key(r,c)
            if orbit not in visible:
                orbit = orbit[::-1]
            if orbit not in visible:
                raise ValueError('Masked cell lacks a visible reconstruction cue')
            row.append(visible[orbit])
        output.append(row)
    return check_grid(output)


def self_tiling(grid):
    """007bbfb7: a copy of the input replaces every nonzero input cell."""
    height, width = len(grid), len(grid[0])
    return [[grid[r % height][c % width] if grid[r // height][c // width] else 0
             for c in range(width * width)] for r in range(height * height)]


def legend_object_chart(grid):
    """aaecdb9a: count 8-connected objects; background is the legend's colour 7.

    Dense scenes can contain more cells of a legend colour than background.
    The modal colour therefore cannot identify background for this rule.
    """
    legend = (5, 2, 8, 9, 6)
    if any(value not in (*legend, 7) for row in grid for value in row):
        raise ValueError('Colour outside the aaecdb9a legend')
    counts = []
    for colour in legend:
        remaining = {(r, c) for r, row in enumerate(grid)
                     for c, value in enumerate(row) if value == colour}
        count = 0
        while remaining:
            count += 1
            frontier = [remaining.pop()]
            while frontier:
                r, c = frontier.pop()
                neighbours = {(r + dr, c + dc) for dr in (-1, 0, 1)
                              for dc in (-1, 0, 1)} & remaining
                remaining -= neighbours
                frontier.extend(neighbours)
        counts.append(count)
    height = max(counts)
    if height == 0:
        raise ValueError('Expected at least one legend object')
    return [[colour if r >= height - count else 7
             for colour, count in zip(legend, counts)] for r in range(height)]


def nested_frame_band(grid):
    """3a301edc: identify nesting by bounding-box containment, not ink area.

    A thin outer frame can have fewer ink cells than the solid inner square.
    The archived size sort reverses the two objects in that case.
    """
    height, width = len(grid), len(grid[0])
    colours = {c for row in grid for c in row if c != 0}
    if len(colours) != 2:
        raise ValueError('Expected two nested foreground colours')
    boxes = []
    for colour in colours:
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                 if v == colour]
        y0, y1 = min(r for r, c in cells), max(r for r, c in cells)
        x0, x1 = min(c for r, c in cells), max(c for r, c in cells)
        boxes.append(((y1-y0+1)*(x1-x0+1), (y0, x0, y1, x1), colour))
    boxes.sort(reverse=True)
    _, (y0, x0, y1, x1), frame = boxes[0]
    _, (iy0, ix0, iy1, ix1), ink = boxes[1]
    if not (y0 < iy0 <= iy1 < y1 and x0 < ix0 <= ix1 < x1):
        raise ValueError('Expected strictly nested boxes')
    for r in range(height):
        for c in range(width):
            expected = ink if iy0 <= r <= iy1 and ix0 <= c <= ix1 else (
                frame if y0 <= r <= y1 and x0 <= c <= x1 else 0)
            if grid[r][c] != expected:
                raise ValueError('Invalid nested rectangle')
    thick = min(iy1-iy0+1, ix1-ix0+1, y0, x0)
    out = [row[:] for row in grid]
    for r in range(max(0, y0-thick), min(height, y1+thick+1)):
        for c in range(max(0, x0-thick), min(width, x1+thick+1)):
            if not (y0 <= r <= y1 and x0 <= c <= x1):
                out[r][c] = ink
    return out


def native_side_beam(grid):
    """7e2bad24: replay the declared native side-contact mirror rule.

    Pair label checker only. It uses the independent coordinate replay in
    beam_endpoint_evidence (original colours: beam 1, mirror 2, glass 3) and
    selects the 'side' reading that the native constructor declares. Exported
    target programs still learn the endpoint convention from demonstrations.
    """
    from .beam_endpoint_evidence import RULES, beam_predictions
    prediction = beam_predictions(grid, list(range(10)))[RULES.index('side')]
    if prediction is None:
        raise ValueError('Visible beam prefix contradicts the side-contact rule')
    return [list(row) for row in prediction]


def midpoint_xor_panels(grid):
    """34b99a2b: XOR of the two equal panels around the midpoint divider.

    Pair label checker only (native colours). Every canonical and teaching
    fixture, and every constructor output, is an odd-width grid whose exact
    midpoint column (W - 1) / 2 is a full single-colour non-zero divider with
    equal panels on both sides. The divider is located geometrically, never
    by scanning for the first full column, so full-height internal panel
    columns are ordinary content. Inputs without this geometry are rejected
    instead of guessed.
    """
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0
    if not rows or width < 3 or width % 2 == 0 or any(len(r) != width for r in rows):
        raise ValueError('Expected an odd-width grid with a midpoint divider column')
    mid = width // 2
    divider = {r[mid] for r in rows}
    if len(divider) != 1 or 0 in divider:
        raise ValueError('Midpoint column is not a full non-background divider')
    return [[2 if (r[x] != 0) != (r[mid + 1 + x] != 0) else 0 for x in range(mid)]
            for r in rows]


def midpoint_or_panels(grid):
    """195ba7dc: OR of the two equal panels around the midpoint divider.

    Pair label checker only (native colours). Every canonical and teaching
    fixture, and every constructor output, is an odd-width grid whose exact
    midpoint column (W - 1) / 2 is a full single-colour non-zero divider with
    equal panels on both sides. A cell is 1 where either panel is non-zero.
    The divider is located geometrically, so full or empty panel columns are
    ordinary content. Inputs without this geometry are rejected, not guessed.
    """
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0
    if not rows or width < 3 or width % 2 == 0 or any(len(r) != width for r in rows):
        raise ValueError('Expected an odd-width grid with a midpoint divider column')
    mid = width // 2
    divider = {r[mid] for r in rows}
    if len(divider) != 1 or 0 in divider:
        raise ValueError('Midpoint column is not a full non-background divider')
    return [[1 if r[x] != 0 or r[mid + 1 + x] != 0 else 0 for x in range(mid)] for r in rows]


def separated_priority_panels(grid):
    """281123b4: overlay four equal panels at fixed separator positions.

    Pair label checker only (native colours). Every canonical and teaching
    fixture, and every constructor output, has width 4w + 3 with full
    single-colour non-zero separator columns at w, 2w + 1 and 3w + 2, and
    background 0. Panels are read at those positions (never by modal colour or
    first uniform column), and each output cell takes the highest-priority
    non-zero panel colour, 9 > 4 > 8 > 5, else 0. Unexpected colours or
    geometry raise.
    """
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0
    if not rows or width < 7 or (width - 3) % 4 or any(len(r) != width for r in rows):
        raise ValueError('Expected width 4w+3 with three separator columns')
    w = (width - 3) // 4
    seps = (w, 2 * w + 1, 3 * w + 2)
    colours = {r[x] for r in rows for x in seps}
    if len(colours) != 1 or 0 in colours:
        raise ValueError('Separator columns are not one full non-background colour')
    rank = {9: 0, 4: 1, 8: 2, 5: 3}
    out = []
    for r in rows:
        row = []
        for x in range(w):
            present = [r[k * (w + 1) + x] for k in range(4)]
            if any(v != 0 and v not in rank for v in present):
                raise ValueError('Panel holds a colour outside 0, 8, 5, 9, 4')
            on = [v for v in present if v != 0]
            row.append(min(on, key=rank.__getitem__) if on else 0)
        out.append(row)
    return out


def native_zero_adjacency(grid):
    """e0fb7511: black (0) cells with a 4-adjacent black cell become 8.

    Pair label checker only (native colours). Every canonical and teaching
    fixture, and every constructor output, is a blue (1) field with black (0)
    cells; a black cell whose up/down/left/right neighbour is also black turns
    azure (8), and an isolated black cell, including one touching other black
    cells only diagonally, stays 0. The target colour is the fixed native 0,
    never the modal or non-modal colour, so dense, tied, all-black and
    all-blue grids are ordinary content. Colours other than 0 and 1 raise.
    """
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0
    if not rows or not width or any(len(r) != width for r in rows):
        raise ValueError('Expected a rectangular grid')
    if any(v not in (0, 1) for r in rows for v in r):
        raise ValueError('Input holds a colour outside 0 and 1')
    height = len(rows)

    def black(y, x):
        return 0 <= y < height and 0 <= x < width and rows[y][x] == 0
    return [[8 if v == 0 and any(black(y + dy, x + dx) for dy, dx in
                                 ((1, 0), (-1, 0), (0, 1), (0, -1))) else v
             for x, v in enumerate(r)] for y, r in enumerate(rows)]


def fixed_colour_histogram(grid):
    """f3cdc58f: bottom-aligned bars of colours 1..4 in columns 0..3.

    Pair label checker only (native colours). Every canonical and teaching
    fixture, and every constructor output, is a black (0) grid holding each of
    colours 1, 2, 3 and 4 at least once. The answer has the same shape and is
    black except that column c - 1 holds a bar of colour c, standing on the
    bottom row, as tall as the number of colour-c cells. The colour-to-column
    legend is fixed by colour value, never by sorting the present non-modal
    colours, so grids where a bar colour is modal or ties with black are
    ordinary content. Inputs outside the domain raise instead of being
    guessed: colours outside 0..4, a missing bar colour, width below 4, or a
    count taller than the grid.
    """
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0
    if not rows or not width or any(len(r) != width for r in rows):
        raise ValueError('Expected a rectangular grid')
    if any(v not in (0, 1, 2, 3, 4) for r in rows for v in r):
        raise ValueError('Input holds a colour outside 0..4')
    height = len(rows)
    if width < 4:
        raise ValueError('Grid is narrower than the four bar columns')
    counts = Counter(v for r in rows for v in r)
    out = [[0] * width for _ in range(height)]
    for colour in (1, 2, 3, 4):
        n = counts[colour]
        if not 1 <= n <= height:
            raise ValueError('Bar colour missing or taller than the grid')
        for j in range(n):
            out[height - 1 - j][colour - 1] = colour
    return out


from .joint_fragments import transform as joint_fragment_completion

def separated_motif_stamp(grid):
    """b4a43f3b: stamp the 3x3 motif shown above the colour-5 separator.

    Pair label checker only (native colours), reconstructed from the native
    layout rather than from a uniform-row heuristic. Every canonical and
    teaching fixture and every constructor output is W = 3s wide (motif
    scale s = 1..3; canonical s = 2). Rows 0..W-1 are the 3x3 motif upscaled
    by s, so the top block is a W x W square. Row W is the separator and is
    entirely colour 5. The rows below are the placement map (height 1..10),
    where any non-0 cell is marked. The answer is 3h x 3W: each marked map
    cell becomes a copy of the motif, zeros included, and unmarked cells
    become 3x3 zero tiles.

    The separator is located by this geometry, never by searching for a
    uniform line. So motif rows that are full single-colour lines, including
    full lines of colour 5 in legacy explicit scenes, are ordinary content.
    Empty maps and all-0 motifs stay valid. Inputs outside the layout raise:
    a width not divisible by 3, a row W that is not all 5, a top block that
    is not an exact s-fold upscale, or a map taller than 10.
    """
    rows = [list(row) for row in grid]
    width = len(rows[0]) if rows else 0
    if not rows or not width or any(len(r) != width for r in rows):
        raise ValueError('Expected a rectangular grid')
    if width % 3 or width > 9:
        raise ValueError('Width is not 3 * scale for a scale of 1..3')
    scale, height = width // 3, len(rows) - width - 1
    if not 1 <= height <= 10:
        raise ValueError('No placement map of height 1..10 below the motif square')
    if any(v != 5 for v in rows[width]):
        raise ValueError('Row W is not the colour-5 separator')
    motif = [[rows[scale * r][scale * c] for c in range(3)] for r in range(3)]
    if any(rows[i][j] != motif[i // scale][j // scale]
           for i in range(width) for j in range(width)):
        raise ValueError('Top block is not an exact upscale of a 3x3 motif')
    out = [[0] * (3 * width) for _ in range(3 * height)]
    for i, line in enumerate(rows[width + 1:]):
        for j, cell in enumerate(line):
            if cell:
                for r in range(3):
                    out[3 * i + r][3 * j:3 * j + 3] = motif[r]
    return out


def fixed_background_band_reflection(grid):
    """e74e1818: reflect each colour within its own vertical span; native BG=0.

    Dense one-band scenes can have more ink than background. Background is a
    task colour with a full outer border, not the most frequent pixel value.
    This coordinate check is independent of the factory's row-block scan.
    """
    g = [list(map(int, row)) for row in grid]
    h, w = len(g), len(g[0])
    if any(len(row) != w for row in g) or any(g[0]) or any(g[-1]) or any(row[0] or row[-1] for row in g):
        raise ValueError('Expected a rectangular grid with a black border')
    out = [[0] * w for _ in range(h)]
    for colour in {c for row in g for c in row} - {0}:
        pixels = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==colour]
        lo, hi = min(r for r,c in pixels), max(r for r,c in pixels)
        for r,c in pixels:
            out[lo+hi-r][c]=colour
    return out


VERIFIERS = {'78332cb0': panel_chain, 'de493100': cropped_mirror_patch,
             '3a301edc': nested_frame_band,
             'd6542281': joint_fragment_completion,
             'aaecdb9a': legend_object_chart, '007bbfb7': self_tiling,
             '7e2bad24': native_side_beam, '34b99a2b': midpoint_xor_panels,
             '195ba7dc': midpoint_or_panels, '281123b4': separated_priority_panels,
             'e0fb7511': native_zero_adjacency, 'f3cdc58f': fixed_colour_histogram,
             'b4a43f3b': separated_motif_stamp, 'e74e1818': fixed_background_band_reflection}
VERIFIER_EVIDENCE = {
    'e74e1818': {
        'mode': 'fixed_background_colour_span_reflection',
        'module': 'arc_agi2.verified_rules.fixed_background_band_reflection',
        'reason': 'The archived modal-background heuristic can select ink on dense one-band scenes. Native background remains 0 with a full black border; reflect each nonzero colour within its own row span.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-band-reflection/archived-checker-failures.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    'e0fb7511': {
        'mode': 'reviewed_native_zero_four_adjacency',
        'module': 'arc_agi2.verified_rules.native_zero_adjacency',
        'reason': 'The archived solver recolours 4-connected components of the NON-MODAL colour, so it depends on blue (1) outnumbering black (0). A legal all-black scene (generate(colors=[0]*169)) is labelled all 8 by the constructor but all 0 by the archived solver, and legal explicit 13x13 scenes at black density 0.5 disagree in 258/500 draws (0.4: 2/500). All canonical and teaching fixtures and every constructor output are 0/1 grids whose label recolours exactly the black cells having a 4-adjacent black cell to 8, so this checker reads the fixed native target colour 0. Dense, tied, all-black, all-blue, diagonal-only and singleton scenes stay valid content; colours outside 0/1 raise. The independent direct factory is unchanged.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-e/e0fb7511-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    'f3cdc58f': {
        'mode': 'reviewed_fixed_colour_value_histogram',
        'module': 'arc_agi2.verified_rules.fixed_colour_histogram',
        'reason': 'The archived solver takes the modal colour as background and orders bars by the sorted remaining colours. A legal 10x4 histogram holding ten cells of each of 1, 2, 3, 4 (one per row, counts equal to the height) makes 1 the "background", so the archived answer rows read [2, 3, 4, 1] instead of [1, 2, 3, 4]. All canonical and teaching fixtures and every constructor output are black grids holding each of colours 1..4 at least once, labelled by bottom-aligned bars of colour c in column c - 1 with height equal to the count, so this checker uses that fixed legend and black background. Modal or tied bar colours stay valid content; colours outside 0..4, a missing bar colour, width below 4 or a count above the height raise. The independent direct factory is unchanged.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-e/f3cdc58f-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    '195ba7dc': {
        'mode': 'reviewed_midpoint_divider_or',
        'module': 'arc_agi2.verified_rules.midpoint_or_panels',
        'reason': 'The archived solver takes the FIRST full single-colour column whose colour occurs only there as the divider. A valid sparse scene whose only 7s fill one left-panel column (width=height=4, top column 0 set, bottom empty) is therefore cut at column 0 and yields an empty 4x0 answer. This is not confined to tiny panels. All 5 canonical and 5 teaching fixtures and every constructor output place the colour-2 divider at the exact midpoint (W-1)/2 of an odd-width grid with equal panels, so this checker reads the midpoint column and ORs the panels. Empty, sparse and full panel rows/columns stay valid content; inputs lacking the geometry raise. The independent direct factory and the panel_overlay_evidence gate are unchanged.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-d/195ba7dc-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    '281123b4': {
        'mode': 'reviewed_fixed_separator_priority_overlay',
        'module': 'arc_agi2.verified_rules.separated_priority_panels',
        'reason': 'The archived solver picks the separator colour as the first non-modal colour whose cells all lie in full uniform columns. A valid sparse scene whose only 8s fill one top-panel column (width=height=4, other panels empty) makes 8 the separator and yields a 4x18 answer instead of 4x4. This is not confined to tiny panels; modal-background errors add further failures at narrow widths. All 7 canonical and 7 teaching fixtures and every constructor output have width 4w+3 with colour-3 separators at w, 2w+1, 3w+2 and background 0, so this checker reads the panels at those positions and applies the priority 9>4>8>5. Empty, sparse and full panel rows/columns stay valid content; inputs lacking the geometry raise. The independent direct factory and the panel_overlay_evidence gate are unchanged.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-d/281123b4-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    '34b99a2b': {
        'mode': 'reviewed_midpoint_divider_xor',
        'module': 'arc_agi2.verified_rules.midpoint_xor_panels',
        'reason': 'The archived solver takes the FIRST full single-colour non-zero column as the divider, so a valid left-panel column filled entirely with 8 is mistaken for the divider (230/2000 unmodified native default pairs; see counterexample). All 5 canonical and 5 teaching fixtures and every constructor output place the divider at the exact midpoint (W-1)/2 of an odd-width grid with equal panels, so this checker reads the midpoint column and XORs the panels. Full internal columns stay valid content; inputs lacking the midpoint geometry raise. The independent direct factory, colour-evidence and episode gates are unchanged.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-d/34b99a2b-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    '7e2bad24': {
        'mode': 'reviewed_native_side_contact_beam_replay',
        'module': 'arc_agi2.verified_rules.native_side_beam',
        'reason': 'The archived solver reflects only when the diagonal target is a mirror; the native constructor reflects when the cell across the wall axis is a mirror. They differ exactly on endpoint-sensitive scenes (corner contact with a mirror end), so the archived checker rejected every endpoint-sensitive native pair (c75138a constructor: 220/220 endpoint-sensitive pairs in 600 seeded draws; 400/1000 pairs overall with seed 11, see counterexample). This checker replays the side-contact reading with the independent coordinate tracer of beam_endpoint_evidence. Exported programs and the unchanged colour-evidence gate still require demonstrations to determine the convention.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-c/7e2bad24-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    '3a301edc': {
        'mode': 'nested_bounding_box_containment',
        'module': 'arc_agi2.verified_rules.nested_frame_band',
        'reason': 'A 5x5 interior has 25 cells while its one-cell frame has 24. Sorting objects by ink area reverses their semantic roles; bounding-box containment identifies the frame independently of the constructor.',
        'counterexample': 'arc_agi2/reports/diversity-v1/3a301edc-broader-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    '007bbfb7': {
        'mode': 'dimension_aware_self_tiling',
        'module': 'arc_agi2.verified_rules.self_tiling',
        'reason': 'Archived solver allocates h*3 by w*3 although its block writes require h*h by w*w. The constructor already supported non-3 square sizes; this extension independently varies height and width in 2..5.',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    'aaecdb9a': {
        'mode': 'fixed_legend_background_component_count',
        'module': 'arc_agi2.verified_rules.legend_object_chart',
        'reason': 'The archived modal-colour heuristic treats colour 9 as background in a valid dense scene. The task has fixed background 7 and five fixed legend colours; count 8-connected objects of those colours directly.',
        'counterexample': 'arc_agi2/reports/diversity-v1/aaecdb9a-dense-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    'd6542281': {
        'mode': 'reviewed_joint_fragment_exact_cover',
        'module': 'arc_agi2.joint_fragments.transform',
        'reason': 'Archived greedy matcher fails on 499/1000 fresh scenes containing jointly disambiguated fragments; independent input-only exact-cover solver passes all 1000 and 8000 D4/palette variants.',
        'counterexample': 'arc_agi2/reports/review-blockers/d6542281.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
        'synthetic_extension': 'Separated multicolour templates and monochrome fragments with globally unique non-touching stamp completions.',
    },
    '78332cb0': {
        'mode': 'reviewed_complete_chain_verifier',
        'module': 'arc_agi2.verified_rules.panel_chain',
        'reason': 'Archived greedy matching fails on a permutation of canonical train[2].',
        'counterexample': 'arc_agi2/reports/review-blockers/78332cb0.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
    'de493100': {
        'mode': 'reviewed_dimension_aware_mirror_verifier',
        'module': 'arc_agi2.verified_rules.cropped_mirror_patch',
        'reason': 'Archived program fixes mirror coordinate 31; synthetic even-sized crops preserve the two-cell crop geometry with coordinate N+1.',
        'counterexample': 'arc_agi2/reports/review-blockers/de493100.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
        'synthetic_extension': 'Even square sizes 12..30; original size 30 and its weak transpose fallback preserved.',
    },
    'b4a43f3b': {
        'mode': 'reviewed_geometric_separator_motif_stamp',
        'module': 'arc_agi2.verified_rules.separated_motif_stamp',
        'reason': 'The archived solver takes as separator the FIRST full uniform non-background row whose colour occurs only there, else the first uniform non-background row. At motif scale 1 a full single-colour motif row is such a row. The legal native scene with motif 111/202/030 (all rows and columns occupied, 8-connected) has three 1s, all in row 0, so the archived solver cuts at row 0 and returns an empty 0x9 grid. In legacy explicit 13x6 scenes with a motif row of colour 5, no row passes the uniqueness test, and the fallback takes that motif row. Every canonical and teaching fixture and every constructor output places the motif square in rows 0..W-1 of a W = 3s wide grid and the colour-5 separator at row W, with any non-0 map cell marked. So this checker reads that geometry. The direct factory, which locates palette[5], is unchanged.',
        'counterexample': 'arc_agi2/reports/diversity-v1/native-batch-i/b4a43f3b-archived-verifier-counterexample.json',
        'canonical_data_changed': False,
        'archived_reference_changed': False,
    },
}
