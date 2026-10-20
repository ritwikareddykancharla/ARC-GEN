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

"""ARC-GEN style generator for task b7cb93ac.

Rule: the input holds a few separated, single-colour, 4-connected
polyominoes on a zero background, with areas summing to 12. The output is
the 3x4 rectangle tiled exactly by those pieces. Pieces may be turned by
quarter turns but never mirrored. Among all tilings, the chosen one has the
fewest rotated pieces. Rotation cost is counted per piece: a piece costs 1
when its slot shape differs from its input shape, whatever the angle.

Cost model evidence: train 2 and train 3 have tilings with more rotated
pieces that paint different grids. Train 2 keeps the 7-cell 1-piece
unrotated and turns only the 8-domino. The source prose says the 1-piece is
turned upside down; the fixture shows it is not.

Preference-critical scene: some tiling with strictly more rotated pieces
paints a DIFFERENT output grid. Rearrangements that change cost but repaint
the same grid (for example same-colour pieces trading places) do not count.
The fixed-scene precheck uses the real colours and runs only when colours
are given, because colour grouping can change the answer.

Tie convention (canonical test pair): two congruent pieces of different
colours may swap slots at equal total cost. Only this rotation-preference
swap is generated: one piece is unrotated in one tiling and rotated in the
other, and its rival does the opposite. The tiling where the piece lying
entirely further left in the input stays unrotated wins. Position ties are
never generated, because only an undemonstrated reading-order rule would
decide them.

Construction:
1. Partition. An anchored sampler builds exactly k 4-connected regions. The
   region holding the first free cell gets a random size, biased toward the
   mean of the remaining cells. Each choice must leave at most
   (regions left) components so the rest can still be split. Translated
   copies are never allowed to touch. In tie-seeking mode, a disjoint
   congruent slot pair in different orientations is drawn first, and the
   rest is partitioned around it.
2. Colours. Translated copies share a colour. Congruent, non-touching
   groups may merge into one colour (as the 2-dominoes of train 3 do).
   Non-congruent pieces never share a colour. A random merge (30%) is
   tried first, then a maximal merge. Merging can only shrink the set of
   painted outputs, so the maximal merge is the strongest colouring for
   uniqueness.
3. Rotations. The base proposal leaves every piece unrotated, so its cost
   is 0 and it is automatically minimal. In tie mode, only the rival is
   turned to the winner's slot shape. With probability 0.7, up to three
   perturbations then rotate one or two further pieces. A valid perturbed
   scene is preferred; otherwise the base is kept.
4. Acceptance guard. A local tiling enumerator checks two things. The
   constructed tiling must be minimum-cost. Every minimum-cost tiling must
   paint the same grid, except for one demonstrated swap tie that the
   constructed grid wins. A bounded search then decides preference
   criticality.
5. Exact packing. Each shape is fattened by a 2x2 Minkowski sum. Two
   pieces keep an empty 8-neighbourhood gap exactly when their fattened
   sets are disjoint on an (H+1)x(W+1) board. A backtracking packer places
   the pieces largest-first, first in random order and then in a compact
   corner-first order. In tie scenes the winner lies entirely left of the
   rival. A fattened-area bound rejects hopeless canvases at once.
6. Fallback. If 1200 random proposals fail, a randomized exhaustive DFS
   over all k-region partitions of the board runs under node and leaf
   budgets. It evaluates each partition the same way. It honours only the
   explicit tie/critical flags; soft default preferences are dropped.

Why six pieces now work: the previous sampler drew rotations for every
piece (about 60% nonzero) and merged colours only partly, so almost no
six-piece scene was minimum-cost and unambiguous. It also often produced
touching translated copies. With unrotated base proposals, maximal
congruent merging, touch-free anchored partitions and an exact packer,
num_pieces=6 on a 6x6 canvas is built constructively. One example is a
multi-cell piece pair plus four same-colour monominoes.

The output is always painted from the latent regions, never from a solver.

Scope:
- The output is always 3x4, the task's target rectangle.
- The input canvas may be 6..30 per side. The random default is 8..16.
- Random scenes have 2..5 pieces by default; num_pieces allows 2..6.
  Explicit regions allow 2..8.
- About 30% of default calls first seek a swap tie, if one can be drawn.
  About 43% of the others first seek a preference-critical scene. Each
  preference is strict for the first half of the attempts and then
  dropped. These are seeking probabilities; the realised share is not
  measured here. Every returned scene is verified for the flags it was
  asked for.
- Explicit latent arguments reconstruct the original fixtures and are
  checked against the same rule.
"""

import random

import common

ROWS, COLS = 3, 4
AREA = ROWS * COLS
FULL = (1 << AREA) - 1
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
MAX_REGIONS = 8
MAX_RANDOM_PIECES = 6
DEFAULT_PIECES = (2, 3, 4, 5)
CANVAS_DEFAULT = (8, 16)
MAX_ATTEMPTS = 1200
FALLBACK_LEAVES = 1500
FALLBACK_NODES = 60000
EXPLICIT_PLACE_ROUNDS = 12
PACK_BUDGET = 2000
TILING_CAP = 400
SEARCH_BUDGET = 100000
TIE_RATE = 0.3
CRITICAL_RATE = 0.43
ROTATE_RATE = 0.7
PERTURB_TRIES = 3
MERGE_RATE = 0.3
_CACHE = {}


