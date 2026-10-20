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

"""ARC task 13e47133: concentric ring fill of divider regions.

Rule: a background grid is cut into regions by axis-aligned divider lines of
one colour (straight lines, T-junctions, and hollow boxes that may be flush
with a wall). Inside some regions, a short chain of single cells sits on a
diagonal. The chain starts at a corner of the region and steps inward one cell
at a time. The first chain cell may be background. In the output each such
region is filled with concentric rings. The ring number of a cell is its
Chebyshev distance to anything outside the region (divider or grid edge). The
cell gets colour chain[(ring - 1) % len(chain)]. The divider and regions
without a chain are unchanged.

Scope: random grids are 10..30 per side. Layouts come from guillotine splits
with optional hollow boxes, which give L-shaped and annular regions. Chains
have 1..4 coloured cells, optionally led by one background cell, on any
convex corner of a region. Background and divider colours are random. The
scene is rejected when the corner-chain reading is ambiguous.
"""

import random
from collections import deque

import common

_DIRS8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)]


def _draw(H, W, bg, div, segments):
  g = common.grid(W, H, bg)
  for (r0, c0, r1, c1) in segments:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        g[r][c] = div
  return g


def _regions(g, div):
  H, W = len(g), len(g[0])
  label = [[-1] * W for _ in range(H)]
  regions = []
  for sy in range(H):
    for sx in range(W):
      if g[sy][sx] == div or label[sy][sx] >= 0:
        continue
      idx = len(regions)
      cells = []
      label[sy][sx] = idx
      dq = deque([(sy, sx)])
      while dq:
        y, x = dq.popleft()
        cells.append((y, x))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
          ny, nx = y + dy, x + dx
          if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != div and label[ny][nx] < 0:
            label[ny][nx] = idx
            dq.append((ny, nx))
      regions.append(cells)
  return regions, label


def _rings(cells):
  """Chebyshev distance of each cell to the complement of the region."""
  cs = set(cells)
  dist = {}
  dq = deque()
  for (y, x) in cells:
    if any((y + a, x + b) not in cs for a, b in _DIRS8):
      dist[(y, x)] = 1
      dq.append((y, x))
  while dq:
    y, x = dq.popleft()
    for a, b in _DIRS8:
      nb = (y + a, x + b)
      if nb in cs and nb not in dist:
        dist[nb] = dist[(y, x)] + 1
        dq.append(nb)
  return dist


def _corners(cs):
  out = []
  for (y, x) in sorted(cs):
    for dy in (-1, 1):
      for dx in (-1, 1):
        if ((y + dy, x) not in cs and (y, x + dx) not in cs and
            (y + dy, x + dx) not in cs):
          out.append((y, x, -dy, -dx))
  return out


def _fits(cs, dist, y, x, dy, dx, length):
  for i in range(length):
    c = (y + i * dy, x + i * dx)
    if c not in cs or dist[c] != i + 1:
      return False
  return True


def _place(g, y, x, dy, dx, colours):
  for i, col in enumerate(colours):
    g[y + i * dy][x + i * dx] = col


def _chain_ok(g, cs, bg, chain):
  """All maximal corner-anchored diagonal readings must equal the chain."""
  seeds = [c for c in cs if g[c[0]][c[1]] != bg]
  best_n, seqs = -1, set()
  for (sy, sx) in seeds:
    for dy in (-1, 1):
      for dx in (-1, 1):
        y, x = sy, sx
        while (y + dy, x + dx) in cs:
          y += dy
          x += dx
        if (y + dy, x) in cs or (y, x + dx) in cs:
          continue
        seq = []
        y2, x2 = y, x
        while (y2, x2) in cs:
          seq.append(g[y2][x2])
          y2 -= dy
          x2 -= dx
        idx = [i for i, v in enumerate(seq) if v != bg]
        if not idx:
          continue
        seq = tuple(seq[:idx[-1] + 1])
        n = len(idx)
        if n > best_n:
          best_n, seqs = n, {seq}
        elif n == best_n:
          seqs.add(seq)
  return seqs == {tuple(chain)}


