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

"""ARC task 3e6067c3: follow a colour legend through a grid of framed boxes.

Rule: the input holds identical square framed boxes on a grid of row bands
and column bands. Each box has a centred square core, and the core colour is
the box's label. A legend row near the bottom lists colours as isolated cells
in columns 1, 3, 5, ... The legend spells a path through the boxes. Each step
goes to an unused box with the next legend colour. That box must lie in the
same row band or column band, with no other box in between. For each
consecutive pair (A, B), the background gap between the two frames is filled
with A's colour. The fill is as wide as the core and lines up with A's core.

Scope (random mode): the generator samples the background and frame colours.
It samples box/core sizes, by default from (3/1, 4/2, 5/1, 5/3, 6/2). The
caller may request any valid size/core pair with size <= 12. It also samples
a slot lattice of 2..4 by 2..4, limited by what fits in 30x30, with uneven
gaps and some empty slots, plus a random self-avoiding path. A step may skip
over empty slots, and each empty slot is crossed at most once, so bridges
never overlap. Up to two unvisited distractor boxes may be added. Labels
repeat often. The colour assignment is always chosen so that exactly one box
path spells the legend. The output is drawn from the latent path.

The optional random-mode controls are width, height, bg, frame, size and core. Explicit mode
requires every latent argument: width, height, bg, frame, size, core, rows,
cols, boxes and path. Partial layout arguments raise ValueError. They are
never silently ignored.
"""

import random

import common

PALETTE = list(range(10))
SHAPES = [(3, 1), (4, 2), (5, 1), (5, 3), (6, 2)]
GAPS = [1, 1, 2, 2, 3, 4]


def _between(a, b):
  """Slots strictly between two slots on one lattice line, or None."""
  (r1, c1), (r2, c2) = a, b
  if r1 == r2 and c1 != c2:
    lo, hi = sorted((c1, c2))
    return [(r1, c) for c in range(lo + 1, hi)]
  if c1 == c2 and r1 != r2:
    lo, hi = sorted((r1, r2))
    return [(r, c1) for r in range(lo + 1, hi)]
  return None


def _linked(a, b, occ):
  s = _between(a, b)
  return s is not None and not any(x in occ for x in s)


def _neighbors(slot, occ, nrows, ncols):
  """Nearest occupied slot in each direction, with the empty slots crossed."""
  res = []
  r, c = slot
  for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    crossed = []
    y, x = r + dr, c + dc
    while 0 <= y < nrows and 0 <= x < ncols:
      if (y, x) in occ:
        res.append(((y, x), crossed))
        break
      crossed.append((y, x))
      y, x = y + dr, x + dc
  return res


def _count_paths(colours, seq, limit=2):
  """Number of box paths (capped at limit) whose labels spell seq."""
  occ = set(colours)
  count = [0]

  def dfs(cur, used, i):
    if count[0] >= limit:
      return
    if i == len(seq):
      count[0] += 1
      return
    for k in occ:
      if k not in used and colours[k] == seq[i] and _linked(cur, k, occ):
        used.add(k)
        dfs(k, used, i + 1)
        used.discard(k)

  for s in occ:
    if colours[s] == seq[0]:
      dfs(s, {s}, 1)
  return count[0]


def _render(width, height, bg, frame, size, core, rows, cols, boxes, path):
  g = common.grid(width, height, bg)
  off = (size - core) // 2
  colour = {}
  for r, c, col in boxes:
    y0, x0 = rows[r], cols[c]
    for y in range(size):
      for x in range(size):
        g[y0 + y][x0 + x] = frame
    for y in range(core):
      for x in range(core):
        g[y0 + off + y][x0 + off + x] = col
    colour[(r, c)] = col
  ly = height - 2
  for i, s in enumerate(path):
    g[ly][1 + 2 * i] = colour[s]
  out = [row[:] for row in g]
  for a, b in zip(path, path[1:]):
    col = colour[a]
    (ra, ca), (rb, cb) = a, b
    if ra == rb:
      lo_c, hi_c = min(ca, cb), max(ca, cb)
      x_lo, x_hi = cols[lo_c] + size, cols[hi_c] - 1
      y0 = rows[ra] + off
      for y in range(y0, y0 + core):
        for x in range(x_lo, x_hi + 1):
          out[y][x] = col
    else:
      lo_r, hi_r = min(ra, rb), max(ra, rb)
      y_lo, y_hi = rows[lo_r] + size, rows[hi_r] - 1
      x0 = cols[ca] + off
      for y in range(y_lo, y_hi + 1):
        for x in range(x0, x0 + core):
          out[y][x] = col
  return {"input": g, "output": out}


