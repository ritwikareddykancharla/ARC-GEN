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

"""Generator for ARC task f931b4a8 (quadrant-programmed tiling).

Rule
----
The input is a square 2n x 2n grid split into four n x n quadrants:

* top-left     -> its number of non-zero cells is the OUTPUT HEIGHT H;
* top-right    -> its number of non-zero cells is the OUTPUT WIDTH W;
* bottom-right -> a motif (colours on a 0 background) tiled over the H x W
                  canvas from the top-left corner, cut off at the edges;
* bottom-left  -> a zero-free fill grid, stretched to H x W with
                  fill[(y * n) // H][(x * n) // W], which supplies every cell
                  where the tiled motif is 0.

Scope
-----
Randomly sampled quadrant sides are 2..10 (inputs 4x4 .. 20x20); an explicit
`size` or explicit quadrants may go up to 15 (30x30 inputs).  Sides other than
2, 4 and 8 are a synthetic extension beyond the fixtures.  Outputs are H x W
with 1 <= H, W <= min(30, n * n).  Count quadrants are solid rectangles /
bars or scattered dots in one or several colours; sometimes the two top
quadrants share one colour, and sometimes they form a single contiguous bar
running across the TL/TR midline (as in train 4), so the counts must be split
by quadrant, not by object.  Sampled fills are solid, row-striped,
column-striped or rectangular multi-colour blocks (2..4 colours).  Whenever a
fill varies along an axis, the matching output dimension is an integer
multiple of n (at least 2n for sampled dimensions so the stretch is visible).
Sampled motifs are checkerboards, frames, diagonals, random sparse patterns
(1..4 colours), or (only with a non-uniform fill) empty.  A motif colour may
occasionally coincide with a fill colour, as in both test inputs.  Unless the
relevant parts are explicit, scenes are rejected when no motif zero lies in the
cropped canvas, when a non-uniform fill gives the same output under plain
tiling as under stretching, or when a multi-cell output is a single colour.
Non-square inputs, odd input sides and n = 1 are not generated.
"""

import random

import common


MAX_SIDE = 15
FILL_KINDS = ("solid", "rows", "cols", "blocks")
MOTIF_KINDS = ("checker", "frame", "diag", "random", "empty")


def _count(quadrant):
  """Number of non-zero cells in a quadrant."""
  return sum(1 for row in quadrant for v in row if v)


def _copy(quadrant):
  return [list(row) for row in quadrant]


def _colours(quadrant):
  return set(v for row in quadrant for v in row if v)


def _varies(fill):
  """Returns (varies along y, varies along x) for a fill quadrant."""
  n = len(fill)
  vy = any(fill[r][c] != fill[0][c] for r in range(n) for c in range(n))
  vx = any(fill[r][c] != fill[r][0] for r in range(n) for c in range(n))
  return vy, vx


def _check_quadrant(quadrant, name):
  """Validates an explicit square quadrant of integer colour values."""
  if not isinstance(quadrant, (list, tuple)):
    raise ValueError("%s must be a list of rows" % name)
  side = len(quadrant)
  if side < 2 or side > MAX_SIDE:
    raise ValueError("%s must have side 2..%d" % (name, MAX_SIDE))
  for row in quadrant:
    if not isinstance(row, (list, tuple)) or len(row) != side:
      raise ValueError("%s must be square" % name)
    for v in row:
      if type(v) is not int or v < 0 or v > 9:
        raise ValueError("%s has an invalid colour" % name)


def _render(top_left, top_right, fill, motif):
  """Assembles the four n x n quadrants into a 2n x 2n input grid."""
  n = len(fill)
  grid = common.grid(2 * n, 2 * n)
  for r in range(n):
    for c in range(n):
      grid[r][c] = top_left[r][c]
      grid[r][n + c] = top_right[r][c]
      grid[n + r][c] = fill[r][c]
      grid[n + r][n + c] = motif[r][c]
  return grid


