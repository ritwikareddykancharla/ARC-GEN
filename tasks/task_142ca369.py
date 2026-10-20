# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator for ARC task 142ca369: bouncing diagonal rays.

Rule: the black canvas holds emitters and reflectors. An emitter is a 3-cell
L filling a 2x2 box with one corner missing. Its tip is the cell diagonally
opposite the missing corner, and it points from the missing corner towards
the tip. A reflector is any other object, here a straight bar of length 1-3.

Each emitter fires a diagonal ray from its tip, one cell per step, painted in
the emitter colour. The ray stops at the grid border, or just before a
reflector cell it would hit head-on. When a newly painted ray cell is
orthogonally adjacent to a reflector cell, two things happen from that cell
onwards: the ray takes the reflector colour, and the ray flips its motion
component towards that reflector. A reflector above or below flips dy. A
reflector to the left or right flips dx. Rays can chain through several
bounces.

Scope: grids are 12-30 cells per side. General scenes have 1-4 emitters with any
pointing direction and 0-6 bars that are horizontal or vertical, length 1-3.
Colours are drawn from 1-9. Most bars are placed beside an existing ray path
so that bounces and chains occur. Other bars are placed at random and act as
distractors or head-on stoppers. A separate parallel-ray branch builds dense
rows of up to 14 emitters, with neighbouring emitters of different colours,
as in the original many-emitter case. All rays in that branch point downward
and share a horizontal direction; general scenes cover all four directions.
"""

import random

import common

_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _l_cells(tr, tc, dy, dx):
  """Cells of the L whose tip is (tr, tc), pointing along (dy, dx)."""
  return [(tr, tc), (tr - dy, tc), (tr, tc - dx)]


def _bar_cells(r, c, orient, length):
  """Cells of a bar that starts at (r, c) and runs right ('h') or down ('v')."""
  if orient == 'h':
    return [(r, c + i) for i in range(length)]
  return [(r + i, c) for i in range(length)]


def _refl_map(bars):
  refl = {}
  for r, c, orient, length, colour in bars:
    for cell in _bar_cells(r, c, orient, length):
      refl[cell] = colour
  return refl


def _trace(height, width, refl, tr, tc, dy, dx, colour):
  """Follow one ray.

  Returns (path, bounces, multi, terminated). path is a list of
  (row, col, colour) cells. multi is True if any cell touched more than one
  reflector. terminated is True if the ray left the grid or met a reflector
  within height + width steps.
  """
  path = []
  bounces = 0
  multi = False
  y, x = tr, tc
  for _ in range(height + width):
    ny, nx = y + dy, x + dx
    if not (0 <= ny < height and 0 <= nx < width) or (ny, nx) in refl:
      return path, bounces, multi, True
    hits = 0
    for ay, ax, vert in ((ny - 1, nx, True), (ny + 1, nx, True),
                         (ny, nx - 1, False), (ny, nx + 1, False)):
      if (ay, ax) in refl:
        hits += 1
        colour = refl[(ay, ax)]
        if vert:
          dy = -dy
        else:
          dx = -dx
    if hits:
      bounces += 1
    if hits > 1:
      multi = True
    path.append((ny, nx, colour))
    y, x = ny, nx
  return path, bounces, multi, False


def _free(cells, occupied, height, width):
  """True if every cell is in bounds and no 8-neighbour is occupied."""
  for r, c in cells:
    if not (0 <= r < height and 0 <= c < width):
      return False
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if (r + dr, c + dc) in occupied:
          return False
  return True


def _sample(requested_height=None, requested_width=None, mode=None):
  """Sample latent scene parameters (height, width, emitters, bars)."""
  for _ in range(400):
    height = requested_height if requested_height is not None else random.randint(12, 30)
    width = requested_width if requested_width is not None else random.randint(12, 30)
    parallel = mode == 'parallel' or (mode is None and random.random() < 0.2)
    if parallel:
      cols = list(range(1, width - 1, 2))
      cols = sorted(random.sample(cols, random.randint(max(3, len(cols)-3), len(cols))))
      dx = random.choice((-1, 1))
      emitters = []
      previous = None
      for col in cols:
        colour = random.choice([c for c in range(1,10) if c != previous])
        emitters.append((1, col, 1, dx, colour))
        previous = colour
      return height, width, emitters, []
    n_emit = random.randint(1, 4)
    n_bars = random.choice([0, 1, 2, 2, 3, 3, 4, 4, 5, 6])
    occupied = set()
    emitters = []
    for _ in range(n_emit * 30):
      if len(emitters) == n_emit:
        break
      dy, dx = random.choice(_DIRS)
      tr = random.randint(1, height - 2)
      tc = random.randint(1, width - 2)
      cells = _l_cells(tr, tc, dy, dx)
      if not _free(cells, occupied, height, width):
        continue
      emitters.append((tr, tc, dy, dx, random.randint(1, 9)))
      occupied.update(cells)
    if not emitters:
      continue
    bars = []
    for _ in range(n_bars * 30):
      if len(bars) == n_bars:
        break
      length = random.choice([1, 2, 3, 3, 3])
      orient = random.choice('hv')
      if random.random() < 0.75:
        refl = _refl_map(bars)
        tr, tc, dy, dx, colour = random.choice(emitters)
        path = _trace(height, width, refl, tr, tc, dy, dx, colour)[0]
        if len(path) < 2:
          continue
        py, px, _ = path[random.randint(1, len(path) - 1)]
        ay, ax = random.choice(((py - 1, px), (py + 1, px),
                                (py, px - 1), (py, px + 1)))
        k = random.randint(0, length - 1)
        if orient == 'h':
          r, c = ay, ax - k
        else:
          r, c = ay - k, ax
      else:
        r = random.randint(0, height - 1)
        c = random.randint(0, width - 1)
      cells = _bar_cells(r, c, orient, length)
      if not _free(cells, occupied, height, width):
        continue
      bars.append((r, c, orient, length, random.randint(1, 9)))
      occupied.update(cells)
    if len(bars) != n_bars:
      continue
    refl = _refl_map(bars)
    used = set(occupied)
    total = 0
    good = True
    for tr, tc, dy, dx, colour in emitters:
      path, b, multi, done = _trace(height, width, refl, tr, tc, dy, dx,
                                    colour)
      if not done or multi or len(path) < 2:
        good = False
        break
      for y, x, _ in path:
        if (y, x) in used:
          good = False
          break
        used.add((y, x))
      if not good:
        break
      total += b
    if not good:
      continue
    if bars and total == 0:
      continue
    return height, width, emitters, bars
  raise RuntimeError('no valid ray scene found for requested canvas')


def generate(height=None, width=None, emitters=None, bars=None, mode=None):
  """Build one input/output pair.

  Args:
    height: grid rows (random 12..30 if omitted). Required with emitters.
    width: grid columns (random 12..30 if omitted). Required with emitters.
    emitters: list of (tip_row, tip_col, dy, dx, colour). The L occupies the
      tip, (tip_row - dy, tip_col) and (tip_row, tip_col - dx). If None, a
      fresh random scene is sampled.
    bars: list of (row, col, orient, length, colour) reflectors. orient 'h'
      runs right from (row, col) and 'v' runs down from it.
    mode: 'general', 'parallel', or None for a mixture, in random mode.
  """
  if emitters is None:
    if bars is not None:
      raise ValueError('explicit bars require explicit emitters')
    if mode not in (None, 'general', 'parallel'):
      raise ValueError('mode must be general or parallel')
    if any(v is not None and not 12 <= v <= 30 for v in (height,width)):
      raise ValueError('random canvas dimensions must be 12..30')
    height, width, emitters, bars = _sample(height,width,mode)
  bars = list(bars or [])
  grid = common.grid(width, height, 0)
  for r, c, orient, length, colour in bars:
    for y, x in _bar_cells(r, c, orient, length):
      grid[y][x] = colour
  for tr, tc, dy, dx, colour in emitters:
    for y, x in _l_cells(tr, tc, dy, dx):
      grid[y][x] = colour
  output = [row[:] for row in grid]
  refl = _refl_map(bars)
  for tr, tc, dy, dx, colour in emitters:
    path = _trace(height, width, refl, tr, tc, dy, dx, colour)[0]
    for y, x, col in path:
      output[y][x] = col
  return {'input': grid, 'output': output}


def validate():
  """Rebuild the canonical fixtures from explicit latent parameters."""
  train = [
      generate(20, 20,
               [(2, 7, 1, 1, 5), (4, 5, 1, 1, 2), (6, 3, 1, 1, 1),
                (8, 1, 1, 1, 3)],
               [(6, 10, 'h', 1, 5), (10, 10, 'h', 1, 2),
                (14, 10, 'h', 1, 1), (18, 10, 'h', 1, 3)]),
      generate(18, 18,
               [(7, 7, -1, -1, 2), (10, 10, 1, 1, 2)],
               [(1, 9, 'v', 3, 5), (4, 4, 'h', 3, 4), (7, 17, 'v', 3, 6),
                (8, 0, 'v', 3, 6), (13, 11, 'h', 3, 4),
                (14, 8, 'v', 3, 5)]),
      generate(20, 20,
               [(1, 1, 1, 1, 4)],
               [(5, 7, 'v', 3, 1), (7, 11, 'h', 3, 2), (9, 1, 'v', 3, 7),
                (15, 5, 'h', 3, 5)]),
  ]
  test = [
      generate(18, 18,
               [(1, 1, 1, 1, 1), (1, 3, 1, 1, 2), (1, 5, 1, 1, 7),
                (1, 7, 1, 1, 5), (1, 10, 1, -1, 2), (1, 12, 1, -1, 8),
                (1, 14, 1, -1, 6), (1, 16, 1, -1, 4), (3, 1, 1, 1, 2),
                (5, 1, 1, 1, 7), (7, 1, 1, 1, 5), (3, 16, 1, -1, 6),
                (5, 16, 1, -1, 8), (7, 16, 1, -1, 2)],
               []),
      generate(20, 19,
               [(1, 1, 1, 1, 7), (1, 17, 1, -1, 6), (18, 1, -1, 1, 6),
                (18, 17, -1, -1, 7)],
               [(6, 8, 'v', 3, 7), (6, 10, 'v', 3, 6), (11, 8, 'v', 3, 6),
                (11, 10, 'v', 3, 7)]),
  ]
  return {'train': train, 'test': test}
