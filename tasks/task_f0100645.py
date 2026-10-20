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

"""ARC task f0100645: blobs slide toward the wall of their own colour.

Rule: column 0 is a solid wall of one colour, and the last column is a solid
wall of a different colour. The background is 7. Small blobs in the two wall
colours sit between the walls. Blobs are grouped by colour with diagonal
(8-way) connectivity. Each blob slides horizontally, as a rigid shape, toward
the wall of its own colour. It stops just before its next step would hit any
non-background cell. Within each colour, the blob nearest its wall moves
first: left movers by smallest min column, right movers by largest max column.
Later blobs therefore pile up against blobs that have already slid.

Scope: the default sampler draws the height from 6..16 and the width from
7..16. Explicit sizes (width 5..30, height 3..30) are a synthetic extension;
the fixtures are 9x9 and 10x10. Wall colours are sampled, distinct and never
7. The background 7 is fixed, as in every example.

The generator builds a latent list of 8-connected shapes. Most shapes fit a
3x3 box. About 30% are elongated: a straight 4- or 5-cell spine in a 4x2,
5x2, 2x4 or 2x5 box, like the tall 8-blob of the test pair. Every shape has
at most 7 cells. Shapes of the same colour never touch, so each latent shape
is exactly one input component. No blob starts touching its own wall. Shapes
of different colours may touch and may block each other.

By default about 75% of scenes require a genuine stacking event. In such an
event, a blob stops short of its wall because every cell blocking its next
step belongs to a same-colour blob that has already slid. Stacked candidates
are placed on a shared row, farther from the wall than a same-colour blocker.
About 40% of scenes require a blob whose grouping depends on a diagonal-only
link, so that 4-connected grouping would give a different answer. Either
requirement can be forced on or off.

Random (soft) demands are dropped when the grid cannot host them, and also
after half of the bounded search fails. Explicit (hard) demands that cannot
fit raise ValueError. Hard demands on grids that are feasible in principle but
very tight may still exhaust the bounded search and raise RuntimeError.

The answer is simulated from the latent objects in the reference order: right
movers first, then left movers. A scene is rejected unless every
nearest-first order gives the same answer. That covers any permutation of
tied keys within a colour and any interleaving of the two colours. The check
is exact: a memoised search over (processed set, shifts) states. A scene is
also rejected if it is the identity, if a colour has no blob that moves, or if
7 is not strictly the most frequent colour.
"""

import random

import common

BG = 7
_ORTH = ((0, 1), (0, -1), (1, 0), (-1, 0))
_DIAG = ((1, 1), (1, -1), (-1, 1), (-1, -1))
_STATE_BUDGET = 3000
_TRIES = 500


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_colour(name, value):
  if value is None:
    return
  if not _is_int(value) or not 0 <= value <= 9 or value == BG:
    raise ValueError("%s must be an int colour 0..9 other than %d" % (name, BG))


def _pick_colours(left, right):
  _check_colour("left", left)
  _check_colour("right", right)
  if left is not None and right is not None and left == right:
    raise ValueError("left and right wall colours must differ")
  lc, rc = left, right
  if lc is None:
    lc = random.choice([c for c in range(10) if c not in (BG, rc)])
  if rc is None:
    rc = random.choice([c for c in range(10) if c not in (BG, lc)])
  return lc, rc


def _walls(w, h, lc, rc):
  g = common.grid(w, h, BG)
  for r in range(h):
    g[r][0] = lc
    g[r][w - 1] = rc
  return g


def _key(objs, i):
  """Nearest-first sort key: min column for left movers, -max for right."""
  d, cells = objs[i][1], objs[i][2]
  if d < 0:
    return min(x for _, x in cells)
  return -max(x for _, x in cells)


def _ref_order(objs):
  """Right blobs farthest-right first, then left blobs leftmost first."""
  rights = [i for i, o in enumerate(objs) if o[1] > 0]
  lefts = [i for i, o in enumerate(objs) if o[1] < 0]
  rights.sort(key=lambda i: (_key(objs, i), i))
  lefts.sort(key=lambda i: (_key(objs, i), i))
  return rights + lefts