def _random_layout(H, W):
  segs = []
  leaves = [(0, 0, H - 1, W - 1)]
  for _ in range(random.randint(1, 4)):
    opts = []
    for i, (r0, c0, r1, c1) in enumerate(leaves):
      if r1 - r0 + 1 >= 7:
        opts.append((i, "h"))
      if c1 - c0 + 1 >= 7:
        opts.append((i, "v"))
    if not opts:
      break
    i, o = random.choice(opts)
    r0, c0, r1, c1 = leaves.pop(i)
    if o == "h":
      p = random.randint(r0 + 3, r1 - 3)
      segs.append((p, c0, p, c1))
      leaves += [(r0, c0, p - 1, c1), (p + 1, c0, r1, c1)]
    else:
      p = random.randint(c0 + 3, c1 - 3)
      segs.append((r0, p, r1, p))
      leaves += [(r0, c0, r1, p - 1), (r0, p + 1, r1, c1)]

  def span(a, b):
    for _ in range(30):
      lo = a - 1 if random.random() < 0.35 else random.randint(a + 2, b)
      hi = b + 1 if random.random() < 0.35 else random.randint(a, b - 2)
      if hi - lo >= 3 and not (lo == a - 1 and hi == b + 1):
        return lo, hi
    return None

  for _ in range(random.choice([0, 0, 1, 1, 2])):
    opts = [i for i, (r0, c0, r1, c1) in enumerate(leaves)
            if r1 - r0 + 1 >= 6 and c1 - c0 + 1 >= 6]
    if not opts:
      break
    i = random.choice(opts)
    r0, c0, r1, c1 = leaves.pop(i)
    rs, cs_ = span(r0, r1), span(c0, c1)
    if rs is None or cs_ is None:
      continue
    lo, hi = rs
    clo, chi = cs_
    ca, cb = max(clo, c0), min(chi, c1)
    ra, rb = max(lo, r0), min(hi, r1)
    if lo >= r0:
      segs.append((lo, ca, lo, cb))
    if hi <= r1:
      segs.append((hi, ca, hi, cb))
    if clo >= c0:
      segs.append((ra, clo, rb, clo))
    if chi <= c1:
      segs.append((ra, chi, rb, chi))
  return segs


def _render(H, W, bg, div, segments, chains):
  g = _draw(H, W, bg, div, segments)
  for (y, x, dy, dx, colours) in chains:
    _place(g, y, x, dy, dx, colours)
  regions, label = _regions(g, div)
  out = [row[:] for row in g]
  for (y, x, dy, dx, colours) in chains:
    cells = regions[label[y][x]]
    dist = _rings(cells)
    for (cy, cx) in cells:
      out[cy][cx] = colours[(dist[(cy, cx)] - 1) % len(colours)]
  return g, out


def _random_scene(height, width, background, divider):
  for _ in range(300):
    H = height if height is not None else random.randint(10, 30)
    W = width if width is not None else random.randint(10, 30)
    bg = background if background is not None else random.choice([c for c in range(10) if c != divider])
    div = divider if divider is not None else random.choice(
        [c for c in range(10) if c != bg])
    segs = _random_layout(H, W)
    if not segs:
      continue
    g = _draw(H, W, bg, div, segs)
    regions, _ = _regions(g, div)
    if len(regions) < 2:
      continue
    pool = [c for c in range(10) if c not in (bg, div)]
    chains = []
    for cells in regions:
      if random.random() > 0.8:
        continue
      cs = set(cells)
      dist = _rings(cells)
      corners = _corners(cs)
      random.shuffle(corners)
      k = random.choice([1, 2, 2, 3, 3, 4])
      lead = random.random() < 0.25
      placed = None
      while k >= 1 and placed is None:
        chain = ([bg] if lead else []) + random.sample(pool, k)
        for (y, x, dy, dx) in corners:
          if not _fits(cs, dist, y, x, dy, dx, len(chain)):
            continue
          _place(g, y, x, dy, dx, chain)
          if _chain_ok(g, cs, bg, chain):
            placed = (y, x, dy, dx, chain)
            break
          _place(g, y, x, dy, dx, [bg] * len(chain))
        k -= 1
      if placed:
        chains.append(placed)
    if not chains:
      continue
    counts = [0] * 10
    for row in g:
      for v in row:
        counts[v] += 1
    if any(counts[c] >= counts[bg] for c in range(10) if c != bg):
      continue
    inp, out = _render(H, W, bg, div, segs, chains)
    if inp == out:
      continue
    return H, W, bg, div, segs, chains
  raise RuntimeError('no unambiguous ring scene found for requested parameters')


