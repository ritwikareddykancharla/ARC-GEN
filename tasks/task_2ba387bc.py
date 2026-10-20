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

"""ARC task 2ba387bc: sort hollow and solid 4x4 squares into two columns.

Rule: the input is a black canvas holding several 4x4 squares, each a
distinct colour. A square is either solid (16 cells) or hollow (a 4x4 ring
with a 2x2 background hole). The output is 8 wide. The left 4-wide column
stacks the hollow squares and the right column stacks the solid squares.
Within each column, squares are ordered by their top row in the input, with
ties broken by the left column. The output height is 4 * max(#hollow,
#solid). Slots that are left over in the shorter column stay background.

Scope: canvas width and height are sampled in 10..30. There are 1..5
hollow and 1..5 solid squares, at most 8 squares in total. Colours are
distinct and drawn from 1..9. Squares never touch, not even diagonally.
Top rows are distinct within each group, so the ordering is unambiguous.
"""

import random

import common


def _separated(r, c, placed):
  for (pr, pc, _, _) in placed:
    if abs(pr - r) < 5 and abs(pc - c) < 5:
      return False
  return True


def _try_layout(width, height, kinds):
  """Place squares of the given kinds (True = hollow) at random positions."""
  placed = []
  for hollow in kinds:
    ok = False
    for _ in range(200):
      r = random.randint(0, height - 4)
      c = random.randint(0, width - 4)
      if not _separated(r, c, placed):
        continue
      if any(p[0] == r and p[3] == hollow for p in placed):
        continue
      placed.append((r, c, 0, hollow))
      ok = True
      break
    if not ok:
      return None
  return placed


def _fallback_layout(kinds):
  """Deterministic lattice layout on a 30x30 canvas (always valid)."""
  spots = [(5 * i, 5 * j) for i in range(6) for j in range(6)]
  random.shuffle(spots)
  placed = []
  for hollow in kinds:
    for (r, c) in spots:
      if any(p[0] == r and p[1] == c for p in placed):
        continue
      if any(p[0] == r and p[3] == hollow for p in placed):
        continue
      placed.append((r, c, 0, hollow))
      break
  return 30, 30, placed


def _stamp(g, r, c, color, hollow):
  for dr in range(4):
    for dc in range(4):
      if hollow and 1 <= dr <= 2 and 1 <= dc <= 2:
        continue
      g[r + dr][c + dc] = color


def generate(width=None, height=None, squares=None):
  """Build one input/output pair.

  Args:
    width: canvas width (columns). Sampled if None.
    height: canvas height (rows). Sampled if None.
    squares: optional list of (row, col, color, hollow) tuples giving each
      square's top-left corner, its colour and whether it is hollow. If
      None, a random non-touching layout is sampled.
  """
  if squares is None:
    n_h = random.randint(1, 5)
    n_s = random.randint(1, 5)
    while n_h + n_s > 8:
      if random.random() < 0.5:
        n_h -= 1
      else:
        n_s -= 1
    kinds = [True] * n_h + [False] * n_s
    random.shuffle(kinds)
    placed = None
    for _ in range(100):
      w = width if width is not None else random.randint(10, 30)
      h = height if height is not None else random.randint(10, 30)
      if w * h < 40 * len(kinds):
        continue
      placed = _try_layout(w, h, kinds)
      if placed is not None:
        width, height = w, h
        break
    if placed is None:
      if width is not None or height is not None:
        raise ValueError("could not place squares in requested canvas")
      width, height, placed = _fallback_layout(kinds)
    colors = random.sample(range(1, 10), len(placed))
    squares = [(p[0], p[1], colors[i], p[3]) for i, p in enumerate(placed)]

  grid = common.grid(width, height, 0)
  for (r, c, color, hollow) in squares:
    _stamp(grid, r, c, color, hollow)

  hollows = sorted([s for s in squares if s[3]], key=lambda s: (s[0], s[1]))
  solids = sorted([s for s in squares if not s[3]], key=lambda s: (s[0], s[1]))
  n = max(len(hollows), len(solids), 1)
  output = common.grid(8, 4 * n, 0)
  for i, s in enumerate(hollows):
    _stamp(output, 4 * i, 0, s[2], True)
  for i, s in enumerate(solids):
    _stamp(output, 4 * i, 4, s[2], False)
  return {"input": grid, "output": output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  H, S = True, False
  train = [
      generate(width=24, height=23, squares=[
          (1, 2, 1, S), (4, 9, 2, S), (6, 17, 8, H), (12, 1, 7, S),
          (13, 8, 3, H), (15, 17, 6, S), (18, 3, 4, H)]),
      generate(width=21, height=20, squares=[
          (1, 4, 2, H), (3, 11, 1, S), (9, 1, 4, H), (10, 7, 8, S),
          (14, 14, 9, S)]),
      generate(width=23, height=20, squares=[
          (1, 2, 8, H), (3, 11, 4, S), (6, 4, 2, S), (14, 17, 7, H)]),
      generate(width=22, height=22, squares=[
          (1, 1, 2, H), (3, 14, 8, H), (7, 3, 3, S), (9, 10, 6, H),
          (15, 10, 4, S)]),
  ]
  test = [
      generate(width=19, height=24, squares=[
          (1, 1, 6, S), (4, 8, 4, H), (7, 14, 7, S), (11, 2, 1, S),
          (14, 8, 2, H), (19, 3, 8, S)]),
  ]
  return {"train": train, "test": test}