def _is_int(x):
  return isinstance(x, int) and not isinstance(x, bool)


def _popcount(mask):
  return bin(mask).count('1')


def _norm(cells):
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot(cells):
  """Rotates a shape 90 degrees clockwise and normalises it."""
  cells = _norm(cells)
  h = max(r for r, _ in cells) + 1
  return _norm([(c, h - 1 - r) for r, c in cells])


def _rotate(cells, k):
  shape = _norm(cells)
  for _ in range(k % 4):
    shape = _rot(shape)
  return shape


def _canon(cells):
  """Rotation-class key: the smallest of the four normalised rotations."""
  cur = _norm(cells)
  best = cur
  for _ in range(3):
    cur = _rot(cur)
    if cur < best:
      best = cur
  return best


def _same_class(a, b):
  return len(a) == len(b) and _canon(a) == _canon(b)


def _dims(shape):
  return (max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1)


def _components(cells):
  cells = set(cells)
  seen = set()
  count = 0
  for start in cells:
    if start in seen:
      continue
    count += 1
    seen.add(start)
    stack = [start]
    while stack:
      r, c = stack.pop()
      for dr, dc in DIRS:
        q = (r + dr, c + dc)
        if q in cells and q not in seen:
          seen.add(q)
          stack.append(q)
  return count


def _connected(cells):
  return bool(cells) and _components(cells) == 1


def _cell(cell):
  if (not isinstance(cell, (list, tuple)) or len(cell) != 2 or
      not all(_is_int(v) for v in cell)):
    raise ValueError('cells/offsets must be (row, col) pairs of ints')
  return (cell[0], cell[1])


def _bit(r, c):
  return 1 << (r * COLS + c)


def _mask_of(cells):
  m = 0
  for r, c in cells:
    m |= _bit(r, c)
  return m


def _cells_of(mask):
  return [divmod(i, COLS) for i in range(AREA) if mask >> i & 1]


def _nbrs():
  if 'nbr' not in _CACHE:
    out = []
    for i in range(AREA):
      r, c = divmod(i, COLS)
      m = 0
      for dr, dc in DIRS:
        y, x = r + dr, c + dc
        if 0 <= y < ROWS and 0 <= x < COLS:
          m |= _bit(y, x)
      out.append(m)
    _CACHE['nbr'] = out
  return _CACHE['nbr']


def _dilate(mask):
  """Cells 4-adjacent to some cell of mask."""
  nbr = _nbrs()
  out = 0
  while mask:
    low = mask & -mask
    out |= nbr[low.bit_length() - 1]
    mask ^= low
  return out


def _comp_table():
  """Number of 4-connected components of every board cell subset."""
  if 'comps' not in _CACHE:
    table = [0] * (FULL + 1)
    for mask in range(1, FULL + 1):
      comp = mask & -mask
      frontier = comp
      while frontier:
        grow = _dilate(frontier) & mask & ~comp
        comp |= grow
        frontier = grow
      table[mask] = 1 + table[mask & ~comp]
    _CACHE['comps'] = table
  return _CACHE['comps']


def _polys():
  """All connected board subsets: list and index by (first cell, size)."""
  if 'polys' not in _CACHE:
    comps = _comp_table()
    allp = []
    by_min = [{} for _ in range(AREA)]
    for mask in range(1, FULL + 1):
      if comps[mask] != 1:
        continue
      cells = _cells_of(mask)
      norm = _norm(cells)
      allp.append((mask, norm))
      first = (mask & -mask).bit_length() - 1
      by_min[first].setdefault(len(cells), []).append((mask, norm))
    _CACHE['polys'] = (allp, by_min)
  return _CACHE['polys']


def _check_regions(regions):
  if not 2 <= len(regions) <= MAX_REGIONS:
    raise ValueError('need between 2 and %d regions' % MAX_REGIONS)
  seen = set()
  for reg in regions:
    if not reg:
      raise ValueError('regions must be non-empty')
    for cell in reg:
      if not (0 <= cell[0] < ROWS and 0 <= cell[1] < COLS) or cell in seen:
        raise ValueError('regions must partition the 3x4 board')
      seen.add(cell)
    if not _connected(reg):
      raise ValueError('each region must be 4-connected')
  if len(seen) != AREA:
    raise ValueError('regions must cover the whole 3x4 board')


def _adjacency(regions):
  index = {}
  for i, reg in enumerate(regions):
    for cell in reg:
      index[cell] = i
  adj = [set() for _ in regions]
  for i, reg in enumerate(regions):
    for r, c in reg:
      for dr, dc in DIRS:
        j = index.get((r + dr, c + dc))
        if j is not None and j != i:
          adj[i].add(j)
  return adj


def _translated_adjacent(regions):
  adj = _adjacency(regions)
  return any(_norm(regions[i]) == _norm(regions[j])
             for i in range(len(regions)) for j in adj[i])


def _same_colour_adjacent(regions, colors):
  adj = _adjacency(regions)
  return any(colors[i] == colors[j]
             for i in range(len(regions)) for j in adj[i])