def _compose(height, width, fill, motif, stretch=True):
  """Tiles the motif on an H x W canvas and fills its zeros from the fill.

  With stretch=False the fill is tiled instead of stretched; this is only
  used to detect scenes where the stretch would be invisible.
  """
  n = len(motif)
  fn = len(fill)
  out = []
  for y in range(height):
    row = []
    for x in range(width):
      v = motif[y % n][x % n]
      if v == 0:
        if stretch:
          v = fill[(y * fn) // height][(x * fn) // width]
        else:
          v = fill[y % fn][x % fn]
      row.append(v)
    out.append(row)
  return out


def _count_quadrant(n, count, colours):
  """Builds an n x n quadrant with exactly `count` non-zero cells."""
  quadrant = common.grid(n, n)
  cells = None
  if random.random() < 0.55:
    pairs = [(a, count // a) for a in range(1, n + 1)
             if count % a == 0 and count // a <= n]
    if pairs:
      a, b = random.choice(pairs)
      r0 = random.randint(0, n - a)
      c0 = random.randint(0, n - b)
      cells = [(r0 + i, c0 + j) for i in range(a) for j in range(b)]
  if cells is None:
    cells = random.sample([(r, c) for r in range(n) for c in range(n)], count)
  for r, c in cells:
    quadrant[r][c] = random.choice(colours)
  return quadrant


def _bar_pair(n, height, width, colour):
  """Builds TL/TR quadrants whose blocks form one bar across the midline.

  Both blocks share the same rows; the TL block ends at column n-1 and the TR
  block starts at column 0, so they read as a single object (like train 4).
  Returns None if no common row count fits.
  """
  options = [a for a in range(1, n + 1)
             if height % a == 0 and width % a == 0 and
             height // a <= n and width // a <= n]
  if not options:
    return None
  a = random.choice(options)
  r0 = random.randint(0, n - a)
  b1, b2 = height // a, width // a
  tl = common.grid(n, n)
  tr = common.grid(n, n)
  for r in range(r0, r0 + a):
    for c in range(n - b1, n):
      tl[r][c] = colour
    for c in range(b2):
      tr[r][c] = colour
  return tl, tr


def _bands(n, count):
  """Splits range(n) into `count` contiguous bands; returns band per index."""
  cuts = sorted(random.sample(range(1, n), count - 1))
  band = []
  b = 0
  for i in range(n):
    while b < len(cuts) and i >= cuts[b]:
      b += 1
    band.append(b)
  return band


def _fill_quadrant(n, kind, colours):
  """Builds the zero-free bottom-left fill quadrant."""
  if kind == "solid":
    return [[colours[0]] * n for _ in range(n)]
  if kind in ("rows", "cols"):
    if random.random() < 0.5:
      phase = random.randint(0, 1)
      line = [colours[(i + phase) % 2] for i in range(n)]
    else:
      line = [random.choice(colours[:2]) for _ in range(n)]
      if len(set(line)) < 2:
        line[random.randrange(n)] = (
            colours[1] if line[0] == colours[0] else colours[0])
    if kind == "rows":
      return [[line[r]] * n for r in range(n)]
    return [list(line) for _ in range(n)]
  # Rectangular blocks: a grid of row bands x column bands.
  rb = random.randint(1, min(n, 3))
  cb = random.randint(1, min(n, 3))
  if rb * cb < 2:
    if random.random() < 0.5:
      rb = 2
    else:
      cb = 2
  row_band = _bands(n, rb)
  col_band = _bands(n, cb)
  block = [[random.choice(colours) for _ in range(cb)] for _ in range(rb)]
  if len(set(v for row in block for v in row)) < 2:
    block[rb - 1][cb - 1] = (
        colours[1] if block[0][0] == colours[0] else colours[0])
  return [[block[row_band[r]][col_band[c]] for c in range(n)]
          for r in range(n)]


def _motif_quadrant(n, kind, colours):
  """Builds the bottom-right motif quadrant (colours on a 0 background)."""
  quadrant = common.grid(n, n)
  half = max(1, n // 2)
  if kind == "checker":
    phase = random.randint(0, 1)
    for r in range(n):
      for c in range(n):
        if (r + c + phase) % 2 == 0:
          idx = (r // half + c // half) if n >= 4 else r
          quadrant[r][c] = colours[idx % len(colours)]
  elif kind == "frame":
    for r in range(n):
      for c in range(n):
        if r in (0, n - 1) or c in (0, n - 1):
          quadrant[r][c] = colours[0]
  elif kind == "diag":
    for i in range(n):
      quadrant[i][i] = colours[0]
    if random.random() < 0.5:
      for i in range(n):
        if quadrant[i][n - 1 - i] == 0:
          quadrant[i][n - 1 - i] = colours[-1]
  elif kind == "random":
    density = random.uniform(0.3, 0.7)
    for r in range(n):
      for c in range(n):
        if random.random() < density:
          quadrant[r][c] = random.choice(colours)
  return quadrant


def _sample_dim(n, stretched):
  """Samples an output dimension.

  If the fill varies along this axis the dimension is n * k with k >= 2, so
  the stretch is visible; otherwise any value 1..min(30, n*n).
  """
  max_dim = min(30, n * n)
  if stretched:
    return n * random.randint(2, max_dim // n)
  roll = random.random()
  if roll < 0.06:
    return 1
  if roll < 0.3:
    return n * random.randint(1, max_dim // n)
  return random.randint(2, max_dim)


def generate(size=None, height=None, width=None, top_left=None,
             top_right=None, fill=None, motif=None, fill_kind=None,
             motif_kind=None):
  """Returns an input/output pair for the quadrant-programmed tiling task.

  Every argument is optional; given arguments are honoured and the rest are
  sampled.  Inconsistent or deterministically infeasible combinations raise
  ValueError.

  Args:
    size: int quadrant side n (input is 2n x 2n), 2..15; sampled from 2..10.
    height: int output height H = non-zero count of the top-left quadrant.
    width: int output width W = non-zero count of the top-right quadrant.
    top_left: explicit n x n height-count quadrant (fixes `height`).
    top_right: explicit n x n width-count quadrant (fixes `width`).
    fill: explicit n x n zero-free bottom-left fill quadrant.  If it varies
      along an axis, the matching output dimension must be a multiple of n.
    motif: explicit n x n bottom-right motif quadrant.
    fill_kind: one of "solid", "rows", "cols", "blocks" (sampled fill only).
    motif_kind: one of "checker", "frame", "diag", "random", "empty"
      (sampled motif only).
  """
  for name, value in (("size", size), ("height", height), ("width", width)):
    if value is not None and type(value) is not int:
      raise ValueError("%s must be an int" % name)
  n_fixed = size
  if n_fixed is not None and not 2 <= n_fixed <= MAX_SIDE:
    raise ValueError("size must be in 2..%d" % MAX_SIDE)
  given = (("top_left", top_left), ("top_right", top_right),
           ("fill", fill), ("motif", motif))
  for name, quadrant in given:
    if quadrant is None:
      continue
    _check_quadrant(quadrant, name)
    if n_fixed is None:
      n_fixed = len(quadrant)
    elif len(quadrant) != n_fixed:
      raise ValueError("%s side disagrees with the other quadrants/size" % name)
  if top_left is not None:
    if height is not None and height != _count(top_left):
      raise ValueError("height disagrees with the top_left count")
    height = _count(top_left)
  if top_right is not None:
    if width is not None and width != _count(top_right):
      raise ValueError("width disagrees with the top_right count")
    width = _count(top_right)
  for dim in (height, width):
    if dim is not None and not 1 <= dim <= 30:
      raise ValueError("output dimensions must be in 1..30")
  if fill_kind is not None and fill_kind not in FILL_KINDS:
    raise ValueError("unknown fill_kind")
  if motif_kind is not None and motif_kind not in MOTIF_KINDS:
    raise ValueError("unknown motif_kind")
  if fill is not None:
    if fill_kind is not None:
      raise ValueError("fill_kind cannot be combined with an explicit fill")
    if any(v == 0 for row in fill for v in row):
      raise ValueError("fill must be zero-free")
    nf = len(fill)
    fvy, fvx = _varies(fill)
    if fvy and height is not None and height % nf:
      raise ValueError("fill varies by row: height must be a multiple of n")
    if fvx and width is not None and width % nf:
      raise ValueError("fill varies by column: width must be a multiple of n")
    if (fvy or fvx) and (height is None or width is None):
      visible = ((fvy and (height is None or height // nf >= 2)) or
                 (fvx and (width is None or width // nf >= 2)))
      if not visible:
        raise ValueError("the stretch of this fill would be invisible for "
                         "the requested dimensions")
  if motif is not None and motif_kind is not None:
    raise ValueError("motif_kind cannot be combined with an explicit motif")
  motif_empty = (motif_kind == "empty" or
                 (motif is not None and _count(motif) == 0))
  if motif_empty:
    if fill_kind == "solid":
      raise ValueError("an empty motif needs a non-uniform fill")
    if fill is not None and len(_colours(fill)) == 1:
      raise ValueError("an empty motif needs a non-uniform fill")
  if (motif is not None and _count(motif) == len(motif) ** 2 and
      (height is None or width is None)):
    raise ValueError("a zero-free motif leaves nothing for the fill to supply")

  need = max(height or 1, width or 1)
  if n_fixed is not None:
    if n_fixed * n_fixed < need:
      raise ValueError("quadrant too small for the requested counts")
    sides = [n_fixed]
  else:
    sides = [s for s in range(2, 11) if s * s >= need]

  def side_ok(s):
    if motif_kind == "frame" and s < 3:
      return False
    if fill_kind == "rows" and height is not None and (
        height % s or height // s < 2):
      return False
    if fill_kind == "cols" and width is not None and (
        width % s or width // s < 2):
      return False
    if fill_kind == "blocks":
      if height is not None and height % s:
        return False
      if width is not None and width % s:
        return False
      if height == s and width == s:
        return False
    if motif_empty and fill is None and fill_kind is None:
      rows_ok = height is None or (height % s == 0 and height // s >= 2)
      cols_ok = width is None or (width % s == 0 and width // s >= 2)
      blocks_ok = ((height is None or height % s == 0) and
                   (width is None or width % s == 0) and
                   not (height == s and width == s))
      if not (rows_ok or cols_ok or blocks_ok):
        return False
    return True

  sides = [s for s in sides if side_ok(s)]
  if not sides:
    raise ValueError("no quadrant side is compatible with the requested "
                     "dimensions and kinds")

  strict_fill = not (fill is not None and height is not None and
                     width is not None)
  strict_expose = not (motif is not None and height is not None and
                       width is not None)
  check_colours = fill is None or motif is None

  for _ in range(300):
    n = random.choice(sides)
    if fill is not None:
      bl = _copy(fill)
    else:
      fk = fill_kind
      if fk is None:
        kinds = ["solid", "solid", "solid"]
        if height is None or (height % n == 0 and height // n >= 2):
          kinds.append("rows")
        if width is None or (width % n == 0 and width // n >= 2):
          kinds.append("cols")
        if ((height is None or height % n == 0) and
            (width is None or width % n == 0) and
            not (height == n and width == n)):
          kinds.append("blocks")
        if motif_empty:
          kinds = [k for k in kinds if k != "solid"]
        if not kinds:
          continue
        fk = random.choice(kinds)
      banned = _colours(motif) if motif is not None else set()
      pool = [c for c in range(1, 10) if c not in banned]
      if fk == "solid":
        want = 1
      elif fk == "blocks":
        want = min(random.randint(2, 4), len(pool))
      else:
        want = 2
      if len(pool) < max(want, 1) or (fk != "solid" and want < 2):
        continue
      bl = _fill_quadrant(n, fk, random.sample(pool, want))
    vy, vx = _varies(bl)
    uniform_fill = not (vy or vx)

    h = height if height is not None else _sample_dim(n, vy)
    w = width if width is not None else _sample_dim(n, vx)
    if (vy and h % n) or (vx and w % n):
      continue
    if height is None and width is None and h == w and random.random() < 0.6:
      continue

    if motif is not None:
      br = _copy(motif)
    else:
      mk = motif_kind
      if mk is None:
        kinds = ["checker", "checker", "random", "random", "diag"]
        if n >= 3:
          kinds.append("frame")
        if not uniform_fill:
          kinds.append("empty")
        mk = random.choice(kinds)
      if mk == "empty" and uniform_fill:
        continue
      fill_cols = sorted(_colours(bl))
      pool = [c for c in range(1, 10) if c not in fill_cols]
      if not pool:
        continue
      if mk == "random":
        k = random.randint(1, min(4, len(pool)))
      elif mk == "checker":
        k = random.randint(1, min(3, len(pool)))
      else:
        k = 1 if random.random() < 0.6 or len(pool) < 2 else 2
      cols = random.sample(pool, k)
      # Occasionally reuse a fill colour in the motif (as in both tests).
      if random.random() < 0.25 and (k >= 2 or len(fill_cols) >= 2):
        cols[random.randrange(k)] = random.choice(fill_cols)
      br = _motif_quadrant(n, mk, cols)
      nonzero = _count(br)
      if mk != "empty" and (nonzero == 0 or nonzero == n * n):
        continue

    if strict_expose and not any(br[y % n][x % n] == 0
                                 for y in range(h) for x in range(w)):
      continue

    count_palette = random.sample(range(1, 10), 6)
    tl = _copy(top_left) if top_left is not None else None
    tr = _copy(top_right) if top_right is not None else None
    if tl is None and tr is None and random.random() < 0.2:
      # Shared count colour; often one bar crossing the TL/TR midline.
      colour = count_palette[0]
      pair = _bar_pair(n, h, w, colour) if random.random() < 0.7 else None
      if pair is not None:
        tl, tr = pair
      else:
        tl = _count_quadrant(n, h, [colour])
        tr = _count_quadrant(n, w, [colour])
    if tl is None:
      cols = count_palette[:1] if random.random() < 0.75 else count_palette[:3]
      tl = _count_quadrant(n, h, cols)
    if tr is None:
      cols = count_palette[3:4] if random.random() < 0.75 else count_palette[3:6]
      tr = _count_quadrant(n, w, cols)

    grid = _render(tl, tr, bl, br)
    out = _compose(h, w, bl, br)
    if strict_fill and not uniform_fill and out == _compose(
        h, w, bl, br, stretch=False):
      continue
    if check_colours and h * w > 1 and len(
        set(v for row in out for v in row)) < 2:
      continue
    if out != grid:
      return {"input": grid, "output": out}
  raise ValueError("could not satisfy the requested parameters")


def validate():
  """Reconstructs the canonical fixtures through explicit generate calls."""
  train = [
      generate(
          top_left=[[1, 1, 1, 1]] * 4,
          top_right=[[3, 3, 3, 3], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
          fill=[[5, 5, 5, 5]] * 4,
          motif=[[6, 0, 6, 0], [0, 6, 0, 6], [6, 0, 6, 0], [0, 6, 0, 6]]),
      generate(
          top_left=[[8, 8, 8, 8]] * 4,
          top_right=[[6, 6, 6, 6]] * 4,
          fill=[[1, 1, 1, 1], [5, 5, 5, 5], [1, 1, 1, 1], [5, 5, 5, 5]],
          motif=[[4, 4, 4, 4], [4, 0, 0, 4], [4, 0, 0, 4], [4, 4, 4, 4]]),
      generate(
          top_left=[[6, 6, 0, 0, 0, 0, 0, 0]] * 5 + [[0] * 8] * 3,
          top_right=[[0, 0, 0, 4, 4, 4, 4, 4]] * 2 + [[0] * 8] * 6,
          fill=[[1] * 8 for _ in range(8)],
          motif=[[8, 0, 8, 0, 0, 6, 0, 6], [0, 8, 0, 0, 0, 0, 6, 0],
                 [8, 0, 8, 0, 0, 6, 0, 6], [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0], [6, 0, 6, 0, 0, 8, 0, 8],
                 [0, 6, 0, 0, 0, 0, 8, 0], [6, 0, 6, 0, 0, 8, 0, 8]]),
      generate(
          top_left=[[4, 4, 4, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
          top_right=[[4, 4, 4, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
          fill=[[2, 5, 2, 5]] * 4,
          motif=[[0, 0, 0, 0]] * 4),
      generate(
          top_left=[[8, 0, 8, 0], [0, 0, 0, 0], [0, 0, 8, 0], [0, 0, 0, 0]],
          top_right=[[4, 0, 4, 0], [0, 0, 0, 0], [4, 0, 0, 4], [0, 0, 0, 0]],
          fill=[[6, 6, 6, 6]] * 4,
          motif=[[1, 1, 1, 1], [0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0]]),
  ]
  test = [
      generate(
          top_left=[[2, 0, 0, 5], [0, 3, 0, 5], [5, 5, 5, 5], [0, 0, 5, 2]],
          top_right=[[1, 0, 1, 0], [0, 1, 3, 1], [1, 0, 1, 0], [0, 0, 3, 0]],
          fill=[[2, 2, 2, 2]] * 4,
          motif=[[0, 3, 3, 3], [3, 2, 3, 0], [3, 0, 0, 5], [3, 3, 1, 0]]),
      generate(
          top_left=[[2, 2], [2, 2]],
          top_right=[[5, 5], [5, 5]],
          fill=[[7, 3], [6, 8]],
          motif=[[7, 0], [0, 7]]),
  ]
  return {"train": train, "test": test}
