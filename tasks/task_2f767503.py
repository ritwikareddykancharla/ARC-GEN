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

"""ARC-GEN style generator for task 2f767503.

Rule: the background is 7. Yellow (4) blobs are scattered over it. There is
one "gun": a straight bar of three grey (5) cells, plus a single maroon (9)
cell touching the middle of the bar on one side. The gun fires a ray from the
9 through the centre of the bar and on to the edge of the grid. Every
4-connected yellow blob that the ray touches is erased completely and becomes
background. Everything else stays the same.

Scope: the grid size is sampled in 8..30 per side. The bar can be horizontal
or vertical, and the 9 can be on either side of it, so all four firing
directions are covered. Yellow blobs are random 4-connected shapes of 1..20
cells on larger grids. At least one blob always sits on the firing line, and there are many
distractor blobs off the line. Some distractors may touch the line blobs
diagonally or touch the bar itself. The colours 7/4/5/9 and the bar length 3
are fixed, as in the original task.
"""

import random

import common

BG, BLOB, BAR, GUN = 7, 4, 5, 9


def _gun_cells(center, vertical, side):
  r, c = center
  if vertical:
    bar = [(r - 1, c), (r, c), (r + 1, c)]
    nine = (r, c + side)
    direction = (0, -side)
  else:
    bar = [(r, c - 1), (r, c), (r, c + 1)]
    nine = (r + side, c)
    direction = (-side, 0)
  return bar, nine, direction


def _components(cells):
  cells = set(cells)
  seen, comps = set(), []
  for start in sorted(cells):
    if start in seen:
      continue
    seen.add(start)
    stack, comp = [start], []
    while stack:
      r, c = stack.pop()
      comp.append((r, c))
      for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = (r + dr, c + dc)
        if q in cells and q not in seen:
          seen.add(q)
          stack.append(q)
    comps.append(comp)
  return comps


def _ray(nine, direction, width, height):
  r, c = nine
  out = []
  while 0 <= r < height and 0 <= c < width:
    out.append((r, c))
    r += direction[0]
    c += direction[1]
  return out


def _neighbours(cell):
  r, c = cell
  return [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]


def _grow(seed, size, width, height, forbidden):
  shape = [seed]
  for _ in range(size * 6):
    if len(shape) >= size:
      break
    r, c = random.choice(shape)
    q = random.choice(_neighbours((r, c)))
    if not (0 <= q[0] < height and 0 <= q[1] < width):
      continue
    if q in forbidden or q in shape:
      continue
    shape.append(q)
  return shape