def _tie_pairs(regions, colors=None):
  """Congruent region pairs in different orientations (and colours)."""
  pairs = []
  for i in range(len(regions)):
    for j in range(i + 1, len(regions)):
      if _norm(regions[i]) == _norm(regions[j]):
        continue
      if not _same_class(regions[i], regions[j]):
        continue
      if colors is not None and colors[i] == colors[j]:
        continue
      pairs.append((i, j))
  return pairs


def _fixed_tie_pairs(regions, rotations, colors=None):
  """(winner, rival) pairs that can form a swap tie under fixed rotations."""
  shapes = [_rotate(reg, k) for reg, k in zip(regions, rotations)]
  out = []
  for i in range(len(regions)):
    for j in range(i + 1, len(regions)):
      if shapes[i] != shapes[j]:
        continue
      if _norm(regions[i]) == _norm(regions[j]):
        continue
      if colors is not None and colors[i] == colors[j]:
        continue
      if shapes[i] == _norm(regions[i]):
        out.append((i, j))
      elif shapes[i] == _norm(regions[j]):
        out.append((j, i))
  return out


def _tie_slots():
  """Disjoint congruent board polyomino pairs in different orientations."""
  if 'ties' not in _CACHE:
    allp, _ = _polys()
    comps = _comp_table()
    groups = {}
    for mask, norm in allp:
      if len(norm) <= AREA // 2:
        groups.setdefault(_canon(norm), []).append((mask, norm))
    out = []
    for members in groups.values():
      for x in range(len(members)):
        ma, na = members[x]
        for y in range(x + 1, len(members)):
          mb, nb = members[y]
          if ma & mb or na == nb:
            continue
          rest = FULL & ~(ma | mb)
          out.append((ma, na, mb, nb, rest, _popcount(rest), comps[rest]))
    _CACHE['ties'] = out
  return _CACHE['ties']


def _tie_slots_for(k):
  """Slot pairs whose leftover cells can be split into k - 2 regions."""
  key = ('tiek', k)
  if key not in _CACHE:
    _CACHE[key] = [s[:5] for s in _tie_slots() if s[6] <= k - 2 <= s[5]]
  return _CACHE[key]


def _pair_fits(shape, width, height):
  """True if two copies of shape fit left-to-right with an 8-gap."""
  key = ('fit', shape, width, height)
  if key in _CACHE:
    return _CACHE[key]
  h, w = _dims(shape)
  ok = False
  if h <= height and 2 * w <= width:
    halo = set()
    for a, b in shape:
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          halo.add((a + dy, b + dx))
    for dc in range(w, width - w + 1):
      for dr in range(-(height - h), height - h + 1):
        if all((a + dr, b + dc) not in halo for a, b in shape):
          ok = True
          break
      if ok:
        break
  _CACHE[key] = ok
  return ok


def _tie_counts(ks, width, height):
  """Piece counts in ks for which a swap-tie pair can be drawn."""
  out = []
  for k in ks:
    if any(_pair_fits(na, width, height) or _pair_fits(nb, width, height)
           for _, na, _, nb, _ in _tie_slots_for(k)):
      out.append(k)
  return out


def _region_ok(mask, norm, free, regs, m_left):
  """Region keeps the rest splittable and touches no translated copy."""
  rest = free & ~mask
  if m_left == 1:
    if rest:
      return False
  elif not rest or _comp_table()[rest] > m_left - 1:
    return False
  grown = _dilate(mask)
  for other, onorm in regs:
    if onorm == norm and grown & other:
      return False
  return True


def _anchored_partition(k, free=FULL, regs=()):
  """Random partition of the free cells; returns k (mask, norm) or None."""
  _, by_min = _polys()
  regs = list(regs)
  while free:
    m_left = k - len(regs)
    if m_left <= 0:
      return None
    f = _popcount(free)
    table = by_min[(free & -free).bit_length() - 1]
    if m_left == 1:
      sizes = [f]
    else:
      mean = f / m_left
      sizes = [s for s in range(1, f - m_left + 2) if s in table]
      sizes.sort(key=lambda s: abs(s - mean) + random.uniform(0, 3))
    pick = None
    for s in sizes:
      cands = [e for e in table.get(s, ()) if not e[0] & ~free]
      random.shuffle(cands)
      for mask, norm in cands:
        if _region_ok(mask, norm, free, regs, m_left):
          pick = (mask, norm)
          break
      if pick is not None:
        break
    if pick is None:
      return None
    regs.append(pick)
    free &= ~pick[0]
  return regs if len(regs) == k else None


def _tie_partition(k, width, height):
  """Partition built around a congruent, differently oriented slot pair."""
  opts = []
  for ma, na, mb, nb, rest in _tie_slots_for(k):
    if _pair_fits(na, width, height):
      opts.append((ma, na, mb, nb, rest))
    if _pair_fits(nb, width, height):
      opts.append((mb, nb, ma, na, rest))
  if not opts:
    return None
  mw, nw, mr, nr, rest = random.choice(opts)
  regs = _anchored_partition(k, rest, [(mw, nw), (mr, nr)])
  if regs is None:
    return None
  order = list(range(k))
  random.shuffle(order)
  cells = [_cells_of(regs[i][0]) for i in order]
  return cells, (order.index(0), order.index(1))


