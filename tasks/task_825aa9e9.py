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

"""ARC-GEN style generator for task 825aa9e9: loose objects fall onto ground.

Rule:
  The air colour is 7. Solid ground is a skyline of cells filled up from the
  bottom edge, so every ground cell belongs to a column that touches the
  bottom row. Each column has a height of 0 or more, which gives full-height
  pillars, stubs, pockets and open gaps. Every other object is a
  single-colour, 4-connected shape. Objects fall straight down as rigid
  bodies, lowest object first (largest bottom row first). A falling cell may
  not enter the bottom row, because the grid edge acts as a virtual floor.
  It may not overlap the ground or an object that has already fallen. It may
  not come to rest directly above a ground cell, so one empty row always
  separates a fallen object from the ground. An object may land directly on
  top of an object that has already fallen, with no gap.

Scope:
  Random widths are 5..30. Random heights are mostly 4..16, with occasional
  synthetic extensions up to 30. Explicit sizes 3..30 are accepted. Sizes
  outside the fixture range (7..20 wide, 4..10 tall) are synthetic
  extensions; the rule does not depend on size. Ground styles are flat floors
  (sometimes with a hole), random skylines, pillar frames, alternating stubs
  and pockets. Ground normally uses one colour. About 20% of eligible
  sampled scenes use a two-colour ground, coloured per column (a synthetic
  extension). Default scenes have 1-5 falling objects; num_objects allows
  1..8. Objects are random dense or sparse polyominoes, bars, hollow rings,
  combs, lattices, and composites of two sub-shapes joined by a bridge. Shape
  caps grow from about 6 cells to about 10 cells across on large grids.
  About 40% of default multi-object scenes must contain an object that comes
  to rest directly on another fallen object, which teaches the no-gap
  stacking case. At least one object always moves. Input objects are always
  8-separated from each other and from the ground. Objects that share a
  column have disjoint row ranges, so the drop order is never ambiguous.
  Mover colours differ from every visible ground colour.
  At least one ground cell is required, including for explicit controls.
  Clearance is vertical: fallen objects may touch a pillar laterally.
  That contact is a labelled synthetic extension consistent with the saved
  transform, but not uniquely determined by the canonical pairs.
"""

import random

import common

AIR = 7
MAX_SIDE = 30
MAX_OBJECTS = 8
PALETTE = tuple(c for c in range(10) if c != AIR)
_DIRS = ((0, 1), (0, -1), (1, 0), (-1, 0))


def _is_int(value):
  """True for genuine ints; bools are rejected."""
  return isinstance(value, int) and not isinstance(value, bool)


def _check_size(name, value):
  """Raises unless value is None or an int side length in 3..30."""
  if value is not None and (not _is_int(value) or
                            not 3 <= value <= MAX_SIDE):
    raise ValueError(name + " must be an int in 3..30")


def _check_color(name, value):
  """Raises unless value is an int colour in 0..9 other than air."""
  if not _is_int(value) or not 0 <= value <= 9 or value == AIR:
    raise ValueError(name + " must be an int colour in 0..9 other than 7")


def _norm_colors(width, ground_colors):
  """Returns a per-column ground colour list, validating the palette."""
  if _is_int(ground_colors):
    cols = [ground_colors] * width
  elif isinstance(ground_colors, (list, tuple)):
    cols = list(ground_colors)
  else:
    raise ValueError("ground_colors must be an int or a list of ints")
  if len(cols) != width:
    raise ValueError("ground_colors must be an int or one colour per column")
  for c in cols:
    _check_color("ground colour", c)
  return cols


def _check_heights(width, height, heights):
  """Validates a skyline: one int height in 0..height per column."""
  if len(heights) != width:
    raise ValueError("heights must have one entry per column")
  for v in heights:
    if not _is_int(v) or not 0 <= v <= height:
      raise ValueError("each column height must be an int in 0..height")


def _column_can_fall(heights, height, c):
  """True if some separated cell started in column c could fall a row."""
  if heights[c] > height - 3:
    return False
  for n in (c - 1, c + 1):
    if 0 <= n < len(heights) and heights[n] > height - 2:
      return False
  return True


