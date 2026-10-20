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

"""ARC-GEN style generator for task 351d6448.

Rule: full rows of colour 5 split the input into equal-sized panels. Read top
to bottom, the panels are the steps of a sequence. The output is the next
panel, the sequence continued by one more step. Each step rewrites a band of
columns. That band moves a constant number of columns `step` per step. The
new cell values come from a cell-level transition that the earlier panels
already show.

Scene families:
  * "bar": a horizontal bar of one or more aligned rows grows by `step`
    columns each panel. It starts with length >= step.
  * "slide": a small 2-D multicolour motif translates `step` columns per
    panel.
  * "stair": a fixed periodic background of 0 and a base colour. A staircase
    colour spreads `step` columns further each panel. Only base-colour cells
    are recoloured; 0 cells stay 0.

Any scene may be mirrored left-right, so that the movement goes leftward.
The bar and slide families may contain static distractor cells. These are
identical in every panel, sit in rows the moving object never touches, and
use a colour that is not otherwise used.

To keep the panel separators unambiguous:
  * The only full uniform rows are the 5 separators, plus all-0 rows.
  * All-0 rows are allowed only when 0 is strictly the most frequent colour
    of the input, so that they read as plain background.
  * The stair family's tile therefore never has an all-zero row.
"""

import random


_PALETTE = [1, 2, 3, 4, 6, 7, 8, 9]


def _zeros(h, w):
  return [[0] * w for _ in range(h)]


def _assemble(panels, w):
  g = []
  for i, p in enumerate(panels):
    if i:
      g.append([5] * w)
    g.extend([row[:] for row in p])
  return g


def _separators_ok(panels):
  """No panel row may look like a separator line.

  A uniform panel row is acceptable only if it is all 0 and 0 is strictly
  the most frequent colour of the input grid (so it is plain background).
  """
  counts = {}
  for p in panels:
    for row in p:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
  w = len(panels[0][0])
  counts[5] = counts.get(5, 0) + w * (len(panels) - 1)
  zero = counts.get(0, 0)
  zero_dominant = all(zero > c for k, c in counts.items() if k != 0)
  for p in panels:
    for row in p:
      if len(set(row)) == 1:
        if row[0] != 0 or not zero_dominant:
          return False
  return True


def _random_static(h, w, rows_free, banned):
  """Random static distractor cells placed in rows_free."""
  if not rows_free or random.random() < 0.5:
    return []
  choices = [c for c in _PALETTE if c not in banned]
  if not choices:
    return []
  sc = random.choice(choices)
  cells = [(r, c) for r in rows_free for c in range(w)]
  k = random.randint(1, 3)
  return [(r, c, sc) for r, c in random.sample(cells, k)]


def _bar(h, w, n, d, rows, start, length, color, static):
  L0 = length if length is not None else random.randint(d, 2 * d + 1)
  s = start if start is not None else random.randint(0, 2)
  req = s + L0 + n * d + 1
  if w is None:
    w = random.randint(req,30) if req <= 30 else 30
  if w < req or w > 30 or L0 < d:
    return None
  if rows is None:
    t = random.randint(1, min(2, h - 1))
    top = random.randint(0, h - t)
    rows = list(range(top, top + t))
  col = color if color is not None else random.choice(_PALETTE)
  if static is None:
    free = [r for r in range(h) if r not in rows]
    static = _random_static(h, w, free, {col})
  if any(r in rows or v == col for r,c,v in static):
    return None
  panels = []
  for i in range(n + 1):
    p = _zeros(h, w)
    for r, c, v in static:
      p[r][c] = v
    for r in rows:
      for c in range(s, s + L0 + i * d):
        p[r][c] = col
    panels.append(p)
  return w, panels


def _random_motif(h):
  mh = random.randint(1, h)
  m = random.randint(2, 7)
  cols = random.sample(_PALETTE, random.randint(1, 3))
  for _ in range(100):
    mot = [[random.choice(cols) if random.random() < 0.75 else 0
            for _ in range(m)] for _ in range(mh)]
    if (any(mot[0]) and any(mot[-1]) and any(row[0] for row in mot)
        and any(row[-1] for row in mot)):
      return mot
  raise RuntimeError("Could not sample edge-spanning motif")


