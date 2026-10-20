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

"""Plus-sign highlighter (ARC task 1818057f).

Rule: the input is a field of colour-4 cells on a colour-2 background.
Every 4-cell whose four orthogonal neighbours are also 4 is the centre of
a plus sign; that centre and its four arms are recoloured 8. Everything
else -- including 4-cells that merely touch a plus diagonally or continue
beyond the end of an arm -- is left unchanged.

Scope: scenes are built from latent plus centres (pairwise Chebyshev
distance >= 3, so pluses never share cells) embedded in four kinds of
distractor material: random scatter with near-plus fragments, gapped grid
lines whose intersections are only sometimes complete pluses, rectangular
blobs with pluses embedded in larger 4-shapes, and periodic tilings whose
motif contains one or two pluses. Colours 2 / 4 / 8 are fixed, as in every
original pair; grid sides range from 8 to 30 and need not be square.
"""

import random

import common

BACKGROUND = 2
INK = 4
HIGHLIGHT = 8
ARMS = ((-1, 0), (1, 0), (0, -1), (0, 1))
PLUS = ((0, 0),) + ARMS


def _plus_cells(y, x):
  """Returns the five cells of the plus centred at (y, x)."""
  return [(y + dy, x + dx) for dy, dx in PLUS]


def _is_center(grid, y, x):
  """True when (y, x) is interior and its whole plus is drawn in INK."""
  h, w = len(grid), len(grid[0])
  if not (0 < y < h - 1 and 0 < x < w - 1):
    return False
  return all(grid[yy][xx] == INK for yy, xx in _plus_cells(y, x))


def _draw_plus(grid, y, x):
  for yy, xx in _plus_cells(y, x):
    grid[yy][xx] = INK


def _well_separated(centers):
  """Pairwise Chebyshev distance >= 3 so no two pluses share a cell."""
  for i, (ay, ax) in enumerate(centers):
    for by, bx in centers[i + 1:]:
      if max(abs(ay - by), abs(ax - bx)) < 3:
        return False
  return True


def _enforce(grid, centers, strict):
  """Makes the intended centres the only plus centres in the grid.

  In strict mode (fixture replay) any mismatch raises ValueError. In
  constructive mode an unintended plus is broken by blanking one of its
  cells that belongs to no intended plus; with intended centres at
  Chebyshev distance >= 3 such a cell always exists. Returns False if it
  nevertheless cannot repair the scene, so the caller can resample.
  """
  h, w = len(grid), len(grid[0])
  wanted = set(centers)
  protected = set()
  for y, x in centers:
    protected.update(_plus_cells(y, x))
  for y, x in centers:
    if not _is_center(grid, y, x):
      raise ValueError('intended plus centre %r is incomplete' % ((y, x),))
  for y in range(1, h - 1):
    for x in range(1, w - 1):
      if (y, x) in wanted or not _is_center(grid, y, x):
        continue
      if strict:
        raise ValueError('unintended plus centre at %r' % ((y, x),))
      options = [c for c in _plus_cells(y, x) if c not in protected]
      if not options:
        return False
      yy, xx = random.choice(options)
      grid[yy][xx] = BACKGROUND
  return True


def _enforce_torus(tile, centers):
  """Like _enforce but on a wrapping motif, so the tiling stays periodic."""
  th, tw = len(tile), len(tile[0])
  wanted = set(centers)
  protected = set()
  for y, x in centers:
    protected.update(_plus_cells(y, x))
  for y in range(th):
    for x in range(tw):
      if (y, x) in wanted:
        continue
      cells = [((y + dy) % th, (x + dx) % tw) for dy, dx in PLUS]
      if all(tile[yy][xx] == INK for yy, xx in cells):
        options = [c for c in cells if c not in protected]
        if not options:
          return False
        yy, xx = random.choice(options)
        tile[yy][xx] = BACKGROUND
  return True


def _render_output(grid, centers):
  out = [row[:] for row in grid]
  for y, x in centers:
    for yy, xx in _plus_cells(y, x):
      out[yy][xx] = HIGHLIGHT
  return out


def _background_dominates(grid):
  ink = sum(row.count(INK) for row in grid)
  return ink * 100 < 45 * len(grid) * len(grid[0])


