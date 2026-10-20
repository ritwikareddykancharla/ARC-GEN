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

"""ARC-GEN style generator for task 28a6681f (water re-pouring).

Rule: colour 1 is water; every other non-zero colour is solid terrain. All N
water cells are removed and poured back one at a time from the topmost-then-
leftmost original water cell. Each poured cell falls while the cell below is
empty. When blocked, it scans left and right along its row (stopping at a solid
or water cell or the grid edge) for the nearest cell with an empty cell below.
It moves to the nearer one (ties go left) and falls again. If neither side has
such a cell, it rests. The grid borders act as walls and the bottom row is a
floor.

Scope: random canvases have sides 8..30. Larger sizes/counts are a synthetic
extension of the original 10x10 examples. Blob counts scale with area (up to
80), while columns contain up to three grid heights of water. An explicit
water_count is honored or sampling raises; no water is silently discarded.
The random scenes have a coloured skyline of ground segments of varying
heights. Optional tall pillars form cups and walls. An optional floating
diagonal ramp (two cells thick, like the 9-staircases in the task) carries the
water sideways from the pour point. The input water is either a connected
blob or stacked columns hanging below the pour point, and the pour point is
always its topmost-leftmost cell. The output is built by physically pouring
the latent water count onto the latent terrain.
"""

import random

import common

WATER = 1
SOLIDS = [2, 3, 4, 5, 6, 7, 8, 9]


def _parse(terrain):
  rows = []
  for r in terrain:
    if isinstance(r, str):
      rows.append([int(c) for c in r])
    else:
      rows.append([int(c) for c in r])
  return rows


def _pour(terrain, src, n):
  """Pours n water cells from src onto terrain; returns grid or None."""
  g = [row[:] for row in terrain]
  h, w = len(g), len(g[0])
  sy, sx = src

  def open_below(y, x):
    return y + 1 < h and g[y + 1][x] == 0

  for _ in range(n):
    if g[sy][sx] != 0:
      return None
    y, x = sy, sx
    for _ in range(4 * h * w + 10):
      if open_below(y, x):
        y += 1
        continue
      best = None
      for d in (-1, 1):
        cx, dist = x, 0
        while True:
          cx += d
          dist += 1
          if cx < 0 or cx >= w or g[y][cx] != 0:
            break
          if open_below(y, cx):
            if best is None or dist < best[0]:
              best = (dist, cx)
            break
      if best is None:
        break
      x = best[1]
    g[y][x] = WATER
  return g


