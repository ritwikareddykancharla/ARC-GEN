# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator."""

import common

_MAX_ATTEMPTS = 200
_NODE_CAP = 60000
_BIG = 1 << 20


def _step(run, good):
  if not good:
    return 0
  if run >= _BIG:
    return run
  return run + 1


def _caps(g, red, gray):
  h, w = len(g), len(g[0])
  ok = [[g[r][c] in (red, gray) for c in range(w)] for r in range(h)]
  cap = [[_BIG] * w for _ in range(h)]
  for c in range(w):
    run = _BIG
    for r in range(h):
      cap[r][c] = min(cap[r][c], run)
      run = _step(run, ok[r][c])
    run = _BIG
    for r in range(h - 1, -1, -1):
      cap[r][c] = min(cap[r][c], run)
      run = _step(run, ok[r][c])
  for r in range(h):
    run = _BIG
    for c in range(w):
      cap[r][c] = min(cap[r][c], run)
      run = _step(run, ok[r][c])
    run = _BIG
    for c in range(w - 1, -1, -1):
      cap[r][c] = min(cap[r][c], run)
      run = _step(run, ok[r][c])
  for r in range(h):
    for c in range(w):
      if not ok[r][c]:
        cap[r][c] = -1
  return cap


def _candidate(r, c, length, h, w, redset):
  cells = set([(r, c)])
  for d in range(1, length + 1):
    for y, x in ((r - d, c), (r + d, c), (r, c - d), (r, c + d)):
      if 0 <= y < h and 0 <= x < w:
        cells.add((y, x))
  halo = set()
  for y, x in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        halo.add((y + dy, x + dx))
  for p in halo:
    if p in redset and p not in cells:
      return None
  reds_in = frozenset(p for p in cells if p in redset)
  if not reds_in:
    return None
  return (frozenset(cells), frozenset(halo), reds_in)


def _solve_length(length, h, w, cap, reds, redset, node_cap, sol_cap):
  """All non-touching cross covers of the red cells with one arm length."""
  cache, cand = {}, {}
  for q in reds:
    qr, qc = q
    pos = set()
    for d in range(-length, length + 1):
      pos.add((qr, qc + d))
      pos.add((qr + d, qc))
    lst = []
    for r, c in sorted(pos):
      if r < 0 or r >= h or c < 0 or c >= w or cap[r][c] < length:
        continue
      if (r, c) not in cache:
        cache[(r, c)] = _candidate(r, c, length, h, w, redset)
      if cache[(r, c)] is not None:
        lst.append((r, c))
    if not lst:
      return [], False
    cand[q] = lst
  order = sorted(reds, key=lambda q: (len(cand[q]), q))
  found = {}
  state = [0, False]

  def rec(covered, chosen, blocked, cells):
    if state[0] >= node_cap:
      state[1] = True
      return
    state[0] += 1
    q = None
    for p in order:
      if p not in covered:
        q = p
        break
    if q is None:
      found[cells] = (tuple(sorted(chosen)), cells)
      return
    for key in cand[q]:
      ccells, halo, rin = cache[key]
      if ccells & blocked or rin & covered:
        continue
      rec(covered | rin, chosen + [key], blocked | halo, cells | ccells)
      if state[1] or len(found) >= sol_cap:
        return

  rec(frozenset(), [], frozenset(), frozenset())
  return list(found.values()), state[1]


def _unique_cross_cells(grid, red, gray):
  """Returns the unique set of cross cells explaining the input, else None.

  Hypothesis space (independent of any solver tie-break): any shared arm
  length L >= 1, centres anywhere in the grid, arms clipped at the border,
  all in-grid cross cells red or grey, every red cell on some cross, every
  cross containing a red cell, crosses pairwise non-touching (Chebyshev
  distance >= 2). Uniqueness is on the resulting output cell set.
  """
  h, w = len(grid), len(grid[0])
  reds = sorted((r, c) for r in range(h) for c in range(w) if grid[r][c] == red)
  if not reds:
    return None
  redset = set(reds)
  cap = _caps(grid, red, gray)
  outputs = set()
  for length in range(1, max(h, w) + 1):
    found, truncated = _solve_length(length, h, w, cap, reds, redset,
                                     _NODE_CAP, 2)
    if truncated:
      raise RuntimeError("Cross exact-cover search budget exhausted")
    for _, cells in found:
      outputs.add(cells)
    if len(outputs) > 1:
      return None
  if len(outputs) != 1:
    return None
  return next(iter(outputs))


def _scene_is_determined(example):
  grid, output = example["input"], example["output"]
  red, gray, cyan = common.red(), common.gray(), common.cyan()
  try:
    cells = _unique_cross_cells(grid, red, gray)
  except RuntimeError:
    return False
  if cells is None:
    return False
  height, width = len(grid), len(grid[0])
  label = frozenset((r, c) for r in range(height) for c in range(width)
                    if output[r][c] in (red, cyan))
  return cells == label