def _simulate(base, objs, order):
  """Slides latent objects in order.

  Returns (grid, shifts, stacked, contact). stacked is True when some blob
  stops only because every non-background cell on its next step belongs to a
  same-colour blob that already slid a nonzero amount. That is a genuine stop
  short of the wall. contact is True when any such cell blocks a blob at all.
  """
  g = [row[:] for row in base]
  h, w = len(g), len(g[0])
  own = [[-1] * w for _ in range(h)]
  for i, (_, _, cells) in enumerate(objs):
    for y, x in cells:
      own[y][x] = i
  shifts = [0] * len(objs)
  stacked = False
  contact = False
  for i in order:
    colour, d, cells = objs[i]
    for y, x in cells:
      g[y][x] = BG
      own[y][x] = -1
    s = 0
    while all(0 <= x + (s + 1) * d < w and g[y][x + (s + 1) * d] == BG
              for y, x in cells):
      s += 1
    passable = True
    for y, x in cells:
      nx = x + (s + 1) * d
      if not 0 <= nx < w:
        passable = False
        continue
      if g[y][nx] == BG:
        continue
      j = own[y][nx]
      if j >= 0 and objs[j][0] == colour and shifts[j] > 0:
        contact = True
      else:
        passable = False
    if passable:
      stacked = True
    for y, x in cells:
      g[y][x + s * d] = colour
      own[y][x + s * d] = i
    shifts[i] = s
  return g, shifts, stacked, contact


def _slide(g, colour, d, cells):
  """Slides one unmoved blob in place on grid g and returns its shift."""
  w = len(g[0])
  for y, x in cells:
    g[y][x] = BG
  s = 0
  while all(0 <= x + (s + 1) * d < w and g[y][x + (s + 1) * d] == BG
            for y, x in cells):
    s += 1
  for y, x in cells:
    g[y][x + s * d] = colour
  return s


def _order_independent(base, objs, expected, budget=_STATE_BUDGET):
  """Checks exactly that every nearest-first order gives `expected`.

  Allowed orders process each colour by its key and permute tied keys freely.
  The two colours may interleave in any way. Two prefixes that processed the
  same set of blobs with the same shifts leave identical grids, so the search
  is memoised on (processed set, shifts).

  Returns True or False, or None if more than `budget` states are needed.
  """
  n = len(objs)
  full = (1 << n) - 1
  keys = [_key(objs, i) for i in range(n)]

  def choices(mask):
    out = []
    for d in (-1, 1):
      rem = [i for i in range(n) if objs[i][1] == d and not (mask >> i) & 1]
      if rem:
        m = min(keys[i] for i in rem)
        out.extend(i for i in rem if keys[i] == m)
    return out

  start = tuple([0] * n)
  seen = {(0, start)}
  stack = [(0, start, [row[:] for row in base])]
  while stack:
    mask, shifts, g = stack.pop()
    if mask == full:
      if g != expected:
        return False
      continue
    for i in choices(mask):
      colour, d, cells = objs[i]
      g2 = [row[:] for row in g]
      s = _slide(g2, colour, d, cells)
      ns = shifts[:i] + (s,) + shifts[i + 1:]
      state = (mask | (1 << i), ns)
      if state in seen:
        continue
      seen.add(state)
      if len(seen) > budget:
        return None
      stack.append((state[0], ns, g2))
  return True


def _normalize(cells):
  my = min(y for y, _ in cells)
  mx = min(x for _, x in cells)
  return sorted((y - my, x - mx) for y, x in cells)


