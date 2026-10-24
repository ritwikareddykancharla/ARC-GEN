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


from .joint_fragments import transform as joint_fragment_completion

VERIFIERS = {'78332cb0': panel_chain, 'de493100': cropped_mirror_patch,
             '3a301edc': nested_frame_band,
             'd6542281': joint_fragment_completion,
             'aaecdb9a': legend_object_chart, '007bbfb7': self_tiling}
VERIFIER_EVIDENCE = {
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
}
