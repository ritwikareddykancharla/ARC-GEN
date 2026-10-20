"""Generator for ARC task 4df5b0ae (bottom-row size sort).

Rule: the input is a background-7 canvas carrying several solid-coloured
4-connected objects (objects are kept 8-separated from each other so each is
its own component).  Optionally a one-cell-thick frame of a distinct colour
runs around the entire edge of the grid; its bounding box is the whole grid,
so it is a border rather than an object.  The output discards the frame,
sorts the remaining objects by cell count (ascending, all counts distinct),
and stamps them unchanged along the bottom row: each object is bottom-aligned
to the last row and starts in the column right after the previous object's
bounding box.

Scope: grid sizes 8..20 per side, 2..6 objects with distinct sizes 1..12,
random polyomino shapes (bars, blocks, L's and irregular shapes), optional
frame, colour reuse between objects allowed, objects may touch the grid edge
or the frame.  Background 7 is always the strict majority colour.  Not
supported: ties in size, multi-colour objects, objects whose bounding-box
widths sum past the canvas width.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random
import common

BG = 7


def _rect(h, w):
  """Returns the cells of an h x w solid block, origin at (0, 0)."""
  return [(y, x) for y in range(h) for x in range(w)]


def _polyomino(size, max_h, max_w):
  """Grows a random 4-connected polyomino of `size` cells within a box.

  Args:
    size: number of cells.
    max_h: maximum bounding-box height.
    max_w: maximum bounding-box width.
  Returns a normalised sorted cell list, or None if growth got stuck.
  """
  cells = {(0, 0)}
  for _ in range(4 * size + 10):
    if len(cells) >= size:
      break
    ys = [y for y, _ in cells]
    xs = [x for _, x in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    frontier = set()
    for y, x in cells:
      for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c = (y + dy, x + dx)
        if c in cells:
          continue
        ny0, ny1 = min(y0, c[0]), max(y1, c[0])
        nx0, nx1 = min(x0, c[1]), max(x1, c[1])
        if ny1 - ny0 + 1 <= max_h and nx1 - nx0 + 1 <= max_w:
          frontier.add(c)
    if not frontier:
      return None
    cells.add(random.choice(sorted(frontier)))
  if len(cells) < size:
    return None
  ys = [y for y, _ in cells]
  xs = [x for _, x in cells]
  y0, x0 = min(ys), min(xs)
  return sorted((y - y0, x - x0) for y, x in cells)


def _bbox(cells):
  h = 1 + max(y for y, _ in cells)
  w = 1 + max(x for _, x in cells)
  return h, w


def _build(width, height, has_frame, frame_colour, objects):
  """Renders input and output grids from latent objects."""
  grid = common.grid(width, height, BG)
  if has_frame:
    for x in range(width):
      grid[0][x] = frame_colour
      grid[height - 1][x] = frame_colour
    for y in range(height):
      grid[y][0] = frame_colour
      grid[y][width - 1] = frame_colour
  for colour, cells, oy, ox in objects:
    for y, x in cells:
      grid[oy + y][ox + x] = colour
  output = common.grid(width, height, BG)
  cursor = 0
  for colour, cells, _, _ in sorted(objects, key=lambda o: len(o[1])):
    h, w = _bbox(cells)
    for y, x in cells:
      output[height - h + y][cursor + x] = colour
    cursor += w
  return grid, output


def _background_is_majority(grid):
  """True when BG strictly outnumbers every other colour in the grid."""
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bg_count = counts.get(BG, 0)
  return all(bg_count > n for c, n in counts.items() if c != BG)


def _sample_scene():
  """Samples one valid random scene; returns (width, height, frame, objs) or None."""
  width = random.randint(8, 20)
  height = random.randint(8, 20)
  has_frame = random.random() < 0.3
  frame_colour = None
  margin = 1 if has_frame else 0
  palette = [c for c in range(10) if c != BG]
  if has_frame:
    frame_colour = random.choice(palette)
    palette = [c for c in palette if c != frame_colour]
  inner_h = height - 2 * margin
  inner_w = width - 2 * margin
  n = random.randint(2, 6)
  sizes = random.sample(range(1, 13), n)
  # Keep background a comfortable majority: foreground (objects + frame)
  # must stay below ~40% of the canvas.
  frame_cells = 2 * width + 2 * height - 4 if has_frame else 0
  if sum(sizes) + frame_cells > (width * height * 2) // 5:
    return None
  objects = []
  occupied = set()  # cells plus 1-cell padding
  total_w = 0
  for size in sizes:
    max_h = min(inner_h, size)
    max_w = min(inner_w, size, max(1, width - total_w))
    cells = _polyomino(size, max_h, max_w)
    if cells is None:
      return None
    h, w = _bbox(cells)
    if total_w + w > width:
      return None
    if h == height and w == width:
      return None
    colour = random.choice(palette)
    placed = False
    for _ in range(60):
      oy = random.randint(margin, height - margin - h)
      ox = random.randint(margin, width - margin - w)
      abs_cells = [(oy + y, ox + x) for y, x in cells]
      if any(c in occupied for c in abs_cells):
        continue
      for y, x in abs_cells:
        for dy in (-1, 0, 1):
          for dx in (-1, 0, 1):
            occupied.add((y + dy, x + dx))
      objects.append((colour, cells, oy, ox))
      total_w += w
      placed = True
      break
    if not placed:
      return None
  return width, height, has_frame, frame_colour, objects


def generate(width=None, height=None, has_frame=None, frame_colour=None,
             objects=None):
  """Returns {"input": grid, "output": grid}.

  Args:
    width: grid width (sampled when None).
    height: grid height (sampled when None).
    has_frame: whether a full-edge frame is present (sampled when None).
    frame_colour: colour of the frame when has_frame is true.
    objects: list of (colour, cells, row, col) tuples; cells is a list of
      (y, x) offsets normalised to the object's top-left corner.  When given,
      the scene is built directly from these latents (used for fixture replay).
  """
  if objects is not None:
    frame = bool(has_frame)
    grid, output = _build(width, height, frame, frame_colour, objects)
    return {"input": grid, "output": output}
  for _ in range(500):
    scene = _sample_scene()
    if scene is None:
      continue
    w, h, frame, fc, objs = scene
    grid, output = _build(w, h, frame, fc, objs)
    if grid == output:
      continue
    if not _background_is_majority(grid):
      continue
    return {"input": grid, "output": output}
  # Fallback deterministic valid scene (should be unreachable in practice).
  objs = [(1, _rect(1, 1), 1, 1), (3, _rect(2, 2), 4, 5)]
  grid, output = _build(10, 10, False, None, objs)
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical train/test pairs from explicit latents."""
  train = [
      generate(width=10, height=10, has_frame=True, frame_colour=2, objects=[
          (0, [(0, 0)], 2, 3),
          (8, _rect(1, 2), 1, 7),
          (6, _rect(3, 1), 3, 1),
          (5, _rect(2, 2), 5, 4),
      ]),
      generate(width=10, height=10, has_frame=False, objects=[
          (1, _rect(3, 4), 0, 0),
          (5, _rect(2, 2), 3, 7),
          (8, [(0, 0)], 4, 4),
          (9, _rect(2, 3), 6, 1),
      ]),
      generate(width=10, height=10, has_frame=False, objects=[
          (1, [(0, 0), (1, 0), (1, 1)], 1, 8),
          (9, _rect(5, 1), 3, 8),
          (3, _rect(1, 4), 5, 0),
      ]),
  ]
  test = [
      generate(width=10, height=10, has_frame=False, objects=[
          (1, [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)], 0, 2),
          (4, _rect(4, 2), 0, 6),
          (1, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (5, 1)], 4, 6),
          (6, [(0, 1), (1, 0), (1, 1)], 6, 3),
      ]),
  ]
  return {"train": train, "test": test}