def generate(height=None, width=None, background=None, divider=None,
             segments=None, chains=None):
  """Build one input/output pair.

  Args:
    height: grid rows (random 10..30 if None).
    width: grid columns (random 10..30 if None).
    background: background colour (random if None).
    divider: divider line colour (random, different from background, if None).
    segments: explicit divider lines as (r0, c0, r1, c1) inclusive rectangles.
      If None, a random layout and random chains are sampled.
    chains: explicit chains as (y, x, dy, dx, colours). (y, x) is the region
      corner and (dy, dx) is the inward diagonal step. colours is the ring
      colour sequence, which may start with the background colour.
  """
  if background is not None and background not in range(10):
    raise ValueError('background must be 0..9')
  if divider is not None and divider not in range(10):
    raise ValueError('divider must be 0..9')
  if background is not None and background == divider:
    raise ValueError('background and divider must differ')
  if segments is None:
    if chains is not None:
      raise ValueError('explicit chains require explicit segments')
    if any(v is not None and not 10 <= v <= 30 for v in (height, width)):
      raise ValueError('random canvas dimensions must be 10..30')
    H, W, bg, div, segs, chs = _random_scene(height, width, background, divider)
  else:
    H, W, bg, div = height, width, background, divider
    segs, chs = segments, (chains or [])
  inp, out = _render(H, W, bg, div, segs, chs)
  return {"input": inp, "output": out}


def validate():
  """Reconstruct the canonical train/test pairs from latent parameters."""
  train = [
      generate(20, 20, 1, 2,
               [(0, 8, 19, 8), (9, 8, 9, 16), (15, 8, 15, 16), (9, 16, 15, 16)],
               [(0, 0, 1, 1, [7, 8]), (0, 19, 1, -1, [8, 4]),
                (10, 15, 1, -1, [3])]),
      generate(20, 20, 4, 2,
               [(0, 10, 19, 10), (12, 10, 12, 19)],
               [(0, 0, 1, 1, [4, 3]), (0, 11, 1, 1, [8, 1]),
                (13, 11, 1, 1, [5, 0, 1])]),
      generate(10, 13, 8, 6,
               [(0, 6, 9, 6), (6, 6, 6, 12)],
               [(0, 0, 1, 1, [9, 1]), (0, 12, 1, -1, [7])]),
  ]
  test = [
      generate(30, 30, 3, 8,
               [(0, 11, 25, 11), (25, 6, 25, 19), (26, 6, 29, 6),
                (26, 19, 29, 19), (0, 20, 7, 20), (7, 17, 7, 23),
                (14, 17, 14, 23), (8, 17, 13, 17), (8, 23, 13, 23),
                (10, 24, 10, 29)],
               [(0, 0, 1, 1, [1, 2]), (0, 12, 1, 1, [6, 4, 5]),
                (0, 21, 1, 1, [2]), (8, 18, 1, 1, [4, 1]),
                (26, 7, 1, 1, [3, 4])]),
      generate(30, 30, 8, 1,
               [(0, 7, 29, 7), (8, 0, 8, 29), (9, 16, 15, 16),
                (15, 8, 15, 15), (23, 21, 23, 29), (24, 21, 29, 21)],
               [(0, 6, 1, -1, [4, 3]), (7, 8, -1, 1, [2, 3, 4]),
                (9, 6, 1, -1, [6, 5, 4]), (14, 15, -1, -1, [2, 7]),
                (16, 8, 1, 1, [4, 9, 2]), (24, 22, 1, 1, [9, 2])]),
  ]
  return {"train": train, "test": test}
