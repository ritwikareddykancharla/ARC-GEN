# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the License); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

"""ARC task c3fa4749 generator: repaint cracks that open onto the grid edge.

Rule: the input is dense colour noise that contains solid rectangular blocks.
For a colour c, a crack is a 4-connected group of 3..40 cells that are not c.
Every in-grid 4-neighbour of the group is c, and exactly one of its cells lies
on the grid border. A pocket of a crack is a 4-connected component of colour c
with at most 10 cells. It lies off the grid border and all of its 4-neighbours
are crack cells. The output repaints every crack, with its pockets, in the
colour of the crack's single border cell. All other cells are unchanged.

Scene construction. Latent geometry builds the input, and the output is
painted only from that latent geometry:
  * Random grid sizes are 12..30 per side. Explicit sizes 8..30 are accepted
    and need not be square. The fixtures are 20, 25 and 30 square.
  * Shared block-size sampler. Every block draws depth and length from the
    same range 4..s_max, where s_max = clamp(sqrt(h*w/blocks) - 2, 4, 12).
    This covers real cracks, near, leak, double, notch, over40, inner and
    plain blocks. The lower bound is raised only for a pocket decoration,
    which every crack kind samples at the same rate, or for the over40
    control, which needs 10x10. Blocks are shrunk toward the lower bound only
    when they cannot be placed. Placement order is shuffled across real and
    negative kinds, so shrinking does not depend on kind.
  * Shared crack-shape sampler (_base_shape). Real, near, leak, double,
    inner and over40 cracks all use it, with the same branches and targets.
    A border cell (0,k) is followed by either a straight perpendicular shaft
    of 3..depth-1 cells (p=.35) or a 2-cell stub. Random-walk growth then
    reaches a target: 3 (p=.15), 3..16 (p=.70), or 17..40 (p=.15, when the
    block allows). Eden growth tops up any shortfall. Any block-colour holes
    the shape encloses are absorbed into the crack.
  * Pocket decoration, at the same rate for every crack kind. A rectangle of
    1..12 c-cells is fully 8-ringed by crack cells. Sizes 1..10 are filled as
    pockets (10 is the tightest positive). Sizes 11 and 12 are threshold
    controls: the crack is filled, the pocket stays c.
  * Each negative is the shared shape with one disqualifying edit:
      - near: drop the border cell, so the crack stops one cell short;
      - double: add an L-shaped shaft to a second border cell;
      - leak: extend a straight branch through a side or far rim into noise;
      - inner: the same shape minus its border cell, in a free-standing block;
      - notch: only the first two cells, in two distinct colours (size-2
        threshold control; size 3 is a frequent real target);
      - over40: the same sampler grown to 41..48 cells, with one border cell
        (size threshold control; real cracks reach up to 40);
      - plain: a block with no crack.
    Crack colours use the same sampler for every kind. The border colour is
    usually not the unique majority colour.
  * Shared decorations on every block:
      - an enclosed impurity of 1..2 non-c cells with no 8-contact to any
        crack, pocket or leak/double path;
      - a ragged rim: a run of 1..3 rim cells repainted with noise colours.
        Edge blocks prefer their grid-border rim, as in train 3. Ragged runs
        also keep away from all planned non-c cells in 8-neighbourhood, so a
        ragged run never connects a crack or impurity to the border or to
        noise.
  * Blocks are at least one cell apart. Blocks within two cells of each other
    get different colours.
  * Acceptance: a local checker of the stated rule runs with both 4- and
    8-connectivity. Its qualifying (crack, pocket) set must equal the planned
    real cracks exactly. This rejects incidental noise cracks and any
    4/8-ambiguous scene.

Count feasibility. The block budget is num_cracks + num_distractors <=
max(1, h*w // 50). Smaller explicit budgets raise ValueError immediately.
The smallest block is 4x4 and blocks need a one-cell gap. So k edge blocks
stacked along a long side need 5k-1 cells. That fits the budget for every
supported shape, including narrow strips (8x25 with 4 blocks needs 19 of 25
rows). Square grids fit the budget through corner and edge slots (15x15:
four corners; 20x20: twelve 4x4 perimeter slots for at most 8 blocks).
Placement enumerates every legal position, prefers flush positions more
often as attempts accumulate, and shrinks dims. Requested counts are never
reduced. A randomly chosen over40 control falls back to near/leak/double if
no 10x10 edge slot exists. A pocket is dropped if it does not fit. An
explicitly requested over40 is never replaced. Very crowded explicit
requests can still end in RuntimeError after the bounded retries.

Not generated (labelled thresholds and cases): pockets enclosed only 4-wise
(diagonal contact with the block, which is 4/8 ambiguous); a crack border
cell on a grid corner; more than one pocket per crack; pockets larger than
12 (they behave like 11); a c-component next to a crack that is partly
bounded by impurities; non-rectangular pockets other than the trimmed 2x6.

Fixture replay: the original inputs are dense random noise and cannot be
rebuilt from a few scene parameters. validate() therefore passes each fixture
input as the explicit `base` field together with its explicit latent crack
geometry. Replay checks that base is a valid grid. It checks that each
supplied crack is a qualifying crack of base with exactly the listed pockets.
It also checks that no qualifying crack that would change the grid is left
out. The output is painted from the supplied geometry. The train 3 pocket
((4,4) becomes 8 while the notch (2,4) stays 7) is canonical data; no
correction is introduced.
"""