def _iter_partitions(k, nodes, free=FULL, regs=None):
  """Randomised exhaustive DFS over k-region partitions (node budget)."""
  regs = [] if regs is None else regs
  nodes[0] += 1
  if nodes[0] > FALLBACK_NODES:
    return
  if not free:
    if len(regs) == k:
      yield list(regs)
    return
  m_left = k - len(regs)
  if m_left <= 0:
    return
  f = _popcount(free)
  first = (free & -free).bit_length() - 1
  lo = f if m_left == 1 else 1
  hi = f if m_left == 1 else f - m_left + 1
  cands = []
  for size, entries in _polys()[1][first].items():
    if lo <= size <= hi:
      for mask, norm in entries:
        if not mask & ~free and _region_ok(mask, norm, free, regs, m_left):
          cands.append((mask, norm))
  random.shuffle(cands)
  for cand in cands:
    regs.append(cand)
    for part in _iter_partitions(k, nodes, free & ~cand[0], regs):
      yield part
    regs.pop()


def _choose_colors(cells, norms, apart, merge):
  """Colours regions: translated copies share, congruent groups may merge.

  apart is an optional (i, j) pair that must get different colours. merge
  is the probability of joining a compatible congruent colour group (1.0
  gives a maximal merge). Returns None if translated copies touch.
  """
  n = len(cells)
  masks = [_mask_of(c) for c in cells]
  grown = [_dilate(m) for m in masks]

  def clash(i, j):
    if grown[i] & masks[j]:
      return True
    return apart is not None and (i, j) in (tuple(apart), tuple(apart)[::-1])

  groups = {}
  for i, nm in enumerate(norms):
    groups.setdefault(nm, []).append(i)
  for members in groups.values():
    if any(clash(i, j) for i in members for j in members if i != j):
      return None
  classes = {}
  for nm in sorted(groups):
    classes.setdefault(_canon(nm), []).append(nm)
  sets = []
  for cls in sorted(classes):
    keys = list(classes[cls])
    random.shuffle(keys)
    local = []
    for key in keys:
      mem = groups[key]
      ok = [s for s in local
            if not any(clash(i, j) for i in s for j in mem)]
      if ok and random.random() < merge:
        random.choice(ok).extend(mem)
      else:
        local.append(list(mem))
    sets.extend(local)
  if len(sets) > 9:
    return None
  palette = random.sample(range(1, 10), len(sets))
  cols = [0] * n
  for members, col in zip(sets, palette):
    for i in members:
      cols[i] = col
  return cols


def _colour_key(cols):
  return tuple(cols.index(c) for c in cols)


def _target(regions, colors):
  out = common.grid(COLS, ROWS, 0)
  for reg, col in zip(regions, colors):
    for r, c in reg:
      out[r][c] = col
  return out


def _piece_types(shapes, colors):
  """Groups identical pieces (same colour and input shape).

  Returns (colour, orientations, member_indices); each orientation is
  (shape, cost) with cost 0 for the original orientation, else 1.
  """
  keys, members = [], []
  for i, (shape, col) in enumerate(zip(shapes, colors)):
    key = (col, shape)
    if key in keys:
      members[keys.index(key)].append(i)
    else:
      keys.append(key)
      members.append([i])
  types = []
  for (col, shape), mem in zip(keys, members):
    orients, cur = [], shape
    for _ in range(4):
      if cur not in [o for o, _ in orients]:
        orients.append((cur, 0 if cur == shape else 1))
      cur = _rot(cur)
    types.append((col, orients, mem))
  return types


def _first_empty(board):
  for r in range(ROWS):
    for c in range(COLS):
      if not board[r][c]:
        return (r, c)
  return None


def _anchored(shape, empty):
  ar, ac = shape[0]
  dr, dc = empty[0] - ar, empty[1] - ac
  return [(a + dr, b + dc) for a, b in shape]


def _free(board, cells):
  return all(0 <= y < ROWS and 0 <= x < COLS and not board[y][x]
             for y, x in cells)


def _mark(board, cells, value):
  for y, x in cells:
    board[y][x] = value


def _tilings_upto(types, bound):
  """Every tiling with cost exactly bound, or None if cheaper/over cap."""
  board = [[False] * COLS for _ in range(ROWS)]
  left = [len(t[2]) for t in types]
  stack = []
  found = []
  state = {'abort': False}

  def rec(cost):
    if state['abort'] or cost > bound:
      return
    empty = _first_empty(board)
    if empty is None:
      if cost < bound or len(found) >= TILING_CAP:
        state['abort'] = True
        return
      found.append(frozenset(stack))
      return
    for ti, (_, orients, _) in enumerate(types):
      if not left[ti]:
        continue
      for shape, oc in orients:
        cs = _anchored(shape, empty)
        if not _free(board, cs):
          continue
        _mark(board, cs, True)
        left[ti] -= 1
        stack.append((ti, frozenset(cs), oc))
        rec(cost + oc)
        stack.pop()
        left[ti] += 1
        _mark(board, cs, False)

  rec(0)
  return None if state['abort'] else found