def _pick_centers(h, w, k):
  """Samples up to k interior centres at Chebyshev distance >= 3."""
  centers = []
  for _ in range(300):
    if len(centers) == k:
      break
    c = (random.randint(1, h - 2), random.randint(1, w - 2))
    if all(max(abs(c[0] - y), abs(c[1] - x)) >= 3 for y, x in centers):
      centers.append(c)
  return centers


def _stamp(grid, offsets):
  """Draws a small shape (non-negative offsets) at a random position."""
  h, w = len(grid), len(grid[0])
  hh = max(dy for dy, _ in offsets) + 1
  ww = max(dx for _, dx in offsets) + 1
  if hh > h or ww > w:
    return
  oy, ox = random.randint(0, h - hh), random.randint(0, w - ww)
  for dy, dx in offsets:
    grid[oy + dy][ox + dx] = INK


def _fragment_shape():
  """A distractor that is almost, but not, a complete plus."""
  kind = random.choice(['broken', 'broken', 'bar', 'block', 'corner', 'diag'])
  if kind == 'broken':
    drop = random.sample(range(4), random.randint(1, 2))
    return [(1, 1)] + [(1 + ARMS[i][0], 1 + ARMS[i][1])
                       for i in range(4) if i not in drop]
  if kind == 'bar':
    n = random.randint(2, 5)
    if random.random() < 0.5:
      return [(0, i) for i in range(n)]
    return [(i, 0) for i in range(n)]
  if kind == 'block':
    hh, ww = random.choice([(2, 2), (2, 3), (3, 2)])
    return [(i, j) for i in range(hh) for j in range(ww)]
  if kind == 'corner':
    return random.choice([[(0, 0), (0, 1), (1, 0)], [(0, 0), (0, 1), (1, 1)],
                          [(0, 0), (1, 0), (1, 1)], [(0, 1), (1, 0), (1, 1)]])
  if random.random() < 0.5:
    return [(0, 0), (1, 1)]
  return [(0, 1), (1, 0)]


def _attach(grid, y, x):
  """Glues a few extra INK cells onto the plus so it sits inside a blob."""
  h, w = len(grid), len(grid[0])
  spots = [(y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1),
           (y - 2, x), (y + 2, x), (y, x - 2), (y, x + 2)]
  for yy, xx in random.sample(spots, random.randint(1, 3)):
    if 0 <= yy < h and 0 <= xx < w:
      grid[yy][xx] = INK


