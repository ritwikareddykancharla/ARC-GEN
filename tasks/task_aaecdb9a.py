"""Generator for ARC task aaecdb9a (bar chart of diagonally-connected objects).

Rule.  The input is a fixed 10x10 canvas with background 7 holding small
shapes in the five legend colours 5, 2, 8, 9 and 6.  For every colour the
number of 8-connected (diagonals count) objects is counted.  The output is a
bar chart that is always 5 columns wide: colour 5 -> column 0, 2 -> column 1,
8 -> column 2, 9 -> column 3, 6 -> column 4.  Each present colour draws a
bottom-anchored bar whose height is its object count; the output height is
the largest count.  Absent colours leave an empty column.

Scope.  Random scenes keep the intrinsic 10x10 size, background 7 and the
fixed legend.  They vary which legend colours are present (2..5), how many
objects each colour has (1..6), the shapes (singles, dominoes, diagonal
chains, pluses, X's, rings, blocks, L's, T's, lines, blobs) and positions.
Same-colour objects are kept out of each other's 8-neighbourhood so object
counts are unambiguous; different colours may touch (irrelevant to the rule).
Non-legend colours are never used.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common

BG = 7
SIZE = 10
LEGEND = {5: 0, 2: 1, 8: 2, 9: 3, 6: 4}


def _norm(cells):
  """Shift a cell list so its minimum row and column are zero."""
  my = min(y for y, _ in cells)
  mx = min(x for _, x in cells)
  return sorted(set((y - my, x - mx) for y, x in cells))


def _blob():
  """Random 8-connected blob of 3..6 cells grown by a random walk."""
  n = random.randint(3, 6)
  cells = {(0, 0)}
  while len(cells) < n:
    y, x = random.choice(sorted(cells))
    dy, dx = random.choice([(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                            if (a, b) != (0, 0)])
    cells.add((y + dy, x + dx))
  return _norm(list(cells))


def _random_shape(small_only):
  """Return a random shape (relative cells)."""
  small = [
      lambda: [(0, 0)],
      lambda: [(0, 0), (0, 1)],
      lambda: [(0, 0), (1, 0)],
      lambda: [(0, 0), (1, 1)],
      lambda: [(0, 1), (1, 0)],
      lambda: [(0, 0), (1, 1), (2, 2)],
      lambda: [(0, 2), (1, 1), (2, 0)],
      lambda: [(0, 0), (0, 1), (1, 0)],
      lambda: [(0, 0), (0, 1), (1, 1)],
      lambda: [(0, 0), (0, 1), (1, 0), (1, 1)],
      lambda: [(0, 0), (0, 1), (1, 1), (2, 2)],
  ]
  medium = [
      lambda: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
      lambda: [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
      lambda: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
      lambda: [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
      lambda: [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
      lambda: [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
      lambda: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3)],
      lambda: [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (3, 3)],
      lambda: [(0, x) for x in range(random.randint(3, 9))],
      lambda: [(y, 0) for y in range(random.randint(3, 9))],
      lambda: [(i, i) for i in range(random.randint(3, 5))],
      _blob,
  ]
  if small_only:
    return _norm(random.choice(small)())
  r = random.random()
  if r < 0.3:
    return [(0, 0)]
  if r < 0.65:
    return _norm(random.choice(small)())
  return _norm(random.choice(medium)())


def _neighbors8(y, x):
  for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
      if dy or dx:
        yield y + dy, x + dx


def _fits(cells, colour, occupied):
  """Cells free, in bounds, and no same-colour cell in the 8-neighbourhood."""
  cellset = set(cells)
  for y, x in cells:
    if not (0 <= y < SIZE and 0 <= x < SIZE):
      return False
    if (y, x) in occupied:
      return False
    for ny, nx in _neighbors8(y, x):
      if (ny, nx) not in cellset and occupied.get((ny, nx)) == colour:
        return False
  return True


def _sample_objects():
  """Sample a list of (colour, cells) objects forming a valid scene."""
  for _ in range(80):
    k = random.randint(2, 5)
    colours = random.sample(sorted(LEGEND), k)
    height = random.randint(2, 6)
    counts = {c: random.randint(1, height) for c in colours}
    counts[random.choice(colours)] = height
    plan = []
    for c in colours:
      plan += [c] * counts[c]
    random.shuffle(plan)
    many = len(plan) > 8
    occupied = {}
    objects = []
    ok = True
    for c in plan:
      placed = False
      for attempt in range(120):
        shape = _random_shape(small_only=(many or attempt > 40))
        hgt = max(y for y, _ in shape) + 1
        wid = max(x for _, x in shape) + 1
        if hgt > SIZE or wid > SIZE:
          continue
        oy = random.randint(0, SIZE - hgt)
        ox = random.randint(0, SIZE - wid)
        cells = [(y + oy, x + ox) for y, x in shape]
        if _fits(cells, c, occupied):
          for cell in cells:
            occupied[cell] = c
          objects.append((c, cells))
          placed = True
          break
      if not placed:
        ok = False
        break
    if ok:
      return objects
  raise RuntimeError("could not place objects")


def generate(objects=None):
  """Returns an input/output pair for task aaecdb9a.

  Args:
    objects: optional list of (colour, cells) where cells are absolute (row,
      col) coordinates on the 10x10 canvas.  Each entry is one diagonally-
      connected object; same-colour entries must not touch (even diagonally)
      and no cells may overlap.  Colours must be legend colours.  When None a
      fresh random scene is sampled.
  """
  if objects is None:
    objects = _sample_objects()
  occupied = {}
  for colour, cells in objects:
    if colour not in LEGEND:
      raise ValueError("non-legend colour")
    if not _fits(cells, colour, occupied):
      raise ValueError("objects overlap or same-colour objects touch")
    for cell in cells:
      occupied[cell] = colour
  grid = common.grid(SIZE, SIZE, BG)
  for (y, x), colour in occupied.items():
    grid[y][x] = colour
  counts = {}
  for colour, _ in objects:
    counts[colour] = counts.get(colour, 0) + 1
  height = max(counts.values())
  out = common.grid(len(LEGEND), height, BG)
  for colour, n in counts.items():
    col = LEGEND[colour]
    for y in range(height - n, height):
      out[y][col] = colour
  return {"input": grid, "output": out}


def validate():
  """Reconstructs the canonical train/test fixtures from explicit objects."""
  train = [
      generate(objects=[
          (6, [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]),
          (9, [(0, 8), (0, 9), (1, 8), (1, 9), (2, 7), (3, 6)]),
          (2, [(6, 0), (6, 2), (7, 1), (8, 0), (8, 2)]),
          (6, [(6, 7), (7, 6), (7, 7), (7, 8), (8, 7)]),
      ]),
      generate(objects=[
          (5, [(0, 8), (0, 9), (1, 9)]),
          (5, [(2, 2), (2, 3), (2, 4), (3, 2), (3, 4), (4, 2), (4, 3), (4, 4)]),
          (5, [(4, 9)]),
          (8, [(6, 7), (7, 6), (7, 7), (7, 8), (8, 5), (8, 6), (8, 7), (8, 8),
               (8, 9)]),
          (9, [(8, 0), (8, 1)]),
      ]),
      generate(objects=[
          (8, [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]),
          (8, [(0, 6)]),
          (8, [(3, 2)]),
          (8, [(5, 0)]),
          (8, [(7, 0)]),
          (9, [(0, 8), (0, 9)]),
          (9, [(2, 6), (3, 6)]),
          (9, [(2, 8), (2, 9), (3, 8), (3, 9)]),
          (9, [(5, 8), (5, 9)]),
          (2, [(5, 5), (5, 6), (6, 6)]),
          (6, [(7, 2), (7, 3), (7, 4), (8, 2), (8, 4), (9, 2), (9, 3), (9, 4)]),
          (5, [(7, 8), (8, 7), (8, 8), (8, 9), (9, 8)]),
      ]),
  ]
  test = [
      generate(objects=[
          (2, [(0, 0), (0, 1), (1, 0), (1, 1)]),
          (2, [(0, 3)]),
          (2, [(2, 3), (3, 0), (3, 1), (3, 2)]),
          (2, [(2, 5), (2, 6), (3, 6)]),
          (2, [(0, 8), (0, 9)]),
          (2, [(8, 5), (9, 6), (9, 7), (9, 8)]),
          (8, [(0, 6)]),
          (8, [(2, 8), (2, 9), (3, 8), (4, 8), (5, 0), (5, 1), (5, 2), (5, 3),
               (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (6, 8), (7, 7), (7, 8)]),
          (6, [(7, 2), (8, 0), (8, 1), (8, 2), (8, 3), (9, 2)]),
      ]),
  ]
  return {"train": train, "test": test}