def _search(types, accept, prune):
  """Bounded search for a tiling with accept(cost); None on budget."""
  board = [[False] * COLS for _ in range(ROWS)]
  left = [len(t[2]) for t in types]
  nodes = [0]

  def rec(cost):
    if prune(cost):
      return False
    nodes[0] += 1
    if nodes[0] > SEARCH_BUDGET:
      return None
    empty = _first_empty(board)
    if empty is None:
      return bool(accept(cost))
    for ti, (_, orients, _) in enumerate(types):
      if not left[ti]:
        continue
      for shape, oc in orients:
        cs = _anchored(shape, empty)
        if not _free(board, cs):
          continue
        _mark(board, cs, True)
        left[ti] -= 1
        res = rec(cost + oc)
        left[ti] += 1
        _mark(board, cs, False)
        if res is None or res:
          return res
    return False

  return rec(0)


def _has_cheaper(types, bound):
  return _search(types, lambda c: True, lambda c: c >= bound)


def _has_costlier_diff(types, bound, target):
  """True if a tiling costing more than bound paints a grid != target.

  Returns None when the node budget runs out.
  """
  board = [[0] * COLS for _ in range(ROWS)]
  left = [len(t[2]) for t in types]
  nodes = [0]

  def rec(cost):
    nodes[0] += 1
    if nodes[0] > SEARCH_BUDGET:
      return None
    empty = _first_empty(board)
    if empty is None:
      return cost > bound and board != target
    for ti, (col, orients, _) in enumerate(types):
      if not left[ti]:
        continue
      for shape, oc in orients:
        cs = _anchored(shape, empty)
        if not _free(board, cs):
          continue
        _mark(board, cs, col)
        left[ti] -= 1
        res = rec(cost + oc)
        left[ti] += 1
        _mark(board, cs, 0)
        if res is None or res:
          return res
    return False

  return rec(0)


def _paint(types, tiling):
  out = [[0] * COLS for _ in range(ROWS)]
  for ti, cells, _ in tiling:
    for y, x in cells:
      out[y][x] = types[ti][0]
  return tuple(tuple(row) for row in out)


def _resolve(types, target, my_cost):
  """None if invalid/ambiguous, () if unique, (winner, rival) for a tie."""
  tilings = _tilings_upto(types, my_cost)
  if not tilings:
    return None
  key = tuple(tuple(row) for row in target)
  painted = [_paint(types, t) for t in tilings]
  grids = set(painted)
  if key not in grids:
    return None
  if len(grids) == 1:
    return ()
  if len(grids) != 2 or len(tilings) != 2:
    return None
  k = painted.index(key)
  t_win, t_alt = tilings[k], tilings[1 - k]
  win = list(t_win - t_alt)
  alt = {p[0]: p for p in t_alt - t_win}
  if len(win) != 2 or len(alt) != 2:
    return None
  (tx, cx, ox), (ty, cy, oy) = win
  if tx == ty or set(alt) != {tx, ty}:
    return None
  if len(types[tx][2]) != 1 or len(types[ty][2]) != 1:
    return None
  _, ax, ox2 = alt[tx]
  _, ay, oy2 = alt[ty]
  if ax != cy or ay != cx:
    return None
  ix, iy = types[tx][2][0], types[ty][2][0]
  if ox == 0 and ox2 == 1:
    return (ix, iy)
  if oy == 0 and oy2 == 1:
    return (iy, ix)
  return None


def _evaluate(cells, cols, rots):
  """Checks a latent scene; returns a scene dict or None."""
  shapes = [_rotate(reg, rot) for reg, rot in zip(cells, rots)]
  target = _target(cells, cols)
  my_cost = sum(1 for reg, s in zip(cells, shapes) if _norm(reg) != s)
  types = _piece_types(shapes, cols)
  verdict = _resolve(types, target, my_cost)
  if verdict is None:
    return None
  crit = _has_costlier_diff(types, my_cost, target)
  return {'shapes': shapes, 'colors': list(cols), 'target': target,
          'tie': verdict, 'critical': crit}


def _flags_ok(scene, seek, want):
  if seek is not None and seek != bool(scene['tie']):
    return False
  if want is not None and scene['critical'] is not want:
    return False
  return True


def _perturb(cells, norms, base, keep):
  movable = []
  for i, reg in enumerate(cells):
    if i in keep:
      continue
    qs = [q for q in (1, 2, 3) if _rotate(reg, q) != norms[i]]
    if qs:
      movable.append((i, qs))
  if not movable:
    return None
  rots = list(base)
  for i, qs in random.sample(movable, random.randint(1, min(2, len(movable)))):
    rots[i] = random.choice(qs)
  return rots


def _fat(shape):
  out = set()
  for a, b in shape:
    for da in (0, 1):
      for db in (0, 1):
        out.add((a + da, b + db))
  return sorted(out)