def _slide(h, w, n, d, motif, mrow, start, static):
  mot = motif if motif is not None else _random_motif(h)
  mh, m = len(mot), len(mot[0])
  if mh > h:
    return None
  if mrow is not None and not 0 <= mrow <= h-mh:
    return None
  if mrow is None:
    mrow = random.randint(0, h - mh)
  p0 = start if start is not None else random.randint(d, d + 2)
  req = p0 + n * d + m + 1
  if w is None:
    w = random.randint(req,30) if req <= 30 else 30
  if w < req or w > 30 or p0 < d:
    return None
  used = {v for row in mot for v in row if v}
  if static is None:
    free = [r for r in range(h) if not mrow <= r < mrow + mh]
    static = _random_static(h, w, free, used)
  if any(mrow <= r < mrow+mh or v in used for r,c,v in static):
    return None
  panels = []
  for i in range(n + 1):
    p = _zeros(h, w)
    for r, c, v in static:
      p[r][c] = v
    off = p0 + i * d
    for y in range(mh):
      for x in range(m):
        if mot[y][x]:
          p[mrow + y][off + x] = mot[y][x]
    panels.append(p)
  return w, panels


def _random_tile(h):
  """0/1 tile: every column has a 1, every row has a 1, some 0 exists."""
  for _ in range(200):
    tp = random.randint(2, 5)
    cols = []
    for _ in range(tp):
      mask = [random.randint(0, 1) for _ in range(h)]
      if not any(mask):
        mask[random.randrange(h)] = 1
      cols.append(mask)
    tile = [[cols[x][y] for x in range(tp)] for y in range(h)]
    if not any(0 in c for c in cols):
      continue
    if not all(any(row) for row in tile):
      continue
    return tile
  return None


def _stair(h, w, n, d, tile, b, k, start):
  if tile is None:
    tile = _random_tile(h)
    if tile is None:
      return None
  if len(tile) != h:
    return None
  tp = len(tile[0])
  if b is None or k is None:
    b2, k2 = random.sample(_PALETTE, 2)
    b = b if b is not None else (b2 if b2 != k else k2)
    k = k if k is not None else (k2 if k2 != b else b2)
  if b == k:
    return None
  c0 = start if start is not None else random.randint(d, d + 3)
  req = c0 + n * d + 2
  if w is None:
    w = random.randint(req,30) if req <= 30 else 30
  if w < req or w > 30 or c0 < d:
    return None
  bg = [[b if tile[y][x % tp] else 0 for x in range(w)] for y in range(h)]
  panels = []
  for i in range(n + 1):
    p = [row[:] for row in bg]
    for x in range(c0 + i * d):
      for y in range(h):
        if p[y][x] == b:
          p[y][x] = k
    panels.append(p)
  # The step must be inferable: every (base, left-neighbour) situation in the
  # predicted front must already appear in an earlier transition.
  seen = set()
  for i in range(n - 1):
    for x in range(c0 + i * d, c0 + (i + 1) * d):
      for y in range(h):
        seen.add((panels[i][y][x], panels[i][y][x - d]))
  last = panels[n - 1]
  for x in range(c0 + (n - 1) * d, c0 + n * d):
    for y in range(h):
      if last[y][x] == b and (b, last[y][x - d]) not in seen:
        return None
  return w, panels


