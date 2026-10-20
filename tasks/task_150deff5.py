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

# Bounds for rejection sampling (random synthetic scenes only).
_MAX_SCENE_TRIES = 2000
_MAX_LAYOUT_TRIES = 20000
_MAX_TILINGS = 20000

# Bricks anchored at their first cell in reading order.
_BRICKS = (
    (((0, 0), (0, 1), (1, 0), (1, 1)), True),
    (((0, 0), (0, 1), (0, 2)), False),
    (((0, 0), (1, 0), (2, 0)), False),
)


def _brick_cells(row, col, idx):
  if idx == 0:
    offs = [(0, 0), (0, 1), (1, 0), (1, 1)]
  elif idx == 1:
    offs = [(0, 0), (1, 0), (2, 0)]
  else:
    offs = [(0, 0), (0, 1), (0, 2)]
  return [(row + dr, col + dc) for dr, dc in offs]


def _num_distinct_colourings(cells, limit=2):
  """Counts distinct square/bar colourings of a cell set, capped at limit.

  Enumerates every exact cover of the cells by 2x2 squares and 1x3 / 3x1
  bars. The count does not depend on any solver's search order. Two tilings
  that give the same colouring count once. Returns `limit` if the enumeration
  is too large to be conclusive, so that case is treated as ambiguous.
  """
  order = sorted(set(cells))
  shape = set(order)
  n = len(order)
  used = set()
  square_cells = []
  colourings = set()
  state = {"tilings": 0, "aborted": False}

  def rec(i):
    if len(colourings) >= limit or state["aborted"]:
      return
    while i < n and order[i] in used:
      i += 1
    if i == n:
      state["tilings"] += 1
      if state["tilings"] > _MAX_TILINGS:
        state["aborted"] = True
        return
      colourings.add(frozenset(square_cells))
      return
    r, c = order[i]
    for offs, is_square in _BRICKS:
      cs = [(r + dr, c + dc) for dr, dc in offs]
      if all(p in shape and p not in used for p in cs):
        used.update(cs)
        if is_square:
          square_cells.extend(cs)
        rec(i + 1)
        if is_square:
          del square_cells[-4:]
        used.difference_update(cs)

  rec(0)
  if state["aborted"]:
    return limit
  return len(colourings)


def _sample_layout(width):
  """Original box/stick sampling, with bounded retries. None on failure."""
  num_boxes = 2 if width < 10 else 3
  for _ in range(_MAX_LAYOUT_TRIES):
    brows = [common.randint(1, 5) for _ in range(num_boxes)]
    bcols = [common.randint(1, 6) for _ in range(num_boxes)]
    bidxs = [0] * num_boxes
    # Check that no two boxes are alongside + parallel to each other.
    parallel = False
    for j in range(num_boxes):
      for i in range(j):
        if brows[i] == brows[j] and abs(bcols[i] - bcols[j]) <= 2:
          parallel = True
        if bcols[i] == bcols[j] and abs(brows[i] - brows[j]) <= 2:
          parallel = True
    if parallel: continue
    bwides, btalls = [2] * num_boxes, [2] * num_boxes
    if not common.overlaps(brows, bcols, bwides, btalls): break
  else:
    return None
  if common.randint(0, 1): num_boxes += 1
  for _ in range(_MAX_LAYOUT_TRIES):
    srows = [common.randint(1, 5) for _ in range(num_boxes)]
    scols = [common.randint(1, 6) for _ in range(num_boxes)]
    sidxs = [common.randint(1, 2) for _ in range(num_boxes)]
    # Check that no two sticks are alongside + parallel to each other.
    parallel = False
    for j in range(num_boxes):
      for i in range(j):
        if sidxs[i] != sidxs[j]: continue
        if srows[i] == srows[j] and abs(scols[i] - scols[j]) <= 1:
          parallel = True
        if scols[i] == scols[j] and abs(srows[i] - srows[j]) <= 1:
          parallel = True
    if parallel: continue
    swides = [1 if idx == 1 else 3 for idx in sidxs]
    stalls = [3 if idx == 1 else 1 for idx in sidxs]
    if not common.overlaps(brows + srows, bcols + scols, bwides + swides,
                           btalls + stalls):
      return brows + srows, bcols + scols, bidxs + sidxs
  return None


def generate(width=None, height=None, rows=None, cols=None, idxs=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the grid
    height: the height of the grid
    rows: a list of vertical coordinates where toys should be placed
    cols: a list of horizontal coordinates where toys should be placed
    idxs: a list of toy indices (0=box, 1=tall stick, 2=flat stick)
  """
  if width is None:
    for _ in range(_MAX_SCENE_TRIES):
      width, height = common.randint(9, 11), common.randint(8, 9)
      layout = _sample_layout(width)
      if layout is None:
        continue
      rows, cols, idxs = layout
      cells = [p for r, c, i in zip(rows, cols, idxs)
               for p in _brick_cells(r, c, i)]
      # Reject scenes whose grey cells admit more than one square/bar
      # colouring: the label must be a function of the visible input.
      if _num_distinct_colourings(cells) == 1:
        break
    else:
      raise RuntimeError("Failed to sample an unambiguous scene.")

  grid, output = common.grids(width, height)
  for row, col, idx in zip(rows, cols, idxs):
    if idx == 0:
      for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        grid[row + dr][col + dc] = common.gray()
        output[row + dr][col + dc] = common.cyan()
    if idx == 1:
      for dr, dc in [(0, 0), (1, 0), (2, 0)]:
        grid[row + dr][col + dc] = common.gray()
        output[row + dr][col + dc] = common.red()
    if idx == 2:
      for dr, dc in [(0, 0), (0, 1), (0, 2)]:
        grid[row + dr][col + dc] = common.gray()
        output[row + dr][col + dc] = common.red()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=11, height=9, rows=[1, 3, 4, 3, 2, 6],
               cols=[2, 4, 6, 3, 4, 5], idxs=[0, 0, 0, 1, 2, 2]),
      generate(width=10, height=8, rows=[1, 1, 4, 1, 1, 4],
               cols=[1, 4, 5, 3, 6, 4], idxs=[0, 0, 0, 1, 1, 1]),
      generate(width=9, height=8, rows=[1, 4, 1, 3], cols=[4, 4, 1, 3],
               idxs=[0, 0, 2, 1]),
  ]
  test = [
      generate(width=11, height=8, rows=[0, 2, 5, 0, 2, 4, 1],
               cols=[2, 4, 5, 5, 1, 3, 6], idxs=[0, 0, 0, 2, 2, 2, 1]),
  ]
  return {"train": train, "test": test}