def _pack_once(shapes, fats, dims, height, width, pair, compact):
  n = len(shapes)
  order = sorted(range(n), key=lambda i: (-len(fats[i]), random.random()))
  occ = [[False] * (width + 1) for _ in range(height + 1)]
  offs = [None] * n
  nodes = [0]
  corner = (random.randint(0, 1), random.randint(0, 1))

  def cands(i):
    hh, ww = dims[i]
    lo, hi = 0, width - ww
    if pair:
      win, riv = pair
      if i == win and offs[riv] is not None:
        hi = min(hi, offs[riv][1] - ww)
      if i == riv and offs[win] is not None:
        lo = max(lo, offs[win][1] + dims[win][1])
    out = []
    for r in range(height - hh + 1):
      for c in range(lo, hi + 1):
        if all(not occ[r + a][c + b] for a, b in fats[i]):
          out.append((r, c))
    if compact:
      out.sort(key=lambda p: (
          (height - hh - p[0] if corner[0] else p[0]) +
          (width - ww - p[1] if corner[1] else p[1]), random.random()))
    else:
      random.shuffle(out)
    return out

  def rec(t):
    if t == n:
      return True
    nodes[0] += 1
    if nodes[0] > PACK_BUDGET:
      return None
    i = order[t]
    for r, c in cands(i):
      for a, b in fats[i]:
        occ[r + a][c + b] = True
      offs[i] = (r, c)
      res = rec(t + 1)
      if res:
        return True
      for a, b in fats[i]:
        occ[r + a][c + b] = False
      offs[i] = None
      if res is None:
        return None
    return False

  return list(offs) if rec(0) else None


def _pack(shapes, height, width, pair):
  """Exact bounded packer with an 8-neighbourhood gap between pieces."""
  dims = [_dims(s) for s in shapes]
  if any(h > height or w > width for h, w in dims):
    return None
  if pair and dims[pair[0]][1] + dims[pair[1]][1] > width:
    return None
  fats = [_fat(s) for s in shapes]
  if sum(len(f) for f in fats) > (height + 1) * (width + 1):
    return None
  for compact in (False, True):
    offs = _pack_once(shapes, fats, dims, height, width, pair, compact)
    if offs is not None:
      return offs
  return None


def _check_input(shapes, offsets, height, width):
  if len(offsets) != len(shapes):
    raise ValueError('need one offset per piece')
  owner = {}
  for i, (shape, off) in enumerate(zip(shapes, offsets)):
    r0, c0 = off
    for a, b in shape:
      y, x = r0 + a, c0 + b
      if not (0 <= y < height and 0 <= x < width):
        raise ValueError('piece lies outside the canvas')
      if (y, x) in owner:
        raise ValueError('pieces overlap')
      owner[(y, x)] = i
  for (y, x), i in owner.items():
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        j = owner.get((y + dy, x + dx))
        if j is not None and j != i:
          raise ValueError('pieces must be separated by an empty cell')


def _ordered(shapes, offsets, pair):
  a, b = pair
  a_right = offsets[a][1] + max(c for _, c in shapes[a])
  return a_right < offsets[b][1]


def _try_colouring(cells, norms, cols, rotations, plan, seek, want,
                   width, height):
  if rotations is not None:
    base = list(rotations)
  else:
    base = [0] * len(cells)
    if plan:
      win, riv = plan
      base[riv] = [q for q in (1, 2, 3)
                   if _rotate(cells[riv], q) == norms[win]][0]
  scene = _evaluate(cells, cols, base)
  if scene is None:
    return None
  options = []
  if rotations is None and random.random() < ROTATE_RATE:
    keep = set(plan) if plan else set()
    for _ in range(PERTURB_TRIES):
      rots = _perturb(cells, norms, base, keep)
      if rots is None:
        break
      alt = _evaluate(cells, cols, rots)
      if alt is not None and _flags_ok(alt, seek, want):
        options.append(alt)
        break
  options.append(scene)
  for sc in options:
    if not _flags_ok(sc, seek, want):
      continue
    offs = _pack(sc['shapes'], height, width, sc['tie'] or None)
    if offs is not None:
      return sc, offs
  return None


def _try_partition(cells, colors, rotations, seek, want, width, height,
                   pair=None):
  """Colours, rotates, verifies and packs one partition; or None."""
  norms = [_norm(c) for c in cells]
  if seek:
    if pair is not None:
      plans = [pair]
    else:
      if rotations is not None:
        cand = _fixed_tie_pairs(cells, rotations, colors)
      else:
        cand = []
        for a, b in _tie_pairs(cells, colors):
          cand.extend([(a, b), (b, a)])
      cand = [p for p in cand if _pair_fits(norms[p[0]], width, height)]
      random.shuffle(cand)
      plans = cand[:2]
    if not plans:
      return None
  else:
    plans = [None]
  for plan in plans:
    if colors is not None:
      colourings = [list(colors)]
    else:
      colourings = [_choose_colors(cells, norms, plan, MERGE_RATE),
                    _choose_colors(cells, norms, plan, 1.0)]
    seen = set()
    for cols in colourings:
      if cols is None:
        continue
      key = _colour_key(cols)
      if key in seen:
        continue
      seen.add(key)
      if plan and cols[plan[0]] == cols[plan[1]]:
        continue
      found = _try_colouring(cells, norms, cols, rotations, plan, seek, want,
                             width, height)
      if found is not None:
        return found
  return None