def _make_terrain(h, w, use_ramp):
  """Builds skyline + pillars + optional ramp. Returns (grid, src) or None."""
  g = common.grid(w, h, 0)
  colors = random.sample(SOLIDS, random.randint(2, 4))
  heights = [0] * w
  x, prev = 0, None
  while x < w:
    seg = random.randint(1, 4)
    sh = random.randint(0, max(1, h // 2 - 1))
    c = random.choice([k for k in colors if k != prev] or colors)
    for xx in range(x, min(w, x + seg)):
      heights[xx] = sh
      for y in range(h - sh, h):
        g[y][xx] = c
    prev = c
    x += seg
  for _ in range(random.randint(0, max(3, w // 5))):
    px = random.randrange(w)
    lo, hi = heights[px] + 2, h - 3
    if lo > hi:
      continue
    ph = random.randint(lo, hi)
    c = random.choice(colors)
    for y in range(h - ph, h):
      g[y][px] = c
    heights[px] = ph
  if use_ramp:
    d = random.choice((-1, 1))
    length = random.randint(2, min(10, h - 4, w - 1))
    r0 = random.randint(1, max(2, h // 5))
    xs = [x0 for x0 in range(w)
          if 0 <= x0 + d * (length - 1) < w and 0 <= x0 + d * length < w]
    if not xs:
      return None
    x0 = random.choice(xs)
    cells = []
    for i in range(length):
      cells.append((r0 + i, x0 + d * i))
      if i < length - 1:
        cells.append((r0 + i, x0 + d * (i + 1)))
    for (y, cx) in cells:
      if y + 2 >= h - heights[cx]:
        return None
    # The ramp must not touch the ground or the pillars.
    for (y, cx) in cells:
      for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
          yy, xx = y + dy, cx + dx
          if 0 <= yy < h and 0 <= xx < w and g[yy][xx] != 0:
            return None
    rc = random.choice(SOLIDS)
    for (y, cx) in cells:
      g[y][cx] = rc
    options = [(r0 - 1, x0)]
    if 0 <= x0 + 2 * d < w:
      options.append((r0, x0 + 2 * d))
    src = random.choice(options)
  else:
    src = (random.randint(0, 1), random.randrange(w))
  if g[src[0]][src[1]] != 0:
    return None
  return g, src


def _make_water(terrain, src, style, count=None):
  h, w = len(terrain), len(terrain[0])
  sy, sx = src
  if style == "columns":
    cw = random.randint(1, 3)
    if sx + cw > w:
      return None
    cells = []
    for x in range(sx, sx + cw):
      y = sy
      while y < h and terrain[y][x] == 0:
        cells.append((y, x))
        y += 1
    if len(cells) < (3 if count is None else count):
      return None
    cells = sorted(cells)
    return cells if count is None else cells[:count]
  n = count if count is not None else random.randint(3, min(80, max(18, h * w // 5)))
  cells = {src}
  frontier = [src]
  for _ in range(8 * n + 40):
    if len(cells) >= n or not frontier:
      break
    y, x = random.choice(frontier)
    nbrs = []
    for dy, dx in ((1, 0), (0, 1), (0, -1), (-1, 0)):
      yy, xx = y + dy, x + dx
      if not (0 <= yy < h and 0 <= xx < w):
        continue
      if (yy, xx) in cells or terrain[yy][xx] != 0:
        continue
      if (yy, xx) <= src:
        continue
      nbrs.append((yy, xx))
    if not nbrs:
      frontier.remove((y, x))
      continue
    c = random.choice(nbrs)
    cells.add(c)
    frontier.append(c)
  if len(cells) < n:
    return None
  return sorted(cells)


def generate(width=None, height=None, terrain=None, water=None, ramp=None,
             water_style=None, water_count=None):
  """Returns an input/output pair.

  Args:
    width: grid width (random 8..30 when sampling).
    height: grid height (random 8..30 when sampling).
    terrain: optional explicit solid terrain (rows of digits, no water).
    water: optional explicit list of (row, col) water cells in the input.
    ramp: whether to add a floating diagonal ramp (random if None).
    water_style: "blob" or "columns" input water layout (random if None).
    water_count: exact water count, or sample a size-dependent count.
      Larger scenes/counts extrapolate the original 10x10 local-flow rule.
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Grid dimensions must be integers in 1..30")
  if water_count is not None and (not isinstance(water_count, int) or not 1 <= water_count <= 900):
    raise ValueError("water_count must be in 1..900")
  if water_style not in (None, "blob", "columns"):
    raise ValueError("Unknown water_style")
  if terrain is not None:
    base = _parse(terrain)
    if (not base or not base[0] or len(base) > 30 or len(base[0]) > 30 or
        any(len(row) != len(base[0]) or any(v not in [0] + SOLIDS for v in row) for row in base)):
      raise ValueError("Terrain must be rectangular, at most 30x30, and contain no water")
    if (width is not None and width != len(base[0])) or (height is not None and height != len(base)):
      raise ValueError("Explicit terrain does not match dimensions")
    if not water:
      raise ValueError("Explicit terrain requires water cells")
    cells = sorted(tuple(c) for c in water)
    if len(set(cells)) != len(cells):
      raise ValueError("Duplicate water cells")
    if any(not (0 <= y < len(base) and 0 <= x < len(base[0])) or base[y][x] != 0 for y, x in cells):
      raise ValueError("Water must occupy empty cells inside the terrain")
    if water_count is not None and len(cells) != water_count:
      raise ValueError("Explicit water cells do not match water_count")
    src = cells[0]
    out = _pour(base, src, len(cells))
    if out is None:
      raise ValueError("pour point fills before all water is placed")
    inp = [row[:] for row in base]
    for (y, x) in cells:
      inp[y][x] = WATER
    return {"input": inp, "output": out}
  if water is not None:
    raise ValueError("Explicit water requires explicit terrain")
  if any(d is not None and d < 8 for d in (width, height)):
    raise ValueError("Random dimensions must be in 8..30")
  for _ in range(2000):
    w = width if width is not None else random.randint(8, 30)
    h = height if height is not None else random.randint(8, 30)
    use_ramp = ramp if ramp is not None else random.random() < 0.5
    style = water_style or random.choice(["blob", "blob", "columns"])
    made = _make_terrain(h, w, use_ramp)
    if made is None:
      continue
    base, src = made
    cells = _make_water(base, src, style, water_count)
    if cells is None:
      continue
    out = _pour(base, src, len(cells))
    if out is None:
      continue
    out_cells = sorted((y, x) for y in range(h) for x in range(w)
                       if out[y][x] == WATER)
    if out_cells == cells:
      continue
    inp = [row[:] for row in base]
    for (y, x) in cells:
      inp[y][x] = WATER
    return {"input": inp, "output": out}
  raise RuntimeError("could not build a valid scene")


def validate():
  """Rebuilds the canonical fixtures from explicit terrain and water."""
  train = [
      generate(terrain=["0000000000", "0000000000", "0000000300",
                        "0000000300", "0000000300", "0000030300",
                        "0000030300", "0000230300", "0000230300",
                        "0222233300"],
               water=[(y, x) for y in range(10) for x in (8, 9)]),
      generate(terrain=["0030000000", "0030000000", "0030000000",
                        "0030000000", "0030000000", "0030030000",
                        "0030035005", "0030035005", "0030035005",
                        "0033335555"],
               water=[(1, 9), (2, 7), (2, 8), (2, 9), (3, 7), (3, 8),
                      (3, 9), (4, 6), (4, 7), (4, 8), (4, 9), (5, 6),
                      (5, 7), (5, 8), (5, 9), (6, 7), (6, 8), (7, 3),
                      (7, 4), (7, 7), (7, 8), (8, 3), (8, 4), (8, 7),
                      (8, 8)]),
      generate(terrain=["0000000000", "9900000099", "0990000990",
                        "0099000900", "0009009900", "0000099000",
                        "0000040000", "2004040000", "2024040000",
                        "2224440000"],
               water=[(1, 2), (1, 3), (2, 3)]),
  ]
  test = [
      generate(terrain=["0000000000", "9900000000", "0990000000",
                        "0099900005", "0000999005", "0000000505",
                        "3000000005", "3300005505", "3330055505",
                        "3333555505"],
               water=[(0, 0), (0, 1), (1, 2), (1, 3), (2, 3)]),
  ]
  return {"train": train, "test": test}
