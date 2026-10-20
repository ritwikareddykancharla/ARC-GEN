"""Generator for ARC task b9e38dc0: a seed colour floods a funnel vessel and pours out.

Rule:
  The wall is the most frequent non-background colour. It draws a vessel with
  one open, funnel-shaped side. A small seed of another colour sits inside the
  vessel, near the side opposite the opening. Every other colour is an
  obstacle. Rotate the grid so the flow points down. Then:
    * Each obstacle casts a shadow: the straight run of background cells below
      it, ending at the first non-background cell. Shadows stay background.
    * The seed floods the vessel interior. The flood is 4-connected, moves
      through background only, avoids shadows and never goes below the last
      wall row.
    * Each flooded vessel row has a left and a right boundary: the nearest
      wall cell beside the flood, or the grid border (-1 or width).
    * Below the vessel, each boundary continues from its last two runs, read
      bottom-up. Let the final value v0 hold for kk rows and the previous
      value v1 hold for m rows. Then stream row t (t = 1, 2, ...) uses
      v0 + (v0 - v1) * ((kk - 1 + t) // m). A boundary with a single run stays
      constant. Cells strictly between the two boundaries become seed, except
      shadows and non-background cells.

Construction:
  Scenes are built in a canonical frame where the flow points down. The
  canonical picture is then turned clockwise `rotation` quarter turns.
  The vessel is latent: one inclusive interior span (l, r) per row. Its wall
  is the 4-neighbour boundary of the interior, minus the cells below the
  opening row, plus optional extra corner wall cells. The answer is computed
  from these latents:
    * the flood of the latent interior from the seeds, avoiding latent shadows;
    * the boundaries L = l - 1 and R = r + 1;
    * the run-rule continuation of those boundaries.

Scope (random mode):
  * Canonical width 9..30 and height 10..30, either requested or sampled
    (biased towards 20 and below). Sampled sizes always lie in the same range
    that can be requested.
  * The layout budget grows with the canvas:
      - free rows above the cap: 1..max(1, H // 6);
      - funnel rows: from the period-dependent minimum up to
        f_min + 2 + H // 3, limited by the width;
      - vessel body rows: 2..2 + H // 3;
      - stream rows: the remainder, at least 3;
      - interior span extent: up to W - 4 (free placement) or W - 2 (one
        side on the border).
  * Funnel walls diverge on each side with a step of s in {1, 2} every m in
    {1, 2, 3} rows. Each side has its own phase. The funnel always contains
    at least two complete runs per side, so the period can be read from the
    input. Step s = 2 is a synthetic extension; the fixtures show only s = 1.
  * The vessel body is a bounded random walk of spans above the funnel.
  * Placement is either free, with a one-cell margin, or has one funnel side
    on the grid border, as in pair 2.
  * Extra wall cells are added sometimes:
      - cap corners, as in pairs 2 and 3 and the test;
      - staircase/concavity corner cells, as in pair 3 and the test.
  * The seed is a 4-connected clump of 1-6 cells in the first three interior
    rows.
  * Obstacles:
      - single cells or 2-cell bars in the stream;
      - distractors above or beside the vessel, whose shadows may cut the
        stream;
      - 0-2 interior obstacles, each reusing an outside obstacle colour.
  * All four flow directions are sampled.
  * Acceptance requires:
      - unambiguous roles and direction, with a margin;
      - flood in every vessel row;
      - at least 2 canonical rows below the opening that receive stream;
      - in some row, stream reaching columns outside the opening span, so the
        widening is visible.
  * Not produced in random mode: converging or vertical funnel sides, several
    vessels, and seeds deeper than the third interior row.

Explicit mode (spans given):
  Fields are checked with exact arity:
    * spans and seeds are (a, b) pairs;
    * extra_walls are (row, col) pairs;
    * obstacles are (row, col, colour) triples.
  Wrong-length records raise ValueError; nothing is truncated. Further checks:
    * extra walls are distinct and not already part of the derived outline;
    * the unshaded interior is 4-connected to the seeds;
    * colour roles and direction are unambiguous;
    * the output differs from the input.
  EXTRAPOLATION (labelled): explicit mode also accepts boundaries that are
  vertical, converging, or whose final run is longer than the previous run.
  The stream then follows the literal last-two-run formula above; it does not
  hold the last value. Such a stream can narrow until it vanishes, or a
  boundary can jump at t = 1. Example: a left boundary read bottom-up as
  5,5,5,4 becomes 8. Only a single-run boundary stays constant. These cases
  go beyond anything the fixtures show.

Fixtures:
  The original pairs are rebuilt through explicit latent arguments: spans,
  extra corner walls, seeds, obstacles and rotation.
"""

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