def _fallback(ks, seek, want, width, height):
  """Randomised exhaustive partition DFS under node/leaf budgets."""
  nodes = [0]
  leaves = 0
  order = list(ks)
  random.shuffle(order)
  for k in order:
    for regs in _iter_partitions(k, nodes):
      leaves += 1
      if leaves > FALLBACK_LEAVES:
        return None
      w = width if width is not None else random.randint(*CANVAS_DEFAULT)
      h = height if height is not None else random.randint(*CANVAS_DEFAULT)
      cells = [_cells_of(m) for m, _ in regs]
      found = _try_partition(cells, None, None, seek, want, w, h)
      if found is not None:
        return found[0], found[1], w, h
  return None


def _emit(scene, offs, width, height):
  shapes = scene['shapes']
  _check_input(shapes, offs, height, width)
  if scene['tie'] and not _ordered(shapes, offs, scene['tie']):
    raise ValueError('tied pieces violate the left-to-right tie rule')
  grid = common.grid(width, height, 0)
  for shape, col, (r0, c0) in zip(shapes, scene['colors'], offs):
    for a, b in shape:
      grid[r0 + a][c0 + b] = col
  return {'input': grid, 'output': [list(row) for row in scene['target']]}


def _parse_ints(values, count, lo, hi, name):
  if not isinstance(values, (list, tuple)) or len(values) != count:
    raise ValueError('%s must be a list of %d ints' % (name, count))
  out = []
  for v in values:
    if not _is_int(v) or not lo <= v <= hi:
      raise ValueError('%s entries must be ints in %d..%d' % (name, lo, hi))
    out.append(v)
  return out


def generate(width=None, height=None, regions=None, colors=None,
             rotations=None, offsets=None, num_pieces=None, tie=None,
             critical=None):
  """Returns an input/output pair for task b7cb93ac.

  Any latent argument left as None is sampled.

  Args:
    width: input canvas width, int in 6..30 (random default 8..16).
    height: input canvas height, int in 6..30 (random default 8..16).
    regions: list of cell lists [(row, col), ...] partitioning the 3x4
      board into 2..8 4-connected regions; 4-adjacent regions may not be
      translated copies. If None, a random partition is built.
    colors: list of ints 1..9, one per region (requires regions);
      4-adjacent regions must differ.
    rotations: list of ints 0..3, clockwise quarter turns turning each
      region into its input shape (requires regions). The result must use
      the fewest rotated pieces, else ValueError.
    offsets: list of (row, col) top-left positions of the rotated pieces
      (requires regions, colors, rotations, width and height).
    num_pieces: piece count for random partitions, 2..6 (default 2..5);
      must equal len(regions) if regions is given.
    tie: True requires a rotation-preference swap tie (left-piece rule);
      False forbids one; None lets the sampler choose.
    critical: True requires a costlier tiling painting a different grid;
      False forbids one; None lets the sampler choose.
  """
  for flag, name in ((tie, 'tie'), (critical, 'critical')):
    if flag is not None and not isinstance(flag, bool):
      raise ValueError('%s must be None, True or False' % name)
  for side in (width, height):
    if side is not None and (not _is_int(side) or not 6 <= side <= 30):
      raise ValueError('canvas sides must be ints in 6..30')
  if num_pieces is not None and not _is_int(num_pieces):
    raise ValueError('num_pieces must be an int')
  if regions is None:
    if colors is not None or rotations is not None or offsets is not None:
      raise ValueError('colors/rotations/offsets require explicit regions')
    if num_pieces is not None and not 2 <= num_pieces <= MAX_RANDOM_PIECES:
      raise ValueError('num_pieces must be in 2..%d' % MAX_RANDOM_PIECES)
  else:
    if not isinstance(regions, (list, tuple)):
      raise ValueError('regions must be a list of cell lists')
    parsed = []
    for reg in regions:
      if not isinstance(reg, (list, tuple)):
        raise ValueError('each region must be a list of cells')
      parsed.append(sorted(_cell(cell) for cell in reg))
    regions = parsed
    _check_regions(regions)
    if _translated_adjacent(regions):
      raise ValueError('two adjacent regions are translated copies; any '
                       'colouring merges them or gives a position tie')
    if num_pieces is not None and num_pieces != len(regions):
      raise ValueError('num_pieces disagrees with regions')
    n = len(regions)
    if colors is not None:
      colors = _parse_ints(colors, n, 1, 9, 'colors')
      if _same_colour_adjacent(regions, colors):
        raise ValueError('adjacent regions must have different colours')
    if rotations is not None:
      rotations = _parse_ints(rotations, n, 0, 3, 'rotations')
    if offsets is not None:
      if colors is None or rotations is None:
        raise ValueError('explicit offsets require colors and rotations')
      if width is None or height is None:
        raise ValueError('explicit offsets require width and height')
      if not isinstance(offsets, (list, tuple)) or len(offsets) != n:
        raise ValueError('need one offset per region')
      offsets = [_cell(o) for o in offsets]

  # Feasibility pre-checks (prompt ValueError instead of wasted attempts).
  fit_w = width if width is not None else CANVAS_DEFAULT[1]
  fit_h = height if height is not None else CANVAS_DEFAULT[1]
  ks, tie_ks = [], []
  if regions is None:
    ks = [num_pieces] if num_pieces is not None else list(DEFAULT_PIECES)
    tie_ks = _tie_counts(ks, fit_w, fit_h) if tie is not False else []
    tie_possible = bool(tie_ks)
  elif rotations is None:
    tie_possible = any(
        _pair_fits(_norm(regions[a]), fit_w, fit_h) or
        _pair_fits(_norm(regions[b]), fit_w, fit_h)
        for a, b in _tie_pairs(regions, colors))
  else:
    tie_possible = any(
        _pair_fits(_norm(regions[win]), fit_w, fit_h)
        for win, _ in _fixed_tie_pairs(regions, rotations, colors))
  if tie is True and not tie_possible:
    raise ValueError('no rotation-preference swap tie can be drawn with '
                     'these regions/rotations/colours on this canvas')
  if regions is not None and rotations is not None:
    shapes0 = [_rotate(reg, k) for reg, k in zip(regions, rotations)]
    cost0 = sum(1 for reg, s in zip(regions, shapes0) if _norm(reg) != s)
    if _has_cheaper(_piece_types(shapes0, [0] * len(shapes0)), cost0):
      raise ValueError('rotations admit a tiling with fewer rotated pieces; '
                       'the constructed output would not be the answer')
    if colors is not None and critical is not None:
      crit0 = _has_costlier_diff(_piece_types(shapes0, colors), cost0,
                                 _target(regions, colors))
      if crit0 is not None and crit0 != critical:
        raise ValueError('fixed shapes and colours contradict critical')

  explicit = (regions is not None and colors is not None and
              rotations is not None)
  if explicit:
    scene = _evaluate(regions, colors, rotations)
    if scene is None:
      raise ValueError('explicit scene is not minimum-cost, ambiguous, or '
                       'an undemonstrated position tie')
    if tie is not None and tie != bool(scene['tie']):
      raise ValueError('explicit scene does not match the tie mode')
    if critical is not None and scene['critical'] is not critical:
      raise ValueError('explicit scene does not match the critical mode')
    for _ in range(EXPLICIT_PLACE_ROUNDS):
      w = width if width is not None else random.randint(*CANVAS_DEFAULT)
      h = height if height is not None else random.randint(*CANVAS_DEFAULT)
      if offsets is not None:
        return _emit(scene, list(offsets), w, h)
      offs = _pack(scene['shapes'], h, w, scene['tie'] or None)
      if offs is not None:
        return _emit(scene, offs, w, h)
    raise ValueError('could not place the pieces on the canvas')

  prefer_tie = False
  prefer_crit = False
  if tie is None and tie_possible and random.random() < TIE_RATE:
    prefer_tie = True
  elif critical is None and random.random() < CRITICAL_RATE:
    prefer_crit = True
  half = MAX_ATTEMPTS // 2
  for attempt in range(MAX_ATTEMPTS):
    early = attempt < half
    seek = tie
    if seek is None and prefer_tie and early:
      seek = True
    want = critical
    if want is None and prefer_crit and early:
      want = True
    w = width if width is not None else random.randint(*CANVAS_DEFAULT)
    h = height if height is not None else random.randint(*CANVAS_DEFAULT)
    pair = None
    if regions is None:
      if seek:
        prop = _tie_partition(random.choice(tie_ks), w, h)
        if prop is None:
          continue
        cells, pair = prop
      else:
        regs = _anchored_partition(random.choice(ks))
        if regs is None:
          continue
        cells = [_cells_of(m) for m, _ in regs]
        random.shuffle(cells)
    else:
      cells = regions
    found = _try_partition(cells, colors, rotations, seek, want, w, h, pair)
    if found is not None:
      return _emit(found[0], found[1], w, h)
  if regions is None:
    found = _fallback(tie_ks if tie else ks, tie, critical, width, height)
    if found is not None:
      return _emit(found[0], found[1], found[2], found[3])
  raise ValueError('could not construct a scene satisfying the requested '
                   'constraints within the attempt budget')


