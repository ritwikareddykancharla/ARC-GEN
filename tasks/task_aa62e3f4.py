"""Generator for ARC task aa62e3f4: outline the erased nested shape in its core colour.

Rule.  Each input is a single 4-connected nested shape drawn on an 8
background.  The shape has an outer colour, sometimes a middle colour, and a
small core (the least frequent non-background colour, 1..3 cells, fully
interior).  The output erases the whole shape to background and paints every
background cell that is ORTHOGONALLY adjacent to a former shape cell with the
core colour.  Diagonal-only neighbours stay 8, and outline cells that would
fall outside the grid are dropped (the shape may touch the grid border).

Scope.  Random scenes sample grid size (5..30 per side), a row-convex /
column-convex blob built from per-row spans (3..12 rows, up to 12 wide), its
placement (edge contact allowed), three distinct non-8 colours, an optional
middle layer, and 1..3 interior core cells.  The background is always 8, it is
always the strict majority colour of the grid, and there is exactly one shape;
multi-shape scenes, holes and non-unique least frequent colours are
deliberately not generated.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import collections
import random

import common

BACKGROUND = 8
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _random_scene():
  """Samples a fresh latent scene: size, placement and colour pattern."""
  for _ in range(500):
    height = random.randint(5, 30)
    width = random.randint(5, 30)
    hh = random.randint(3, min(12, height))
    l, r = 0, random.randint(0, 2)
    spans = [(l, r)]
    for i in range(1, hh):
      if i < hh / 2.0:
        nl = l + random.choice((-1, -1, 0))
        nr = r + random.choice((1, 1, 0))
      else:
        nl = l + random.choice((0, 1, 1))
        nr = r + random.choice((0, -1, -1))
      if nr < nl:
        nr = nl
      # Keep consecutive spans overlapping so the shape stays 4-connected.
      nl = min(nl, r)
      nr = max(nr, l)
      l, r = nl, nr
      spans.append((l, r))
    minl = min(s[0] for s in spans)
    ww = max(s[1] for s in spans) - minl + 1
    if ww > min(12, width):
      continue
    shape = set()
    for i, (a, b) in enumerate(spans):
      for c in range(a, b + 1):
        shape.add((i, c - minl))
    # The 8 background must remain the strict majority colour of the grid so
    # that the background is unambiguous (the shape must not dominate).
    if height * width - len(shape) <= len(shape):
      continue
    interior = sorted(
        (i, j) for (i, j) in shape
        if all((i + dr, j + dc) in shape for dr, dc in ORTHO))
    if not interior:
      continue
    k = random.randint(1, min(3, len(interior)))
    outer_count = len(shape) - len(interior)
    middle_count = len(interior) - k
    if outer_count <= k:
      continue
    use_middle = middle_count > k and random.random() < 0.5
    if not use_middle and (len(shape) - k) <= k:
      continue
    outer_color, middle_color, core_color = random.sample(
        [c for c in range(10) if c != BACKGROUND], 3)
    core_cells = set(random.sample(interior, k))
    interior_set = set(interior)
    pattern = []
    for i in range(hh):
      row = []
      for j in range(ww):
        if (i, j) not in shape:
          row.append(".")
        elif (i, j) in core_cells:
          row.append(str(core_color))
        elif use_middle and (i, j) in interior_set:
          row.append(str(middle_color))
        else:
          row.append(str(outer_color))
      pattern.append("".join(row))
    top = random.randint(0, height - hh)
    left = random.randint(0, width - ww)
    return width, height, top, left, pattern
  raise RuntimeError("could not sample a valid scene")


def generate(width=None, height=None, top=None, left=None, pattern=None):
  """Returns {"input": grid, "output": grid} for one scene.

  Args:
    width: grid width (sampled when pattern is None).
    height: grid height.
    top: row of the pattern's first line inside the grid.
    left: column of the pattern's first character inside the grid.
    pattern: list of equal-length strings; '.' is background, a digit is the
      colour of a shape cell.  The least frequent digit must be unique; it is
      the core colour used for the outline.
  """
  if pattern is None:
    width, height, top, left, pattern = _random_scene()
  cells = {}
  for r, row in enumerate(pattern):
    for c, ch in enumerate(row):
      if ch != ".":
        cells[(top + r, left + c)] = int(ch)
  counts = collections.Counter(cells.values())
  least = min(counts.values())
  core_colors = [col for col, n in counts.items() if n == least]
  if len(core_colors) != 1:
    raise ValueError("least frequent colour must be unique")
  core = core_colors[0]
  grid = common.grid(width, height, BACKGROUND)
  for (r, c), col in cells.items():
    grid[r][c] = col
  output = common.grid(width, height, BACKGROUND)
  for (r, c) in cells:
    for dr, dc in ORTHO:
      nr, nc = r + dr, c + dc
      if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in cells:
        output[nr][nc] = core
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical train/test fixtures from explicit latents."""
  train = [
      generate(width=16, height=16, top=10, left=0, pattern=[
          ".33..",
          "3223.",
          "32423",
          "32423",
          "32223",
          "3333."]),
      generate(width=7, height=7, top=0, left=1, pattern=[
          "3...",
          "33..",
          "313.",
          "3313",
          "313.",
          "33..",
          "3..."]),
  ]
  test = [
      generate(width=5, height=5, top=0, left=1, pattern=[
          ".4.",
          ".44",
          "444",
          "434",
          "444"]),
  ]
  return {"train": train, "test": test}
