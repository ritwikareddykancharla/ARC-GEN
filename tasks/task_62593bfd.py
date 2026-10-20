"""Generator for ARC task 62593bfd: shared-size objects rise, unique-size objects sink.

Rule: every 8-connected single-colour object keeps its shape and column.  If
another object in the grid has exactly the same cell count, the object slides
up until it touches the top edge; if its cell count is unique it slides down
until it touches the bottom edge.

Scope: random grids 12..30 on each side with any background colour, 3..7
objects of 2..12 cells (random 8-connected shapes inside a 5x5 box, including
shapes held together only by diagonal contact), one or two shared-size groups
(pairs or triples) plus one or more unique-size distractors, optional repeated
colours, and column spans that may overlap between a riser and a sinker.
Objects never touch (even diagonally) in the input, so colour-wise and
colour-blind connectivity give the same decomposition.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import collections
import random

import common


_NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
               (1, 1)]


def _normalise(cells):
  """Shifts a cell set so its minimum row and column are zero."""
  min_y = min(y for y, _ in cells)
  min_x = min(x for _, x in cells)
  return sorted((y - min_y, x - min_x) for y, x in cells)


def _random_shape(size, box=5):
  """Grows a random 8-connected shape of the given size inside a box."""
  cells = {(random.randrange(box), random.randrange(box))}
  attempts = 0
  while len(cells) < size and attempts < 600:
    attempts += 1
    y, x = random.choice(sorted(cells))
    dy, dx = random.choice(_NEIGHBOURS)
    ny, nx = y + dy, x + dx
    if 0 <= ny < box and 0 <= nx < box:
      cells.add((ny, nx))
  if len(cells) < size:
    return None
  return _normalise(cells)


def _size_plan(n):
  """Returns a list of n sizes with >=1 shared group and >=1 unique size."""
  groups = 1 if n < 5 else random.choice([1, 2])
  group_sizes = [2] * groups
  if n - sum(group_sizes) >= 2 and random.random() < 0.3:
    group_sizes[random.randrange(groups)] = 3
  unique = n - sum(group_sizes)
  values = random.sample(range(2, 13), groups + unique)
  sizes = []
  for g, count in enumerate(group_sizes):
    sizes.extend([values[g]] * count)
  sizes.extend(values[groups:])
  random.shuffle(sizes)
  return sizes


def _destinations(height, objects):
  """Maps each object index to its output top row."""
  counts = collections.Counter(len(cells) for _, _, _, cells in objects)
  dests = []
  for _, _, _, cells in objects:
    obj_height = max(y for y, _ in cells) + 1
    if counts[len(cells)] > 1:
      dests.append(0)
    else:
      dests.append(height - obj_height)
  return dests


def _random_scene():
  """Samples a fresh valid scene; returns (width, height, background, objects)."""
  for _ in range(80):
    height = random.randint(12, 30)
    width = random.randint(12, 30)
    background = random.randint(0, 9)
    area = width * height
    max_n = min(7, max(3, area // 45))
    n = random.randint(3, max_n)
    sizes = _size_plan(n)
    shapes = [_random_shape(s) for s in sizes]
    if any(shape is None for shape in shapes):
      continue
    pool = [c for c in range(10) if c != background]
    colours = random.sample(pool, n)
    if n >= 4 and random.random() < 0.3:
      i, j = random.sample(range(n), 2)
      colours[i] = colours[j]
    counts = collections.Counter(sizes)
    occupied_in = set()
    occupied_out = set()
    objects = []
    ok = True
    for idx in range(n):
      cells = shapes[idx]
      obj_h = max(y for y, _ in cells) + 1
      obj_w = max(x for _, x in cells) + 1
      dest = 0 if counts[sizes[idx]] > 1 else height - obj_h
      placed = False
      for _ in range(300):
        row = random.randint(0, height - obj_h)
        col = random.randint(0, width - obj_w)
        in_cells = [(row + y, col + x) for y, x in cells]
        if any((y + dy, x + dx) in occupied_in
               for y, x in in_cells for dy, dx in _NEIGHBOURS + [(0, 0)]):
          continue
        out_cells = [(dest + y, col + x) for y, x in cells]
        if any(c in occupied_out for c in out_cells):
          continue
        occupied_in.update(in_cells)
        occupied_out.update(out_cells)
        objects.append((colours[idx], row, col, cells))
        placed = True
        break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    dests = _destinations(height, objects)
    if all(obj[1] == d for obj, d in zip(objects, dests)):
      continue
    if len(occupied_in) * 2 >= area:
      continue
    return width, height, background, objects
  raise RuntimeError("could not sample a valid scene")


def generate(width=None, height=None, background=None, objects=None):
  """Returns {"input": grid, "output": grid} for one scene.

  Args:
    width: grid width (columns).
    height: grid height (rows).
    background: background colour.
    objects: list of (colour, row, col, cells) where cells are (dy, dx)
      offsets normalised so the minimum dy and dx are zero; (row, col) is the
      position of that normalised origin in the input grid.
  Any missing argument triggers sampling of a fresh random scene.
  """
  if width is None or height is None or background is None or objects is None:
    width, height, background, objects = _random_scene()
  objects = [(c, r, k, [tuple(cell) for cell in cells])
             for c, r, k, cells in objects]
  grid_in = common.grid(width, height, background)
  grid_out = common.grid(width, height, background)
  dests = _destinations(height, objects)
  for (colour, row, col, cells), dest in zip(objects, dests):
    for y, x in cells:
      grid_in[row + y][col + x] = colour
      grid_out[dest + y][col + x] = colour
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstructs the canonical train and test pairs from explicit latents."""
  train = [
      generate(width=19, height=28, background=0, objects=[
          (4, 4, 0, [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1)]),
          (2, 5, 4, [(0, 4), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3),
                     (3, 1), (3, 2), (3, 3), (4, 0)]),
          (1, 11, 11, [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2),
                       (2, 2)]),
          (3, 17, 2, [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (3, 2),
                      (4, 2)]),
      ]),
      generate(width=30, height=30, background=5, objects=[
          (3, 3, 22, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1),
                      (2, 2), (3, 1)]),
          (1, 5, 4, [(0, 2), (1, 0), (1, 1), (1, 2)]),
          (7, 12, 12, [(0, 1), (1, 0), (1, 1)]),
          (9, 12, 16, [(0, 0), (0, 1), (1, 0)]),
          (2, 17, 4, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0),
                      (2, 1), (2, 2)]),
          (4, 17, 20, [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)]),
      ]),
  ]
  test = [
      generate(width=25, height=25, background=1, objects=[
          (2, 2, 3, [(0, 2), (0, 3), (0, 4), (1, 2), (2, 0), (2, 1), (2, 2)]),
          (5, 3, 19, [(0, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1),
                      (3, 2), (3, 3), (4, 0), (4, 4)]),
          (3, 11, 4, [(0, 0), (0, 4), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3),
                      (3, 1), (3, 2), (3, 3), (4, 0), (4, 4)]),
          (3, 11, 18, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2),
                       (4, 2)]),
          (4, 19, 12, [(0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)]),
      ]),
      generate(width=28, height=19, background=9, objects=[
          (3, 2, 22, [(0, 1), (1, 0), (1, 2), (2, 1)]),
          (4, 4, 15, [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]),
          (1, 5, 4, [(0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2), (3, 2)]),
          (7, 7, 11, [(0, 0), (0, 1), (1, 0)]),
          (6, 11, 21, [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3),
                       (3, 1)]),
          (8, 15, 1, [(0, 1), (1, 0), (1, 1)]),
      ]),
  ]
  return {"train": train, "test": test}
