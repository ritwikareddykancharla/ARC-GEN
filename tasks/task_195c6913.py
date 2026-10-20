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

"""ARC-GEN style generator for ARC task 195c6913.

Rule:
  The scene is a two-colour terrain. There is a background colour A and a
  path colour B. It also contains three kinds of objects:
  * a legend row of 2x2 blocks in the top-left corner, starting at column 1,
    separated by one A cell. Their colours, read left to right, form a cyclic
    pattern;
  * one extra 2x2 marker block elsewhere in an A area, with its own colour M;
  * single seed cells on the left edge (colour = first pattern colour) lying in
    B regions.
  The output erases every 2x2 block (they become A). It then draws a path
  from each seed. The path starts with the seed as pattern index 0 and moves
  right through cells of the seed's region colour, painting the pattern
  cyclically. When the next cell is a wall (any other terrain colour), the
  wall cell is painted M and the direction toggles between right and up. The
  path stops when it would leave the grid, or when the cell after a turn is
  also a wall. That second wall is not marked.

Scope:
  Random scenes use grids of 16..30 per side and 1..3 staircase-like B bands
  rising toward the upper right, with optional rectangular A pockets. They
  have 1..4 seeds (up to three bands plus an extra seed in one band) and legends of 2..4
  blocks with at least two distinct colours (repeats allowed). There is one
  marker block. Paths from different seeds never share cells, so the drawing
  order is irrelevant.
  Original fixtures are replayed through explicit latent arguments: the
  terrain map (run-length rows with blocks erased and seeds shown as terrain),
  the pattern, the marker colour and position, the seed rows and the legend
  row. The output is always computed from these latents by the path rule.
"""

import random

import common


def _decode_terrain(terrain):
  rows = []
  for row in terrain:
    if isinstance(row, str):
      cells = []
      for tok in row.split():
        if "*" in tok:
          colour, count = tok.split("*")
          cells.extend([int(colour)] * int(count))
        else:
          cells.append(int(tok))
      rows.append(cells)
    else:
      rows.append([int(v) for v in row])
  return rows


def _components(g):
  h, w = len(g), len(g[0])
  seen = [[False] * w for _ in range(h)]
  comps = []
  for r in range(h):
    for c in range(w):
      if seen[r][c]:
        continue
      colour = g[r][c]
      seen[r][c] = True
      stack = [(r, c)]
      cells = []
      while stack:
        y, x = stack.pop()
        cells.append((y, x))
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
          if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx]:
            if g[ny][nx] == colour:
              seen[ny][nx] = True
              stack.append((ny, nx))
      comps.append((colour, cells))
  return comps


def _trace(base, row, pattern):
  """Right/up zig-zag path from the left-edge seed at `row`."""
  h, w = len(base), len(base[0])
  y, x = row, 0
  reg = base[y][1]
  cells = [(y, x, pattern[0])]
  marks = []
  dirs = [(0, 1), (-1, 0)]
  di = 0
  idx = 0
  while True:
    dy, dx = dirs[di]
    ny, nx = y + dy, x + dx
    if not (0 <= ny < h and 0 <= nx < w):
      break
    if base[ny][nx] != reg:
      marks.append((ny, nx))
      di ^= 1
      dy, dx = dirs[di]
      ny, nx = y + dy, x + dx
      if not (0 <= ny < h and 0 <= nx < w) or base[ny][nx] != reg:
        break
    y, x = ny, nx
    idx += 1
    cells.append((y, x, pattern[idx % len(pattern)]))
  return cells, marks


def _place_objects(terrain, pattern, seed_rows, legend_row):
  g = [row[:] for row in terrain]
  for i, colour in enumerate(pattern):
    for dr in (0, 1):
      for dc in (0, 1):
        g[legend_row + dr][1 + 3 * i + dc] = colour
  for r in seed_rows:
    g[r][0] = pattern[0]
  return g


def _build(terrain, pattern, marker_color, marker_pos, seed_rows, legend_row):
  grid = _place_objects(terrain, pattern, seed_rows, legend_row)
  mr, mc = marker_pos
  for dr in (0, 1):
    for dc in (0, 1):
      grid[mr + dr][mc + dc] = marker_color
  output = [row[:] for row in terrain]
  for r in sorted(seed_rows):
    cells, marks = _trace(terrain, r, pattern)
    for y, x in marks:
      output[y][x] = marker_color
    for y, x, colour in cells:
      output[y][x] = colour
  return {"input": grid, "output": output}


