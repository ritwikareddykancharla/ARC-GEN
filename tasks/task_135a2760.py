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

"""Repair of damaged periodic strips inside rectangular frames (ARC 135a2760).

Every panel is a one-cell-thick rectangular frame drawn on a uniform
background.  Inside each frame lies a strip whose content repeats with a
short period along the strip's long axis, except for a few corrupted cells.
The output keeps background and frames unchanged and rewrites every strip
cleanly from its periodic tile, which removes the stray cells.

Scope: 1-4 panels sharing one periodic length (8-26), strips horizontal or
vertical, strip width 1-4 (per panel), periods 2-6 drawn from stripe,
shifted-stripe, block, diagonal sweep, zigzag and random tile families, one
or two pattern colours plus the background colour, and 1-6 corrupted cells
per panel (isolated spots or a shifted segment as in train 2).  Every
corruption occupies its own period class, each class has at least three
repeats, and the true period is the unique minimiser of the majority
mismatch count (ties only with its own multiples), so the repair is
unambiguous.  Corruptions never use the frame colour and no pattern
component forms a hollow ring, so frames are the only ring objects.
"""

import random

import common


def _tile_min_period(tile):
  """Smallest cyclic period of the tile along its first axis."""
  p = len(tile)
  for d in range(1, p):
    if p % d == 0 and all(tile[i] == tile[(i + d) % p] for i in range(p)):
      return d
  return p


def _majority(strip, p):
  """Majority tile of a strip under period p and the number of dissenters."""
  length, width = len(strip), len(strip[0])
  tile = [[0] * width for _ in range(p)]
  mismatch = 0
  for r in range(p):
    for j in range(width):
      counts = {}
      n = 0
      for i in range(r, length, p):
        v = strip[i][j]
        counts[v] = counts.get(v, 0) + 1
        n += 1
      best = max(counts.values())
      tile[r][j] = [v for v in counts if counts[v] == best][0]
      mismatch += n - best
  return tile, mismatch