def _make_shape(allow_diag=True, max_cells=7, elongated=True):
  """A random connected shape with at most `max_cells` cells.

  Usually the shape fits a box of at most 3x3. If `elongated`, it is
  sometimes a straight 4- or 5-cell spine of thickness up to 2. If
  allow_diag is False, only orthogonal growth steps are used, so the shape is
  4-connected.
  """
  if elongated and random.random() < 0.3:
    span = random.randint(4, 5)
    thick = random.randint(1, 2)
    lane = random.randrange(thick)
    if random.random() < 0.5:
      bh, bw = span, thick
      cells = {(y, lane) for y in range(span)}
    else:
      bh, bw = thick, span
      cells = {(lane, x) for x in range(span)}
    size = random.randint(span, min(max_cells, bh * bw))
  else:
    bh = random.randint(1, 3)
    bw = random.randint(1, 3)
    size = random.randint(1, min(max_cells, bh * bw))
    cells = {(random.randrange(bh), random.randrange(bw))}
  for _ in range(80):
    if len(cells) >= size:
      break
    y, x = random.choice(sorted(cells))
    if allow_diag and random.random() < 0.3:
      dy, dx = random.choice(_DIAG)
    else:
      dy, dx = random.choice(_ORTH)
    ny, nx = y + dy, x + dx
    if 0 <= ny < bh and 0 <= nx < bw:
      cells.add((ny, nx))
  return _normalize(cells)


def _make_diag_shape():
  """A 4-connected base shape plus one cell linked to it only diagonally."""
  for _ in range(30):
    base = _make_shape(False, 6, elongated=False)
    bset = set(base)
    cands = []
    for y, x in base:
      for dy, dx in _DIAG:
        ny, nx = y + dy, x + dx
        if (ny, nx) in bset:
          continue
        if any((ny + a, nx + b) in bset for a, b in _ORTH):
          continue
        cells = base + [(ny, nx)]
        ys = [p for p, _ in cells]
        xs = [q for _, q in cells]
        if max(ys) - min(ys) <= 2 and max(xs) - min(xs) <= 2:
          cands.append(cells)
    if cands:
      return _normalize(random.choice(cands))
  return random.choice([[(0, 0), (1, 1)], [(0, 1), (1, 0)]])


def _bg_dominant(g):
  counts = {}
  for row in g:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  b = counts.get(BG, 0)
  return all(c < b for v, c in counts.items() if v != BG)