def _random_terrain(h, w, a, b, top, zone_w):
  t = common.grid(w, h, a)
  nb_max = max(1, min(3, (h - top) // 7))
  nb = random.randint(1, nb_max)
  cur = h - 1 + random.randint(-3, 2)
  bands = []
  for _ in range(nb):
    hi = min(cur, h + 1)
    lo = min(hi - random.randint(3, 8) + 1, h - 3)
    if lo < top:
      break
    bands.append((lo, hi))
    cur = lo - random.randint(3, 6)
  if not bands:
    return None
  for lo, hi in bands:
    p_hi = random.uniform(0.25, 0.6)
    p_lo = random.uniform(0.25, 0.6)
    for x in range(w):
      if x:
        if random.random() < p_hi:
          hi -= random.randint(1, 3)
        if random.random() < p_lo:
          lo -= random.randint(1, 3)
        lo = min(lo, hi - 1)
      for y in range(max(lo, 0), min(hi, h - 1) + 1):
        t[y][x] = b
  if random.random() < 0.35:
    for _ in range(random.randint(1, 2)):
      ph, pw = random.choice([(2, 3), (3, 2), (3, 3), (2, 4), (4, 2),
                              (3, 4), (4, 3)])
      for _ in range(30):
        r = random.randint(0, h - ph)
        c = random.randint(2, w - pw)
        if all(t[r + i][c + j] == b for i in range(ph) for j in range(pw)):
          for i in range(ph):
            for j in range(pw):
              t[r + i][c + j] = a
          break
  for y in range(top):
    for x in range(zone_w):
      t[y][x] = a
  for _ in range(8):
    small = [cells for _, cells in _components(t) if len(cells) < 5]
    if not small:
      break
    for cells in small:
      for y, x in cells:
        t[y][x] = b if t[y][x] == a else a
  if any(len(cells) < 5 for _, cells in _components(t)):
    return None
  for y in range(top):
    for x in range(zone_w):
      if t[y][x] != a:
        return None
  return t


def _choose_seeds(t, b, top, pattern):
  h = len(t)
  cand = [y for y in range(top, h) if t[y][0] == b and t[y][1] == b]
  runs = []
  for y in cand:
    if runs and runs[-1][-1] == y - 1:
      runs[-1].append(y)
    else:
      runs.append([y])
  if not runs:
    return None
  for _ in range(20):
    k = random.randint(1, min(3, len(runs)))
    rows = [random.choice(run) for run in random.sample(runs, k)]
    if random.random() < 0.3:
      big = [run for run in runs if len(run) >= 5]
      if big:
        rows.append(random.choice(random.choice(big)))
    rows = sorted(set(rows))
    if any(rows[i + 1] - rows[i] < 2 for i in range(len(rows) - 1)):
      continue
    seen = set()
    ok = True
    total = 0
    for r in rows:
      cells, marks = _trace(t, r, pattern)
      if not marks or len(cells) < 4:
        ok = False
        break
      total += len(marks)
      for y, x, _ in cells:
        if (y, x) in seen:
          ok = False
          break
        seen.add((y, x))
      if not ok:
        break
    if ok and total >= 2:
      return rows
  return None


def _random_scene(width, height, background, path_color, pattern,
                  marker_color, legend_row):
  for _ in range(500):
    h = height if height is not None else random.randint(16, 30)
    w = width if width is not None else random.randint(16, 30)
    ly = legend_row if legend_row is not None else random.choice([1, 1, 1, 2])
    pat = list(pattern) if pattern is not None else []
    used = set(pat) | {c for c in (background, path_color, marker_color) if c is not None}
    a = background
    if a is None:
      a = random.choice([c for c in range(10) if c not in used])
    used.add(a)
    b = path_color
    if b is None:
      b = random.choice([c for c in range(10) if c not in used])
    used.add(b)
    m = marker_color
    if m is None:
      m = random.choice([c for c in range(10) if c not in used])
    used.add(m)
    if not pat:
      length = random.randint(2, 4)
      free = [c for c in range(10) if c not in used]
      pool = random.sample(free, random.randint(2, min(length, 3)))
      pat = pool[:2] + [random.choice(pool) for _ in range(length - 2)]
      random.shuffle(pat)
    top = ly + 3
    zone_w = 3 * len(pat) + 1
    if zone_w + 3 > w or top + 8 > h:
      continue
    t = _random_terrain(h, w, a, b, top, zone_w)
    if t is None:
      continue
    rows = _choose_seeds(t, b, top, pat)
    if rows is None:
      continue
    g = _place_objects(t, pat, rows, ly)
    cands = []
    for r in range(1, h - 2):
      if r == ly:
        continue
      for c in range(1, w - 2):
        if r - 1 <= ly + 2 and c - 1 <= zone_w - 1:
          continue
        if all(g[y][x] == a for y in range(r - 1, r + 3)
               for x in range(c - 1, c + 3)):
          cands.append((r, c))
    if not cands:
      continue
    pos = random.choice(cands)
    pair = _build(t, pat, m, pos, rows, ly)
    if all(len(cells) >= 5 for colour, cells in _components(pair["input"])
           if colour in (a, b)):
      return pair
  raise RuntimeError("could not construct a valid scene")


def generate(width=None, height=None, terrain=None, pattern=None,
             marker_color=None, marker_pos=None, seed_rows=None,
             legend_row=None, background=None, path_color=None):
  """Returns an input/output pair for task 195c6913.

  Args:
    width: grid width for random scenes (16..30 when None).
    height: grid height for random scenes (16..30 when None).
    terrain: optional explicit terrain map (list of run-length strings like
      "3*19 0" or lists of ints). Legend and marker cells are shown as the
      background colour, and seed cells as the terrain beneath them. When
      given, the scene is rebuilt exactly from the latent arguments below.
    pattern: legend colours left to right (pattern[0] is the seed colour).
    marker_color: colour of the extra 2x2 marker block and of wall marks.
    marker_pos: (row, col) of the marker block's top-left cell.
    seed_rows: rows of the seeds on column 0.
    legend_row: top row of the legend blocks (blocks start at column 1).
    background: colour A of the legend/marker terrain (random mode).
    path_color: colour B of the regions the paths travel through (random).
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Grid dimensions must be integers in 1..30")
  fixed = [c for c in (background, path_color, marker_color) if c is not None]
  if any(c not in range(10) for c in fixed) or len(set(fixed)) != len(fixed):
    raise ValueError("Terrain and marker colours must be distinct values in 0..9")
  if pattern is not None and (not 2 <= len(pattern) <= 4 or len(set(pattern)) < 2 or
                              any(c not in range(10) or c in fixed for c in pattern)):
    raise ValueError("Pattern requires 2..4 entries with at least two distinct colours separate from terrain/marker")
  if terrain is not None:
    base = _decode_terrain(terrain)
    if not base or not base[0] or len(base) > 30 or len(base[0]) > 30 or any(len(row) != len(base[0]) or any(v not in range(10) for v in row) for row in base):
      raise ValueError("Terrain must be rectangular and at most 30x30")
    if (width is not None and width != len(base[0])) or (height is not None and height != len(base)):
      raise ValueError("Terrain does not match dimensions")
    if (pattern is None or marker_color is None or marker_pos is None or
        seed_rows is None):
      raise ValueError("explicit terrain needs pattern, marker and seeds")
    ly = 1 if legend_row is None else legend_row
    mr, mc = marker_pos
    if not (0 <= ly < len(base)-1 and 3*len(pattern) <= len(base[0]) and
            0 <= mr < len(base)-1 and 0 <= mc < len(base[0])-1):
      raise ValueError("Legend or marker outside terrain")
    if not seed_rows or len(set(seed_rows)) != len(seed_rows) or any(not 0 <= r < len(base) for r in seed_rows):
      raise ValueError("Seeds must be nonempty distinct valid rows")
    if background is not None and any(base[ly+dr][1+3*i+dc] != background for i in range(len(pattern)) for dr in (0,1) for dc in (0,1)):
      raise ValueError("Legend terrain does not match background")
    if path_color is not None and any(base[r][1] != path_color for r in seed_rows):
      raise ValueError("Seed terrain does not match path_color")
    return _build(base, list(pattern), marker_color, tuple(marker_pos),
                  list(seed_rows), ly)
  if marker_pos is not None or seed_rows is not None:
    raise ValueError("Explicit marker position or seeds require explicit terrain")
  if any(d is not None and d < 16 for d in (width, height)):
    raise ValueError("Random dimensions must be in 16..30")
  return _random_scene(width, height, background, path_color, pattern,
                       marker_color, legend_row)


_TRAIN1 = [
    "3*19 0", "3*16 0*4", "3*16 0*4", "3*14 0*5 3", "3*12 0*6 3*2",
    "3*9 0*8 3*3", "3*7 0*9 3*4", "3*5 0*11 3*4", "3*2 0*18", "0*20",
    "0*20", "0*19 3", "0*17 3*3", "0*15 3*5", "0*14 3*6", "0*13 3*7",
    "0*11 3*9", "0*10 3*10", "0*9 3*11", "0*8 3*12",
]

_TRAIN2 = [
    "2*17 8*8", "2*17 8*8", "2*15 8*8 2*2", "2*12 8*9 2*4",
    "2*11 8*9 2*5", "2*10 8*7 2*8", "2*9 8*8 2*8", "2*9 8*13 2*3",
    "2*7 8*15 2*3", "2*7 8*17 2", "2*3 8 2 8*19 2", "8*15 2*10",
    "8*15 2*10", "8*15 2*10", "8*17 2*8", "2 8*19 2*5", "2*6 8*15 2*4",
    "2*8 8*12 2*5", "2*5 8*9 2*2 8*2 2*7", "2*5 8*9 2*11",
    "2*3 8*10 2*12", "2 8*11 2*13", "8*16 2*9", "8*17 2*8", "8*17 2*8",
]

_TRAIN3 = [
    "1*25", "1*25", "1*23 4*2", "1*22 4*3", "1*18 4*7", "1*19 4*6",
    "1*19 4*6", "1*17 4*8", "1*12 4*3 1 4*9", "1*12 4*13",
    "1*6 4*15 1 4*3", "1*3 4*17 1*2 4*3", "1 4*17 1*3 4*4",
    "4*17 1*3 4*5", "4*13 1*6 4*5 1", "4*9 1*11 4*4 1", "4*7 1*10 4*7 1",
    "4 1*12 4*10 1*2", "1*12 4*11 1*2", "1*5 4*2 1*4 4*11 1*3",
    "1 4*20 1*4", "4*21 1*4", "4*16 1 4 1*2 4 1*4", "4*10 1*15",
    "4*9 1*16",
]

_TEST1 = [
    "4*30", "4*30", "4*30", "4*30", "4*13 7*5 4*12", "4*11 7*12 4*7",
    "4*7 7*18 4*5", "4*4 7*22 4*4", "4*2 7*5 4*4 7*17 4*2",
    "7*6 4*6 7*17 4", "7*4 4*8 7*17 4", "7*3 4*9 7*16 4*2",
    "7*3 4*8 7*15 4*4", "7*2 4*8 7*14 4*6", "7 4*6 7*18 4*5",
    "7 4*4 7*19 4*6", "7*23 4*7", "7*23 4*7", "7*23 4*7", "7*23 4*7",
    "7*22 4*8", "7*22 4*8", "7*20 4*10", "7*18 4*12", "7*13 4*17",
    "7*11 4*19", "7*9 4*21", "7*8 4*22", "7*5 4*25", "7*2 4*28",
]

_TEST2 = [
    "8*16 9*6 8*8", "8*15 9*7 8*8", "8*14 9*8 8*8", "8*13 9*8 8*9",
    "8*10 9*10 8*10", "8*7 9*12 8*11", "8*4 9*20 8*4 9*2", "9*30",
    "9*30", "9*30", "9*30", "9*30", "9*30", "9*16 8*6 9*8",
    "9*7 8*15 9*7 8", "9*6 8*16 9*7 8", "9*2 8*16 9*10 8*2",
    "8*12 9*16 8*2", "8*8 9*19 8*3", "8*7 9*20 8*3", "9*26 8*4",
    "9*25 8*5", "9*24 8*6", "9*23 8*7", "9*19 8*11", "9*15 8*15",
    "9*11 8*19", "9*10 8*20", "9*9 8*21", "9*8 8*22",
]


def validate():
  """Rebuilds the canonical fixtures from explicit latent parameters."""
  train = [
      generate(terrain=_TRAIN1, pattern=[2, 2, 8], marker_color=4,
               marker_pos=(16, 16), seed_rows=[15], legend_row=1),
      generate(terrain=_TRAIN2, pattern=[4, 1], marker_color=9,
               marker_pos=(21, 21), seed_rows=[13, 23], legend_row=1),
      generate(terrain=_TRAIN3, pattern=[2, 2, 3], marker_color=8,
               marker_pos=(21, 22), seed_rows=[15, 23], legend_row=1),
  ]
  test = [
      generate(terrain=_TEST1, pattern=[1, 2, 8, 3], marker_color=6,
               marker_pos=(25, 25), seed_rows=[11, 26], legend_row=2),
      generate(terrain=_TEST2, pattern=[3, 3, 3, 6], marker_color=7,
               marker_pos=(25, 24), seed_rows=[14, 26], legend_row=1),
  ]
  return {"train": train, "test": test}
