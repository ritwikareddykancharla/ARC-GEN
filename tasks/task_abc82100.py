# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC-GEN style generator for task abc82100 (legend-driven stencil stamping).

Rule: the background is black (0). The input holds one or more legends. A
legend is a straight orthogonal chain of three cells: a source colour s, then
an adjacent different target colour t, then an anchor cell one more step in
the same direction. One diagonally connected shape of colour 8 (the stencil)
touches the anchor's 3x3 neighbourhood. The anchor itself is either an 8 or
background; it is never covered by another colour.

Every loose cell of colour s is replaced by the stencil drawn in colour t. The
loose cell takes the anchor's place, and the stamp is clipped at the border.
All legend cells (s, t and the 8s) are erased, and so is every original cell
of a mapped source colour. Cells of unmapped colours are kept. Stamping reads
only the input, so swaps (a->b, b->a) and chains are not transitive.

Layouts of random scenes:
  * separated: legend footprints are at Chebyshev distance >= 2.
  * pinwheel: 2-4 legends radiate from one shared background centre cell.
    The source sits at centre+d, the target at centre+2d and the anchor at
    centre+3d, so the sources touch diagonally, as in train pair 2. Arms are
    often paired into swaps (6->7 / 7->6 style).
  * touch: a legend is placed so that one of its visible cells (s, t or 8)
    is 8-adjacent to a visible cell of an earlier legend.
  Interlocked layouts (pinwheel or touch) are used in about 30% of default
  scenes with >= 2 legends. interlock=True forces them, and interlock=False
  forbids them. Exact read-back of the input decides whether an interlocked
  layout still assigns every stencil uniquely.

Other variation:
  * There are 1-4 legends. Four legends are possible by default when the
    area is >= 225, three when it is >= 120. Source colours are distinct, and
    a target may be another legend's source (swaps and chains).
  * Stencil families: lines, bars, chevrons, vees, rings, tees, diamonds,
    X shapes, diagonals, hooks, wings/rails flanking the target, and randomly
    grown 8-connected shapes. Anchors may lie in background.
  * Long straight runs: about 30% of default scenes (or long_runs=True) hold
    a straight run of a mapped colour of length 3 up to the full side. It
    usually abuts a partner run: an L corner, a collinear continuation or a T.
    The partner is a second mapped colour, often its swap partner (canonical
    pair 4); with one legend it is an unmapped colour.
  * Loose cells may be isolated, attached into blobs, or placed diagonally
    next to a legend. Decoy s/t pairs with no 8 near their would-be anchor
    and unmapped distractor colours also occur.
  * Default sides are 6..24. Explicit sides 5..30 are accepted; sides above
    20 are a synthetic extension of the 5..20 fixtures.