def generate(family=None, height=None, width=None, num_panels=None,
             step=None, mirror=None, bar_rows=None, start=None, length=None,
             color=None, motif=None, motif_row=None, tile=None,
             base_color=None, stair_color=None, static=None):
  """Generate one input/output pair.

  Args:
    family: "bar", "slide" or "stair" (random if None).
    height: panel height (rows per panel).
    width: grid width.
    num_panels: number of input panels (>= 3).
    step: columns advanced per step.
    mirror: if True, the scene is mirrored left-right (movement leftward).
    bar_rows: rows covered by the bar (bar family).
    start: bar start column, motif start column, or initial staircase width.
    length: initial bar length (>= step).
    color: bar colour.
    motif: 2-D motif (list of rows, 0 = empty) for the slide family.
    motif_row: top row of the motif.
    tile: 0/1 mask (height rows) tiled horizontally as the stair background.
    base_color: background colour that gets recoloured (stair family).
    stair_color: staircase colour (stair family).
    static: list of (row, col, colour) static distractor cells.
  """
  if family not in (None,"bar","slide","stair"):
    raise ValueError("Unknown sequence family")
  if num_panels is not None and (not isinstance(num_panels,int) or not 3 <= num_panels <= 7):
    raise ValueError("num_panels must be in 3..7")
  if height is not None and (not isinstance(height,int) or not 3 <= height <= 9):
    raise ValueError("Panel height must be in 3..9")
  if width is not None and (not isinstance(width,int) or not 3 <= width <= 30):
    raise ValueError("Width must be in 3..30")
  if step is not None and (not isinstance(step,int) or not 1 <= step <= 3):
    raise ValueError("step must be in 1..3")
  if start is not None and (not isinstance(start,int) or start < 0):
    raise ValueError("start must be nonnegative")
  if length is not None and (not isinstance(length,int) or length < 1):
    raise ValueError("length must be positive")
  specific={"bar":(bar_rows,length,color),"slide":(motif,motif_row),"stair":(tile,base_color,stair_color)}
  for name,values in specific.items():
    if family != name and any(v is not None for v in values):
      raise ValueError("Family-specific controls require the matching explicit family")
  if static is not None and family not in ("bar","slide"):
    raise ValueError("Static distractors require bar or slide family")
  for colour in (color,base_color,stair_color):
    if colour is not None and colour not in _PALETTE:
      raise ValueError("Foreground colours cannot be background or separator")
  if base_color is not None and base_color == stair_color:
    raise ValueError("Stair colours must differ")
  for mask,allowed in ((tile,(0,1)),(motif,[0]+_PALETTE)):
    if mask is not None and (not mask or not mask[0] or any(len(row)!=len(mask[0]) or any(v not in allowed for v in row) for row in mask)):
      raise ValueError("Tile and motif must be valid rectangular arrays")
  if tile is not None:
    if height is not None and len(tile)!=height:
      raise ValueError("Tile height must match panel height")
    if not 3 <= len(tile) <= 9:
      raise ValueError("Tile height must be in 3..9")
  requested_h=height if height is not None else len(tile) if tile is not None else None
  ns=[num_panels] if num_panels is not None else list(range(3,8))
  ns=[n for n in ns if n*(requested_h if requested_h is not None else 3)+n-1 <= 30]
  if not ns:raise ValueError("Requested panels cannot fit within 30 rows")
  if bar_rows is not None and (height is None or not bar_rows or any(not isinstance(r,int) or not 0 <= r < height for r in bar_rows)):
    raise ValueError("bar_rows require panel height and valid row indices")
  if static is not None:
    if width is None or height is None:
      raise ValueError("Explicit static cells require width and height")
    if any(not (0 <= r < height and 0 <= c < width and v in _PALETTE) for r,c,v in static):
      raise ValueError("Static cell outside canvas or invalid colour")
  for _ in range(400):
    fam = family if family is not None else random.choice(
        ["bar", "slide", "stair"])
    n = random.choice(ns)
    hmax = (31 - n) // n
    if height is not None:
      h = height
    elif tile is not None:
      h = len(tile)
    else:
      h = 3 if random.random() < 0.5 else random.randint(3, hmax)
    if step is not None:
      d = step
    else:
      d = random.randint(1, 3 if fam == "bar" else 2)
    mir = mirror if mirror is not None else random.random() < 0.3
    if fam == "bar":
      res = _bar(h, width, n, d, bar_rows, start, length, color, static)
    elif fam == "slide":
      res = _slide(h, width, n, d, motif, motif_row, start, static)
    else:
      res = _stair(h, width, n, d, tile, base_color, stair_color, start)
    if res is None:
      continue
    w, panels = res
    if not _separators_ok(panels[:n]):
      continue
    if mir:
      panels = [[row[::-1] for row in p] for p in panels]
    return {"input": _assemble(panels[:n], w),
            "output": [row[:] for row in panels[n]]}
  raise ValueError("could not construct a valid scene")


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(family="bar", height=3, width=13, num_panels=4, step=2,
               mirror=False, bar_rows=[1], start=0, length=2, color=1,
               static=[]),
      generate(family="slide", height=3, width=13, num_panels=4, step=1,
               mirror=False, motif=[[2, 2, 3]], motif_row=1, start=1,
               static=[]),
  ]
  test = [
      generate(family="stair", height=3, width=13, num_panels=4, step=1,
               mirror=False,
               tile=[[0, 0, 1, 0], [0, 1, 1, 1], [1, 1, 1, 1]],
               base_color=2, stair_color=3, start=2),
  ]
  return {"train": train, "test": test}