def _random_scene(requested_width, requested_height, requested_center, requested_vertical, requested_side):
  for _ in range(200):
    width = requested_width if requested_width is not None else random.randint(8, 30)
    height = requested_height if requested_height is not None else random.randint(8, 30)
    vertical = requested_vertical if requested_vertical is not None else random.choice([True, False])
    side = requested_side if requested_side is not None else random.choice([-1, 1])
    r, c = requested_center if requested_center is not None else (random.randint(1, height - 2), random.randint(1, width - 2))
    bar, nine, direction = _gun_cells((r, c), vertical, side)
    if not (0 <= nine[0] < height and 0 <= nine[1] < width):
      continue
    ray = _ray(nine, direction, width, height)
    beyond = ray[3:]  # cells after the 9, bar centre and the next cell
    if len(beyond) < 2:
      continue
    blocked = set(bar) | {nine}
    fours = set()

    def forbidden_for_new():
      f = set(blocked) | set(fours)
      for cell in fours:
        f.update(_neighbours(cell))
      return f

    # Guarantee at least one blob on the firing line.
    for _ in range(random.randint(1, 3)):
      forb = forbidden_for_new()
      choices = [p for p in beyond if p not in forb]
      if not choices:
        break
      seed = random.choice(choices)
      fours.update(_grow(seed, random.randint(1, max(7, min(20, width * height // 40))), width, height, forb))
    if not fours:
      continue
    target = int(width * height * random.uniform(0.14, 0.24))
    for _ in range(max(400, width * height)):
      if len(fours) >= target:
        break
      forb = forbidden_for_new()
      seed = (random.randrange(height), random.randrange(width))
      if seed in forb:
        continue
      size = random.choice([1, 1, 2, 3, 4, 5, 6, 7, max(7, min(20, width * height // 40))])
      fours.update(_grow(seed, size, width, height, forb))
    hit = set(ray) & fours
    erased = {p for comp in _components(fours) if set(comp) & hit for p in comp}
    if not hit or len(fours - erased) < 3:
      continue
    return width, height, (r, c), vertical, side, fours
  raise RuntimeError("failed to build scene")


def generate(width=None, height=None, center=None, vertical=None, side=None,
             pattern=None):
  """Builds one input/output pair.

  Args:
    width: requested grid width, random 8..30; must match explicit pattern.
    height: requested grid height, random 8..30; must match explicit pattern.
    center: (row, col) of the middle cell of the 3-cell grey bar.
    vertical: True if the bar runs vertically, False if horizontally.
    side: -1 or +1. This is the offset of the 9 from the bar centre, across
      the bar (columns if vertical, rows if horizontal). The ray fires the
      opposite way.
    pattern: optional list of strings, one per row. '4' marks a yellow cell
      and any other character marks background. Used to rebuild fixtures.
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Grid dimensions must be integers in 1..30")
  if side not in (None, -1, 1):
    raise ValueError("side must be -1 or +1")
  if pattern is not None:
    if not pattern or not pattern[0] or any(len(row) != len(pattern[0]) for row in pattern) or max(len(pattern),len(pattern[0])) > 30:
      raise ValueError("Pattern must be rectangular and at most 30x30")
    if any(v is None for v in (center, vertical, side)):
      raise ValueError("Explicit pattern requires complete gun geometry")
    if (width is not None and width != len(pattern[0])) or (height is not None and height != len(pattern)):
      raise ValueError("Pattern does not match dimensions")
    height, width = len(pattern), len(pattern[0])
    fours = {(r, c) for r, row in enumerate(pattern)
             for c, ch in enumerate(row) if ch == "4"}
  else:
    if any(d is not None and d < 8 for d in (width, height)):
      raise ValueError("Random dimensions must be in 8..30")
    if center is not None and (width is None or height is None or not (1 <= center[0] < height-1 and 1 <= center[1] < width-1)):
      raise ValueError("Explicit center requires dimensions and an interior position")
    width, height, center, vertical, side, fours = _random_scene(width, height, center, vertical, side)
  bar, nine, direction = _gun_cells(center, vertical, side)
  if any(not (0 <= r < height and 0 <= c < width) for r,c in bar + [nine]) or (set(bar) | {nine}) & fours:
    raise ValueError("Gun outside grid or overlapping yellow blobs")
  grid = common.grid(width, height, BG)
  for r, c in fours:
    grid[r][c] = BLOB
  for r, c in bar:
    grid[r][c] = BAR
  grid[nine[0]][nine[1]] = GUN
  output = [row[:] for row in grid]
  ray = set(_ray(nine, direction, width, height))
  for comp in _components(fours):
    if ray & set(comp):
      for r, c in comp:
        output[r][c] = BG
  return {"input": grid, "output": output}


def validate():
  """Rebuilds the canonical examples from explicit latent parameters."""
  train = [
      generate(center=(7, 2), vertical=False, side=1, pattern=[
          "44...44.44",
          "4.....4.4.",
          ".44...4...",
          "..........",
          ".....4....",
          "4.4.......",
          "...4.4....",
          "......4...",
          "..........",
          ".........4",
      ]),
      generate(center=(7, 6), vertical=True, side=1, pattern=[
          "............",
          "4..4..4.....",
          "......4.4...",
          "..4..4....44",
          ".4......4...",
          ".4......44.4",
          ".44......44.",
          "4...4......4",
          "4..444....44",
          "..4.4...4...",
          "..4.........",
          ".........4..",
          ".4....4.....",
          "............",
      ]),
      generate(center=(2, 4), vertical=True, side=-1, pattern=[
          ".4...........",
          "44.....4.....",
          "44.....4.44..",
          ".......4.4..4",
          ".......4.....",
          "......444....",
          ".4...........",
          "...........4.",
          "....4.....4..",
          ".4.4.........",
      ]),
  ]
  test = [
      generate(center=(4, 3), vertical=True, side=-1, pattern=[
          "...4.......",
          "4......4...",
          "4..........",
          ".......4..4",
          "4....44..44",
          "4...4.44...",
          "....4......",
          "....4.4....",
          "........4.4",
      ]),
  ]
  return {"train": train, "test": test}