Invariants: the input must read back as exactly the latent legends. A local
legend scan checks this and serves only as a validity check. Random scenes
never stamp two colours onto one cell and never stamp over an unmapped cell.
0 is strictly the most frequent input colour. The output is always built from
the latent legends and loose cells.
"""

import random

import common

BG = 0
STENCIL = 8
COLOURS = [1, 2, 3, 4, 5, 6, 7, 9]
DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
NBHD = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
NEIGH8 = [p for p in NBHD if p != (0, 0)]
MIN_SIDE, MAX_SIDE = 5, 30
RANDOM_MIN, RANDOM_MAX = 6, 24
ALL_KINDS = ['single', 'line', 'bar', 'chevron', 'vee', 'ring', 'tee',
             'diamond', 'xcross', 'diag', 'hook', 'wings', 'rail', 'random',
             'random', 'random']
SMALL_KINDS = ['single', 'single', 'line', 'bar', 'chevron', 'vee', 'wings']


def _local_shape(kinds=None):
  """Returns stencil offsets in a local frame.

  u runs along the legend direction, with the anchor at u = 0 and the target
  at (u, v) = (-1, 0). v runs across the legend direction. Offsets always
  have u >= -1 and never equal (-1, 0).
  """
  kind = random.choice(kinds or ALL_KINDS)
  if kind == 'single':
    shape = [(0, 0)]
  elif kind == 'line':
    u0 = random.choice([0, 0, 1])
    shape = [(u0 + k, 0) for k in range(random.randint(2, 4))]
  elif kind == 'bar':
    n = random.randint(1, 2)
    u0 = random.choice([0, 1])
    shape = [(u0, v) for v in range(-n, n + 1)]
  elif kind == 'chevron':
    shape = [(1, 0), (0, -1), (0, 1)]
  elif kind == 'vee':
    shape = [(0, 0), (1, -1), (1, 1)]
  elif kind == 'ring':
    shape = [(0, 0), (1, -1), (1, 1), (2, 0)]
  elif kind == 'tee':
    shape = [(0, 0), (1, 0), (1, -1), (1, 1)]
  elif kind == 'diamond':
    r = random.randint(2, 3)
    shape = [(u, v) for u in range(0, 2 * r + 1) for v in range(-r, r + 1)
             if abs(u - r) + abs(v) == r]
  elif kind == 'xcross':
    r = random.randint(1, 2)
    shape = [(u, v) for u in range(0, 2 * r + 1) for v in range(-r, r + 1)
             if abs(u - r) == abs(v)]
  elif kind == 'diag':
    shape = [(k, k) for k in range(random.randint(2, 4))]
  elif kind == 'hook':
    shape = [(0, 0), (1, 0), (2, 0), (2, 1)]
  elif kind == 'wings':
    shape = [(-1, -1), (0, 0), (-1, 1)]
    if random.random() < 0.5:
      shape.append((1, 0))
  elif kind == 'rail':
    shape = [(u, 1) for u in range(-1, random.randint(1, 3))]
  else:
    start = random.choice([(0, 0), (1, 0), (0, 1), (0, -1), (1, 1), (1, -1),
                           (-1, 1), (-1, -1)])
    size = random.randint(2, 7)
    if random.random() < 0.5:
      steps = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    else:
      steps = NEIGH8
    shape = [start]
    for _ in range(60):
      if len(shape) >= size:
        break
      cands = []
      for u, v in shape:
        for du, dv in steps:
          nu, nv = u + du, v + dv
          if (-1 <= nu <= 4 and -3 <= nv <= 3 and (nu, nv) != (-1, 0)
              and (nu, nv) not in shape):
            cands.append((nu, nv))
      if not cands:
        break
      shape.append(random.choice(cands))
  if random.random() < 0.5:
    shape = [(u, -v) for u, v in shape]
  return shape


def _orient(shape, d):
  """Maps local (u, v) offsets to grid offsets relative to the anchor."""
  dr, dc = d
  pr, pc = dc, dr
  return {(u * dr + v * pr, u * dc + v * pc) for u, v in shape}


def _connected(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    r, c = stack.pop()
    for a, b in NBHD:
      q = (r + a, c + b)
      if q in cells and q not in seen:
        seen.add(q)
        stack.append(q)
  return len(seen) == len(cells)


def _near(cell, occupied):
  r, c = cell
  return any((r + a, c + b) in occupied for a, b in NBHD)


def _orth_adj(cell, cells):
  r, c = cell
  return any((r + a, c + b) in cells for a, b in DIRS)


def _shape_for(d, kinds=None):
  """Samples an oriented, connected stencil that touches the anchor 3x3.

  The checks on the source and target offsets are defensive only, because
  local shapes never use u < -1 or (-1, 0). Exact read-back is the real
  arbiter against reverse or spurious reads.
  """
  dr, dc = d
  for _ in range(40):
    rel = _orient(_local_shape(kinds), d)
    if (-dr, -dc) in rel or (-2 * dr, -2 * dc) in rel:
      continue
    if not any(max(abs(a), abs(b)) <= 1 for a, b in rel):
      continue
    if not _connected(rel):
      continue
    return rel
  return None


def _visible(leg):
  sp, d, cells = leg[2], leg[3], leg[4]
  return {sp, (sp[0] + d[0], sp[1] + d[1])} | set(cells)


def _anchor(leg):
  sp, d = leg[2], leg[3]
  return (sp[0] + 2 * d[0], sp[1] + 2 * d[1])


def _paint(height, width, legends, loose):
  grid = common.grid(width, height, BG)
  for s, t, sp, d, cells in legends:
    grid[sp[0]][sp[1]] = s
    grid[sp[0] + d[0]][sp[1] + d[1]] = t
    for r, c in cells:
      grid[r][c] = STENCIL
  for r, c, col in loose:
    grid[r][c] = col
  return grid


def _detect_legends(grid):
  """Reads every chain s, t, anchor whose anchor 3x3 touches an 8-component.

  This is used only to check validity (unambiguity). Outputs are never
  derived from it.
  """
  height, width = len(grid), len(grid[0])
  comp_of, comps = {}, []
  for r in range(height):
    for c in range(width):
      if grid[r][c] != STENCIL or (r, c) in comp_of:
        continue
      idx = len(comps)
      comp_of[(r, c)] = idx
      stack, members = [(r, c)], [(r, c)]
      while stack:
        y, x = stack.pop()
        for a, b in NBHD:
          q = (y + a, x + b)
          if (0 <= q[0] < height and 0 <= q[1] < width and
              grid[q[0]][q[1]] == STENCIL and q not in comp_of):
            comp_of[q] = idx
            stack.append(q)
            members.append(q)
      comps.append(members)
  found = {}
  for r in range(height):
    for c in range(width):
      s = grid[r][c]
      if s in (BG, STENCIL):
        continue
      for dr, dc in DIRS:
        ar, ac = r + 2 * dr, c + 2 * dc
        if not (0 <= ar < height and 0 <= ac < width):
          continue
        t = grid[r + dr][c + dc]
        if t in (BG, STENCIL) or t == s:
          continue
        ids = {comp_of[(ar + a, ac + b)] for a, b in NBHD
               if (ar + a, ac + b) in comp_of}
        if ids:
          found[((r, c), (dr, dc))] = frozenset(
              p for i in ids for p in comps[i])
  return found


def _readback_ok(height, width, legends):
  expected = {(L[2], L[3]): frozenset(L[4]) for L in legends}
  return _detect_legends(_paint(height, width, legends, [])) == expected


def _interlocked(legends):
  vis = [_visible(L) for L in legends]
  for i in range(len(vis)):
    for j in range(i + 1, len(vis)):
      if any(_near(p, vis[j]) for p in vis[i]):
        return True
  return False


def _try_sep(s, t, height, width, kinds, foot):
  """Places a legend whose footprint is at distance >= 2 from foot."""
  for _ in range(200):
    d = random.choice(DIRS)
    rel = _shape_for(d, kinds)
    if rel is None:
      continue
    dr, dc = d
    rs, rt = (-2 * dr, -2 * dc), (-dr, -dc)
    pts = rel | {rs, rt, (0, 0)}
    rmin, rmax = min(p[0] for p in pts), max(p[0] for p in pts)
    cmin, cmax = min(p[1] for p in pts), max(p[1] for p in pts)
    if rmax - rmin >= height or cmax - cmin >= width:
      continue
    ar = random.randint(-rmin, height - 1 - rmax)
    ac = random.randint(-cmin, width - 1 - cmax)
    leg = (s, t, (ar + rs[0], ac + rs[1]), d,
           sorted((ar + a, ac + b) for a, b in rel))
    fp = {(ar + a, ac + b) for a, b in pts}
    guard = (ar - 3 * dr, ac - 3 * dc)
    if 0 <= guard[0] < height and 0 <= guard[1] < width:
      fp.add(guard)
    if any(_near(p, foot) for p in fp):
      continue
    return leg, fp
  return None


def _try_touch(s, t, height, width, kinds, legends, strict):
  """Places a legend with a visible cell 8-adjacent to an earlier legend.

  Overlap with earlier visible or anchor cells is forbidden. Exact read-back
  of all legends placed so far decides whether the touching layout is still
  unambiguous.
  """
  existing = sorted(set().union(*(_visible(L) for L in legends)))
  for _ in range(150):
    d = random.choice(DIRS)
    rel = _shape_for(d, kinds)
    if rel is None:
      continue
    dr, dc = d
    offs = set(rel) | {(-2 * dr, -2 * dc), (-dr, -dc)}
    f = random.choice(existing)
    o = random.choice(sorted(offs))
    a, b = random.choice(NEIGH8)
    ar, ac = f[0] + a - o[0], f[1] + b - o[1]
    pts = [(ar + x, ac + y) for x, y in offs | {(0, 0)}]
    if any(not (0 <= p[0] < height and 0 <= p[1] < width) or p in strict
           for p in pts):
      continue
    leg = (s, t, (ar - 2 * dr, ac - 2 * dc), d,
           sorted((ar + x, ac + y) for x, y in rel))
    if not _readback_ok(height, width, legends + [leg]):
      continue
    fp = set(pts)
    guard = (ar - 3 * dr, ac - 3 * dc)
    if 0 <= guard[0] < height and 0 <= guard[1] < width:
      fp.add(guard)
    return leg, fp
  return None


def _try_pinwheel(sources, targets, kinds, height, width):
  """Places 2-4 legends radiating from one shared background centre."""
  k = len(sources)
  for _ in range(150):
    if k >= 4:
      dirs = list(DIRS)
    elif k == 3:
      dirs = random.sample(DIRS, 3)
    else:
      dirs = [random.choice([(0, 1), (0, -1)]),
              random.choice([(1, 0), (-1, 0)])]
    random.shuffle(dirs)
    rels = []
    for d, kd in zip(dirs, kinds):
      rel = _shape_for(d, kd)
      if rel is None:
        break
      rels.append(rel)
    if len(rels) < k:
      continue
    pts = [(0, 0)]
    for (dr, dc), rel in zip(dirs, rels):
      pts += [(dr, dc), (2 * dr, 2 * dc), (3 * dr, 3 * dc)]
      pts += [(3 * dr + a, 3 * dc + b) for a, b in rel]
    if len(set(pts)) != len(pts):
      continue
    rmin, rmax = min(p[0] for p in pts), max(p[0] for p in pts)
    cmin, cmax = min(p[1] for p in pts), max(p[1] for p in pts)
    if rmax - rmin >= height or cmax - cmin >= width:
      continue
    cr = random.randint(-rmin, height - 1 - rmax)
    cc = random.randint(-cmin, width - 1 - cmax)
    legends = []
    for s, t, (dr, dc), rel in zip(sources, targets, dirs, rels):
      legends.append((s, t, (cr + dr, cc + dc), (dr, dc),
                      sorted((cr + 3 * dr + a, cc + 3 * dc + b)
                             for a, b in rel)))
    if not _readback_ok(height, width, legends):
      continue
    return legends, {(cr + a, cc + b) for a, b in pts}
  return None


def _scene_error(height, width, legends, loose):
  """Returns a message if the scene is invalid or ambiguous, else None."""
  def inside(p):
    return 0 <= p[0] < height and 0 <= p[1] < width
  seen, sources, expected = {}, set(), {}
  for s, t, sp, d, cells in legends:
    if s not in COLOURS or t not in COLOURS:
      return 'legend colours must be in %s' % (COLOURS,)
    if s == t:
      return 'source and target colours must differ'
    if s in sources:
      return 'duplicate source colour %d' % s
    sources.add(s)
    if d not in DIRS:
      return 'legend direction must be an orthogonal unit step'
    tp = (sp[0] + d[0], sp[1] + d[1])
    ap = (sp[0] + 2 * d[0], sp[1] + 2 * d[1])
    if not (inside(sp) and inside(tp) and inside(ap)):
      return 'legend chain leaves the grid'
    if not cells:
      return 'stencil must be non-empty'
    for p, col in [(sp, s), (tp, t)] + [(q, STENCIL) for q in cells]:
      if not inside(p):
        return 'cell %s is out of bounds' % (p,)
      if p in seen:
        return 'cell %s is used twice' % (p,)
      seen[p] = col
    expected[(sp, d)] = frozenset(cells)
  for r, c, col in loose:
    if col not in COLOURS:
      return 'loose colours must be in %s' % (COLOURS,)
    if not inside((r, c)):
      return 'loose cell %s is out of bounds' % ((r, c),)
    if (r, c) in seen:
      return 'loose cell %s overlaps another cell' % ((r, c),)
    seen[(r, c)] = col
  for leg in legends:
    if seen.get(_anchor(leg), BG) not in (BG, STENCIL):
      return 'anchor %s must be background or 8' % (_anchor(leg),)
  grid = common.grid(width, height, BG)
  for (r, c), col in seen.items():
    grid[r][c] = col
  if _detect_legends(grid) != expected:
    return ('the input does not read back as exactly the given legends '
            '(stray chain, merged or disconnected stencil, or foreign 8s '
            'near an anchor)')
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  if any(n >= counts.get(BG, 0) for v, n in counts.items() if v != BG):
    return 'background 0 must be the most frequent input colour'
  return None


def _stamp_plan(height, width, legends, loose):
  """Returns (colour, cells) stamps in legend scan order (by source cell)."""
  plan = []
  for s, t, (sr, sc), (dr, dc), cells in sorted(legends, key=lambda L: L[2]):
    ar, ac = sr + 2 * dr, sc + 2 * dc
    offs = [(r - ar, c - ac) for r, c in cells]
    for r, c, col in loose:
      if col != s:
        continue
      group = []
      for orr, occ in offs:
        nr, nc = r + orr, c + occ
        if 0 <= nr < height and 0 <= nc < width:
          group.append((nr, nc))
      plan.append((t, group))
  return plan


def _sample(height, width, num_legends, interlock, long_runs):
  h = height if height is not None else random.randint(RANDOM_MIN, RANDOM_MAX)
  w = width if width is not None else random.randint(RANDOM_MIN, RANDOM_MAX)
  area = h * w
  if num_legends is not None:
    n_leg = num_legends
  else:
    if area >= 225:
      opts = [1, 2, 2, 3, 3, 4]
    elif area >= 120:
      opts = [1, 2, 2, 3]
    else:
      opts = [1, 2]
    if interlock:
      opts = [n for n in opts if n >= 2]
    n_leg = random.choice(opts)
  if interlock is None:
    inter = n_leg >= 2 and random.random() < 0.3
  else:
    inter = interlock
  if inter and n_leg < 2:
    return None
  runs = long_runs if long_runs is not None else random.random() < 0.3
  style = 'sep'
  if inter:
    style = ('pinwheel' if min(h, w) >= 7 and random.random() < 0.5
             else 'touch')

  sources = random.sample(COLOURS, n_leg)
  targets = []
  for s in sources:
    others = [x for x in sources if x != s]
    if others and random.random() < 0.35:
      targets.append(random.choice(others))
    else:
      targets.append(random.choice([x for x in COLOURS if x != s]))
  if runs and n_leg >= 2 and random.random() < 0.65:
    targets[0], targets[1] = sources[1], sources[0]
  elif style == 'pinwheel' and random.random() < 0.6:
    idx = list(range(n_leg))
    random.shuffle(idx)
    for a, b in zip(idx[0::2], idx[1::2]):
      targets[a], targets[b] = sources[b], sources[a]
  kinds = [None] * n_leg
  if runs:
    for i in range(min(2, n_leg)):
      if random.random() < 0.6:
        kinds[i] = SMALL_KINDS
  spare = [x for x in COLOURS if x not in sources]

  legends, foot, strict = [], set(), set()
  if style == 'pinwheel':
    res = _try_pinwheel(sources, targets, kinds, h, w)
    if res is None:
      return None
    legends, foot = res
  else:
    for i, (s, t) in enumerate(zip(sources, targets)):
      if style == 'touch' and legends and (i == 1 or random.random() < 0.5):
        res = _try_touch(s, t, h, w, kinds[i], legends, strict)
      else:
        res = _try_sep(s, t, h, w, kinds[i], foot)
      if res is None:
        return None
      leg, fp = res
      legends.append(leg)
      foot |= fp
      strict |= _visible(leg) | {_anchor(leg)}
  if inter and not _interlocked(legends):
    return None

  def inside(p):
    return 0 <= p[0] < h and 0 <= p[1] < w

  info, chain_cells, stencil_near, stencil_near2 = {}, set(), set(), set()
  for leg in legends:
    s, t, sp, d, cells = leg
    ap = _anchor(leg)
    chain_cells |= {sp, (sp[0] + d[0], sp[1] + d[1])}
    info[s] = (t, [(r - ap[0], c - ap[1]) for r, c in cells])
    for r, c in cells:
      for a in range(-2, 3):
        for b in range(-2, 3):
          stencil_near2.add((r + a, c + b))
          if abs(a) <= 1 and abs(b) <= 1:
            stencil_near.add((r + a, c + b))
  near_foot = {(r + a, c + b) for r, c in foot for a, b in NBHD}
  all_cells = [(r, c) for r in range(h) for c in range(w)]
  loose, loose_col, near_loose = [], {}, {}
  painted, preserved = {}, set()

  def group(p, col):
    t, offs = info[col]
    cells = [(p[0] + a, p[1] + b) for a, b in offs]
    return t, [q for q in cells if inside(q)]

  def fits(p, col):
    if p in loose_col or p in foot:
      return False
    if col in info:
      t, cells = group(p, col)
      return bool(cells) and all(
          painted.get(q, t) == t and q not in preserved for q in cells)
    return p not in painted

  def commit(p, col):
    record = []
    loose.append((p[0], p[1], col))
    loose_col[p] = col
    for a, b in NBHD:
      q = (p[0] + a, p[1] + b)
      near_loose[q] = near_loose.get(q, 0) + 1
    if col in info:
      t, cells = group(p, col)
      for q in cells:
        record.append((q, painted.get(q)))
        painted[q] = t
    else:
      preserved.add(p)
    return record

  def undo(p, record):
    loose.pop()
    del loose_col[p]
    for a, b in NBHD:
      q = (p[0] + a, p[1] + b)
      near_loose[q] -= 1
      if not near_loose[q]:
        del near_loose[q]
    for q, old in reversed(record):
      if old is None:
        del painted[q]
      else:
        painted[q] = old
    preserved.discard(p)

  def lay(cells, col, members, stack):
    """Commits a straight run; on failure rolls back this run only."""
    n0 = len(stack)
    for p in cells:
      bad = (not inside(p) or p in near_foot or p in stencil_near2 or
             p in loose_col or
             any((p[0] + a, p[1] + b) in loose_col and
                 (p[0] + a, p[1] + b) not in members for a, b in NBHD) or
             not fits(p, col))
      if bad:
        while len(stack) > n0:
          q, rec = stack.pop()
          undo(q, rec)
          members.discard(q)
        return False
      stack.append((p, commit(p, col)))
      members.add(p)
    return True

  def place_run_group(c1, c2):
    """Lays a long straight run of c1, optionally abutted by a run of c2."""
    for _ in range(40):
      step = random.choice([(0, 1), (1, 0)])
      extent = w if step == (0, 1) else h
      length = random.randint(3, extent)
      r0 = random.randint(0, h - 1 - (length - 1) * step[0])
      c0 = random.randint(0, w - 1 - (length - 1) * step[1])
      cells1 = [(r0 + k * step[0], c0 + k * step[1]) for k in range(length)]
      members, stack = set(), []
      if not lay(cells1, c1, members, stack):
        continue
      if c2 is None:
        return True
      perp = (step[1], step[0])
      for _ in range(25):
        ps = random.choice([1, -1])
        pd = (ps * perp[0], ps * perp[1])
        if random.random() < 0.7:
          sign = random.choice([1, -1])
          end = cells1[-1] if sign == 1 else cells1[0]
          first = (end[0] + sign * step[0], end[1] + sign * step[1])
          d2 = random.choice([pd, pd, (sign * step[0], sign * step[1])])
        else:
          base = random.choice(cells1)
          first = (base[0] + pd[0], base[1] + pd[1])
          d2 = pd
        maxl, q = 0, first
        while inside(q):
          maxl += 1
          q = (q[0] + d2[0], q[1] + d2[1])
        if maxl == 0:
          continue
        l2 = random.randint(min(3, maxl), maxl)
        cells2 = [(first[0] + k * d2[0], first[1] + k * d2[1])
                  for k in range(l2)]
        if lay(cells2, c2, members, stack):
          return True
      while stack:
        q, rec = stack.pop()
        undo(q, rec)
    return False

  if runs:
    c1 = sources[0]
    if n_leg >= 2:
      c2 = sources[1]
    else:
      c2 = targets[0] if random.random() < 0.6 else random.choice(spare)
    want_partner = long_runs is True or random.random() < 0.75
    have_runs = place_run_group(c1, c2 if want_partner else None)
    if not have_runs and long_runs:
      return None
    if have_runs and n_leg >= 3 and random.random() < 0.3:
      place_run_group(sources[2], None)

  def candidates(mode, col):
    if mode == 'attach':
      base = [p for p, cq in loose_col.items() if cq == col] or list(loose_col)
      cands = set()
      for r, c in base:
        for a, b in NBHD:
          q = (r + a, c + b)
          if inside(q) and q not in loose_col and q not in near_foot:
            cands.add(q)
      return sorted(cands)
    if mode == 'near':
      return [p for p in all_cells if p in near_foot and p not in foot and
              p not in near_loose and not _orth_adj(p, chain_cells)]
    return [p for p in all_cells
            if p not in near_foot and p not in near_loose]

  attach_p = random.choice([0.0, 0.25, 0.5])
  near_p = random.choice([0.0, 0.0, 0.15])

  def place(col):
    roll = random.random()
    modes = ['iso']
    if loose_col and roll < attach_p:
      modes.insert(0, 'attach')
    elif attach_p <= roll < attach_p + near_p:
      modes.insert(0, 'near')
    for mode in modes:
      cands = candidates(mode, col)
      random.shuffle(cands)
      for p in cands:
        if fits(p, col):
          commit(p, col)
          return True
    return False

  kmax = max(2, min(7, area // 40))
  used = set(loose_col.values())
  order = []
  for s in sources:
    if s in used:
      order.extend([s] * random.randint(0, max(1, kmax // 2)))
    else:
      order.extend([s] * random.randint(2, kmax))
  for col in random.sample(spare, random.randint(0, min(2, len(spare)))):
    order.extend([col] * random.randint(1, 4))
  random.shuffle(order)
  for col in order:
    if not place(col):
      return None

  # Optional decoy pairs: two orthogonally adjacent loose cells (often s next
  # to t) whose forward and backward anchors have no 8 nearby.
  if random.random() < 0.35:
    for _ in range(random.randint(1, 2)):
      if random.random() < 0.5:
        a_col, b_col = random.choice(legends)[:2]
      else:
        a_col, b_col = random.sample(COLOURS, 2)
      dr, dc = random.choice(DIRS)
      cands = []
      for p in all_cells:
        q = (p[0] + dr, p[1] + dc)
        if not inside(q):
          continue
        if (p in near_foot or q in near_foot or p in near_loose or
            q in near_loose):
          continue
        if ((p[0] + 2 * dr, p[1] + 2 * dc) in stencil_near or
            (p[0] - dr, p[1] - dc) in stencil_near):
          continue
        cands.append(p)
      random.shuffle(cands)
      for p in cands:
        q = (p[0] + dr, p[1] + dc)
        if not fits(p, a_col):
          continue
        record = commit(p, a_col)
        if fits(q, b_col):
          commit(q, b_col)
          break
        undo(p, record)

  if _scene_error(h, w, legends, loose) is not None:
    return None
  return h, w, legends, loose


def _render(height, width, legends, loose):
  grid_in = _paint(height, width, legends, loose)
  legend_cells = set()
  for leg in legends:
    legend_cells |= _visible(leg)
  out = [row[:] for row in grid_in]
  mapped = {leg[0] for leg in legends}
  for r, c in legend_cells:
    out[r][c] = BG
  for r, c, col in loose:
    if col in mapped:
      out[r][c] = BG
  for colour, cells in _stamp_plan(height, width, legends, loose):
    for r, c in cells:
      out[r][c] = colour
  return {'input': grid_in, 'output': out}


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_int(name, value, lo, hi):
  if value is None:
    return
  if not _is_int(value):
    raise ValueError('%s must be an int (bool/float rejected)' % name)
  if not lo <= value <= hi:
    raise ValueError('%s must be in %d..%d' % (name, lo, hi))


def _ints(value, n, what):
  if (not isinstance(value, (list, tuple)) or len(value) != n or
      not all(_is_int(v) for v in value)):
    raise ValueError('%s must be a list/tuple of %d ints' % (what, n))
  return tuple(value)


def _parse_legends(legends):
  if not isinstance(legends, (list, tuple)) or not legends:
    raise ValueError('legends must be a non-empty list')
  out = []
  for leg in legends:
    if not isinstance(leg, (list, tuple)) or len(leg) != 5:
      raise ValueError('each legend is (source, target, (sr, sc), (dr, dc), '
                       'stencil_cells)')
    s, t, sp, d, cells = leg
    if not _is_int(s) or not _is_int(t):
      raise ValueError('legend colours must be ints')
    if not isinstance(cells, (list, tuple)):
      raise ValueError('stencil cells must be a list')
    out.append((s, t, _ints(sp, 2, 'source cell'), _ints(d, 2, 'direction'),
                [_ints(p, 2, 'stencil cell') for p in cells]))
  return out


def _parse_loose(loose):
  if loose is None:
    return []
  if not isinstance(loose, (list, tuple)):
    raise ValueError('loose must be a list of (row, col, colour)')
  return [_ints(p, 3, 'loose cell') for p in loose]


def generate(height=None, width=None, legends=None, loose=None,
             num_legends=None, interlock=None, long_runs=None):
  """Builds one input/output pair.

  Args:
    height: number of rows (int). When None it is random in 6..24. An
      explicit value may be 5..30.
    width: number of columns (int). When None it is random in 6..24. An
      explicit value may be 5..30.
    legends: optional explicit, non-empty list of
      (source, target, (sr, sc), (dr, dc), stencil_cells). The target sits at
      source+d and the anchor at source+2d; stencil_cells are the absolute
      positions of the 8s. All entries must be ints (bool/float rejected).
      height and width are then required, and no sampling happens. The scene
      must read back as exactly these legends, otherwise ValueError.
    loose: optional list of (row, col, colour) loose cells; only valid with
      legends. A loose cell may not cover a background anchor.
    num_legends: optional int 1..4 for random scenes.
    interlock: optional bool for random scenes. True forces a pinwheel or
      touching layout (needs >= 2 legends); False forces separated legends.
    long_runs: optional bool for random scenes. True forces a straight run
      of a mapped colour (length 3..full side) abutted by a partner run;
      False disables runs.
  """
  _check_int('height', height, MIN_SIDE, MAX_SIDE)
  _check_int('width', width, MIN_SIDE, MAX_SIDE)
  _check_int('num_legends', num_legends, 1, 4)
  for name, v in (('interlock', interlock), ('long_runs', long_runs)):
    if v is not None and not isinstance(v, bool):
      raise ValueError('%s must be None or a bool' % name)
  if legends is not None:
    if height is None or width is None:
      raise ValueError('explicit legends require height and width')
    if num_legends is not None or interlock is not None or (
        long_runs is not None):
      raise ValueError('random-scene controls cannot be combined with '
                       'explicit legends')
    legs = _parse_legends(legends)
    pts = _parse_loose(loose)
    err = _scene_error(height, width, legs, pts)
    if err is not None:
      raise ValueError(err)
    return _render(height, width, legs, pts)
  if loose is not None:
    raise ValueError('loose cells require explicit legends')
  if interlock and num_legends == 1:
    raise ValueError('interlock requires at least 2 legends')
  for _ in range(200):
    scene = _sample(height, width, num_legends, interlock, long_runs)
    if scene is not None:
      return _render(*scene)
  raise ValueError('could not place the requested scene (grid too small for '
                   'the requested legends or layout?)')


def validate():
  """Reconstructs the canonical pairs from explicit latent parameters."""
  diamond = [(4, 9), (5, 8), (5, 10), (6, 7), (6, 11), (7, 6), (7, 12),
             (8, 7), (8, 11), (9, 8), (9, 10), (10, 9)]
  xshape = [(15, 12), (15, 16), (16, 13), (16, 15), (17, 14), (18, 13),
            (18, 15), (19, 12), (19, 16)]
  train = [
      generate(5, 5, [(1, 2, (0, 0), (0, 1), [(0, 2), (0, 3), (0, 4)])],
               [(1, 4, 1), (2, 3, 1), (3, 3, 1), (4, 4, 1)]),
      generate(15, 15, [
          (6, 7, (9, 4), (-1, 0), [(6, 4), (7, 3), (7, 5)]),
          (7, 6, (11, 4), (1, 0), [(13, 3), (13, 5), (14, 4)]),
          (2, 4, (10, 3), (0, -1), [(9, 1), (10, 0), (11, 1)]),
          (4, 2, (10, 5), (0, 1), [(9, 7), (11, 7), (10, 8)])],
               [(1, c, 6) for c in range(1, 14, 2)] +
               [(3, 1, 2), (5, 1, 2), (7, 1, 2), (11, 13, 2),
                (3, 13, 4), (5, 13, 4), (7, 13, 4),
                (13, 1, 7), (13, 7, 7), (13, 9, 7), (13, 11, 7)]),
      generate(20, 20, [
          (4, 2, (12, 9), (-1, 0), diamond),
          (1, 7, (13, 14), (1, 0), xshape)],
               [(2, 3, 4), (2, 15, 4), (4, 1, 4), (4, 13, 4), (4, 17, 4),
                (6, 3, 4), (6, 15, 4),
                (13, 2, 1), (15, 0, 1), (15, 4, 1), (17, 2, 1)]),
      generate(8, 8, [
          (2, 1, (3, 1), (0, 1), [(3, 3)]),
          (1, 2, (7, 2), (-1, 0), [(5, 2)])],
               [(0, c, 1) for c in range(5)] + [(r, 5, 2) for r in range(8)]),
  ]
  test = [
      generate(20, 20, [
          (4, 1, (2, 1), (0, 1), [(1, 3), (2, 3), (3, 3)]),
          (2, 4, (6, 1), (0, 1), [(5, 4), (6, 3), (6, 5), (7, 4)]),
          (5, 7, (10, 1), (0, 1), [(9, 4), (10, 3), (10, 4), (11, 4)])],
               [(1, 0, 2), (6, 11, 2), (8, 6, 2), (12, 16, 2), (14, 1, 2),
                (14, 5, 2), (14, 13, 2),
                (5, 17, 4), (9, 13, 4), (15, 9, 4), (17, 13, 4),
                (3, 13, 5), (8, 18, 5), (10, 9, 5), (16, 2, 5), (19, 0, 5),
                (0, 17, 6), (1, 7, 6), (1, 19, 6), (14, 19, 6), (17, 16, 6),
                (19, 9, 6), (2, 10, 1)]),
  ]
  return {'train': train, 'test': test}