def _can_fall_somewhere(heights, height):
  """Necessary condition for any separated object to be able to fall."""
  return any(_column_can_fall(heights, height, c)
             for c in range(len(heights)))


def _capacity(width, height):
  """Upper bound on 8-separated objects inside rows 0..height-2."""
  return ((width + 1) // 2) * (height // 2)


def _ground(width, height, heights, colors):
  """Returns dict (r, c) -> colour of the static ground skyline."""
  static = {}
  for c in range(width):
    for r in range(height - heights[c], height):
      static[(r, c)] = colors[c]
  return static


def _render_input(width, height, static, movers):
  """Paints ground and the loose objects at their input positions."""
  grid = common.grid(width, height, AIR)
  for (r, c), col in static.items():
    grid[r][c] = col
  for col, cells in movers:
    for r, c in cells:
      grid[r][c] = col
  return grid


def _drop(width, height, static, movers):
  """Drops the latent movers (lowest first) and returns (output, shifts)."""
  out = common.grid(width, height, AIR)
  for (r, c), col in static.items():
    out[r][c] = col
  occupied = set(static)
  order = sorted(range(len(movers)),
                 key=lambda i: -max(r for r, _ in movers[i][1]))
  shifts = [0] * len(movers)
  for i in order:
    col, cells = movers[i]
    d = 0
    while d < height:
      ok = True
      for r, c in cells:
        nr = r + d + 1
        if nr > height - 2 or (nr, c) in occupied or (nr + 1, c) in static:
          ok = False
          break
      if not ok:
        break
      d += 1
    for r, c in cells:
      out[r + d][c] = col
      occupied.add((r + d, c))
    shifts[i] = d
  return out, shifts


def _has_contact(movers, shifts):
  """True if some fallen object rests directly on another fallen object."""
  owner = {}
  for i, (_, cells) in enumerate(movers):
    for r, c in cells:
      owner[(r + shifts[i], c)] = i
  for (r, c), i in owner.items():
    j = owner.get((r + 1, c))
    if j is not None and j != i:
      return True
  return False


def _connected(cells):
  """True if the cell set is 4-connected."""
  cells = set(cells)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in _DIRS:
      n = (r + dr, c + dc)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _normalise(cells):
  """Shifts a cell set so its bounding box starts at (0, 0)."""
  mr = min(r for r, _ in cells)
  mc = min(c for _, c in cells)
  return sorted({(r - mr, c - mc) for r, c in cells})


def _blob(bw, bh, sparse):
  """Grows a random 4-connected polyomino inside a bw x bh box."""
  total = bw * bh
  if sparse:
    lo = min(total, bw + bh - 1)
    hi = max(lo, total // 2 + 1)
  else:
    lo = max(1, total // 2)
    hi = total
  n = random.randint(lo, min(hi, total))
  cells = {(random.randint(0, bh - 1), random.randint(0, bw - 1))}
  for _ in range(600):
    if len(cells) >= n:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice(_DIRS)
    if 0 <= r + dr < bh and 0 <= c + dc < bw:
      cells.add((r + dr, c + dc))
  return _normalise(cells)


def _simple_shape(maxw, maxh, big):
  """Returns one normalised 4-connected shape no larger than the caps."""
  roll = random.random()
  if roll < 0.14 and maxw >= 3 and maxh >= 3:
    bw = random.randint(3, min(big - 1, maxw))
    bh = random.randint(3, min(big - 2, maxh))
    return [(r, c) for r in range(bh) for c in range(bw)
            if r in (0, bh - 1) or c in (0, bw - 1)]
  if roll < 0.24:
    ws = [v for v in (3, 5, 7, 9) if v <= min(maxw, big + 1)]
    hs = [v for v in (3, 5, 7) if v <= min(maxh, big - 1)]
    if ws and hs:
      bw, bh = random.choice(ws), random.choice(hs)
      return [(r, c) for r in range(bh) for c in range(bw)
              if r % 2 == 0 or c % 2 == 0]
  if roll < 0.36 and maxw >= 3:
    bw = random.randint(3, min(big - 1, maxw))
    cells = [(0, c) for c in range(bw)]
    stems = [c for c in range(bw) if random.random() < 0.6] or [0]
    for c in stems:
      for r in range(1, min(random.randint(2, big - 2), maxh)):
        cells.append((r, c))
    return sorted(set(cells))
  if roll < 0.54:
    if random.random() < 0.5:
      return [(r, 0) for r in range(random.randint(1, min(big + 1, maxh)))]
    return [(0, c) for c in range(random.randint(1, min(big + 1, maxw)))]
  bw = random.randint(1, min(big, maxw))
  bh = random.randint(1, min(big, maxh))
  return _blob(bw, bh, random.random() < 0.35)


def _random_shape(maxw, maxh, big):
  """Returns a shape; sometimes two sub-shapes joined by an L bridge."""
  if random.random() < 0.15 and maxw >= 5:
    a = _simple_shape(max(1, maxw // 2), maxh, big)
    b = _simple_shape(max(1, maxw // 2), maxh, big)
    dc = max(c for _, c in a) + 1 + random.randint(1, 2)
    dr = random.randint(0, 2)
    b = [(r + dr, c + dc) for r, c in b]
    pa, pb = random.choice(a), random.choice(b)
    cells = set(a) | set(b)
    r, c = pa
    while c != pb[1]:
      c += 1 if pb[1] > c else -1
      cells.add((r, c))
    while r != pb[0]:
      r += 1 if pb[0] > r else -1
      cells.add((r, c))
    return _normalise(cells)
  return _simple_shape(maxw, maxh, big)


def _can_place(cells, width, height, static, movers):
  """Checks bounds, 8-separation and row separation of shared columns."""
  blocked = set(static)
  for _, pcells in movers:
    blocked.update(pcells)
  for r, c in cells:
    if not (0 <= r <= height - 2 and 0 <= c < width):
      return False
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if (r + dr, c + dc) in blocked:
          return False
  cols = {c for _, c in cells}
  top, bot = min(r for r, _ in cells), max(r for r, _ in cells)
  for _, pcells in movers:
    if cols & {c for _, c in pcells}:
      ptop, pbot = min(r for r, _ in pcells), max(r for r, _ in pcells)
      if not (bot < ptop or pbot < top):
        return False
  return True


def _parse_mover(entry):
  """Validates one explicit (colour, cells) entry; returns (col, cells)."""
  if not isinstance(entry, (list, tuple)) or len(entry) != 2:
    raise ValueError("each mover must be a (colour, cells) pair")
  col, raw = entry
  _check_color("mover colour", col)
  if not isinstance(raw, (list, tuple)) or not raw:
    raise ValueError("mover cells must be a non-empty list of (r, c)")
  cells = []
  for p in raw:
    if (not isinstance(p, (list, tuple)) or len(p) != 2 or
        not _is_int(p[0]) or not _is_int(p[1])):
      raise ValueError("mover cells must be pairs of ints")
    cells.append((p[0], p[1]))
  if len(set(cells)) != len(cells) or not _connected(cells):
    raise ValueError("each mover must be a 4-connected set of distinct cells")
  return col, cells


def _random_heights(width, height):
  """Samples a ground skyline (list of column heights)."""
  cap = max(1, height - 4)
  style = random.choice(["flat", "skyline", "pillars", "stubs", "pocket"])
  if style == "flat":
    level = random.randint(1, min(2, cap))
    heights = [level] * width
    if random.random() < 0.3:
      heights[random.randint(0, width - 1)] = 0
  elif style == "skyline":
    level = random.randint(0, cap)
    heights = []
    for _ in range(width):
      heights.append(level)
      level = min(cap, max(0, level + random.choice([-1, 0, 0, 1])))
  elif style == "pillars":
    period = random.randint(4, 6)
    off = random.randint(0, period - 1)
    base = random.choice([0, 1, 1])
    heights = [height if (c - off) % period == 0 else base
               for c in range(width)]
  elif style == "stubs":
    lo = 0 if cap <= 1 else random.choice([0, 1])
    hi = min(cap, lo + random.randint(1, 2))
    phase = random.randint(0, 1)
    heights = [hi if (c + phase) % 2 == 0 else lo for c in range(width)]
    if random.random() < 0.5:
      a = random.randint(0, width - 1)
      for c in range(a, width):
        heights[c] = lo
  else:
    wall = random.randint(1, max(1, height - 2))
    floor = random.randint(0, min(wall - 1, cap))
    a = random.randint(0, max(0, width - 3))
    b = random.randint(a + 1, width - 1)
    heights = [floor if a <= c <= b else wall for c in range(width)]
  return heights


def _random_ground_colors(heights):
  """Usually one ground colour; sometimes tallest columns get a second."""
  a = random.choice(PALETTE)
  top = max(heights)
  if random.random() < 0.2 and any(0 < v < top for v in heights):
    b = random.choice([c for c in PALETTE if c != a])
    return [a if v == top else b for v in heights]
  return [a] * len(heights)


def _place_objects(w, h, static, target, others, shared, stack_prob, big):
  """Places up to `target` separated movers; some stacked above others."""
  placed = []
  for _ in range(target):
    for _ in range(40):
      shape = _random_shape(w, h - 2, big)
      bh = max(r for r, _ in shape) + 1
      bw = max(c for _, c in shape) + 1
      if bh > h - 2 or bw > w:
        continue
      if placed and random.random() < stack_prob:
        _, mcells = random.choice(placed)
        mtop = min(r for r, _ in mcells)
        mcols = [c for _, c in mcells]
        clo = max(0, min(mcols) - bw + 1)
        chi = min(w - bw, max(mcols))
        rmax = mtop - 1 - bh
        if chi < clo or rmax < 0:
          continue
        r0, c0 = random.randint(0, rmax), random.randint(clo, chi)
      else:
        rmax = h - 1 - bh
        if rmax < 0:
          continue
        r0 = random.randint(0, random.randint(0, rmax))
        c0 = random.randint(0, w - bw)
      cells = [(r + r0, c + c0) for r, c in shape]
      if _can_place(cells, w, h, static, placed):
        col = shared if shared is not None else random.choice(others)
        placed.append((col, cells))
        break
  return placed


def _fallback(width, height, heights, ground_colors, num_objects):
  """Last-resort constructive scene of separated single falling cells.

  It is reached only when the randomized search fails, which happens for
  tight explicit controls. It honours every supplied control, retries with
  fresh samples, guarantees a fall-able column when it samples the ground,
  allows cells in several rows (so narrow tall grids can hold many objects)
  and raises ValueError if no valid scene is found.
  """
  for _ in range(60):
    if width is not None:
      w = width
    elif heights is not None:
      w = len(heights)
    else:
      w = random.randint(5, 12)
    h = height if height is not None else random.randint(6, 12)
    if heights is not None:
      hts = list(heights)
    else:
      hts = [random.choice([0, 1, 1]) for _ in range(w)]
      z = random.randrange(w)
      hts[z] = 0
      if sum(hts) == 0:
        hts[(z + 1) % w] = 1
    _check_heights(w, h, hts)
    if ground_colors is not None:
      gcols = _norm_colors(w, ground_colors)
    else:
      gcols = [random.choice(PALETTE)] * w
    static = _ground(w, h, hts, gcols)
    visible = set(static.values())
    others = [c for c in PALETTE if c not in visible]
    if not others:
      continue
    target = num_objects if num_objects is not None else random.randint(1, 2)
    if target > _capacity(w, h):
      continue
    fallable = {c for c in range(w) if _column_can_fall(hts, h, c)}
    cands = [(r, c) for r in range(h - 1) for c in range(w)]
    keys = {p: random.random() for p in cands}
    cands.sort(key=lambda p: (p[0], 0 if p[1] in fallable else 1, keys[p]))
    placed = []
    for r, c in cands:
      if len(placed) == target:
        break
      if _can_place([(r, c)], w, h, static, placed):
        placed.append((random.choice(others), [(r, c)]))
    if len(placed) < target:
      continue
    out, shifts = _drop(w, h, static, placed)
    if not any(shifts):
      continue
    return {"input": _render_input(w, h, static, placed), "output": out}
  raise ValueError("requested controls leave no room for a valid scene")


def generate(width=None, height=None, heights=None, ground_colors=None,
             movers=None, num_objects=None):
  """Generates one input/output pair.

  Args:
    width: grid width (columns), 3..30. If None, it is inferred from heights
      or from a per-column ground_colors list; otherwise it is sampled 5..30.
    height: grid height (rows), 3..30. If None and heights is given, it
      defaults to max(4, max(heights)); only columns whose height equals the
      grid height become full pillars. Otherwise it is sampled (mostly 4..16,
      sometimes up to 30).
    heights: list of per-column ground heights (ints, measured from the
      bottom edge, 0..height). A height equal to the grid height is a full
      pillar. At least one ground cell must be visible. Sampled if None.
      In random mode the skyline must leave some
      column where a separated object can fall, else ValueError is raised.
    ground_colors: one colour for all ground, or one colour per column; never
      7. Sampled if None. A declared palette naming all nine non-air colours
      is rejected. Colours of zero-height columns are invisible and do not
      restrict mover colours.
    movers: list of (colour, [(r, c), ...]) loose single-colour objects in
      absolute input coordinates, for explicit scene reconstruction. It needs
      heights and ground_colors. The objects are validated: non-empty list,
      int coordinates, 4-connected, colours distinct from air and from the
      visible ground colours, off the bottom row, 8-separated from ground and
      from each other, disjoint row ranges where they share columns, and at
      least one object must fall. Explicit scenes contain at most eight
      movers, like random scenes. Ground clearance is vertical in each
      mover cell's own column; lateral ground contact after falling is a
      labelled synthetic extension, not established uniquely by the fixtures.
    num_objects: exact number of falling objects (1..8). Sampled if None.
      Counts above the 8-separation capacity of the grid are rejected.
  """
  _check_size("width", width)
  _check_size("height", height)
  if ground_colors is not None:
    if isinstance(ground_colors, (list, tuple)):
      ground_colors = list(ground_colors)
      if width is None:
        width = len(ground_colors)
        _check_size("width", width)
      elif len(ground_colors) != width:
        raise ValueError("ground_colors list must have one colour per column")
      declared = ground_colors
    elif _is_int(ground_colors):
      declared = [ground_colors]
    else:
      raise ValueError("ground_colors must be an int or a list of ints")
    for c in declared:
      _check_color("ground colour", c)
    if not [c for c in PALETTE if c not in declared]:
      raise ValueError("ground colours leave no colour for falling objects")
  if heights is not None:
    if not isinstance(heights, (list, tuple)) or not heights:
      raise ValueError("heights must be a non-empty list of ints")
    heights = list(heights)
    for v in heights:
      if not _is_int(v) or v < 0:
        raise ValueError("column heights must be non-negative ints")
    if width is None:
      width = len(heights)
      _check_size("width", width)
    elif len(heights) != width:
      raise ValueError("heights must have one entry per column")
    if height is None:
      height = max(4, max(heights))
      _check_size("height", height)
    _check_heights(width, height, heights)
    if not any(heights):
      raise ValueError("at least one visible ground cell is required")
  if num_objects is not None and (not _is_int(num_objects) or
                                  not 1 <= num_objects <= MAX_OBJECTS):
    raise ValueError("num_objects must be an int in 1..8")

  if movers is not None:
    if heights is None or ground_colors is None:
      raise ValueError("explicit movers need heights and ground_colors")
    if not isinstance(movers, (list, tuple)) or not movers:
      raise ValueError("explicit movers must contain at least one object")
    if len(movers) > MAX_OBJECTS:
      raise ValueError("explicit scenes support at most eight movers")
    if num_objects is not None and num_objects != len(movers):
      raise ValueError("num_objects disagrees with the number of movers")
    gcols = _norm_colors(width, ground_colors)
    static = _ground(width, height, heights, gcols)
    visible = set(static.values())
    placed = []
    for entry in movers:
      col, cells = _parse_mover(entry)
      if col in visible:
        raise ValueError("mover colours must differ from ground colours")
      if not _can_place(cells, width, height, static, placed):
        raise ValueError("mover overlaps, touches or is out of bounds")
      placed.append((col, cells))
    out, shifts = _drop(width, height, static, placed)
    if not any(shifts):
      raise ValueError("no explicit mover can fall; the pair would be identity")
    return {"input": _render_input(width, height, static, placed),
            "output": out}

  if heights is not None and not _can_fall_somewhere(heights, height):
    raise ValueError("requested ground leaves no column where objects fall")
  if num_objects is not None:
    cw = width if width is not None else MAX_SIDE
    ch = height if height is not None else MAX_SIDE
    if num_objects > _capacity(cw, ch):
      raise ValueError("num_objects exceeds what the grid can hold")

  want_stack = ((num_objects is None or num_objects >= 2) and
                random.random() < 0.4)
  for attempt in range(400):
    need_stack = want_stack and attempt < 250
    w = width if width is not None else random.randint(5, MAX_SIDE)
    if height is not None:
      h = height
    elif random.random() < 0.85:
      h = random.randint(4, 16)
    else:
      h = random.randint(4, MAX_SIDE)
    if num_objects is not None and num_objects > _capacity(w, h):
      continue
    if heights is not None:
      hts = list(heights)
    else:
      hts = _random_heights(w, h)
      if sum(hts) == 0 or not _can_fall_somewhere(hts, h):
        continue
    if ground_colors is not None:
      gcols = _norm_colors(w, ground_colors)
    else:
      gcols = _random_ground_colors(hts)
    static = _ground(w, h, hts, gcols)
    visible = set(static.values())
    others = [c for c in PALETTE if c not in visible]
    if not others:
      continue
    if num_objects is not None:
      target = num_objects
    else:
      cap = min(5, max(2, (w * h) // 20))
      target = random.randint(2 if need_stack else 1, cap)
    big = 6 if min(w, h) < 14 else random.randint(6, 10)
    shared = random.choice(others) if random.random() < 0.6 else None
    placed = _place_objects(w, h, static, target, others, shared,
                            0.6 if need_stack else 0.3, big)
    if len(placed) != target:
      continue
    out, shifts = _drop(w, h, static, placed)
    if not any(shifts):
      continue
    if need_stack and not _has_contact(placed, shifts):
      continue
    return {"input": _render_input(w, h, static, placed), "output": out}
  return _fallback(width, height, heights, ground_colors, num_objects)


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  ring = [(r, c) for r in range(3) for c in range(1, 4) if (r, c) != (1, 2)]
  tee = [(1, 5), (1, 6), (1, 7), (2, 5), (2, 6), (2, 7), (3, 6), (4, 6)]
  left9 = [(1, 2), (1, 3), (1, 4), (2, 2), (2, 4), (3, 2), (3, 4), (4, 2),
           (4, 4), (5, 2), (6, 2), (1, 6), (1, 7), (1, 8), (2, 6), (2, 8),
           (3, 6), (3, 8), (4, 5), (4, 6), (4, 8)]
  left9 = sorted(set(left9))
  right9 = [(r, c) for r in range(5) for c in range(11, 16)
            if r % 2 == 0 or c % 2 == 1]
  train = [
      generate(10, 6, [6, 1, 1, 1, 6, 1, 1, 1, 6, 1], 8,
               [(2, [(0, 2), (1, 2), (2, 2)]), (2, [(0, 6)]),
                (2, [(2, 6)])]),
      generate(9, 4, [1, 0, 0, 0, 1, 0, 0, 0, 1], 2,
               [(6, [(0, 1), (0, 2), (1, 2), (2, 2)]),
                (6, [(0, 5), (0, 6), (0, 7), (1, 6)])]),
      generate(10, 9, [1, 1, 1, 1, 1, 2, 2, 2, 4, 9], 1,
               [(4, ring), (4, tee)]),
      generate(7, 6, [4, 4, 4, 2, 2, 2, 4], 5, [(9, [(0, 4)])]),
  ]
  test = [
      generate(20, 10, [1] * 10 + [0] + [2, 1, 2, 1, 2, 1, 2, 1, 2], 1,
               [(9, left9), (9, right9)]),
  ]
  return {"train": train, "test": test}
