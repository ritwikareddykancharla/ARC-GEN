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

"""ARC task 1ae2feb7: periodic stamping across a vertical divider.

Rule: a vertical divider column splits the grid. On one side (the pattern
side) some rows hold short horizontal runs of colour, stacked outward from
the divider. The other side is empty. For each pattern row, every run of
colour c and length n stamps c on the empty side at distances 1, 1+n,
1+2n, ... from the divider. Runs nearer the divider are drawn on top of
farther runs (so a length-1 run touching the divider fills the whole row).

Scope: random grid size, divider column, divider colour, optional divider
that stops one row short of the bottom, pattern side left or right, a set
of non-adjacent pattern rows each with 1-3 contiguous runs (lengths 1-5),
optionally separated from the divider by one blank cell. Background is 0.
"""

import random

import common


def _render(width, height, divider_col, divider_color, divider_length,
            pattern_side, rows):
  """Builds the input and output grids from latent parameters."""
  grid = common.grid(width, height, 0)
  for y in range(divider_length):
    grid[y][divider_col] = divider_color
  # out_step: direction from divider toward the output (empty) side.
  out_step = 1 if pattern_side == "left" else -1
  output = [row[:] for row in grid]
  for (y, offset, runs) in rows:
    dist = offset + 1
    for (color, length) in runs:
      for _ in range(length):
        grid[y][divider_col - out_step * dist] = color
        output[y][divider_col - out_step * dist] = color
        dist += 1
  for (y, offset, runs) in rows:
    for (color, length) in reversed(runs):
      d = 1
      while 0 <= divider_col + out_step * d < width:
        output[y][divider_col + out_step * d] = color
        d += length
  return {"input": grid, "output": output}


def _sample_runs(space, divider_color, offset):
  """Samples runs (nearest first) that fit within `space` cells."""
  nruns = random.randint(1, min(3, space))
  runs = []
  remaining = space
  prev = None
  for k in range(nruns):
    left_after = nruns - k - 1
    max_len = min(5, remaining - left_after)
    length = random.randint(1, max_len)
    choices = [c for c in range(1, 10) if c != prev]
    if k == 0 and offset == 0:
      choices = [c for c in choices if c != divider_color]
    color = random.choice(choices)
    runs.append((color, length))
    remaining -= length
    prev = color
  return runs


def generate(width=None, height=None, divider_col=None, divider_color=None,
             divider_length=None, pattern_side=None, rows=None):
  """Returns an input/output pair.

  Args:
    width: grid width.
    height: grid height.
    divider_col: x coordinate of the divider column.
    divider_color: colour of the divider.
    divider_length: number of rows (from the top) the divider covers.
    pattern_side: "left" or "right", side holding the runs.
    rows: list of (row, offset, runs); offset is the blank gap between the
      divider and the first run; runs is a list of (colour, length) listed
      from the divider outward.
  """
  if rows is None:
    if any(v is not None and not 5 <= v <= 30 for v in (width, height)):
      raise ValueError("random grid dimensions must be 5..30")
    if pattern_side is not None and pattern_side not in ("left", "right"):
      raise ValueError("pattern_side must be left or right")
    if divider_color is not None and divider_color not in range(1, 10):
      raise ValueError("divider colour must be nonzero")
    for _ in range(100):
      h = height if height is not None else random.randint(5, 30)
      w = width if width is not None else random.randint(6, 30)
      side = pattern_side or random.choice(["left", "right"])
      if divider_col is None:
        pw = random.randint(2, min(8, w - 3))
        dc = pw if side == "left" else w - 1 - pw
      else:
        dc = divider_col
        pw = dc if side == "left" else w - 1 - dc
      if pw < 2 or not 1 <= dc < w - 1:
        raise ValueError("divider must leave room for pattern and output")
      col = divider_color if divider_color is not None else random.randint(1, 9)
      dl = divider_length if divider_length is not None else (h if random.random() < 0.8 else h - 1)
      if dl not in (h, h - 1):
        raise ValueError("divider length must be height or height minus one")
      candidates = list(range(dl))
      random.shuffle(candidates)
      want = random.randint(2, (dl + 1) // 2)
      chosen = []
      for y in candidates:
        if len(chosen) >= want:
          break
        if all(abs(y - z) > 1 for z in chosen):
          chosen.append(y)
      if not chosen:
        continue
      chosen.sort()
      sampled_rows = []
      for y in chosen:
        offset = 1 if random.random() < 0.25 else 0
        sampled_rows.append((y, offset, _sample_runs(pw - offset, col, offset)))
      if any(len(r[2]) > 1 for r in sampled_rows) or random.random() < 0.3:
        return _render(w, h, dc, col, dl, side, sampled_rows)
    raise RuntimeError("could not sample a periodic-pattern scene")
  return _render(width, height, divider_col, divider_color, divider_length,
                 pattern_side, rows)


def validate():
  """Reconstructs the canonical examples via explicit latent parameters."""
  train = [
      generate(16, 11, 5, 2, 11, "left",
               [(3, 1, [(1, 4)]), (5, 0, [(8, 1), (6, 4)]),
                (7, 0, [(3, 5)]), (9, 0, [(5, 4)])]),
      generate(16, 11, 5, 2, 11, "left",
               [(3, 1, [(1, 2), (2, 1)]), (7, 0, [(4, 2), (3, 3)])]),
      generate(15, 13, 3, 2, 13, "left",
               [(1, 0, [(1, 2)]), (5, 0, [(5, 1)]), (9, 0, [(7, 3)])]),
  ]
  test = [
      generate(20, 10, 5, 4, 9, "left",
               [(0, 0, [(5, 4)]), (1, 0, [(1, 2)]), (2, 0, [(2, 1)]),
                (5, 0, [(6, 2), (7, 1)]), (7, 0, [(8, 3), (6, 2)])]),
      generate(15, 8, 12, 3, 8, "left",
               [(1, 0, [(2, 1)]), (3, 0, [(4, 2)]), (5, 0, [(6, 4)]),
                (7, 0, [(7, 1), (9, 1)])]),
      generate(15, 8, 12, 3, 8, "right",
               [(1, 0, [(4, 1)]), (3, 0, [(7, 2)]), (5, 0, [(6, 1)]),
                (7, 0, [(5, 2)])]),
  ]
  return {"train": train, "test": test}