def validate():
  """Reconstructs the original fixtures from explicit latent parameters."""
  train = [
      generate(width=12, height=10,
               regions=[[(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)],
                        [(0, 1), (0, 2), (0, 3), (1, 3), (2, 2), (2, 3)],
                        [(2, 1)]],
               colors=[2, 3, 8], rotations=[0, 0, 0],
               offsets=[(2, 4), (5, 8), (6, 1)]),
      generate(width=13, height=10,
               regions=[[(0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0),
                         (2, 3)],
                        [(2, 1), (2, 2)],
                        [(0, 0), (0, 1), (0, 2)]],
               colors=[1, 8, 2], rotations=[0, 1, 0],
               offsets=[(3, 1), (1, 10), (8, 5)]),
      generate(width=11, height=10,
               regions=[[(0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)],
                        [(0, 2), (0, 3)], [(2, 2), (2, 3)],
                        [(0, 0)], [(2, 0)]],
               colors=[1, 2, 2, 8, 8], rotations=[0, 0, 1, 0, 0],
               offsets=[(1, 2), (5, 7), (7, 8), (6, 4), (8, 1)]),
  ]
  test = [
      generate(width=10, height=10,
               regions=[[(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)],
                        [(1, 1), (2, 0), (2, 1)],
                        [(1, 2), (2, 2), (2, 3)]],
               colors=[8, 3, 6], rotations=[0, 0, 3],
               offsets=[(2, 2), (6, 3), (3, 7)]),
  ]
  return {'train': train, 'test': test}
