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

"""Generator for ARC task 16de56c4: periodic lines growing from one border.

Every coloured row (or column) of the input touches the same single border of
the grid: the "growth" side.  Reading inward from that border each such line
holds a seed pair -- the border cell and the next cell of the same colour,
whose distance is the period -- and optionally one marker of another colour
farther along.  The output repeats the seed colour with its period all the way
to the opposite edge.  If the marker lies on the line's lattice (its distance
from the border is a multiple of the period) the whole line, seed included, is
recoloured to the marker colour and stops at the marker; an off-lattice marker
is left untouched while the line marches past it.  Extra seed-colour cells on
the lattice are simply part of the line.

Scope: all four growth sides, grid sizes from 5 x 7 up to 25 x 22, periods
1..5, markers of all three kinds (none / on-lattice / off-lattice), optional
extra seed-colour lattice cells, repeated line colours across lines.
Background is always 0.  Deliberately not supported: more than one marker per
line, markers between the two seed cells, lines that do not touch the growth
border, non-zero backgrounds.
"""

import random

import common


SIDES = ("left", "right", "top", "bottom")


def _place(side, length, slot, dist):
  """Maps (line slot, distance from growth border) to (row, col)."""
  if side == "left":
    return slot, dist
  if side == "right":
    return slot, length - 1 - dist
  if side == "top":
    return dist, slot
  return length - 1 - dist, slot


def _dims(side, slots, length):
  """Returns (width, height) of the grid for the given orientation."""
  if side in ("left", "right"):
    return length, slots
  return slots, length


def _touch_sides(grid):
  """Returns the set of borders that every coloured row/column touches."""
  h, w = len(grid), len(grid[0])
  found = set()
  rows = [r for r in range(h) if any(grid[r][c] for c in range(w))]
  if rows and all(grid[r][0] for r in rows):
    found.add("left")
  if rows and all(grid[r][w - 1] for r in rows):
    found.add("right")
  cols = [c for c in range(w) if any(grid[r][c] for r in range(h))]
  if cols and all(grid[0][c] for c in cols):
    found.add("top")
  if cols and all(grid[h - 1][c] for c in cols):
    found.add("bottom")
  return found


def _build(side, slots, length, lines):
  """Constructs input and output grids from the latent line descriptions."""
  width, grid_h = _dims(side, slots, length)
  inp = common.grid(width, grid_h, 0)
  out = common.grid(width, grid_h, 0)
  for (slot, color, period, marker, extras) in lines:
    # Input: seed pair, extra seed cells, marker.
    cells = {0: color, period: color}
    for e in extras:
      cells[e] = color
    if marker is not None:
      cells[marker[0]] = marker[1]
    for dist, c in cells.items():
      y, x = _place(side, length, slot, dist)
      inp[y][x] = c
    # Output: extended (possibly recoloured and truncated) line.
    end, fill = length - 1, color
    if marker is not None and marker[0] % period == 0:
      end, fill = marker
    elif marker is not None:
      y, x = _place(side, length, slot, marker[0])
      out[y][x] = marker[1]
    for dist in range(0, end + 1, period):
      y, x = _place(side, length, slot, dist)
      out[y][x] = fill
  return inp, out


def _sample_lines(slots, length):
  """Samples a list of latent line descriptions."""
  n = random.randint(2, min(8, slots))
  chosen = sorted(random.sample(range(slots), n))
  lines = []
  max_period = min(5, (length - 1) // 2)
  for slot in chosen:
    period = random.randint(1, max_period)
    color = random.randint(1, 9)
    other = [c for c in range(1, 10) if c != color]
    marker = None
    kind = random.random()
    if kind < 0.35:
      k = random.randint(2, (length - 1) // period)
      marker = (k * period, random.choice(other))
    elif kind < 0.6 and period >= 2:
      cands = [d for d in range(period + 1, length) if d % period]
      if cands:
        marker = (random.choice(cands), random.choice(other))
    extras = ()
    limit = marker[0] if (marker and marker[0] % period == 0) else length
    cands = [d for d in range(2 * period, limit, period)]
    if cands and period >= 2 and random.random() < 0.25:
      extras = (random.choice(cands),)
    lines.append((slot, color, period, marker, extras))
  return lines


def generate(side=None, slots=None, length=None, lines=None):
  """Returns input and output grids according to the given parameters.

  Args:
    side: border the lines grow from ("left", "right", "top", "bottom").
    slots: number of parallel line positions (rows for left/right growth,
      columns for top/bottom growth).
    length: extent of each line from the growth border to the opposite edge.
    lines: list of (slot, color, period, marker, extras); marker is None or
      (distance, color), extras is a tuple of extra seed-colour lattice
      distances.
  """
  if lines is not None:
    inp, out = _build(side, slots, length, lines)
    return {"input": inp, "output": out}
  for _ in range(300):
    s = side if side is not None else random.choice(SIDES)
    n = slots if slots is not None else random.randint(5, 22)
    ln = length if length is not None else random.randint(7, 25)
    ls = _sample_lines(n, ln)
    inp, out = _build(s, n, ln, ls)
    if _touch_sides(inp) != {s}:
      continue
    if inp == out:
      continue
    filled = sum(1 for row in inp for v in row if v)
    if 2 * filled >= len(inp) * len(inp[0]):
      continue
    return {"input": inp, "output": out}
  # Fallback: a guaranteed-valid simple scene.
  return generate(side="left", slots=6, length=9,
                  lines=[(1, 1, 3, None, ()), (4, 9, 2, (6, 6), ())])


def validate():
  """Validates the generator by reconstructing the canonical examples."""
  train = [
      generate(side="left", slots=12, length=9,
               lines=[(1, 1, 3, None, ()), (4, 1, 1, None, ()),
                      (8, 9, 2, (6, 6), ()), (11, 8, 1, (7, 3), ())]),
      generate(side="bottom", slots=20, length=9,
               lines=[(2, 3, 3, (6, 4), ()), (9, 3, 1, None, ()),
                      (15, 1, 4, None, ()), (18, 9, 2, (5, 5), ())]),
      generate(side="bottom", slots=15, length=7,
               lines=[(1, 2, 2, None, ()), (5, 2, 1, None, ()),
                      (9, 6, 1, None, ()), (13, 2, 3, None, ())]),
  ]
  test = [
      generate(side="right", slots=9, length=21,
               lines=[(1, 2, 3, (11, 7), ()), (2, 5, 1, (14, 9), ()),
                      (3, 2, 1, (17, 6), ()), (5, 6, 5, (7, 1), ()),
                      (7, 8, 3, None, ()), (8, 7, 2, (13, 4), ())]),
      generate(side="top", slots=21, length=9,
               lines=[(1, 2, 1, (6, 4), ()), (4, 3, 2, (4, 2), ()),
                      (7, 4, 3, None, ()), (9, 6, 4, (6, 3), ()),
                      (11, 7, 1, None, ()), (13, 7, 2, (6, 6), ()),
                      (15, 9, 3, None, ()), (17, 2, 1, None, ()),
                      (19, 7, 3, (6, 9), ())]),
  ]
  return {"train": train, "test": test}
