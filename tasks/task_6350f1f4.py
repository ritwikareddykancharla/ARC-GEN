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

"""ARC-GEN style generator for task 6350f1f4.

Rule: divider lines of colour 0 cut the grid into equal square panels. Each
panel is one of two kinds:

- a pattern panel, which is a copy of a single two-colour motif;
- a solid panel, which is filled with the motif's minority colour.

Colour 5 noise blobs are splattered over panels and dividers. In the output
the two kinds swap roles:

- every solid panel receives the motif;
- every pattern panel becomes solid in the motif's majority colour;
- all noise is removed, so the dividers are pure 0.

Scope: the panel size is 2..6 and the panel counts are 2..6 per axis, limited
so that the grid fits within 30x30. Non-square panel layouts and panel sizes
or counts beyond the fixtures' range (2..4 panels, size 2..4) are synthetic
extensions. The motif colours are any two distinct colours other than 0 and 5.
The number and placement of minority cells are random, and the minority is
strict. The set of solid panels is random, with at least one panel and at most
half of them.

Noise is made of random-walk blobs of 5 that may cross dividers. Every scene
satisfies all of the following:

- each divider keeps at least one visible 0;
- no panel row or column is entirely noise, so it cannot look like a divider;
- at least one pattern panel is noise-free, so the motif is recoverable;
- every solid panel shows at least one visible cell where the motif has its
  majority colour, so the panel cannot pass for a pattern panel.

If no noisy candidate passes, the noise budget shrinks over a bounded number of
attempts. The final fallback is the same latent scene without noise, which is
always valid.
"""

import random

import common


NOISE = 5
COLORS = [1, 2, 3, 4, 6, 7, 8, 9]


def _counts(motif):
  cnt = {}
  for row in motif:
    for v in row:
      cnt[v] = cnt.get(v, 0) + 1
  return cnt


def _major_minor(motif):
  """Returns (major, minor) and rejects motifs that do not fit the task."""
  size = len(motif)
  if size < 2 or any(len(row) != size for row in motif):
    raise ValueError("motif must be a square of side >= 2")
  if any(type(v) is not int or v not in COLORS for row in motif for v in row):
    raise ValueError("motif colours must be integers in 1..9 excluding 5")
  cnt = _counts(motif)
  if len(cnt) != 2 or 0 in cnt or NOISE in cnt:
    raise ValueError("motif must use exactly two colours other than 0 and 5")
  (major, n_major), (minor, n_minor) = sorted(cnt.items(),
                                              key=lambda kv: -kv[1])
  if n_major == n_minor:
    raise ValueError("motif needs a strict majority colour")
  return major, minor


def _valid(grid, size, rows, cols, motif, solids, major):
  """Checks that the noisy scene is unambiguous."""
  height, width = len(grid), len(grid[0])
  step = size + 1
  # Dividers must keep at least one 0 cell.
  for r in range(height):
    if r % step == size and all(v == NOISE for v in grid[r]):
      return False
  for c in range(width):
    if c % step == size and all(grid[r][c] == NOISE for r in range(height)):
      return False
  # Panel lines must never look like dividers, so they cannot be all noise.
  for r in range(height):
    if r % step != size:
      if all(grid[r][c] == NOISE for c in range(width) if c % step != size):
        return False
  for c in range(width):
    if c % step != size:
      if all(grid[r][c] == NOISE for r in range(height) if r % step != size):
        return False
  clean_pattern = False
  cells = [(y, x) for y in range(size) for x in range(size)]
  for pr in range(rows):
    for pc in range(cols):
      top, left = pr * step, pc * step
      noisy = any(grid[top + y][left + x] == NOISE for y, x in cells)
      if (pr, pc) in solids:
        # A visible cell must contradict the motif.
        if not any(grid[top + y][left + x] != NOISE and motif[y][x] == major
                   for y, x in cells):
          return False
      elif not noisy:
        clean_pattern = True
  return clean_pattern