def _shape_options(size, core):
  """Valid (box size, core size) pairs compatible with the requested ones."""
  if size is None and core is None:
    return list(SHAPES)
  if size is not None and core is not None:
    cand = [(size, core)]
  elif size is not None:
    cand = [(size, c) for c in range(1, size - 1)]
  else:
    cand = [(s, core) for s in range(core + 2, 13)]
  good = []
  for s, c in cand:
    if c < 1 or s - c < 2 or (s - c) % 2 or s > 12:
      continue
    if s * s - c * c <= c * c:  # frame must outnumber any core colour
      continue
    good.append((s, c))
  if not good:
    raise ValueError("no valid box/core size for the requested size/core")
  return good


def _max_bands(size, start, tail, bound=30):
  """Largest band count (<= 4) that fits in 30 cells with 1-cell gaps."""
  best = 1
  for n in range(2, 5):
    if start + n * size + (n - 1) + tail <= bound:
      best = n
  return best


def _sample(bg_req, frame_req, size_req, core_req, width_req=None, height_req=None):
  for v in (bg_req, frame_req):
    if v is not None and v not in PALETTE:
      raise ValueError("colour out of range")
  if bg_req is not None and bg_req == frame_req:
    raise ValueError("bg and frame must differ")
  shapes = _shape_options(size_req, core_req)
  for d in (width_req, height_req):
    if d is not None and (not isinstance(d, int) or not 1 <= d <= 30):
      raise ValueError("dimensions must be integers in 1..30")
  maxh = 30 if height_req is None else height_req
  maxw = 30 if width_req is None else width_req
  shapes = [(s, c) for s, c in shapes if 2 * s + 5 <= maxh and
            max(2 * s + 3, 9) <= maxw]
  if not shapes:
    raise ValueError("dimensions cannot fit four boxes and the legend")
  for _ in range(1000):
    if bg_req is not None:
      bg = bg_req
    else:
      bg = random.choice([c for c in PALETTE if c != frame_req])
    if frame_req is not None:
      frame = frame_req
    else:
      frame = random.choice([c for c in PALETTE if c != bg])
    labels = [c for c in PALETTE if c not in (bg, frame)]
    size, core = random.choice(shapes)
    top, left = random.choice([1, 1, 2]), random.choice([1, 1, 2])
    mr = _max_bands(size, top, 3, maxh)
    mc = _max_bands(size, left, 1, maxw)
    if mr < 2 or mc < 2:
      continue
    nr, nc = random.randint(2, mr), random.randint(2, mc)
    rgaps = [random.choice(GAPS) for _ in range(nr - 1)]
    cgaps = [random.choice(GAPS) for _ in range(nc - 1)]
    rows, y = [], top
    for i in range(nr):
      rows.append(y)
      y += size + (rgaps[i] if i < nr - 1 else 0)
    cols, x = [], left
    for i in range(nc):
      cols.append(x)
      x += size + (cgaps[i] if i < nc - 1 else 0)
    height = y + random.randint(1, 4) + 2 if height_req is None else height_req
    if y + 3 > height or height > maxh or x + 1 > maxw:
      continue
    slots = [(r, c) for r in range(nr) for c in range(nc)]
    occ = set(slots)
    for s in random.sample(slots, random.randint(0, len(slots) // 4)):
      occ.discard(s)
    if len(occ) < 4:
      continue
    n = len(occ)
    target = random.randint(max(4, n - 2), n)
    best = None
    for _ in range(60):
      path = [random.choice(sorted(occ))]
      used_empty = set()
      while len(path) < target:
        opts = [(nb, cr) for nb, cr in _neighbors(path[-1], occ, nr, nc)
                if nb not in path and not any(e in used_empty for e in cr)]
        if not opts:
          break
        nb, cr = random.choice(opts)
        path.append(nb)
        used_empty.update(cr)
      if best is None or len(path) > len(best):
        best = path
      if len(best) >= target:
        break
    path = best
    if len(path) < 4 or 2 * len(path) + 1 > maxw:
      continue
    leftover = sorted(occ - set(path))
    kept = random.sample(leftover, random.randint(0, min(2, len(leftover))))
    final = list(path) + kept
    m = len(final)
    width = (max(x + random.randint(1, 4),
                 2 * len(path) + 1 + random.randint(0, 2))
             if width_req is None else width_req)
    if width > maxw:
      continue
    colours = None
    for _ in range(300):
      p = random.randint(max(3, (m + 1) // 2), min(len(labels), m))
      pal = random.sample(labels, p)
      cand = {s: random.choice(pal) for s in final}
      seq = [cand[s] for s in path]
      if _count_paths(cand, seq) == 1:
        colours = cand
        break
    if colours is None:
      continue
    boxes = [(r, c, colours[(r, c)]) for (r, c) in final]
    pair = _render(width, height, bg, frame, size, core, rows, cols, boxes,
                   path)
    counts = {}
    for row in pair["input"]:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    if any(v != bg and counts[v] >= counts[bg] for v in counts):
      continue
    return pair
  raise RuntimeError("could not sample a valid scene")


def generate(width=None, height=None, bg=None, frame=None, size=None,
             core=None, rows=None, cols=None, boxes=None, path=None):
  """Builds one input/output pair.

  Args:
    width, height: exact grid dimensions, optionally sampled when omitted.
    bg: background colour (random-mode control or explicit value).
    frame: frame colour shared by all boxes (random-mode control or explicit).
    size: box side length (random-mode control or explicit value).
    core: core side length, centred inside each box (control or explicit).
    rows: top row of each lattice row band (explicit mode only).
    cols: left column of each lattice column band (explicit mode only).
    boxes: list of (row_index, col_index, label_colour); explicit mode.
    path: ordered list of (row_index, col_index) slots. The legend is the
      labels along it (explicit mode).
  If boxes is None, a fresh random scene is sampled, honouring bg, frame,
  size, core and dimensions when given. In that case, passing rows, cols
  or path is rejected.
  """
  if boxes is None:
    if any(v is not None for v in (rows, cols, path)):
      raise ValueError("layout arguments require explicit boxes; random mode "
                       "only accepts dimensions, bg, frame, size, core")
    return _sample(bg, frame, size, core, width, height)
  if any(v is None for v in (width, height, bg, frame, size, core, rows,
                             cols, path)):
    raise ValueError("explicit mode requires all latent arguments")
  _shape_options(size, core)
  if not (1 <= width <= 30 and 1 <= height <= 30 and
          bg in PALETTE and frame in PALETTE and bg != frame):
    raise ValueError("invalid dimensions or palette")
  if (not rows or not cols or rows[0] < 0 or cols[0] < 0 or
      rows[-1] + size >= height - 2 or cols[-1] + size > width or
      any(b <= a + size for a, b in zip(rows, rows[1:])) or
      any(b <= a + size for a, b in zip(cols, cols[1:]))):
    raise ValueError("box bands overlap, exceed grid or touch legend")
  colours = {}
  for r, c, colour in boxes:
    if (not 0 <= r < len(rows) or not 0 <= c < len(cols) or
        colour not in PALETTE or colour in (bg, frame) or (r, c) in colours):
      raise ValueError("invalid or duplicate box")
    colours[r, c] = colour
  path = [tuple(s) for s in path]
  if (len(path) < 2 or len(set(path)) != len(path) or
      2 * len(path) > width or any(s not in colours for s in path) or
      any(not _linked(a, b, set(colours)) for a, b in zip(path, path[1:]))):
    raise ValueError("invalid path or legend")
  if _count_paths(colours, [colours[s] for s in path]) != 1:
    raise ValueError("legend does not identify a unique path")
  crossed = set()
  for a, b in zip(path, path[1:]):
    gap = set(_between(a, b))
    if gap & crossed:
      raise ValueError("bridges cross an empty slot twice")
    crossed.update(gap)
  return _render(width, height, bg, frame, size, core, rows, cols, boxes, path)


def validate():
  """Reconstructs the canonical fixtures through explicit latent arguments."""
  train = [
      generate(20, 20, 8, 1, 4, 2, [1, 8, 13], [1, 7, 14],
               [(0, 0, 2), (0, 1, 5), (0, 2, 7), (1, 0, 3), (1, 1, 9),
                (1, 2, 6), (2, 1, 4), (2, 2, 2)],
               [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (1, 2), (0, 2),
                (0, 1)]),
      generate(20, 13, 8, 1, 3, 1, [1, 5], [1, 5, 9, 13],
               [(0, 0, 2), (0, 1, 3), (0, 2, 5), (0, 3, 7), (1, 0, 7),
                (1, 1, 4), (1, 2, 6), (1, 3, 9)],
               [(0, 0), (0, 1), (1, 1), (1, 2), (0, 2), (0, 3), (1, 3)]),
      generate(27, 27, 8, 1, 5, 1, [1, 7, 17], [1, 9, 17],
               [(0, 0, 3), (0, 1, 2), (0, 2, 9), (1, 1, 6), (1, 2, 4),
                (2, 1, 7)],
               [(0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (2, 1)]),
  ]
  test = [
      generate(29, 29, 1, 2, 5, 1, [1, 8, 15, 21], [1, 8, 14, 20],
               [(0, 0, 4), (0, 1, 8), (0, 3, 9), (1, 0, 6), (1, 1, 7),
                (1, 3, 4), (2, 0, 9), (2, 1, 4), (2, 2, 5), (2, 3, 3),
                (3, 3, 7)],
               [(0, 0), (0, 1), (0, 3), (1, 3), (1, 1), (1, 0), (2, 0),
                (2, 1), (2, 2), (2, 3), (3, 3)]),
      generate(30, 30, 1, 8, 6, 2, [1, 9, 16], [1, 10, 20],
               [(0, 0, 2), (0, 1, 4), (0, 2, 3), (1, 0, 3), (1, 1, 6),
                (1, 2, 9), (2, 0, 9), (2, 1, 4), (2, 2, 5)],
               [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (1, 1),
                (1, 0), (2, 0)]),
  ]
  return {"train": train, "test": test}