import random

import common

_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_STEPS = (-2, -1, -1, 0, 0, 0, 1, 1, 2)
_PERIODS = (1, 1, 2, 2, 3)
_SLOPES = (1, 1, 1, 1, 2)
_SEED_ROWS = (0, 0, 0, 1, 1, 2)
_MIN_WIDTH = 9
_MIN_HEIGHT = 10
_MAX_TRIES = 4000


def _rotate_cw(g):
  h, w = len(g), len(g[0])
  return [[g[h - 1 - j][i] for j in range(h)] for i in range(w)]


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _check_colours(*colours):
  given = [c for c in colours if c is not None]
  for c in given:
    if not _is_int(c) or not 0 <= c <= 9:
      raise ValueError("colours must be integers 0..9")
  if len(set(given)) != len(given):
    raise ValueError("bg, wall and seed colours must be distinct")


def _records(value, arity, name):
  """Checks a list of fixed-arity integer records; never truncates."""
  if not isinstance(value, (list, tuple)):
    raise ValueError("%s must be a list of records" % name)
  out = []
  for item in value:
    if not isinstance(item, (list, tuple)) or len(item) != arity:
      raise ValueError("each %s record must have exactly %d fields" %
                       (name, arity))
    if not all(_is_int(v) for v in item):
      raise ValueError("%s fields must be integers" % name)
    out.append(tuple(item))
  return out


def _vessel(top, spans, height, width, extra_walls):
  """Interior cells, in-grid wall cells and the bottom (opening) row."""
  interior = set()
  for i, (l, r) in enumerate(spans):
    for x in range(l, r + 1):
      interior.add((top + i, x))
  bottom = top + len(spans) - 1
  walls = set()
  for (y, x) in interior:
    for dy, dx in _DIRS4:
      ny, nx = y + dy, x + dx
      if (ny, nx) in interior or ny > bottom:
        continue
      if 0 <= ny < height and 0 <= nx < width:
        walls.add((ny, nx))
  for cell in extra_walls:
    walls.add((cell[0], cell[1]))
  return interior, walls, bottom


def _paint(width, height, bg, wall, seed, walls, seeds, obstacles):
  g = common.grid(width, height, bg)
  for (y, x) in walls:
    g[y][x] = wall
  for (y, x) in seeds:
    g[y][x] = seed
  for (y, x, c) in obstacles:
    g[y][x] = c
  return g


def _shadows(g, bg, cells):
  h = len(g)
  shade = set()
  for (y, x) in cells:
    yy = y + 1
    while yy < h and g[yy][x] == bg:
      shade.add((yy, x))
      yy += 1
  return shade


def _flood(seeds, interior, blocked):
  reach = set(seeds)
  stack = list(reach)
  while stack:
    y, x = stack.pop()
    for dy, dx in _DIRS4:
      nb = (y + dy, x + dx)
      if nb in interior and nb not in reach and nb not in blocked:
        reach.add(nb)
        stack.append(nb)
  return reach