def _unambiguous(strip, tile, k):
  """True when the true period is the unique best explanation of the strip."""
  p = len(tile)
  length = len(strip)
  maj, mm = _majority(strip, p)
  if maj != tile or mm != k:
    return False
  for q in range(1, length // 2 + 1):
    if q == p:
      continue
    mq = _majority(strip, q)[1]
    if (q < p and mq <= k) or (q > p and mq < k):
      return False
  return True


def _sample_tile(w, bg, colours, pmax):
  """Samples a p x w tile with minimal period p <= pmax, or None."""
  fams = ["stripe", "stripe", "shifted", "blocks", "random"]
  if 2 <= w <= pmax:
    fams.append("sweep")
  if w >= 3 and 2 * (w - 1) <= pmax:
    fams += ["zigzag", "zigzag"]
  fam = random.choice(fams)
  c = colours[0]
  palette = [bg] + list(colours)
  if fam == "sweep":
    p = w
    tile = [[c if j == i else bg for j in range(w)] for i in range(p)]
  elif fam == "zigzag":
    p = 2 * (w - 1)
    tile = []
    for i in range(p):
      pos = i if i < w else p - i
      tile.append([c if j == pos else bg for j in range(w)])
  elif fam == "random":
    p = random.randint(2, min(5, pmax))
    tile = [[random.choice(palette) for _ in range(w)] for _ in range(p)]
  else:
    p = random.randint(2, min(6, pmax))
    seq = [random.choice(palette) for _ in range(p)]
    if fam == "stripe":
      tile = [[seq[i] for _ in range(w)] for i in range(p)]
    elif fam == "shifted":
      s = random.randint(1, p - 1)
      tile = [[seq[(i + s * j) % p] for j in range(w)] for i in range(p)]
    else:
      cols = [j for j in range(w) if random.random() < 0.6]
      if not cols:
        cols = [random.randrange(w)]
      tile = [[seq[i] if j in cols else bg for j in range(w)]
              for i in range(p)]
  if _tile_min_period(tile) != p:
    return None
  if all(v == bg for row in tile for v in row):
    return None
  return tile


def _sample_corruptions(tile, length, palette):
  """Samples corrupted cells (i, j, colour), one per period class."""
  p, w = len(tile), len(tile[0])
  if p >= 3 and random.random() < 0.3:
    m = random.randint(2, p - 1)
    start = random.randint(0, length - m)
    d = random.choice([-1, 1])
    cells = []
    for i in range(start, start + m):
      for j in range(w):
        v = tile[(i + d) % p][j]
        if v != tile[i % p][j]:
          cells.append((i, j, v))
    if 1 <= len(cells) <= 6:
      return cells
  k = random.choice([1, 1, 2, 2, 3, 4])
  classes = random.sample([(r, j) for r in range(p) for j in range(w)],
                          min(k, p * w))
  cells = []
  for r, j in classes:
    i = random.choice(range(r, length, p))
    true = tile[r][j]
    colour = random.choice([c for c in palette if c != true])
    cells.append((i, j, colour))
  return cells


def _sample_panel(length, w, bg, colours):
  """Samples one panel (tile + corruptions) whose repair is unambiguous."""
  pmax = min(6, length // 3)
  palette = [bg] + list(colours)
  for _ in range(60):
    tile = _sample_tile(w, bg, colours, pmax)
    if tile is None:
      continue
    corr = _sample_corruptions(tile, length, palette)
    p = len(tile)
    strip = [[tile[i % p][j] for j in range(w)] for i in range(length)]
    for i, j, c in corr:
      strip[i][j] = c
    if _unambiguous(strip, tile, len(corr)):
      return {"tile": tile, "corruptions": corr}
  return None


def _sample_panels(length, bg, fc, margin, gap):
  """Samples the panel list for a scene, or None on failure."""
  n = random.choice([1, 2, 2, 3, 3, 4, 4])
  while True:
    avail = 30 - 2 * margin - gap * (n - 1) - 2 * n
    if avail >= n or n == 1:
      break
    n -= 1
  if avail < 1:
    return None
  max_w = min(4, avail // n)
  if random.random() < 0.7:
    widths = [random.randint(1, max_w)] * n
  else:
    widths = [random.randint(1, max_w) for _ in range(n)]
  colours = random.sample([c for c in range(10) if c not in (bg, fc)], n)
  panels = []
  for w, c in zip(widths, colours):
    cols = [c]
    if random.random() < 0.2:
      cols.append(random.choice([x for x in range(10)
                                 if x not in (bg, fc, c)]))
    pn = _sample_panel(length, w, bg, cols)
    if pn is None:
      return None
    panels.append(pn)
  return panels


def _build(bg, fc, vertical, margin, gap, length, panels):
  """Draws input and output grids from the latent scene description."""
  widths = [len(pn["tile"][0]) for pn in panels]
  across = 2 * margin + sum(w + 2 for w in widths) + gap * (len(panels) - 1)
  along = 2 * margin + length + 2
  if vertical:
    width, height = across, along
  else:
    width, height = along, across
  inp = common.grid(width, height, bg)
  out = common.grid(width, height, bg)
  pos = margin
  for pn, w in zip(panels, widths):
    tile = pn["tile"]
    p = len(tile)
    clean = [[tile[i % p][j] for j in range(w)] for i in range(length)]
    dirty = [row[:] for row in clean]
    for i, j, c in pn["corruptions"]:
      dirty[i][j] = c
    if vertical:
      y0, x0, y1, x1 = margin, pos, margin + length + 1, pos + w + 1
    else:
      y0, x0, y1, x1 = pos, margin, pos + w + 1, margin + length + 1
    for g in (inp, out):
      for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
          if y in (y0, y1) or x in (x0, x1):
            g[y][x] = fc
    for i in range(length):
      for j in range(w):
        if vertical:
          y, x = y0 + 1 + i, x0 + 1 + j
        else:
          y, x = y0 + 1 + j, x0 + 1 + i
        inp[y][x] = dirty[i][j]
        out[y][x] = clean[i][j]
    pos += w + 2 + gap
  return inp, out


def _has_stray_ring(grid, skip):
  """True if some 4-connected same-colour component (colour not in skip)
  is exactly the border of a bounding box of at least 3 x 3."""
  h, w = len(grid), len(grid[0])
  seen = [[False] * w for _ in range(h)]
  for y in range(h):
    for x in range(w):
      c = grid[y][x]
      if seen[y][x] or c in skip:
        continue
      seen[y][x] = True
      stack = [(y, x)]
      cells = []
      while stack:
        cy, cx = stack.pop()
        cells.append((cy, cx))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          ny, nx = cy + dy, cx + dx
          if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] \
              and grid[ny][nx] == c:
            seen[ny][nx] = True
            stack.append((ny, nx))
      ys = [q[0] for q in cells]
      xs = [q[1] for q in cells]
      y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
      if y1 - y0 >= 2 and x1 - x0 >= 2:
        border = {(yy, xx) for yy in range(y0, y1 + 1)
                  for xx in range(x0, x1 + 1)
                  if yy in (y0, y1) or xx in (x0, x1)}
        if set(cells) == border:
          return True
  return False


def _scene_ok(inp, out, bg, fc):
  """Background must be the strict majority and only frames may be rings."""
  counts = {}
  for row in inp:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  for v, n in counts.items():
    if v != bg and n >= counts.get(bg, 0):
      return False
  for g in (inp, out):
    if _has_stray_ring(g, (bg, fc)):
      return False
  return True


def generate(background=None, frame_colour=None, vertical=None, margin=None,
             gap=None, length=None, panels=None):
  """Returns input and output grids according to the given parameters.

  Args:
    background: the background colour.
    frame_colour: the colour of every panel frame.
    vertical: True when strips run vertically (panels side by side), False
        when they run horizontally (panels stacked).
    margin: background cells between the frames and the grid edge.
    gap: background cells between neighbouring panels.
    length: number of interior cells along the periodic axis of every panel.
    panels: list of dicts {"tile": p x w list of rows (first index runs along
        the periodic axis), "corruptions": list of (i, j, colour)} describing
        each panel in reading order.  When None, the whole scene is sampled.
  """
  explicit = panels is not None
  for _ in range(200):
    bg = background if background is not None else random.randint(0, 9)
    fc = frame_colour if frame_colour is not None else random.choice(
        [c for c in range(10) if c != bg])
    vert = vertical if vertical is not None else random.random() < 0.5
    mg = margin if margin is not None else random.choice([1, 1, 1, 2])
    gp = gap if gap is not None else random.choice([1, 1, 2])
    if explicit:
      pans = panels
      lng = length
    else:
      lng = length if length is not None else random.randint(8, 28 - 2 * mg)
      pans = _sample_panels(lng, bg, fc, mg, gp)
      if pans is None:
        continue
    inp, out = _build(bg, fc, vert, mg, gp, lng, pans)
    if explicit or _scene_ok(inp, out, bg, fc):
      return {"input": inp, "output": out}
  raise RuntimeError("failed to sample a valid scene")


def validate():
  """Validates the generator against the canonical fixtures."""
  train = [
      generate(background=3, frame_colour=2, vertical=False, margin=1, gap=1,
               length=9,
               panels=[{"tile": [[1], [3]], "corruptions": [(6, 0, 3)]}]),
      generate(background=4, frame_colour=2, vertical=False, margin=1, gap=1,
               length=18,
               panels=[
                   {"tile": [[3, 3], [3, 3], [4, 4]],
                    "corruptions": [(15, 0, 4), (17, 0, 3), (15, 1, 4),
                                    (17, 1, 3)]},
                   {"tile": [[1, 4], [4, 1]], "corruptions": [(7, 0, 1)]},
                   {"tile": [[8, 8], [4, 8], [8, 8], [8, 4]],
                    "corruptions": [(2, 0, 4), (2, 1, 4)]},
                   {"tile": [[9, 9], [4, 4]],
                    "corruptions": [(17, 0, 9), (7, 1, 9)]},
               ]),
  ]
  test = [
      generate(background=8, frame_colour=3, vertical=True, margin=1, gap=1,
               length=25,
               panels=[
                   {"tile": [[8, 8, 8, 8], [8, 2, 2, 8], [8, 2, 2, 8]],
                    "corruptions": [(22, 1, 8)]},
                   {"tile": [[1, 8, 8, 8], [8, 1, 8, 8], [8, 8, 1, 8],
                             [8, 8, 8, 1], [8, 8, 1, 8], [8, 1, 8, 8]],
                    "corruptions": [(10, 0, 1), (21, 2, 1), (21, 3, 8)]},
                   {"tile": [[4, 8, 8, 8], [4, 4, 4, 4], [8, 8, 8, 4],
                             [4, 4, 4, 4]],
                    "corruptions": [(0, 1, 4), (11, 1, 8), (21, 1, 8)]},
                   {"tile": [[8, 8, 8, 8], [8, 9, 8, 8], [8, 9, 9, 8],
                             [8, 9, 8, 8]],
                    "corruptions": [(1, 1, 8), (23, 2, 9)]},
               ]),
  ]
  return {"train": train, "test": test}