def _count_cap(w, h):
  """Upper bound on mutually non-touching same-colour blobs."""
  return ((h + 1) // 2) * ((w - 1) // 2)


def _cells_ok(w, h, total):
  """Whether `total` blob cells, split as evenly as possible, keep 7 dominant."""
  return (w - 2) * h - total > h + (total + 1) // 2


def _k_max(w, h, extra):
  """Largest object count 2..10 that fits, or 0 if none does."""
  best = 0
  cap = _count_cap(w, h)
  for k in range(2, 11):
    if k <= cap and _cells_ok(w, h, k + extra):
      best = k
  return best


def _size_ok(w, h, k, want_stack, want_diag):
  extra = 1 if want_diag is True else 0
  km = _k_max(w, h, extra)
  if km < 2:
    return False
  if k is not None and k > km:
    return False
  if want_stack is True:
    # A same-row stack needs a moved blocker and a stacked blob two columns
    # further out, which needs at least four interior columns.
    if w < 6:
      return False
    if (k if k is not None else km) < 3:
      return False
  return True


def _feasible_sizes(hs, ws, k, want_stack, want_diag):
  return [(h, w) for h in hs for w in ws
          if _size_ok(w, h, k, want_stack, want_diag)]


def _try_place(g, colour, lc, kind, ref=None):
  """Places one shape; own-colour cells never touch or hug their wall.

  If `ref` (cells of a same-colour blob) is given, the new shape must have a
  cell in one of ref's rows. It must also lie entirely farther from its own
  wall than ref, so it is a stacking candidate behind ref.
  """
  h, w = len(g), len(g[0])
  for _ in range(60):
    if kind == "diag":
      shape = _make_diag_shape()
    else:
      shape = _make_shape(kind != "orth")
    bh = max(y for y, _ in shape) + 1
    bw = max(x for _, x in shape) + 1
    if bh > h:
      continue
    if colour == lc:
      lo, hi = 2, w - 1 - bw
    else:
      lo, hi = 1, w - 2 - bw
    row_hint = None
    if ref is not None:
      row_hint = random.choice(ref)[0]
      if colour == lc:
        lo = max(lo, max(x for _, x in ref) + 2)
      else:
        hi = min(hi, min(x for _, x in ref) - 1 - bw)
    if lo > hi:
      continue
    if row_hint is None:
      rlo, rhi = 0, h - bh
    else:
      rlo, rhi = max(0, row_hint - bh + 1), min(h - bh, row_hint)
    if rlo > rhi:
      continue
    r0 = random.randint(rlo, rhi)
    c0 = random.randint(lo, hi)
    cells = [(r0 + y, c0 + x) for y, x in shape]
    if row_hint is not None and not any(y == row_hint for y, _ in cells):
      continue
    ok = True
    for y, x in cells:
      if g[y][x] != BG:
        ok = False
        break
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          ny, nx = y + dy, x + dx
          if 0 <= ny < h and 1 <= nx < w - 1 and g[ny][nx] == colour:
            ok = False
      if not ok:
        break
    if ok:
      return cells
  return None


def _components(g, lc, rc, diagonal=True):
  """Same-colour interior components (8- or 4-connected), left colour first."""
  h, w = len(g), len(g[0])
  steps = _ORTH + _DIAG if diagonal else _ORTH
  objs = []
  for colour, d in ((lc, -1), (rc, 1)):
    seen = set()
    for r in range(h):
      for c in range(1, w - 1):
        if g[r][c] != colour or (r, c) in seen:
          continue
        stack = [(r, c)]
        seen.add((r, c))
        cells = []
        while stack:
          y, x = stack.pop()
          cells.append((y, x))
          for dy, dx in steps:
            ny, nx = y + dy, x + dx
            if (0 <= ny < h and 1 <= nx < w - 1 and (ny, nx) not in seen
                and g[ny][nx] == colour):
              seen.add((ny, nx))
              stack.append((ny, nx))
        objs.append((colour, d, sorted(cells)))
  return objs


def _four_conn_output(g, lc, rc):
  """Foil answer obtained by grouping blobs with 4-connectivity."""
  objs4 = _components(g, lc, rc, diagonal=False)
  return _simulate(g, objs4, _ref_order(objs4))[0]


def _random_scene(width, height, left, right, num_objects, stacking,
                  diagonal):
  want_stack = stacking
  if stacking is None and num_objects != 2 and random.random() < 0.75:
    want_stack = True
  want_diag = diagonal
  if diagonal is None and random.random() < 0.4:
    want_diag = True
  hs = [height] if height is not None else list(range(6, 17))
  ws = [width] if width is not None else list(range(7, 17))
  pairs = _feasible_sizes(hs, ws, num_objects, want_stack, want_diag)
  # Soft (randomly drawn) demands are dropped if the grid cannot host them.
  if not pairs and stacking is None and want_stack is True:
    want_stack = None
    pairs = _feasible_sizes(hs, ws, num_objects, want_stack, want_diag)
  if not pairs and diagonal is None and want_diag is True:
    want_diag = None
    pairs = _feasible_sizes(hs, ws, num_objects, want_stack, want_diag)
  if not pairs and (height is None or width is None):
    hs = [height] if height is not None else list(range(3, 31))
    ws = [width] if width is not None else list(range(5, 31))
    pairs = _feasible_sizes(hs, ws, num_objects, want_stack, want_diag)
  if not pairs:
    raise ValueError("the requested size, num_objects, stacking and diagonal "
                     "cannot be satisfied with 7 as the dominant colour")
  for it in range(_TRIES):
    if it == _TRIES // 2:
      # Soft demands must never make a call fail: relax them halfway.
      if stacking is None:
        want_stack = None
      if diagonal is None:
        want_diag = None
    h, w = random.choice(pairs)
    extra = 1 if want_diag is True else 0
    km = _k_max(w, h, extra)
    if num_objects is not None:
      k = num_objects
    else:
      lo = 3 if want_stack is True else min(3, km)
      hi = max(lo, min(km, 2 + h * (w - 2) // 10))
      k = random.randint(lo, hi)
    lc, rc = _pick_colours(left, right)
    g = _walls(w, h, lc, rc)
    colours = [lc, rc]
    random.shuffle(colours)
    colours += [random.choice((lc, rc)) for _ in range(k - 2)]
    if want_diag is True:
      n_diag = random.randint(1, 2) if _cells_ok(w, h, k + 2) else 1
    else:
      n_diag = 0
    objs = []
    for i, colour in enumerate(colours):
      if i < n_diag:
        kind = "diag"
      elif want_diag is False:
        kind = "orth"
      else:
        kind = "free"
      cells = None
      if want_stack is True and i >= 2 and (i == 2 or random.random() < 0.4):
        same = [o for o in objs if o[0] == colour]
        if same:
          cells = _try_place(g, colour, lc, kind, random.choice(same)[2])
      if cells is None:
        cells = _try_place(g, colour, lc, kind)
      if cells is None:
        continue
      for y, x in cells:
        g[y][x] = colour
      objs.append((colour, -1 if colour == lc else 1, cells))
    if len(objs) < 2:
      continue
    if num_objects is not None and len(objs) != num_objects:
      continue
    if not any(o[1] < 0 for o in objs) or not any(o[1] > 0 for o in objs):
      continue
    if len(_components(g, lc, rc)) != len(objs):
      continue
    if not _bg_dominant(g):
      continue
    out, shifts, stacked, contact = _simulate(g, objs, _ref_order(objs))
    if out == g:
      continue
    if not any(shifts[i] > 0 for i, o in enumerate(objs) if o[1] < 0):
      continue
    if not any(shifts[i] > 0 for i, o in enumerate(objs) if o[1] > 0):
      continue
    if want_stack is True and not stacked:
      continue
    if want_stack is False and contact:
      continue
    if want_diag is True and _four_conn_output(g, lc, rc) == out:
      continue
    if _order_independent(g, objs, out) is not True:
      continue
    return g, out
  raise RuntimeError("could not build a valid scene for the requested "
                     "parameters within the bounded search")


def generate(width=None, height=None, left=None, right=None,
             num_objects=None, stacking=None, diagonal=None, layout=None,
             strict=True):
  """Generates one input/output pair.

  Args:
    width: grid width including both walls, 5..30. If None, a random width
      in 7..16 is used. The full 5..30 range is used only if needed to
      satisfy explicit requests.
    height: grid height, 3..30. If None, a random height in 6..16 is used,
      widened to 3..30 only when needed.
    left: colour of the left wall (column 0), not 7. Random if None.
    right: colour of the right wall (last column), not 7 and not left.
      Random if None.
    num_objects: exact number of blobs, 2..10. If None, a random target is
      drawn, usually 3..10, limited by grid area and background dominance.
      Very small grids may give 2. Infeasible sizes raise ValueError.
    stacking: True requires at least one genuine stacking event, where a blob
      stops short of its wall against an already-slid blob of its colour.
      False forbids any blob from being blocked by an already-slid blob of
      its colour. If None, stacking is required with probability 0.75 when
      the grid can host it; the demand is relaxed if the search struggles.
      True needs num_objects >= 3 and width >= 6.
    diagonal: True requires a blob with a diagonal-only link whose 4-connected
      grouping would change the answer. False uses only 4-connected shapes.
      If None, it is required with probability 0.4 when the grid can host it,
      and relaxed if the search struggles.
    layout: optional list of equal-length strings, one per row, describing
      interior columns 1..width-2. '.' is background 7, 'L' is a left-colour
      cell and 'R' is a right-colour cell. Used for fixture replay. It cannot
      be combined with num_objects, stacking or diagonal. If width or height is
      also given, it must match the layout.
    strict: bool, used only with a layout. When True, raise ValueError if 7 is
      not the dominant colour, if the output equals the input, or if the answer
      depends on the processing order or cannot be verified. Random
      generation always enforces these checks.
  """
  if width is not None and (not _is_int(width) or not 5 <= width <= 30):
    raise ValueError("width must be an int in 5..30")
  if height is not None and (not _is_int(height) or not 3 <= height <= 30):
    raise ValueError("height must be an int in 3..30")
  if num_objects is not None and (not _is_int(num_objects) or
                                  not 2 <= num_objects <= 10):
    raise ValueError("num_objects must be an int in 2..10")
  for name, flag in (("stacking", stacking), ("diagonal", diagonal)):
    if flag is not None and not isinstance(flag, bool):
      raise ValueError("%s must be None, True or False" % name)
  if not isinstance(strict, bool):
    raise ValueError("strict must be True or False")
  if stacking is True and num_objects == 2:
    raise ValueError("stacking=True needs at least 3 objects")
  if stacking is True and width == 5:
    raise ValueError("stacking=True needs width >= 6")
  if (num_objects is not None and width is not None and height is not None
      and num_objects > _count_cap(width, height)):
    raise ValueError("num_objects does not fit in the requested grid")
  if layout is not None:
    if num_objects is not None or stacking is not None or diagonal is not None:
      raise ValueError("num_objects, stacking and diagonal cannot be combined "
                       "with layout")
    if not isinstance(layout, (list, tuple)) or not 3 <= len(layout) <= 30:
      raise ValueError("layout must have 3..30 rows")
    if any(not isinstance(row, str) for row in layout):
      raise ValueError("layout rows must be strings")
    h = len(layout)
    iw = len(layout[0])
    if not 3 <= iw <= 28 or any(len(row) != iw for row in layout):
      raise ValueError("layout rows must share one length in 3..28")
    if any(ch not in ".LR" for row in layout for ch in row):
      raise ValueError("layout may only contain '.', 'L' and 'R'")
    w = iw + 2
    if (width is not None and width != w) or (height is not None and
                                              height != h):
      raise ValueError("width/height disagree with layout")
    lc, rc = _pick_colours(left, right)
    g = _walls(w, h, lc, rc)
    for r in range(h):
      for c, ch in enumerate(layout[r]):
        if ch == "L":
          g[r][c + 1] = lc
        elif ch == "R":
          g[r][c + 1] = rc
    objs = _components(g, lc, rc)
    out = _simulate(g, objs, _ref_order(objs))[0]
    if strict:
      if not _bg_dominant(g):
        raise ValueError("layout: background 7 must be the dominant colour")
      if out == g:
        raise ValueError("layout: output equals input")
      res = _order_independent(g, objs, out)
      if res is None:
        raise ValueError("layout: too many processing states to verify order "
                         "independence (use strict=False to skip)")
      if res is False:
        raise ValueError("layout: answer depends on the processing order")
    return {"input": g, "output": out}
  g, out = _random_scene(width, height, left, right, num_objects, stacking,
                         diagonal)
  return {"input": g, "output": out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent layouts."""
  train = [
      generate(left=4, right=6, layout=[
          "...L....",
          "..LLL...",
          "........",
          "....R...",
          "...LRRR.",
          "...L....",
          "..RR....",
          ".LR...R.",
          ".LL..RR.",
          ".LLL....",
      ]),
      generate(left=9, right=8, layout=[
          "....RR.",
          ".LL..R.",
          ".L.L...",
          ".....LL",
          ".....L.",
          "....R..",
          "...RRR.",
          ".R..R..",
          ".......",
      ]),
  ]
  test = [
      generate(left=8, right=1, layout=[
          ".......",
          ".RR....",
          ".R.....",
          "....RR.",
          ".L.RRR.",
          ".LL...L",
          ".LL.RR.",
          ".L.RRR.",
          ".L..RR.",
      ]),
  ]
  return {"train": train, "test": test}