def _extrapolate(seq, t):
  """Continue a boundary t rows below its last row using its last two runs."""
  ys = sorted(seq, reverse=True)
  v = [seq[y] for y in ys]
  v0, kk = v[0], 1
  while kk < len(v) and v[kk] == v0:
    kk += 1
  if kk >= len(v):
    return v0
  v1, m = v[kk], 1
  while kk + m < len(v) and v[kk + m] == v1:
    m += 1
  return v0 + (v0 - v1) * ((kk - 1 + t) // m)


def _identifiable(g, bg, wall, walls, seeds, obstacles, margin):
  """Colour roles and flow direction must be readable from the input alone."""
  h, w = len(g), len(g[0])
  for (y, x) in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
    if g[y][x] != bg:
      return False
  counts = {}
  for row in g:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  for v, k in counts.items():
    if v != bg and k >= counts[bg]:
      return False
    if v not in (bg, wall) and k >= counts.get(wall, 0):
      return False
  wy = [y for y, _ in walls]
  wx = [x for _, x in walls]
  y0, y1, x0, x1 = min(wy), max(wy), min(wx), max(wx)

  def inside(c):
    return y0 <= c[0] <= y1 and x0 <= c[1] <= x1

  if not all(inside(c) for c in seeds):
    return False
  by_colour = {}
  for (y, x, c) in obstacles:
    by_colour.setdefault(c, []).append((y, x))
  for cells in by_colour.values():
    if all(inside(c) for c in cells):
      return False
  my = sum(y for y, _ in seeds) / len(seeds)
  mx = sum(x for _, x in seeds) / len(seeds)
  oy = (my - (y0 + y1) / 2) / max(1, y1 - y0)
  ox = (mx - (x0 + x1) / 2) / max(1, x1 - x0)
  return -oy > abs(ox) + margin


def _scene_problem(width, height, bg, wall, seed, top, spans, extra_walls,
                   seeds, obstacles, margin=1e-6, every_row=False):
  """Returns a description of the first violated invariant, or None."""
  if not (_is_int(width) and _is_int(height)):
    return "width and height must be integers"
  if not (1 <= width <= 30 and 1 <= height <= 30):
    return "grid size must be within 1..30"
  if not spans:
    return "spans must be non-empty"
  if not _is_int(top) or top < 1:
    return "top must be an integer >= 1 (cap row inside the grid)"
  bottom = top + len(spans) - 1
  if bottom > height - 2:
    return "the vessel must leave at least one stream row"
  for (l, r) in spans:
    if not (0 <= l <= r < width):
      return "spans must satisfy 0 <= l <= r < width"
  interior, walls, _ = _vessel(top, spans, height, width, [])
  seen = set()
  for (y, x) in extra_walls:
    if not (0 <= y <= bottom and 0 <= x < width):
      return "extra walls must be in the grid, not below the opening row"
    if (y, x) in interior:
      return "extra walls must not lie inside the vessel interior"
    if (y, x) in walls or (y, x) in seen:
      return "extra walls must be distinct and not part of the derived outline"
    seen.add((y, x))
  walls = walls | seen
  if not any(y == bottom for (y, _) in walls):
    return "the opening row needs at least one wall cell"
  seedset = set(seeds)
  if not seedset or len(seedset) != len(seeds) or not seedset <= interior:
    return "seeds must be distinct cells inside the vessel interior"
  occupied = walls | seedset
  ocells = set()
  for (y, x, c) in obstacles:
    if not (0 <= y < height and 0 <= x < width):
      return "obstacle outside the grid"
    if not 0 <= c <= 9 or c in (bg, wall, seed):
      return "obstacle colours must be 0..9 and differ from bg, wall, seed"
    if (y, x) in occupied or (y, x) in ocells:
      return "obstacles must not overlap walls, seeds or each other"
    ocells.add((y, x))
  g = _paint(width, height, bg, wall, seed, walls, seeds, obstacles)
  blocked = _shadows(g, bg, sorted(ocells)) | ocells
  reach = _flood(seedset, interior, blocked)
  if any(c not in reach and c not in blocked for c in interior):
    return "the unshaded interior must be 4-connected to the seeds"
  if every_row:
    for i, (l, r) in enumerate(spans):
      if not any((top + i, x) in reach for x in range(l, r + 1)):
        return "every vessel row must receive flood"
  if not _identifiable(g, bg, wall, walls, seeds, obstacles, margin):
    return "colour roles or flow direction are ambiguous"
  return None


def _render(width, height, rotation, bg, wall, seed, top, spans, extra_walls,
            seeds, obstacles):
  interior, walls, bottom = _vessel(top, spans, height, width, extra_walls)
  g = _paint(width, height, bg, wall, seed, walls, seeds, obstacles)
  ocells = set((y, x) for (y, x, _) in obstacles)
  shade = _shadows(g, bg, sorted(ocells))
  filled = _flood(seeds, interior, shade | ocells)
  out = [row[:] for row in g]
  for (y, x) in filled:
    out[y][x] = seed
  lefts, rights = {}, {}
  for i, (l, r) in enumerate(spans):
    y = top + i
    if any((y, x) in filled for x in range(l, r + 1)):
      lefts[y] = l - 1
      rights[y] = r + 1
  for t in range(1, height - bottom):
    y = bottom + t
    lo = _extrapolate(lefts, t)
    hi = _extrapolate(rights, t)
    for x in range(max(0, lo + 1), min(width, hi)):
      if g[y][x] == bg and (y, x) not in shade:
        out[y][x] = seed
  for _ in range(rotation % 4):
    g = _rotate_cw(g)
    out = _rotate_cw(out)
  return {"input": g, "output": out}


def _fits(cells, inside, height, width, interior, taken):
  corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
  for (y, x) in cells:
    if not (0 <= y < height and 0 <= x < width) or (y, x) in corners:
      return False
    if ((y, x) in interior) != inside:
      return False
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        if (y + dy, x + dx) in taken:
          return False
  return True


def _corner_cells(interior, walls, top, bottom, width):
  """Outside cells diagonal to the interior that close a staircase corner."""
  found = set()
  for (y, x) in interior:
    for dy in (-1, 1):
      for dx in (-1, 1):
        c = (y + dy, x + dx)
        if c in interior or c in walls:
          continue
        if not (top - 1 <= c[0] <= bottom and 0 <= c[1] < width):
          continue
        nbs = [(c[0] + a, c[1] + b) for a, b in _DIRS4]
        if any(n in interior for n in nbs):
          continue
        if sum(1 for n in nbs if n in walls) >= 2:
          found.add(c)
  return sorted(found)


def _side_drop(f, s, m, p):
  """Inward shift of one funnel side between its bottom and top rows."""
  return s * ((f - 1 + p) // m)


def _stream_evidence(out, bottom, span, seed):
  """Counts stream rows with seed colour; checks widening past the opening."""
  rows, wide = 0, False
  l, r = span
  for y in range(bottom + 1, len(out)):
    xs = [x for x, v in enumerate(out[y]) if v == seed]
    if xs:
      rows += 1
      if xs[0] < l or xs[-1] > r:
        wide = True
  return rows, wide


def _sample_size(lo):
  if random.random() < 0.7:
    return random.randint(lo, 20)
  return random.randint(lo, 30)


def _try_scene(bg, wall, seed, width, height):
  # Funnel periods, steps and phases for each side.
  m_l = random.choice(_PERIODS)
  m_r = m_l if random.random() < 0.5 else random.choice(_PERIODS)
  s_l = random.choice(_SLOPES)
  s_r = s_l if random.random() < 0.6 else random.choice(_SLOPES)
  p_l = random.randint(0, m_l - 1)
  p_r = random.randint(0, m_r - 1)
  mode = random.choice(("free", "free", "free", "free", "left", "right"))
  max_ext = width - 4 if mode == "free" else width - 2
  # Vertical budget: cap rows + cap wall + funnel + body + stream (>= 3).
  f_min = max(2 * m_l - p_l, 2 * m_r - p_r) + 1
  cap = random.randint(1, max(1, height // 6))
  base = height - cap - 1 - 3
  f_hi = min(base - 2, f_min + 2 + height // 3)
  while f_hi >= f_min and (_side_drop(f_hi, s_l, m_l, p_l) +
                           _side_drop(f_hi, s_r, m_r, p_r) + 1 > max_ext):
    f_hi -= 1
  if f_hi < f_min:
    return None
  f = random.randint(f_min, f_hi)
  b = random.randint(2, min(base - f, 2 + height // 3))
  shrink = _side_drop(f, s_l, m_l, p_l) + _side_drop(f, s_r, m_r, p_r)
  wb = random.randint(shrink + 1,
                      min(max_ext, shrink + 1 + max(3, width // 3)))
  # Funnel spans, relative columns, built bottom-up.
  rel = [(s_l * ((i + p_l) // m_l), wb - 1 - s_r * ((i + p_r) // m_r))
         for i in range(f)]
  ext_lo, ext_hi = 0, wb - 1
  # Vessel body: bounded random walk of spans above the funnel.
  for j in range(b):
    l, r = rel[-1]
    minw = 2 if j == b - 1 else 1
    nxt = None
    for _ in range(30):
      nl = l + random.choice(_STEPS)
      nr = r + random.choice(_STEPS)
      if nr - nl + 1 < minw or nl > r or nr < l:
        continue
      if max(ext_hi, nr) - min(ext_lo, nl) + 1 > max_ext:
        continue
      if mode == "left" and nl < 1:
        continue
      if mode == "right" and nr > wb - 2:
        continue
      nxt = (nl, nr)
      break
    if nxt is None:
      return None
    rel.append(nxt)
    ext_lo, ext_hi = min(ext_lo, nxt[0]), max(ext_hi, nxt[1])
  rel.reverse()
  # Horizontal placement.
  if mode == "free":
    shift = random.randint(2 - ext_lo, width - 3 - ext_hi)
  elif mode == "left":
    shift = 0
  else:
    shift = width - wb
  spans = [(l + shift, r + shift) for l, r in rel]
  top = cap + 1
  bottom = top + len(spans) - 1
  stream = height - bottom - 1
  if stream < 3:
    return None
  interior, walls, _ = _vessel(top, spans, height, width, [])
  # Seed: a small 4-connected clump within the first three interior rows.
  k0 = min(random.choice(_SEED_ROWS), len(spans) - 1)
  lk, rk = spans[k0]
  size = random.choice((1, 1, 2, 2, 3, 3, 4, 5, 6))
  seeds = [(top + k0, random.randint(lk, rk))]
  for _ in range(40):
    if len(seeds) >= size:
      break
    y, x = random.choice(seeds)
    dy, dx = random.choice(_DIRS4)
    nb = (y + dy, x + dx)
    if nb in interior and nb[0] <= top + 2 and nb not in seeds:
      seeds.append(nb)
  seeds.sort()
  # Optional extra wall cells: cap corners and staircase corners.
  corners = _corner_cells(interior, walls, top, bottom, width)
  cap_c = [c for c in corners if c[0] == top - 1]
  body_c = [c for c in corners if c[0] != top - 1]
  extra = []
  if cap_c and random.random() < 0.55:
    extra += [c for c in cap_c if random.random() < 0.75]
  if body_c and random.random() < 0.45:
    random.shuffle(body_c)
    extra += body_c[:random.randint(1, min(3, len(body_c)))]
  extra.sort()
  walls = walls | set(extra)
  # Colours.
  fixed = [c for c in (bg, wall, seed) if c is not None]
  rest = [c for c in range(10) if c not in fixed]
  random.shuffle(rest)
  c_bg = bg if bg is not None else rest.pop()
  c_wall = wall if wall is not None else rest.pop()
  c_seed = seed if seed is not None else rest.pop()
  palette = rest[:random.randint(1, 3)]
  # Obstacles.
  taken = set(walls) | set(seeds)
  obst = []

  def add(cells, colour):
    for (y, x) in cells:
      obst.append((y, x, colour))
      taken.add((y, x))

  lefts = {top + i: l - 1 for i, (l, _) in enumerate(spans)}
  rights = {top + i: r + 1 for i, (_, r) in enumerate(spans)}
  n_stream = random.choice((0, 1, 1, 2, 2, 3)) + random.randint(0, stream // 5)
  for _ in range(n_stream):
    for _ in range(40):
      t = random.randint(1, stream)
      y = bottom + t
      xl = max(0, _extrapolate(lefts, t) + 1)
      xh = min(width, _extrapolate(rights, t)) - 1
      length = random.choice((1, 1, 2, 2))
      if length == 2 and random.random() < 0.4:
        if xh - xl + 1 < 2:
          continue
        x = random.randint(xl, xh)
        cells = [(y, x), (y + 1, x)]
      else:
        if xh - xl + 1 < length + 1:
          continue
        x = random.randint(xl, xh - length + 1)
        cells = [(y, x + d) for d in range(length)]
      if _fits(cells, False, height, width, interior, taken):
        add(cells, random.choice(palette))
        break
  x0 = min(x for _, x in walls)
  x1 = max(x for _, x in walls)
  for _ in range(random.randint(0, 2 + height // 12)):
    for _ in range(40):
      y = random.randint(0, bottom)
      x = random.randint(0, width - 1)
      if not (y < cap or x < x0 or x > x1):
        continue
      if _fits([(y, x)], False, height, width, interior, taken):
        add([(y, x)], random.choice(palette))
        break
  outside = sorted(set(c for (_, _, c) in obst))
  n_inner = random.choice((0, 0, 0, 1, 1, 2)) if outside else 0
  cand = sorted(c for c in interior if c[0] >= top + 2)
  random.shuffle(cand)
  placed = 0
  for cell in cand[:60]:
    if placed >= n_inner:
      break
    if _fits([cell], True, height, width, interior, taken):
      add([cell], random.choice(outside))
      placed += 1
  params = dict(width=width, height=height, bg=c_bg, wall=c_wall, seed=c_seed,
                top=top, spans=spans, extra_walls=extra, seeds=seeds,
                obstacles=obst)
  if _scene_problem(margin=0.08, every_row=True, **params) is not None:
    return None
  pair = _render(rotation=0, **params)
  if pair["input"] == pair["output"]:
    return None
  rows, wide = _stream_evidence(pair["output"], bottom, spans[-1], c_seed)
  if rows < 2 or not wide:
    return None
  return params


def generate(width=None, height=None, rotation=None, bg=None, wall=None,
             seed=None, top=None, spans=None, extra_walls=None, seeds=None,
             obstacles=None):
  """Returns an input/output pair.

  All geometry is in the canonical frame, where the flow points down.

  Args:
    width: canonical grid width. Random mode accepts 9..30 and samples
      9..30 if None. Explicit mode accepts 1..30.
    height: canonical grid height. Random mode accepts 10..30 and samples
      10..30 if None. Explicit mode accepts 1..30.
    rotation: number of clockwise quarter turns applied to the canonical
      picture, an int in 0..3. 0 = flow down, 1 = flow left, 2 = flow up,
      3 = flow right. Sampled if None, in both modes.
    bg: background colour.
    wall: vessel wall colour.
    seed: seed / flood colour.
    top: first interior row of the vessel; the cap is row top - 1.
      Explicit mode only.
    spans: list of (l, r) pairs, each an inclusive interior column span, one
      per row starting at `top`. The last span is the opening row. If None,
      a fresh random scene is sampled.
    extra_walls: list of (row, col) extra wall cells, for example corner
      cells. Explicit mode only.
    seeds: list of (row, col) seed cells inside the vessel. Explicit mode only.
    obstacles: list of (row, col, colour) obstacle cells. Explicit mode only.

  Random mode (spans is None):
    * Honours width, height, rotation, bg, wall and seed.
    * Raises ValueError if top, extra_walls, seeds or obstacles is given.

  Explicit mode:
    * Requires width, height, bg, wall, seed, top, spans and seeds.
    * Validates exact record arity and the scene invariants.
    * Raises ValueError on any violation.
  """
  _check_colours(bg, wall, seed)
  if rotation is None:
    rotation = random.randint(0, 3)
  if not _is_int(rotation) or not 0 <= rotation <= 3:
    raise ValueError("rotation must be an integer in 0..3")
  if spans is None:
    if any(v is not None for v in (top, extra_walls, seeds, obstacles)):
      raise ValueError("top, extra_walls, seeds and obstacles require spans")
    if width is not None and (not _is_int(width) or
                              not _MIN_WIDTH <= width <= 30):
      raise ValueError("random canonical width must be an integer in 9..30")
    if height is not None and (not _is_int(height) or
                               not _MIN_HEIGHT <= height <= 30):
      raise ValueError("random canonical height must be an integer in 10..30")
    params = None
    for _ in range(_MAX_TRIES):
      w = width if width is not None else _sample_size(_MIN_WIDTH)
      h = height if height is not None else _sample_size(_MIN_HEIGHT)
      params = _try_scene(bg, wall, seed, w, h)
      if params is not None:
        break
    if params is None:
      raise ValueError("could not build a scene with the requested controls")
    return _render(rotation=rotation, **params)
  if any(v is None for v in (width, height, bg, wall, seed, top, seeds)):
    raise ValueError("explicit scenes need width, height, colours, top, seeds")
  spans = _records(spans, 2, "spans")
  extra_walls = _records(extra_walls if extra_walls is not None else [], 2,
                         "extra_walls")
  seeds = _records(seeds, 2, "seeds")
  obstacles = _records(obstacles if obstacles is not None else [], 3,
                       "obstacles")
  problem = _scene_problem(width, height, bg, wall, seed, top, spans,
                           extra_walls, seeds, obstacles)
  if problem is not None:
    raise ValueError(problem)
  pair = _render(width, height, rotation, bg, wall, seed, top, spans,
                 extra_walls, seeds, obstacles)
  if pair["input"] == pair["output"]:
    raise ValueError("the scene produces no change")
  return pair


def validate():
  """Rebuilds the original task pairs from explicit latent parameters."""
  train = [
      generate(width=15, height=15, rotation=0, bg=1, wall=3, seed=9, top=4,
               spans=[(6, 11), (5, 8), (5, 7), (6, 7), (7, 8), (6, 9),
                      (5, 10)],
               seeds=[(4, 8)], obstacles=[(11, 7, 5), (11, 8, 5)]),
      generate(width=8, height=15, rotation=1, bg=0, wall=5, seed=4, top=2,
               spans=[(3, 6), (3, 6), (4, 6), (5, 5), (4, 6), (3, 7)],
               extra_walls=[(1, 2), (1, 7)], seeds=[(2, 4)], obstacles=[]),
      generate(width=16, height=18, rotation=2, bg=7, wall=9, seed=3, top=5,
               spans=[(7, 9), (6, 10), (6, 10), (8, 9), (8, 8), (8, 8),
                      (7, 9), (7, 9), (6, 10), (6, 10)],
               extra_walls=[(8, 5)],
               seeds=[(5, 7), (5, 8), (6, 6), (6, 7), (6, 8), (7, 6)],
               obstacles=[(1, 6, 8), (2, 13, 6), (3, 2, 6), (13, 8, 6),
                          (16, 10, 6)]),
  ]
  test = [
      generate(width=15, height=19, rotation=1, bg=1, wall=4, seed=2, top=3,
               spans=[(6, 9), (6, 9), (7, 8), (8, 8), (7, 9), (7, 9),
                      (6, 10), (6, 10)],
               extra_walls=[(2, 5), (5, 10)], seeds=[(4, 8)],
               obstacles=[(12, 9, 3), (14, 6, 3), (16, 8, 8)]),
  ]
  return {"train": train, "test": test}