def _sample_colors(width, height):
  # First, create random static.
  grid = common.grid(width, height)
  for r, c in common.random_pixels(width, height):
    grid[r][c] = common.gray()
  # Second, create a few crosses underneath.
  length = common.randint(2, 3)
  rows, cols, lens = [], [], []
  for _ in range(4):
    r = common.randint(length, height - length - 1)
    c = common.randint(length, width - length - 1)
    if common.overlaps(rows + [r], cols + [c], lens + [2 * length],
                       lens + [2 * length], 2): continue
    rows.append(r)
    cols.append(c)
    lens.append(2 * length)
    # Paint every cross cell exactly once (the original double-painted the
    # centre, which made it always hidden).
    cells = [(r, c + idx) for idx in range(-length, length + 1)]
    cells += [(r + idx, c) for idx in range(-length, length + 1) if idx != 0]
    for rr, cc in cells:
      grid[rr][cc] = common.cyan() if grid[rr][cc] else common.red()
  # Finally, flatten the colors into a list.
  colors = []
  for r in range(height):
    for c in range(width):
      colors.append(grid[r][c])
  return colors


def _render(width, height, colors):
  grid, output = common.grids(width, height)
  for r in range(height):
    for c in range(width):
      output[r][c] = colors[r * width + c]
      if colors[r * width + c] != common.cyan():
        grid[r][c] = colors[r * width + c]
      else:
        grid[r][c] = common.gray()
  return {"input": grid, "output": output}