def _scene_scatter():
  """Random scatter plus near-plus fragments, like the first train pair."""
  h, w = random.randint(8, 30), random.randint(8, 30)
  area = h * w
  k = random.randint(1, max(1, min(8, area // 36)))
  centers = _pick_centers(h, w, k)
  grid = common.grid(w, h, BACKGROUND)
  density = random.uniform(0.08, 0.3)
  for y in range(h):
    for x in range(w):
      if random.random() < density:
        grid[y][x] = INK
  for _ in range(random.randint(1, 1 + area // 40)):
    _stamp(grid, _fragment_shape())
  for y, x in centers:
    _draw_plus(grid, y, x)
    if random.random() < 0.5:
      _attach(grid, y, x)
  return grid, centers


def _scene_lines():
  """Gapped grid lines; some intersections are complete pluses."""
  h, w = random.randint(10, 30), random.randint(10, 30)
  step = random.randint(4, 7)
  rows = list(range(random.randint(0, step - 1), h, step))
  cols = list(range(random.randint(0, step - 1), w, step))
  crossings = [(y, x) for y in rows for x in cols
               if 1 <= y <= h - 2 and 1 <= x <= w - 2]
  if not crossings:
    return None
  centers = random.sample(crossings, random.randint(1, min(8, len(crossings))))
  grid = common.grid(w, h, BACKGROUND)
  keep = random.uniform(0.75, 0.95)
  for y in rows:
    for x in range(w):
      if random.random() < keep:
        grid[y][x] = INK
  for x in cols:
    for y in range(h):
      if random.random() < keep:
        grid[y][x] = INK
  density = random.uniform(0.03, 0.18)
  for y in range(h):
    for x in range(w):
      if random.random() < density:
        grid[y][x] = INK
  for y, x in centers:
    _draw_plus(grid, y, x)
  return grid, centers


def _scene_blobs():
  """Rectangles and bars with pluses embedded in bigger shapes."""
  h, w = random.randint(8, 22), random.randint(8, 22)
  k = random.randint(1, max(1, min(4, h * w // 40)))
  centers = _pick_centers(h, w, k)
  grid = common.grid(w, h, BACKGROUND)
  for _ in range(random.randint(3, 9)):
    if random.random() < 0.7:
      hh, ww = random.randint(1, 2), random.randint(2, 6)
      if random.random() < 0.5:
        hh, ww = ww, hh
    else:
      hh, ww = random.randint(2, 4), random.randint(2, 4)
    _stamp(grid, [(i, j) for i in range(hh) for j in range(ww)])
  for y, x in centers:
    _draw_plus(grid, y, x)
    if random.random() < 0.8:
      _attach(grid, y, x)
  return grid, centers


def _tile_grid(tile, height, width, tile_centers):
  """Tiles the motif and lists every plus centre whose plus fits inside."""
  th, tw = len(tile), len(tile[0])
  grid = [[tile[y % th][x % tw] for x in range(width)] for y in range(height)]
  centers = []
  for ty, tx in tile_centers:
    for y in range(ty, height, th):
      for x in range(tx, width, tw):
        if 1 <= y <= height - 2 and 1 <= x <= width - 2:
          centers.append((y, x))
  centers.sort()
  return grid, centers


def _scene_tile():
  """Periodic motif containing one or two pluses, like the second pair."""
  th, tw = random.randint(4, 10), random.randint(4, 10)
  want = 2 if random.random() < 0.4 else 1
  tcenters = []
  for _ in range(80):
    if len(tcenters) == want:
      break
    c = (random.randint(1, th - 2), random.randint(1, tw - 2))
    ok = True
    for y, x in tcenters:
      dy, dx = abs(c[0] - y), abs(c[1] - x)
      if max(min(dy, th - dy), min(dx, tw - dx)) < 3:
        ok = False
    if ok:
      tcenters.append(c)
  tile = common.grid(tw, th, BACKGROUND)
  plus = set()
  for y, x in tcenters:
    plus.update(_plus_cells(y, x))
  density = random.uniform(0.08, 0.3)
  for y in range(th):
    for x in range(tw):
      if (y, x) not in plus and random.random() < density:
        tile[y][x] = INK
  for y, x in tcenters:
    _draw_plus(tile, y, x)
  if not _enforce_torus(tile, tcenters):
    return None
  height = random.randint(max(8, th + 1), 30)
  width = random.randint(max(8, tw + 1), 30)
  grid, centers = _tile_grid(tile, height, width, tcenters)
  if not centers:
    return None
  return grid, centers


_SCENES = {
    'scatter': _scene_scatter,
    'lines': _scene_lines,
    'blobs': _scene_blobs,
    'tile': _scene_tile,
}


def generate(width=None, height=None, mode=None, centers=None, extras=None,
             tile_height=None, tile_width=None, tile_centers=None,
             tile_extras=None, input_grid=None):
  """Returns {'input': grid, 'output': grid} for the plus-highlight task.

  With no arguments a fresh random scene is constructed. Three explicit
  forms reconstruct fixtures from latent parameters:

  Args:
    width: grid width (explicit scatter and tile forms).
    height: grid height (explicit scatter and tile forms).
    mode: optional random scene style: 'scatter', 'lines', 'blobs', 'tile'.
    centers: list of (row, col) plus centres. Required with input_grid or
      extras; every listed centre is painted as a full plus.
    extras: list of (row, col) INK cells that are not part of any plus.
    tile_height: motif height for the periodic form.
    tile_width: motif width for the periodic form.
    tile_centers: plus centres inside the motif (periodic form).
    tile_extras: other INK cells of the motif (periodic form).
    input_grid: replay of an original input whose scatter is too large to
      list as coordinates; centers must then be supplied explicitly and are
      verified to be exactly the plus centres of that grid.
  """
  if input_grid is not None:
    grid = [list(row) for row in input_grid]
    centers = [tuple(c) for c in centers]
    _enforce(grid, centers, strict=True)
    return {'input': grid, 'output': _render_output(grid, centers)}
  if tile_centers is not None:
    tile = common.grid(tile_width, tile_height, BACKGROUND)
    for y, x in tile_extras or []:
      tile[y][x] = INK
    tcenters = [tuple(c) for c in tile_centers]
    for y, x in tcenters:
      _draw_plus(tile, y, x)
    grid, centers = _tile_grid(tile, height, width, tcenters)
    _enforce(grid, centers, strict=True)
    return {'input': grid, 'output': _render_output(grid, centers)}
  if centers is not None:
    grid = common.grid(width, height, BACKGROUND)
    for y, x in extras or []:
      grid[y][x] = INK
    centers = [tuple(c) for c in centers]
    for y, x in centers:
      _draw_plus(grid, y, x)
    _enforce(grid, centers, strict=True)
    return {'input': grid, 'output': _render_output(grid, centers)}

  for _ in range(200):
    style = mode or random.choices(
        ['scatter', 'lines', 'blobs', 'tile'], weights=[4, 3, 3, 3])[0]
    scene = _SCENES[style]()
    if scene is None:
      continue
    grid, centers = scene
    if not centers or not _well_separated(centers):
      continue
    if not _enforce(grid, centers, strict=False):
      continue
    if not _background_dominates(grid):
      continue
    return {'input': grid, 'output': _render_output(grid, centers)}
  raise RuntimeError('could not construct a valid plus scene')


def validate():
  """Reconstructs the original train/test pairs from latent parameters."""
  train = [
      generate(
          width=12, height=10, centers=[(5, 9)],
          extras=[(0, 4), (0, 5), (1, 5), (1, 8), (1, 10), (2, 0), (2, 10),
                  (3, 3), (3, 8), (3, 9), (4, 2), (4, 8), (5, 0), (5, 6),
                  (6, 1), (6, 3), (6, 6), (7, 6), (8, 1), (8, 6), (8, 9),
                  (9, 3), (9, 4), (9, 7), (9, 9), (9, 11)]),
      generate(
          width=17, height=15, tile_height=9, tile_width=5,
          tile_centers=[(3, 3), (7, 3)],
          tile_extras=[(0, 0), (0, 1), (1, 0), (1, 1), (5, 0), (5, 1),
                       (5, 3)]),
      generate(
          width=12, height=12, centers=[(5, 6), (8, 1)],
          extras=[(0, 5), (0, 6), (0, 7), (0, 11), (1, 5), (1, 6), (1, 7),
                  (1, 11), (2, 11), (3, 11), (4, 5), (4, 7), (4, 8), (4, 9),
                  (4, 10), (4, 11), (5, 11), (6, 0), (6, 7), (6, 11), (7, 0),
                  (7, 7), (7, 8), (7, 9), (7, 10), (7, 11), (8, 6), (8, 7),
                  (8, 8), (8, 9), (9, 0), (9, 2), (9, 6), (10, 3), (10, 4),
                  (10, 5), (10, 6), (10, 10), (10, 11), (11, 3), (11, 4),
                  (11, 5), (11, 6), (11, 7), (11, 8), (11, 9), (11, 10),
                  (11, 11)]),
  ]
  test = [
      generate(
          centers=[(2, 2), (7, 2), (7, 12), (12, 7), (17, 7), (17, 17)],
          input_grid=[
              [4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2],
              [4, 4, 4, 4, 4, 4, 4, 2, 4, 4, 2, 4, 4, 4, 4, 2, 4, 4, 2, 2, 4, 2],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2],
              [4, 2, 4, 2, 2, 4, 2, 2, 2, 4, 2, 2, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2],
              [4, 2, 4, 2, 2, 4, 2, 2, 2, 4, 4, 2, 4, 2, 4, 4, 2, 4, 2, 2, 4, 2],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2],
              [4, 4, 4, 4, 2, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4, 4, 4, 2, 2, 4, 4, 4],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2],
              [4, 2, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 4, 2],
              [4, 2, 4, 2, 2, 4, 2, 4, 2, 4, 4, 2, 2, 2, 2, 4, 2, 4, 2, 4, 4, 2],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2],
              [4, 4, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2],
              [4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2],
              [4, 2, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2, 2, 2, 4, 4, 2, 4, 2, 4, 2, 2],
              [2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2],
              [4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4, 4, 4, 2, 4, 2],
              [2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2],
              [4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 4, 2, 4, 2, 2, 4, 2, 2, 2, 4, 4, 2],
              [4, 2, 4, 2, 4, 4, 2, 4, 2, 4, 2, 2, 4, 2, 4, 4, 2, 2, 2, 4, 4, 2],
              [2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2],
          ]),
  ]
  return {'train': train, 'test': test}
