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

"""Generator for ARC-AGI task a6953f00.

Rule: the input is a square mosaic of colours with side n. The output is the
2x2 block from the top two rows. If n is even, the block comes from the
top-right corner (columns n-2..n-1). If n is odd, it comes from the top-left
corner (columns 0..1).

Scope: square grids with side 3..30, filled from a sampled palette of 2..10
distinct colours in 0..9. The fixtures have sides 3, 4, 5 and 8. Larger sides
are synthetic extensions of the same parity rule. The four 2x2 corner windows
are pairwise different, so the wrong corner always gives a different answer.
All four windows contain at least two colours, so flatness gives no hint
about which corner is chosen. For n=3 the windows overlap, and distinctness
is enforced by bounded rejection sampling. Non-square grids are not
generated. Every original is square, and the rule is only defined by a single
side length.
"""

import random

import common


def _crop(cells, n):
  """Returns the 2x2 answer block determined by the parity of the side."""
  x = n - 2 if n % 2 == 0 else 0
  return [list(row[x:x + 2]) for row in cells[:2]]


def _block(cells, y, x):
  return [list(row[x:x + 2]) for row in cells[y:y + 2]]


def _set_block(cells, y, x, blk):
  for dy in range(2):
    for dx in range(2):
      cells[y + dy][x + dx] = blk[dy][dx]


def _is_flat(blk):
  return len(set(blk[0] + blk[1])) < 2


def _non_flat_block(palette):
  """Random 2x2 block that uses at least two colours (palette has >= 2)."""
  for _ in range(50):
    blk = [[random.choice(palette) for _ in range(2)] for _ in range(2)]
    if not _is_flat(blk):
      return blk
  blk = [[random.choice(palette) for _ in range(2)] for _ in range(2)]
  y, x = random.randrange(2), random.randrange(2)
  blk[y][x] = random.choice([c for c in palette if c != blk[y][x]])
  return blk


def _corner_origins(n):
  return [(0, 0), (0, n - 2), (n - 2, 0), (n - 2, n - 2)]


def _corners_ok(grid, n):
  """All four corner windows are pairwise distinct and non-flat."""
  corners = [_block(grid, y, x) for (y, x) in _corner_origins(n)]
  for i in range(4):
    if _is_flat(corners[i]):
      return False
    for j in range(i + 1, 4):
      if corners[i] == corners[j]:
        return False
  return True


def _is_colour(v):
  return type(v) is int and 0 <= v <= 9


def generate(size=None, cells=None, palette=None):
  """Returns {"input": grid, "output": grid} for a parity-corner crop scene.

  Args:
    size: side length n of the square input (an int in 3..30). Sampled if
      None. Out-of-range or non-int values raise ValueError. They are not
      clamped.
    cells: optional full square list of rows (the latent mosaic), used
      verbatim. This is how the original fixtures are reconstructed, because
      the whole scene is the mosaic itself. It must not be combined with
      `palette`. A `size` is allowed only if it equals the side of `cells`.
    palette: optional list of 2..10 distinct int colours (0..9) used to fill
      the mosaic. Sampled (4..10 distinct colours) if None.
  """
  if cells is not None:
    if not isinstance(cells, (list, tuple)):
      raise ValueError("cells must be a list of rows")
    n = len(cells)
    if (n < 3 or n > 30 or
        any(not isinstance(row, (list, tuple)) or len(row) != n
            for row in cells)):
      raise ValueError("cells must be a square grid with side 3..30")
    if any(not _is_colour(v) for row in cells for v in row):
      raise ValueError("cell colours must be ints in 0..9")
    if size is not None and size != n:
      raise ValueError("size conflicts with the side of cells")
    if palette is not None:
      raise ValueError("palette cannot be combined with explicit cells")
    grid = [list(row) for row in cells]
    return {"input": grid, "output": _crop(grid, n)}

  if size is None:
    # Bias toward small/medium sizes like the originals, but allow up to 30.
    size = random.choice([random.randint(3, 10), random.randint(3, 30)])
  if type(size) is not int or size < 3 or size > 30:
    raise ValueError("size must be an int in 3..30")
  n = size

  if palette is None:
    palette = random.sample(range(10), random.randint(4, 10))
  palette = list(palette)
  if (len(palette) < 2 or any(not _is_colour(c) for c in palette)
      or len(set(palette)) != len(palette)):
    raise ValueError("palette must hold 2..10 distinct int colours in 0..9")

  for _ in range(1000):
    grid = common.grid(n, n, 0)
    for y in range(n):
      for x in range(n):
        grid[y][x] = random.choice(palette)
    if n >= 4:
      # The corners are disjoint, so assign them directly as distinct,
      # non-flat blocks. Every corner gets the same treatment, so no corner
      # stands out statistically.
      used = []
      ok = True
      for (y, x) in _corner_origins(n):
        for _ in range(100):
          blk = _non_flat_block(palette)
          if blk not in used:
            break
        else:
          ok = False
          break
        used.append(blk)
        _set_block(grid, y, x, blk)
      if not ok:
        continue
    if _corners_ok(grid, n):
      return {"input": grid, "output": _crop(grid, n)}
  raise RuntimeError("could not construct a scene with distinct corners")


def validate():
  """Reconstructs the canonical train/test pairs via explicit latent cells."""
  train = [
      generate(cells=[[7, 5, 8, 2], [8, 0, 4, 7], [1, 6, 4, 7], [8, 9, 6, 9]]),
      generate(cells=[[0, 7, 9], [5, 6, 5], [3, 7, 9]]),
      generate(cells=[[5, 8, 8, 9, 2], [8, 0, 5, 6, 5], [7, 7, 2, 2, 9],
                      [5, 5, 1, 7, 4], [3, 3, 8, 7, 7]]),
  ]
  test = [
      generate(cells=[[3, 6, 0, 2, 8, 7, 9, 2], [6, 7, 5, 6, 3, 7, 3, 4],
                      [8, 0, 8, 6, 3, 0, 8, 3], [8, 8, 5, 9, 0, 1, 6, 7],
                      [7, 6, 9, 7, 8, 7, 4, 3], [7, 3, 8, 8, 3, 7, 6, 1],
                      [3, 7, 0, 7, 7, 0, 5, 1], [8, 7, 5, 2, 7, 7, 6, 6]]),
  ]
  return {"train": train, "test": test}