def generate(width=None, height=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the input grid
    height: the height of the input grid
    colors: a list of colors to be used in the input grid
  """
  if width is None:
    for _ in range(_MAX_ATTEMPTS):
      height = common.randint(10, 25)
      width = height + common.randint(-3, 3)
      example = _render(width, height, _sample_colors(width, height))
      if _scene_is_determined(example):
        return example
    raise RuntimeError("could not sample an unambiguous cross scene")
  return _render(width, height, colors)


def validate():
  """Validates the generator."""
  train = [
      generate(width=22, height=20,
               colors=[0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 5,
                       0, 0, 0, 0, 5, 0, 0, 5, 5, 5, 5, 0, 0, 5, 0, 5, 0, 5, 0,
                       0, 5, 0, 0, 5, 5, 5, 0, 5, 5, 0, 5, 5, 5, 0, 0, 5, 5, 2,
                       0, 0, 0, 0, 0, 0, 0, 5, 0, 5, 0, 0, 5, 5, 0, 0, 0, 5, 0,
                       0, 0, 2, 5, 5, 5, 0, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 0,
                       0, 0, 5, 0, 0, 2, 5, 5, 0, 0, 5, 0, 5, 5, 0, 0, 5, 0, 0,
                       5, 0, 0, 0, 5, 2, 8, 2, 8, 8, 8, 2, 5, 0, 5, 0, 0, 0, 0,
                       5, 5, 0, 5, 0, 0, 0, 0, 0, 5, 0, 2, 5, 0, 0, 5, 0, 0, 5,
                       5, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 5, 0, 2, 5, 0, 5, 5,
                       0, 5, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 0, 5, 0, 0, 0, 2, 0,
                       0, 0, 0, 0, 0, 5, 0, 5, 5, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5,
                       0, 5, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 0, 5, 0, 5, 5, 5,
                       5, 5, 0, 0, 0, 0, 5, 0, 5, 5, 5, 0, 5, 5, 0, 5, 5, 0, 0,
                       8, 0, 0, 5, 0, 5, 5, 0, 5, 5, 0, 5, 5, 0, 0, 5, 5, 0, 0,
                       5, 5, 0, 2, 5, 5, 5, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 0, 0,
                       0, 5, 0, 5, 0, 0, 8, 5, 5, 0, 0, 0, 0, 0, 5, 0, 0, 5, 5,
                       0, 0, 0, 5, 0, 0, 2, 8, 8, 2, 2, 2, 2, 0, 0, 0, 5, 5, 0,
                       5, 0, 0, 5, 0, 5, 0, 0, 5, 5, 0, 0, 8, 5, 0, 5, 0, 0, 5,
                       0, 0, 5, 5, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 2, 0, 5, 5,
                       0, 5, 0, 0, 5, 0, 0, 5, 5, 5, 0, 0, 0, 0, 0, 5, 5, 0, 2,
                       5, 0, 0, 0, 5, 0, 0, 0, 5, 5, 0, 0, 0, 5, 5, 5, 0, 5, 5,
                       5, 0, 0, 0, 5, 5, 5, 5, 0, 0, 5, 5, 0, 5, 0, 0, 0, 5, 5,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 5, 0, 5, 0,
                       0, 0, 5]),
      generate(width=20, height=20,
               colors=[0, 5, 0, 5, 0, 0, 0, 5, 5, 0, 5, 5, 0, 0, 0, 5, 5, 0, 5,
                       5, 5, 5, 0, 5, 5, 5, 0, 5, 5, 0, 5, 0, 0, 5, 0, 0, 0, 5,
                       5, 0, 0, 5, 0, 5, 5, 0, 8, 5, 0, 5, 0, 0, 5, 0, 0, 5, 0,
                       0, 5, 5, 5, 0, 0, 5, 5, 0, 2, 5, 0, 5, 0, 5, 0, 0, 0, 5,
                       5, 5, 5, 5, 0, 5, 0, 5, 2, 8, 2, 2, 2, 0, 5, 5, 0, 5, 0,
                       5, 5, 0, 0, 0, 5, 5, 0, 0, 5, 5, 2, 5, 5, 5, 0, 5, 0, 0,
                       5, 5, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 8, 5, 0, 0, 5, 5, 0,
                       0, 5, 0, 0, 5, 0, 5, 0, 0, 0, 5, 0, 5, 0, 5, 5, 5, 0, 5,
                       5, 5, 0, 0, 5, 5, 0, 5, 5, 0, 0, 0, 5, 0, 0, 5, 5, 5, 5,
                       0, 5, 5, 8, 0, 0, 5, 0, 5, 5, 0, 0, 5, 0, 5, 5, 5, 0, 5,
                       5, 0, 5, 0, 8, 5, 5, 5, 5, 5, 5, 0, 5, 5, 0, 5, 5, 5, 5,
                       5, 0, 5, 2, 8, 2, 2, 2, 0, 0, 5, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 5, 5, 5, 0, 0, 8, 0, 0, 5, 0, 5, 0, 0, 5, 0, 0, 5, 0,
                       5, 5, 0, 5, 5, 5, 5, 8, 5, 5, 5, 5, 0, 5, 5, 0, 0, 5, 5,
                       0, 8, 0, 0, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0,
                       5, 5, 8, 0, 5, 5, 0, 5, 5, 5, 5, 0, 0, 5, 5, 0, 0, 5, 0,
                       5, 8, 8, 2, 2, 8, 5, 0, 0, 5, 0, 0, 5, 5, 0, 0, 0, 5, 5,
                       0, 0, 5, 5, 2, 5, 0, 5, 5, 0, 0, 5, 0, 5, 5, 0, 0, 0, 0,
                       5, 0, 5, 0, 5, 8, 0, 5, 5, 5, 0, 0, 5, 0, 0, 0, 5, 0, 0,
                       0, 5, 0, 5, 5, 0, 5, 5, 5, 0, 5, 5, 5, 0, 5, 0, 0, 5, 5,
                       5, 5, 5, 0, 5, 0, 5, 0, 5, 5, 0, 0, 5, 5, 0, 0, 0, 0, 0,
                       5]),
      generate(width=19, height=18,
               colors=[0, 0, 5, 0, 5, 0, 5, 5, 5, 5, 0, 5, 5, 0, 0, 0, 5, 5, 0,
                       0, 0, 5, 5, 5, 0, 5, 5, 5, 5, 0, 0, 5, 5, 5, 5, 5, 0, 5,
                       0, 5, 5, 5, 0, 5, 0, 5, 5, 0, 0, 0, 5, 5, 5, 0, 5, 0, 0,
                       5, 5, 5, 5, 5, 0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 5, 0, 0,
                       5, 5, 0, 0, 0, 5, 5, 5, 0, 5, 5, 8, 5, 0, 0, 0, 5, 0, 0,
                       5, 0, 0, 0, 0, 0, 5, 0, 5, 0, 5, 2, 5, 0, 0, 5, 0, 5, 5,
                       5, 0, 5, 0, 0, 5, 5, 0, 5, 2, 2, 8, 2, 2, 5, 5, 0, 5, 0,
                       0, 8, 0, 5, 5, 5, 5, 5, 0, 5, 0, 8, 5, 5, 5, 0, 5, 5, 5,
                       5, 8, 5, 0, 5, 5, 5, 5, 0, 0, 5, 2, 5, 5, 5, 0, 0, 0, 0,
                       8, 2, 2, 8, 0, 0, 5, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0,
                       5, 2, 5, 5, 5, 0, 0, 5, 5, 5, 5, 0, 0, 5, 5, 5, 5, 0, 5,
                       0, 2, 5, 0, 5, 5, 0, 0, 5, 5, 5, 5, 5, 0, 5, 5, 5, 5, 0,
                       0, 5, 0, 0, 5, 5, 0, 0, 5, 5, 0, 0, 5, 0, 0, 5, 0, 0, 0,
                       5, 0, 0, 5, 5, 5, 5, 5, 0, 0, 5, 5, 5, 0, 5, 5, 5, 0, 5,
                       0, 5, 5, 5, 0, 0, 5, 0, 0, 0, 5, 0, 5, 5, 5, 5, 0, 0, 0,
                       5, 5, 0, 0, 5, 5, 5, 5, 0, 5, 5, 0, 5, 0, 5, 0, 0, 0, 0,
                       5, 0, 5, 0, 5, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0, 5, 0, 5,
                       0, 5, 5, 0, 5, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0, 5, 5, 5,
                       5]),
      generate(width=12, height=11,
               colors=[0, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 5, 5, 0, 5, 0, 0, 0, 0,
                       0, 5, 0, 0, 5, 5, 0, 5, 0, 0, 5, 5, 0, 2, 0, 5, 0, 5, 5,
                       0, 0, 5, 0, 5, 0, 2, 5, 0, 5, 5, 0, 0, 5, 5, 5, 2, 8, 2,
                       2, 2, 0, 5, 5, 5, 0, 5, 5, 0, 5, 2, 0, 0, 5, 5, 5, 5, 0,
                       5, 0, 0, 5, 8, 0, 0, 0, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0,
                       0, 0, 5, 5, 0, 5, 0, 0, 0, 0, 5, 0, 0, 5, 0, 0, 0, 5, 5,
                       5, 5, 5, 0, 0, 0, 5, 0, 0, 0, 0, 5, 0, 0, 5, 5, 5, 5]),
  ]
  test = [
      generate(width=22, height=19,
               colors=[0, 5, 0, 5, 0, 0, 5, 5, 0, 5, 0, 0, 0, 5, 0, 5, 0, 0, 0,
                       5, 5, 0, 0, 5, 0, 5, 5, 0, 0, 0, 5, 5, 0, 0, 5, 5, 0, 0,
                       0, 0, 0, 5, 5, 5, 0, 0, 0, 0, 5, 5, 8, 0, 0, 0, 0, 5, 5,
                       0, 0, 5, 5, 0, 0, 5, 5, 5, 0, 0, 5, 5, 0, 5, 8, 5, 0, 5,
                       0, 5, 0, 5, 0, 5, 5, 0, 5, 5, 5, 0, 0, 5, 0, 5, 2, 2, 8,
                       2, 2, 5, 0, 0, 5, 0, 5, 5, 5, 0, 0, 5, 5, 0, 0, 0, 0, 5,
                       0, 5, 2, 5, 5, 5, 0, 5, 0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 5,
                       5, 0, 0, 5, 5, 2, 0, 5, 5, 0, 0, 0, 8, 0, 0, 0, 5, 5, 5,
                       5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 8, 0, 5, 0,
                       0, 5, 0, 5, 0, 5, 5, 5, 5, 5, 0, 0, 5, 5, 0, 5, 2, 8, 2,
                       8, 8, 0, 0, 5, 5, 5, 0, 0, 0, 0, 5, 5, 5, 0, 0, 5, 0, 0,
                       0, 5, 8, 0, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 0, 5,
                       0, 5, 0, 5, 5, 2, 5, 0, 5, 0, 0, 5, 5, 0, 0, 5, 5, 5, 0,
                       0, 0, 5, 5, 5, 5, 0, 0, 5, 0, 5, 5, 0, 0, 0, 5, 5, 5, 5,
                       0, 0, 5, 8, 5, 0, 0, 5, 5, 0, 5, 0, 5, 5, 0, 0, 5, 5, 0,
                       5, 0, 0, 5, 5, 5, 8, 5, 5, 5, 5, 0, 0, 5, 5, 5, 5, 5, 0,
                       0, 5, 0, 5, 5, 5, 0, 8, 8, 2, 2, 2, 5, 5, 5, 0, 5, 8, 5,
                       0, 5, 0, 0, 5, 5, 0, 5, 0, 0, 0, 5, 2, 5, 0, 5, 0, 5, 0,
                       5, 8, 5, 5, 0, 0, 0, 0, 5, 5, 5, 5, 5, 0, 0, 2, 0, 5, 5,
                       0, 0, 2, 2, 2, 2, 2, 5, 0, 5, 0, 5, 5, 5, 0, 5, 0, 0, 5,
                       0, 5, 0, 0, 0, 0, 0, 8, 0, 5, 5, 5, 0, 5, 5, 0, 5, 5, 5,
                       5, 5, 0, 5, 0, 5, 5, 5, 5, 0, 8, 0, 0, 5, 5, 0, 5, 0,
                       5]),
  ]
  return {"train": train, "test": test}