import collections
import math
import random

import common

_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DIRS8 = _DIRS4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
_KINDS = ('inner', 'near', 'leak', 'double', 'plain', 'notch', 'over40')
_KIND_WEIGHTS = (2, 3, 3, 2, 1, 1, 1)
_FALLBACK_KINDS = ('near', 'leak', 'double')
_CELLS_PER_BLOCK = 50
_MAX_CRACK = 40
_MAX_POCKET = 10
# Pocket rectangles as (rows, cols, trimmed corner).
_POCKETS_SMALL = ((1, 1, 0), (1, 2, 0))
_POCKETS_MID = ((1, 3, 0), (2, 2, 0), (1, 4, 0), (2, 3, 0), (3, 3, 0),
                (2, 4, 0), (2, 5, 0))
_POCKETS_BIG = ((2, 6, 1), (2, 6, 0), (3, 4, 0))


def _on_border(p, h, w):
  return p[0] in (0, h - 1) or p[1] in (0, w - 1)


def _components(grid, keep, dirs):
  h, w = len(grid), len(grid[0])
  seen = [[False] * w for _ in range(h)]
  comps = []
  for y in range(h):
    for x in range(w):
      if seen[y][x] or not keep(grid[y][x]):
        continue
      seen[y][x] = True
      stack, comp = [(y, x)], []
      while stack:
        cy, cx = stack.pop()
        comp.append((cy, cx))
        for dy, dx in dirs:
          ny, nx = cy + dy, cx + dx
          if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx]:
            if keep(grid[ny][nx]):
              seen[ny][nx] = True
              stack.append((ny, nx))
      comps.append(comp)
  return comps


def _qualifying(grid, dirs):
  """Edge-opening cracks with their pockets, ordered by block colour.

  Used only to reject sampled scenes and to check replayed geometry.
  """
  h, w = len(grid), len(grid[0])
  found = []
  for c in sorted({v for row in grid for v in row}):
    same = [set(s) for s in _components(grid, lambda v, c=c: v == c, dirs)
            if len(s) <= _MAX_POCKET]
    for comp in _components(grid, lambda v, c=c: v != c, dirs):
      if not 3 <= len(comp) <= _MAX_CRACK:
        continue
      if sum(1 for p in comp if _on_border(p, h, w)) != 1:
        continue
      cs = set(comp)
      ok = True
      for y, x in comp:
        for dy, dx in _DIRS4:
          ny, nx = y + dy, x + dx
          if (0 <= ny < h and 0 <= nx < w and (ny, nx) not in cs
              and grid[ny][nx] != c):
            ok = False
            break
        if not ok:
          break
      if not ok:
        continue
      pockets = set()
      for ss in same:
        enc = True
        for p in ss:
          if _on_border(p, h, w):
            enc = False
            break
          for dy, dx in _DIRS4:
            q = (p[0] + dy, p[1] + dx)
            if q not in ss and q not in cs:
              enc = False
              break
          if not enc:
            break
        if enc:
          pockets |= ss
      found.append((frozenset(cs), frozenset(pockets)))
  return found