def generate(size=None, rows=None, cols=None, motif=None, solids=None,
             noise=None):
  """Returns an input/output pair.

  Args:
    size: the side length of each square panel, 2..6 when sampled. If a motif
      is given, the size defaults to the motif's side and must match it.
    rows: the number of panels stacked vertically (2..6 when sampled; any
      value that fits within 30 rows is accepted when given).
    cols: the number of panels placed horizontally (same limits as rows).
    motif: a size x size list of rows that uses two colours other than 0 and
      5, with a strict majority.
    solids: a list of (panel_row, panel_col) panels that are solid minority.
      At least one panel must remain a pattern panel.
    noise: a dict mapping a grid row to the list of grid columns painted 5.
      An explicit noise map must give an unambiguous scene, otherwise a
      ValueError is raised.
  """
  if motif is not None:
    motif = [list(row) for row in motif]
    if size is None:
      size = len(motif)
    elif size != len(motif):
      raise ValueError("size does not match the motif")
  for name, value in (("rows",rows),("cols",cols)):
    if value is not None and (type(value) is not int or value < 1):
      raise ValueError(name + " must be a positive integer")
  if size is None:
    feasible = [s for s in range(2,7)
                if all(v is None or v*(s+1)-1<=30 for v in (rows,cols))]
    if not feasible:
      raise ValueError("no sampled panel size fits the requested layout")
    size = random.choice(feasible)
  if type(size) is not int or size < 2:
    raise ValueError("size must be at least 2")
  limit = 31 // (size + 1)
  max_panels = min(6, limit)
  if rows is None:
    if max_panels < 2:
      raise ValueError("size too large for a multi-panel grid")
    rows = random.randint(2, max_panels)
  if cols is None:
    if max_panels < 2:
      raise ValueError("size too large for a multi-panel grid")
    cols = random.randint(2, max_panels)
  if not (1 <= rows <= limit and 1 <= cols <= limit) or rows * cols < 2:
    raise ValueError("panel layout does not fit within 30x30")
  if motif is None:
    major, minor = random.sample(COLORS, 2)
    k = random.randint(1, (size * size - 1) // 2)
    spots = set(random.sample(range(size * size), k))
    motif = [[minor if y * size + x in spots else major for x in range(size)]
             for y in range(size)]
  major, minor = _major_minor(motif)
  total = rows * cols
  if solids is None:
    count = random.randint(1, max(1, total // 2))
    panels = [(r, c) for r in range(rows) for c in range(cols)]
    solids = random.sample(panels, count)
  solids = set(tuple(p) for p in solids)
  for pr, pc in solids:
    if not (type(pr) is int and type(pc) is int and
            0 <= pr < rows and 0 <= pc < cols):
      raise ValueError("solid panel out of range")
  if not solids or len(solids) >= total:
    raise ValueError("need at least one solid and one pattern panel")

  step = size + 1
  height, width = rows * step - 1, cols * step - 1
  base = common.grid(width, height, 0)
  output = common.grid(width, height, 0)
  for pr in range(rows):
    for pc in range(cols):
      top, left = pr * step, pc * step
      for y in range(size):
        for x in range(size):
          if (pr, pc) in solids:
            base[top + y][left + x] = minor
            output[top + y][left + x] = motif[y][x]
          else:
            base[top + y][left + x] = motif[y][x]
            output[top + y][left + x] = major

  def paint(cells):
    grid = [row[:] for row in base]
    for r in cells:
      for c in cells[r]:
        if not (type(r) is int and type(c) is int and
                0 <= r < height and 0 <= c < width):
          raise ValueError("noise cell out of range")
        grid[r][c] = NOISE
    return grid

  if noise is not None:
    grid = paint(noise)
    if not _valid(grid, size, rows, cols, motif, solids, major):
      raise ValueError("noise makes the scene ambiguous")
  else:
    # The noiseless scene is always valid; it is only the last-resort fallback.
    grid = [row[:] for row in base]
    attempts = 60
    max_blobs = total // 2 + 1
    for attempt in range(attempts):
      budget = int(round(max_blobs * (attempts - attempt) / attempts))
      cells = {}
      blobs = random.randint(0, max(0, budget))
      for _ in range(blobs):
        r, c = random.randrange(height), random.randrange(width)
        for _ in range(random.randint(1, 2 * size + 2)):
          cells.setdefault(r, set()).add(c)
          dr, dc = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
          r = min(height - 1, max(0, r + dr))
          c = min(width - 1, max(0, c + dc))
      candidate = paint(cells)
      if _valid(candidate, size, rows, cols, motif, solids, major):
        grid = candidate
        break
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical examples."""
  train = [
      generate(size=2, rows=2, cols=2, motif=[[3, 2], [3, 3]],
               solids=[(0, 1)], noise={}),
      generate(size=2, rows=2, cols=2, motif=[[1, 1], [1, 8]],
               solids=[(1, 1)],
               noise={2: [3], 3: [0, 2, 4], 4: [0, 1]}),
      generate(size=3, rows=3, cols=3,
               motif=[[3, 3, 4], [3, 3, 4], [4, 3, 3]],
               solids=[(0, 2), (1, 2), (2, 0)],
               noise={5: [7], 6: [4], 7: [4, 5], 8: [3, 4, 5],
                      9: [1, 2, 3], 10: [2]}),
      generate(size=3, rows=3, cols=3,
               motif=[[4, 4, 2], [2, 4, 2], [4, 4, 4]],
               solids=[(0, 2), (1, 0), (1, 2)],
               noise={2: [7, 10], 3: [10], 4: [7], 5: [5, 7, 8],
                      6: [2, 5, 6, 9], 7: [2], 8: [1, 2, 3, 7],
                      9: [0, 1, 2, 5], 10: [1]}),
  ]
  test = [
      generate(size=4, rows=4, cols=4,
               motif=[[1, 1, 1, 2], [1, 2, 2, 1], [2, 1, 1, 1],
                      [1, 2, 1, 1]],
               solids=[(0, 3), (1, 1), (1, 2), (2, 0), (3, 1)],
               noise={0: [16], 1: [15, 16], 2: [15], 3: [15],
                      4: [13, 14, 15], 5: [13, 14, 15],
                      6: [4, 5, 6, 12, 13], 7: [3, 4, 5, 11, 12, 16, 17],
                      8: [2, 3, 9, 10, 11, 12, 13, 14, 15, 17, 18],
                      9: [2, 8, 9, 11, 17, 18],
                      10: [2, 3, 7, 8, 9, 11, 17],
                      11: [0, 1, 2, 3, 9, 10, 11, 12, 16, 17],
                      12: [9, 10, 12, 13, 15, 16],
                      13: [9, 11, 12, 13, 14, 15],
                      14: [9, 10, 11, 13, 14], 15: [9, 13, 14, 15],
                      16: [8, 10, 12, 13, 14, 15], 17: [7, 10, 11, 14],
                      18: [11, 12, 13, 14]}),
  ]
  return {"train": train, "test": test}