def _connected(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    y, x = stack.pop()
    for dy, dx in _DIRS4:
      q = (y + dy, x + dx)
      if q in cells and q not in seen:
        seen.add(q)
        stack.append(q)
  return len(seen) == len(cells)


def _cell(p):
  try:
    y, x = p
  except (TypeError, ValueError):
    raise ValueError('cells must be (row, column) pairs')
  for v in (y, x):
    if isinstance(v, bool) or not isinstance(v, int):
      raise ValueError('cell coordinates must be integers')
  return (y, x)


def _check_base(base):
  """Returns a copy of base after checking it is a valid ARC grid."""
  if not isinstance(base, (list, tuple)) or not 1 <= len(base) <= 30:
    raise ValueError('base must be a list of 1..30 rows')
  grid = []
  for row in base:
    if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 30:
      raise ValueError('base rows must hold 1..30 cells')
    for v in row:
      if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9:
        raise ValueError('base cells must be integers in 0..9')
    grid.append(list(row))
  if len({len(row) for row in grid}) != 1:
    raise ValueError('base must be rectangular')
  return grid


def _normalise_cracks(grid, cracks):
  """Checks replayed latent geometry and returns it as tuple lists."""
  h, w = len(grid), len(grid[0])
  if not isinstance(cracks, (list, tuple)) or not cracks:
    raise ValueError('base replay requires a non-empty cracks list')
  out = []
  for item in cracks:
    try:
      cells, pockets = item
      cells, pockets = list(cells), list(pockets)
    except (TypeError, ValueError):
      raise ValueError('each crack must be a (cells, pockets) pair')
    cells = [_cell(p) for p in cells]
    pockets = [_cell(p) for p in pockets]
    if not cells or len(set(cells)) != len(cells):
      raise ValueError('crack cells must be a non-empty list of unique cells')
    if len(set(pockets)) != len(pockets):
      raise ValueError('pocket cells must be unique')
    for y, x in cells + pockets:
      if not (0 <= y < h and 0 <= x < w):
        raise ValueError('crack geometry lies outside the base grid')
    if set(cells) & set(pockets):
      raise ValueError('pocket cells must not overlap crack cells')
    if not _connected(cells):
      raise ValueError('crack cells must be 4-connected')
    out.append((cells, pockets))
  return out


def _fill(grid, cracks):
  """Returns a new grid with every crack and pocket in its border colour."""
  h, w = len(grid), len(grid[0])
  out = [row[:] for row in grid]
  for cells, pockets in cracks:
    edge = [p for p in cells if _on_border(p, h, w)]
    if len(edge) != 1:
      raise ValueError('a crack must touch the grid border exactly once')
    colour = grid[edge[0][0]][edge[0][1]]
    for y, x in list(cells) + list(pockets):
      out[y][x] = colour
  return out


# ---------------------------------------------------------------- layout --


def _mapper(orient, y0, x0, depth):
  """Maps block-frame (r, c) to grid cells; frame row 0 is the open side."""
  if orient == 0:
    return lambda r, c: (y0 + r, x0 + c)
  if orient == 1:
    return lambda r, c: (y0 + depth - 1 - r, x0 + c)
  if orient == 2:
    return lambda r, c: (y0 + c, x0 + r)
  return lambda r, c: (y0 + c, x0 + depth - 1 - r)


def _rect_of(orient, y0, x0, depth, length):
  if orient < 2:
    return (y0, x0, y0 + depth - 1, x0 + length - 1)
  return (y0, x0, y0 + length - 1, x0 + depth - 1)


def _apart(a, b, gap):
  return (a[2] + gap < b[0] or b[2] + gap < a[0] or a[3] + gap < b[1]
          or b[3] + gap < a[1])


def _candidates(h, w, depth, length, rects, on_edge):
  """All legal (orient, y0, x0, rect) placements for a block."""
  raw = []
  if on_edge:
    for side in range(4):
      along, across = (w, h) if side < 2 else (h, w)
      if length > along or depth > across - 2:
        continue
      for off in range(along - length + 1):
        if side == 0:
          raw.append((0, 0, off))
        elif side == 1:
          raw.append((1, h - depth, off))
        elif side == 2:
          raw.append((2, off, 0))
        else:
          raw.append((3, off, w - depth))
  else:
    for orient in (0, 2):
      rows, cols = (depth, length) if orient == 0 else (length, depth)
      for y0 in range(h - rows + 1):
        for x0 in range(w - cols + 1):
          raw.append((orient, y0, x0))
  keep = []
  for orient, y0, x0 in raw:
    rect = _rect_of(orient, y0, x0, depth, length)
    if all(_apart(rect, r, 1) for r in rects):
      keep.append((orient, y0, x0, rect))
  return keep


def _score(rect, rects, h, w):
  """Number of sides that are flush with the grid edge or a one-cell gap."""
  y0, x0, y1, x1 = rect
  s = int(y0 == 0) + int(x0 == 0) + int(y1 == h - 1) + int(x1 == w - 1)
  for a0, b0, a1, b1 in rects:
    if b0 <= x1 and x0 <= b1 and (a1 == y0 - 2 or a0 == y1 + 2):
      s += 1
    if a0 <= y1 and y0 <= a1 and (b1 == x0 - 2 or b0 == x1 + 2):
      s += 1
  return s


def _place(h, w, lo_d, lo_l, s_max, rects, on_edge, p_tight):
  depth = random.randint(lo_d, max(lo_d, s_max))
  length = random.randint(lo_l, max(lo_l, s_max))
  for _ in range(20):
    cands = _candidates(h, w, depth, length, rects, on_edge)
    if cands:
      if random.random() < p_tight:
        scores = [_score(c[3], rects, h, w) for c in cands]
        best = max(scores)
        cands = [c for c, s in zip(cands, scores) if s == best]
      orient, y0, x0, rect = random.choice(cands)
      if not on_edge:
        orient += random.randint(0, 1)
      return depth, length, orient, y0, x0, rect
    if depth - lo_d >= length - lo_l and depth > lo_d:
      depth -= 1
    elif length > lo_l:
      length -= 1
    else:
      return None
  return None


def _pick_colour(rect, layout):
  avoid = {col for r, col in layout if not _apart(rect, r, 2)}
  return random.choice([v for v in range(10) if v not in avoid])


# ---------------------------------------------------------------- shapes --


def _dilate(cells):
  out = set(cells)
  for y, x in cells:
    for dy, dx in _DIRS8:
      out.add((y + dy, x + dx))
  return out


def _enclosed(depth, length, cells):
  """Block-frame cells outside `cells` that are 4-cut off from the rim."""
  taken = set(cells)
  free = {(r, c) for r in range(depth) for c in range(length)
          if (r, c) not in taken}
  stack = [p for p in free
           if p[0] in (0, depth - 1) or p[1] in (0, length - 1)]
  seen = set(stack)
  while stack:
    r, c = stack.pop()
    for dy, dx in _DIRS4:
      q = (r + dy, c + dx)
      if q in free and q not in seen:
        seen.add(q)
        stack.append(q)
  return free - seen


def _grow(start, interior, target):
  """Random-walk branching growth with an Eden top-up to reach target."""
  cells = list(start)
  taken = set(cells)
  for _ in range(400):
    if len(cells) >= target:
      break
    if random.random() < 0.55:
      base = cells[-1]
    else:
      base = random.choice(cells[1:])
    dy, dx = random.choice(_DIRS4)
    for _ in range(random.randint(1, 3)):
      nxt = (base[0] + dy, base[1] + dx)
      if nxt not in interior or nxt in taken:
        break
      cells.append(nxt)
      taken.add(nxt)
      base = nxt
      if len(cells) >= target:
        break
  while len(cells) < target:
    front = set()
    for y, x in cells[1:]:
      for dy, dx in _DIRS4:
        q = (y + dy, x + dx)
        if q in interior and q not in taken:
          front.add(q)
    if not front:
      break
    q = random.choice(sorted(front))
    cells.append(q)
    taken.add(q)
  return cells


def _base_shape(depth, length, over):
  """Shared edge-crack sampler; cells[0] is the border cell (0, k)."""
  interior = {(r, c) for r in range(1, depth - 1)
              for c in range(1, length - 1)}
  n_int = len(interior)
  big_hi = min(_MAX_CRACK, int(0.6 * n_int))
  for _ in range(30):
    k = random.randint(1, length - 2)
    if over:
      target = random.randint(_MAX_CRACK + 1, min(_MAX_CRACK + 8, n_int + 1))
    else:
      u = random.random()
      if u < 0.15:
        target = 3
      elif u < 0.85 or big_hi < 17:
        target = random.randint(3, min(16, n_int + 1))
      else:
        target = random.randint(17, big_hi)
    if random.random() < 0.35:
      run = random.randint(3, depth - 1)
      start = [(r, k) for r in range(run)]
      target = max(target, run)
    else:
      start = [(0, k), (1, k)]
    cells = _grow(start, interior, target)
    cells += sorted(_enclosed(depth, length, cells))
    if over and len(cells) > _MAX_CRACK:
      return cells
    if not over and 3 <= len(cells) <= _MAX_CRACK:
      return cells
  return None


def _pocket_shape():
  u = random.random()
  if u < 0.55:
    a, b, trim = random.choice(_POCKETS_SMALL)
  elif u < 0.85:
    a, b, trim = random.choice(_POCKETS_MID)
  else:
    a, b, trim = random.choice(_POCKETS_BIG)
  if random.random() < 0.5:
    a, b = b, a
  return (a, b, trim)


def _add_pocket(depth, length, cells, shape, limit):
  """Encloses a block-colour pocket in a full 8-ring of crack cells."""
  a, b, trim = shape
  if depth < a + 4 or length < b + 4:
    return None
  taken = set(cells)
  touch = set(taken)
  for y, x in cells:
    for dy, dx in _DIRS4:
      touch.add((y + dy, x + dx))
  cands = []
  for r0 in range(2, depth - 1 - a):
    for c0 in range(2, length - 1 - b):
      rect = {(r0 + i, c0 + j) for i in range(a) for j in range(b)}
      if rect & taken:
        continue
      ring = _dilate(rect) - rect
      if ring & touch:
        cands.append((sorted(rect), ring))
  random.shuffle(cands)
  for rect, ring in cands[:12]:
    pocket = set(rect)
    ring = set(ring)
    if trim:
      corner = (random.choice((rect[0][0], rect[-1][0])),
                random.choice((rect[0][1], rect[-1][1])))
      pocket.discard(corner)
      ring.add(corner)
    new = list(cells) + sorted(ring - taken)
    new += sorted(_enclosed(depth, length, new) - pocket)
    if limit is not None and len(new) > limit:
      continue
    if _enclosed(depth, length, new) != pocket:
      continue
    return new, sorted(pocket)
  return None


def _crack_shape(depth, length, over, pocket_shape):
  limit = None if over else _MAX_CRACK
  if pocket_shape is not None:
    for _ in range(8):
      cells = _base_shape(depth, length, over)
      if cells is None:
        continue
      res = _add_pocket(depth, length, cells, pocket_shape, limit)
      if res is not None:
        return res
  cells = _base_shape(depth, length, over)
  return None if cells is None else (cells, [])


def _crack_colours(n, others):
  """Colours for crack cells; index 0 is the border (fill) colour."""
  cols = [random.choice(others) for _ in range(n)]
  b = cols[0]
  strict = random.random() < 0.7
  for _ in range(n):
    counts = collections.Counter(cols)
    rival = max([m for v, m in counts.items() if v != b] or [0])
    need = counts[b] > rival if strict else rival == 0
    if not need:
      break
    idx = [i for i in range(1, n) if cols[i] == b]
    cols[random.choice(idx)] = random.choice([v for v in others if v != b])
  return cols


def _double_path(length, cells, pocket):
  """L-shaped shaft from a crack cell to a second border cell."""
  taken, pk = set(cells), set(pocket)
  k = cells[0][1]
  opts = []
  for r, c in cells[1:]:
    for c2 in range(1, length - 1):
      if c2 == k:
        continue
      step = 1 if c2 > c else -1
      path = []
      if c2 != c:
        path = [(r, cc) for cc in range(c + step, c2 + step, step)]
      path += [(rr, c2) for rr in range(r - 1, -1, -1)]
      if any(p in pk for p in path):
        continue
      opts.append([p for p in path if p not in taken])
  picks = random.sample(opts, min(3, len(opts)))
  return min(picks, key=len)


def _leak_path(depth, length, cells, pocket, mp, h, w):
  """Straight branch through a side or far rim; returns (path, exit)."""
  taken, pk = set(cells), set(pocket)
  opts = []
  for r, c in cells[1:]:
    for dr, dc in ((1, 0), (0, 1), (0, -1)):
      path, rr, cc, ok = [], r + dr, c + dc, True
      while 0 <= rr < depth and 0 <= cc < length:
        if (rr, cc) in pk:
          ok = False
          break
        if (rr, cc) not in taken:
          path.append((rr, cc))
        rr, cc = rr + dr, cc + dc
      if not ok:
        continue
      y, x = mp(rr, cc)
      if 0 <= y < h and 0 <= x < w:
        opts.append((path, (y, x)))
  if not opts:
    return None
  picks = random.sample(opts, min(3, len(opts)))
  return min(picks, key=lambda o: len(o[0]))


def _impurities(depth, length, blocked, rate):
  """A 1..2-cell enclosed non-block group with no 8-contact to `blocked`."""
  if random.random() >= rate:
    return []
  near = _dilate(blocked)
  free = {(r, c) for r in range(1, depth - 1) for c in range(1, length - 1)
          if (r, c) not in near}
  if not free:
    return []
  p = random.choice(sorted(free))
  out = [p]
  if random.random() < 0.5:
    nb = [(p[0] + dy, p[1] + dx) for dy, dx in _DIRS4
          if (p[0] + dy, p[1] + dx) in free]
    if nb:
      out.append(random.choice(nb))
  return out


def _ragged(depth, length, blocked, prefer_border, rate):
  """A run of 1..3 rim cells, away from all planned non-block cells."""
  if random.random() >= rate:
    return []
  near = _dilate(blocked)
  lines = [[(0, c) for c in range(length)],
           [(depth - 1, c) for c in range(length)],
           [(r, 0) for r in range(depth)],
           [(r, length - 1) for r in range(depth)]]
  if prefer_border and random.random() < 0.6:
    line = lines[0]
  else:
    line = random.choice(lines)
  runs, cur = [], []
  for p in line:
    if p in near:
      if cur:
        runs.append(cur)
      cur = []
    else:
      cur.append(p)
  if cur:
    runs.append(cur)
  if not runs:
    return []
  run = random.choice(runs)
  n = random.randint(1, min(3, len(run)))
  s = random.randint(0, len(run) - n)
  return run[s:s + n]


# ---------------------------------------------------------------- blocks --


def _requirement(spec):
  lo = 10 if spec['kind'] == 'over40' else 4
  lo_d = lo_l = lo
  if spec['pocket'] is not None:
    a, b, _ = spec['pocket']
    lo_d, lo_l = max(lo_d, a + 4), max(lo_l, b + 4)
  return lo_d, lo_l


def _build(spec, grid, h, w, layout, s_max, rates, planned, p_tight):
  """Places and paints one block; appends real cracks to planned."""
  rects = [r for r, _ in layout]
  while True:
    lo_d, lo_l = _requirement(spec)
    placed = _place(h, w, lo_d, lo_l, s_max, rects, spec['edge'], p_tight)
    if placed is not None:
      break
    if spec['pocket'] is not None:
      spec['pocket'] = None
    elif spec['kind'] == 'over40' and not spec['fixed']:
      spec['kind'] = random.choice(_FALLBACK_KINDS)
    else:
      return False
  depth, length, orient, y0, x0, rect = placed
  kind = spec['kind']
  mp = _mapper(orient, y0, x0, depth)
  colour = _pick_colour(rect, layout)
  layout.append((rect, colour))
  others = [v for v in range(10) if v != colour]
  cells, pocket, paint = [], [], []
  if kind == 'notch':
    k = random.randint(1, length - 2)
    cells = [(0, k), (1, k)]
    first = random.choice(others)
    second = random.choice([v for v in others if v != first])
    paint = [(cells[0], first), (cells[1], second)]
  elif kind != 'plain':
    shape = _crack_shape(depth, length, kind == 'over40', spec['pocket'])
    if shape is None:
      return False
    cells, pocket = shape
    paint = list(zip(cells, _crack_colours(len(cells), others)))
  extra, exit_cell = [], None
  if kind in ('near', 'inner'):
    paint = paint[1:]
  elif kind == 'double':
    extra = _double_path(length, cells, pocket)
  elif kind == 'leak':
    res = _leak_path(depth, length, cells, pocket, mp, h, w)
    if res is None:
      return False
    extra, exit_cell = res
  paint += [(p, random.choice(others)) for p in extra]
  blocked = set(cells) | set(pocket) | set(extra)
  imp = _impurities(depth, length, blocked, rates[1])
  paint += [(p, random.choice(others)) for p in imp]
  rag = _ragged(depth, length, blocked | set(imp), spec['edge'], rates[2])
  paint += [(p, random.choice(others)) for p in rag]
  for r in range(depth):
    for c in range(length):
      y, x = mp(r, c)
      grid[y][x] = colour
  for (r, c), v in paint:
    y, x = mp(r, c)
    grid[y][x] = v
  if exit_cell is not None:
    grid[exit_cell[0]][exit_cell[1]] = random.choice(others)
  if kind == 'real':
    keep = pocket if len(pocket) <= _MAX_POCKET else []
    planned.append(([mp(r, c) for r, c in cells],
                    [mp(r, c) for r, c in keep]))
  return True


# ------------------------------------------------------------- arguments --


def _check_int(name, value, lo, hi):
  if value is None:
    return
  if isinstance(value, bool) or not isinstance(value, int) or not (
      lo <= value <= hi):
    raise ValueError('%s must be an integer in %d..%d' % (name, lo, hi))


def _rate(name, value, default):
  if value is None:
    return default
  if isinstance(value, bool) or not isinstance(
      value, (int, float)) or not 0.0 <= value <= 1.0:
    raise ValueError('%s must be a number in [0, 1]' % name)
  return float(value)


def _capacity(h, w):
  return max(1, (h * w) // _CELLS_PER_BLOCK)


def _over40_fits(h, w):
  return (w >= 10 and h >= 12) or (h >= 10 and w >= 12)


def _replay(base, cracks, width, height, num_cracks, unused):
  grid = _check_base(base)
  _check_int('width', width, 1, 30)
  _check_int('height', height, 1, 30)
  _check_int('num_cracks', num_cracks, 1, 30)
  if width is not None and width != len(grid[0]):
    raise ValueError('width does not match base')
  if height is not None and height != len(grid):
    raise ValueError('height does not match base')
  for name, value in unused:
    if value is not None:
      raise ValueError('%s cannot be applied to a replayed base' % name)
  geometry = _normalise_cracks(grid, cracks)
  if num_cracks is not None and num_cracks != len(geometry):
    raise ValueError('num_cracks does not match cracks')
  found = set(_qualifying(grid, _DIRS4))
  for cells, pockets in geometry:
    if (frozenset(cells), frozenset(pockets)) not in found:
      raise ValueError('a supplied crack is not a qualifying edge crack of '
                       'base with exactly the listed pockets')
  output = _fill(grid, geometry)
  if output != _fill(grid, sorted(found, key=lambda f: sorted(f[0]))):
    raise ValueError('cracks omit a qualifying crack that changes base')
  return {'input': grid, 'output': output}


def generate(width=None, height=None, num_cracks=None, num_distractors=None,
             distractor_kinds=None, pocket_rate=None, impurity_rate=None,
             ragged_rate=None, base=None, cracks=None):
  """Returns one input/output pair for task c3fa4749.

  Args:
    width: grid width (columns), 8..30. Random 12..30 when None.
    height: grid height (rows), 8..30. Random 12..30 when None.
    num_cracks: number of real edge-opening cracks, 1..4. Random 1..3 when
      None, limited by the block budget.
    num_distractors: number of distractor blocks, 0..4. Random 0..3 when
      None, limited by the block budget. Exactly this many are placed. The
      total num_cracks + num_distractors must not exceed
      max(1, width * height // 50), or ValueError is raised.
    distractor_kinds: optional list of 0..4 kinds from 'inner', 'near',
      'leak', 'double', 'plain', 'notch', 'over40'. It fixes the distractors
      exactly, and num_distractors must match its length if given. An
      explicit 'over40' needs a grid with a 10x10 edge slot and is never
      replaced. A randomly chosen 'over40' falls back to near/leak/double if
      it cannot be placed.
    pocket_rate: probability in [0, 1] that any crack (real or negative)
      tries to enclose a block-colour pocket. Defaults to 0.3. About 15% of
      pockets are 11..12-cell threshold controls that are not filled.
    impurity_rate: per-block probability in [0, 1] of a 1..2-cell enclosed
      impurity. Defaults to 0.25.
    ragged_rate: per-block probability in [0, 1] of a ragged rim run.
      Defaults to 0.3.
    base: optional explicit input grid, used for fixture replay of the noise.
      It requires `cracks`. With base, width/height must match if given,
      num_cracks must equal len(cracks) if given, and every other option is
      rejected.
    cracks: used only with base. A non-empty list of (cells, pockets) latent
      crack descriptions. Each must be a qualifying crack of base with
      exactly the listed pockets. Every qualifying crack that would change
      base must be listed.
  """
  if base is not None:
    return _replay(base, cracks, width, height, num_cracks,
                   (('num_distractors', num_distractors),
                    ('distractor_kinds', distractor_kinds),
                    ('pocket_rate', pocket_rate),
                    ('impurity_rate', impurity_rate),
                    ('ragged_rate', ragged_rate)))
  if cracks is not None:
    raise ValueError('cracks is only meaningful together with base')
  _check_int('width', width, 8, 30)
  _check_int('height', height, 8, 30)
  _check_int('num_cracks', num_cracks, 1, 4)
  _check_int('num_distractors', num_distractors, 0, 4)
  kinds = None
  if distractor_kinds is not None:
    if not isinstance(distractor_kinds, (list, tuple)) or len(
        distractor_kinds) > 4:
      raise ValueError('distractor_kinds must be a list of at most 4 kinds')
    kinds = list(distractor_kinds)
    for kd in kinds:
      if not isinstance(kd, str) or kd not in _KINDS:
        raise ValueError('unknown distractor kind %r' % (kd,))
    if num_distractors is not None and num_distractors != len(kinds):
      raise ValueError('num_distractors does not match distractor_kinds')
    num_distractors = len(kinds)
  rates = (_rate('pocket_rate', pocket_rate, 0.3),
           _rate('impurity_rate', impurity_rate, 0.25),
           _rate('ragged_rate', ragged_rate, 0.3))
  need = ((1 if num_cracks is None else num_cracks) +
          (0 if num_distractors is None else num_distractors))
  big = kinds is not None and 'over40' in kinds
  hs = [height] if height is not None else list(range(12, 31))
  ws = [width] if width is not None else list(range(12, 31))
  sizes = [(a, b) for a in hs for b in ws
           if _capacity(a, b) >= need and (not big or _over40_fits(a, b))]
  if not sizes:
    raise ValueError('%d blocks do not fit: at most width*height//%d blocks '
                     'are allowed (over40 needs a 10x10 edge slot)'
                     % (need, _CELLS_PER_BLOCK))
  h = w = cap = None
  for attempt in range(300):
    if attempt % 30 == 0:
      h, w = random.choice(sizes)
      cap = _capacity(h, w)
    if num_cracks is not None:
      n_real = num_cracks
    else:
      n_real = random.randint(
          1, max(1, min(3, cap - (num_distractors or 0))))
    if num_distractors is not None:
      n_dis = num_distractors
    else:
      n_dis = random.randint(0, max(0, min(3, cap - n_real)))
    if kinds is not None:
      dkinds = list(kinds)
    else:
      dkinds = random.choices(_KINDS, weights=_KIND_WEIGHTS, k=n_dis)
    n_blocks = n_real + n_dis
    s_max = int(math.sqrt(h * w / float(n_blocks))) - 2
    s_max = max(4, min(12, s_max))
    crowd = n_blocks * _CELLS_PER_BLOCK / float(h * w)
    p_tight = min(0.9, 0.2 + 0.5 * crowd + 0.01 * attempt)
    specs = []
    for _ in range(n_real):
      specs.append({'kind': 'real', 'fixed': True, 'edge': True,
                    'pocket': (_pocket_shape()
                               if random.random() < rates[0] else None)})
    for kd in dkinds:
      crack_kind = kd not in ('plain', 'notch')
      specs.append({
          'kind': kd, 'fixed': kinds is not None,
          'edge': kd != 'inner' and (kd != 'plain' or random.random() < 0.5),
          'pocket': (_pocket_shape() if crack_kind and
                     random.random() < rates[0] else None)})
    edge_specs = [s for s in specs if s['edge']]
    free_specs = [s for s in specs if not s['edge']]
    random.shuffle(edge_specs)
    random.shuffle(free_specs)
    edge_specs.sort(key=lambda s: -_requirement(s)[0] * _requirement(s)[1])
    grid = common.grid(w, h, 0)
    for y in range(h):
      for x in range(w):
        grid[y][x] = random.randrange(10)
    layout, planned = [], []
    if not all(_build(s, grid, h, w, layout, s_max, rates, planned, p_tight)
               for s in edge_specs + free_specs):
      continue
    expected = {(frozenset(c), frozenset(p)) for c, p in planned}
    if set(_qualifying(grid, _DIRS4)) != expected:
      continue
    if set(_qualifying(grid, _DIRS8)) != expected:
      continue
    output = _fill(grid, planned)
    if output == grid:
      continue
    return {'input': grid, 'output': output}
  raise RuntimeError('could not build a c3fa4749 scene with the requested '
                     'size and counts within the retry budget')


def _parse(rows):
  return [[int(ch) for ch in row.replace(' ', '')] for row in rows]


_TRAIN1 = [
    '84218 92471 62053 51729 96771', '46500 61506 00344 18189 28843',
    '44750 97547 33927 26411 98361', '35878 72768 02350 29764 88211',
    '74247 16603 31408 85284 74346', '10111 63990 96182 17741 95123',
    '32070 96618 65647 17373 12118', '75347 97559 31679 16012 82048',
    '75086 62983 51847 32751 11111', '66365 15804 98059 55561 11111',
    '32002 10876 38651 27641 18459', '88888 88888 56393 21311 15111',
    '88888 88888 78596 15631 11111', '95960 52288 92380 96291 11122',
    '88888 88888 75598 51565 21935', '88888 88888 26494 08859 91844',
    '04521 67400 20876 06676 54878', '88610 28572 88558 88888 27963',
    '29726 47419 07208 88888 39739', '97640 98385 27628 85788 68469',
    '94791 56285 48078 85288 54710', '88081 53019 86348 85288 82175',
    '87221 73825 36688 85888 85406', '75273 11384 49598 86883 21166',
    '62118 79725 25028 89886 55080']

_TRAIN2 = [
    '63334 33930 63602 13006', '78339 33905 20010 69329',
    '00334 33909 17041 63016', '20333 33466 21039 82715',
    '77333 33020 47931 95357', '59161 82844 70817 70909',
    '65791 40867 33201 15042', '34802 17700 07025 22010',
    '70850 67932 93533 15577', '57905 20705 47733 31700',
    '87702 24207 90666 66666', '00817 26637 21666 66666',
    '43648 83728 81667 00134', '32853 57820 30660 66666',
    '38415 05178 06660 66666', '20077 09712 36660 66690',
    '47250 66062 02665 66676', '04420 48310 05662 66410',
    '10481 58999 46910 94150', '47107 52107 00156 62980']

_TRAIN3 = [
    '77787 77796 32222 20404', '77717 77730 32222 27384',
    '77467 67740 52242 20707', '77731 37705 02282 25090',
    '27797 07772 92222 24852', '97758 37751 42222 29891',
    '07777 77726 69004 45067', '67777 77762 80120 91569',
    '24660 91813 56806 87613', '05999 67946 98980 87420',
    '86722 82882 74223 06333', '92739 63739 60353 56878',
    '47345 66801 58315 27930', '08808 40952 01215 84550',
    '15066 66666 66695 37043', '77066 66666 66634 87355',
    '29366 80797 16607 20376', '79266 59666 66682 83933',
    '25466 06666 66600 64298', '57466 86604 15160 97121']

_TEST1 = [
    '47948 26579 97371 53313 33982 66697',
    '91712 12952 35303 93353 36541 26466',
    '42966 10317 21759 33343 36218 11968',
    '33907 81691 92617 73313 38905 72954',
    '58379 67815 85493 73363 35933 35547',
    '33149 53185 11066 33323 33567 66925',
    '74337 59951 64938 23363 36635 19254',
    '29957 96635 67773 43383 33355 55824',
    '77644 31648 09836 73323 32255 55559',
    '42341 52718 54045 13383 33155 41555',
    '65508 62264 22847 13333 35855 76355',
    '61635 97941 84047 53333 36655 80141',
    '22377 99721 94681 95617 87755 05555',
    '21019 59288 67423 97984 94755 55555',
    '01873 82762 87533 00987 19355 55867',
    '94976 40077 61716 98323 89852 73497',
    '41437 54691 78885 78377 62756 73434',
    '64546 52298 53661 21884 27649 74701',
    '55902 25473 27863 71116 36888 32365',
    '24511 35355 49539 54519 76595 73146',
    '65222 82228 21478 95386 55467 98738',
    '22222 32229 56849 47374 42722 88878',
    '22269 76225 82779 87152 31389 51463',
    '13638 38226 66666 65226 29848 64744',
    '22222 22226 66666 66686 31131 18582',
    '22222 22266 60876 61137 64465 97961',
    '39797 22236 63886 69098 28418 83865',
    '13177 31626 62666 69488 97534 22932',
    '29832 23766 61666 98889 84866 29842',
    '53843 78506 61660 43297 72857 91652']

_TEST2 = [
    '06038 68772 77395 29013 85273 50410',
    '16183 02773 77933 30443 04192 55262',
    '93154 49776 77405 20124 32510 01277',
    '71592 78771 77029 90572 02721 44145',
    '04764 92776 77103 27575 63295 49450',
    '33598 33773 77690 71482 78245 38392',
    '90449 53777 77049 01904 50643 92750',
    '55322 43777 77859 85231 26213 05043',
    '66994 64481 99856 70606 82201 01429',
    '09531 01374 66957 74862 14826 48551',
    '31639 16680 51336 50676 88545 15367',
    '11372 03602 74753 85411 58539 64897',
    '79025 19380 21871 00324 92867 57769',
    '90872 40341 88000 91210 29780 27741',
    '48419 73929 54851 76882 63402 86425',
    '39434 28552 65559 16897 60937 31440',
    '30636 94399 02638 06300 81800 42844',
    '39396 70801 93075 66409 48380 04005',
    '76553 85161 74938 87414 49000 03000',
    '47788 50350 73199 66608 90000 05000',
    '77420 18922 25209 59110 01001 68400',
    '06436 99569 89657 19531 95008 16582',
    '68005 95900 70008 43954 73002 33700',
    '31210 89595 72831 80873 08001 97200',
    '38000 14370 91792 37023 52000 00000',
    '67144 44444 46500 20522 62000 00005',
    '52144 44444 40083 11733 54001 04551',
    '95044 30734 48568 87932 72088 20208',
    '69144 94444 43880 76558 00813 33941',
    '96644 24444 49992 54174 54606 60455']


def validate():
  """Rebuilds the canonical fixtures from explicit latent crack geometry."""
  train = [
      generate(base=_parse(_TRAIN1), cracks=[
          ([(13, c) for c in range(8)], []),
          ([(10, 21), (10, 22), (10, 23), (10, 24), (11, 21)], []),
          ([(19, 16), (19, 17), (20, 16), (20, 17), (21, 16), (21, 17),
            (22, 16), (23, 16), (24, 16)], []),
      ]),
      generate(base=_parse(_TRAIN2), cracks=[
          ([(0, 4), (1, 4), (2, 4)], []),
      ]),
      generate(base=_parse(_TRAIN3), cracks=[
          ([(0, 3), (1, 3), (2, 2), (2, 3), (2, 5), (3, 3), (3, 4), (3, 5),
            (4, 3), (4, 5), (5, 3), (5, 4), (5, 5)], [(4, 4)]),
          ([(16, 5), (16, 6), (16, 7), (16, 8), (16, 9), (16, 10), (17, 5),
            (17, 6), (18, 5), (19, 5)], []),
      ]),
  ]
  test = [
      generate(base=_parse(_TEST1), cracks=[
          ([(r, 18) for r in range(10)], []),
          ([(9, 25), (9, 26), (10, 25), (10, 26), (10, 27), (11, 25),
            (11, 26), (11, 27), (11, 28), (11, 29), (12, 25)], []),
          ([(25, 11), (25, 12), (25, 13), (26, 11), (26, 12), (26, 13),
            (27, 11), (28, 11), (29, 11)], []),
      ]),
      generate(base=_parse(_TEST2), cracks=[
          ([(r, 9) for r in range(6)], []),
          ([(27, 5), (27, 6), (27, 7), (27, 8), (28, 5), (29, 5)], []),
      ]),
  ]
  return {'train': train, 'test': test}
