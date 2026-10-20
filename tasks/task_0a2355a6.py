"""Generator for ARC task 0a2355a6 (recolour outline objects by hole count).

Rule: the input is a background of 0 containing several colour-8 objects.
Every object is a union of rectangular rings (closed 1-cell outlines) that
share walls, so each object encloses one or more empty pockets (holes).
The output keeps every cell in place and recolours each object as a whole
according to the number of holes it encloses, using the fixed legend
1 hole -> 1, 2 holes -> 3, 3 holes -> 2, 4 holes -> 4.

Scope: objects are chains of 1 to 4 axis-aligned rectangular rings glued
along shared walls (stacked, side by side, or L/zig-zag chains, as in the
original fixtures).  Grid sizes, object count, ring sizes, chain layouts
and positions are sampled; the background 0, shape colour 8 and the
hole-count legend are fixed properties of the task.  Objects never touch,
not even diagonally.  Shapes with more than 4 holes, non-rectangular holes
or objects with holes that are not ring interiors are deliberately not
generated because the legend only covers 1..4 holes.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common

# Hole count -> output colour legend (arbitrary, as given by the task).
TABLE = {1: 1, 2: 3, 3: 2, 4: 4}
SHAPE_COLOR = 8
BACKGROUND = 0


def _ring_cells(top, left, height, width):
  """Returns the outline cells of a rectangle box as a set of (row, col)."""
  cells = set()
  for r in range(top, top + height):
    for c in range(left, left + width):
      if r in (top, top + height - 1) or c in (left, left + width - 1):
        cells.add((r, c))
  return cells


def _object_cells(rings):
  """Returns the union of outline cells of all rings of an object."""
  cells = set()
  for ring in rings:
    cells |= _ring_cells(*ring)
  return cells


def _count_holes(cells):
  """Counts background pockets fully enclosed by the given cell set.

  Used only to validate a randomly built chain (every ring interior must
  stay a separate pocket and no extra pocket may appear between rings).
  """
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  r0, r1 = min(rows) - 1, max(rows) + 1
  c0, c1 = min(cols) - 1, max(cols) + 1

  def fill(start, seen):
    stack = [start]
    while stack:
      r, c = stack.pop()
      if (r, c) in seen or (r, c) in cells:
        continue
      if not (r0 <= r <= r1 and c0 <= c <= c1):
        continue
      seen.add((r, c))
      stack.extend(((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)))

  outside = set()
  fill((r0, c0), outside)
  seen = set()
  pockets = 0
  for r in range(r0, r1 + 1):
    for c in range(c0, c1 + 1):
      if (r, c) in cells or (r, c) in outside or (r, c) in seen:
        continue
      pockets += 1
      fill((r, c), seen)
  return pockets


def _box_overlap(a, b):
  """Returns (row overlap, col overlap) of two boxes; <=0 means a gap."""
  at, al, ah, aw = a
  bt, bl, bh, bw = b
  rows = min(at + ah, bt + bh) - max(at, bt)
  cols = min(al + aw, bl + bw) - max(al, bl)
  return rows, cols


def _compatible(new, rings):
  """Checks that a new ring either shares a wall strip or stays apart.

  Allowed relations with every existing ring: the boxes intersect in a
  1-wide strip of length >= 2 (a shared wall), or they do not touch at all
  (no edge or corner adjacency).
  """
  for old in rings:
    rows, cols = _box_overlap(new, old)
    if rows > 0 and cols > 0:
      if min(rows, cols) != 1 or max(rows, cols) < 2:
        return False
    else:
      touching = (rows == 0 and cols >= 0) or (cols == 0 and rows >= 0)
      if touching:
        return False
  return True


def _random_object(num_rings, max_size):
  """Builds a chain of num_rings wall-sharing rings, normalised to (0, 0).

  Returns a list of (top, left, height, width) boxes whose union encloses
  exactly num_rings holes and fits in a max_size x max_size box, or None.
  """
  dim_hi = 5 if num_rings <= 2 else 4
  for _ in range(40):
    rings = [(0, 0, random.randint(3, dim_hi), random.randint(3, dim_hi))]
    ok = True
    for _ in range(num_rings - 1):
      placed = False
      for _ in range(30):
        bt, bl, bh, bw = random.choice(rings)
        nh, nw = random.randint(3, dim_hi), random.randint(3, dim_hi)
        side = random.choice("NSEW")
        if side in "EW":
          nl = bl + bw - 1 if side == "E" else bl - nw + 1
          nt = random.randint(bt - nh + 2, bt + bh - 2)
        else:
          nt = bt + bh - 1 if side == "S" else bt - nh + 1
          nl = random.randint(bl - nw + 2, bl + bw - 2)
        new = (nt, nl, nh, nw)
        if _compatible(new, rings):
          rings.append(new)
          placed = True
          break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    min_r = min(t for t, _, _, _ in rings)
    min_c = min(l for _, l, _, _ in rings)
    rings = [(t - min_r, l - min_c, h, w) for t, l, h, w in rings]
    span_r = max(t + h for t, _, h, _ in rings)
    span_c = max(l + w for _, l, _, w in rings)
    if span_r > max_size or span_c > max_size:
      continue
    if _count_holes(_object_cells(rings)) != num_rings:
      continue
    return rings
  return None


def _random_scene(width, height):
  """Samples grid size and a list of non-touching ring-chain objects."""
  for _ in range(60):
    w = width if width is not None else random.randint(10, 20)
    h = height if height is not None else random.randint(10, 20)
    num_objects = random.randint(3, 5)
    counts = random.sample([1, 2, 3, 4], 2)
    counts += [random.randint(1, 4) for _ in range(num_objects - 2)]
    random.shuffle(counts)
    max_size = min(h, w) - 1
    blocked = set()
    objects = []
    for n in counts:
      shape = _random_object(n, max_size)
      if shape is None:
        continue
      cells = _object_cells(shape)
      oh = max(r for r, _ in cells) + 1
      ow = max(c for _, c in cells) + 1
      if oh > h or ow > w:
        continue
      for _ in range(60):
        top = random.randint(0, h - oh)
        left = random.randint(0, w - ow)
        shifted = {(r + top, c + left) for r, c in cells}
        if shifted & blocked:
          continue
        objects.append([(t + top, l + left, rh, rw) for t, l, rh, rw in shape])
        for r, c in shifted:
          for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
              blocked.add((r + dr, c + dc))
        break
    if len(objects) >= 2 and len({len(o) for o in objects}) >= 2:
      return w, h, objects
  raise RuntimeError("could not build a valid 0a2355a6 scene")


def generate(width=None, height=None, objects=None):
  """Returns an input/output pair for task 0a2355a6.

  Args:
    width: grid width (sampled in 10..20 when None).
    height: grid height (sampled in 10..20 when None).
    objects: list of objects, each a list of (top, left, height, width)
      rectangle boxes in absolute grid coordinates; the object is the union
      of the outlines of its boxes and encloses one hole per box.  When
      None, a fresh random scene of 2..5 wall-sharing ring chains is built.
  """
  if objects is None:
    width, height, objects = _random_scene(width, height)
  grid = common.grid(width, height, BACKGROUND)
  output = common.grid(width, height, BACKGROUND)
  for rings in objects:
    colour = TABLE[len(rings)]
    for r, c in _object_cells(rings):
      grid[r][c] = SHAPE_COLOR
      output[r][c] = colour
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the original train and test pairs via explicit latents."""
  train = [
      generate(width=14, height=14, objects=[
          [(1, 2, 3, 5)],
          [(0, 9, 3, 3), (2, 9, 3, 3), (4, 9, 3, 3)],
          [(8, 3, 3, 3), (7, 5, 5, 3)],
          [(10, 10, 3, 3)],
      ]),
      generate(width=11, height=14, objects=[
          [(1, 2, 3, 3), (1, 4, 3, 3), (3, 2, 4, 3)],
          [(4, 8, 3, 3)],
          [(8, 0, 3, 3), (10, 0, 3, 5)],
          [(9, 6, 4, 4)],
      ]),
      generate(width=14, height=15, objects=[
          [(0, 2, 3, 3), (1, 4, 3, 3), (1, 6, 3, 4), (1, 9, 3, 3)],
          [(6, 1, 3, 4), (8, 1, 3, 4)],
          [(6, 9, 4, 4), (9, 8, 3, 3), (11, 8, 3, 4)],
          [(12, 2, 3, 3)],
      ]),
      generate(width=11, height=9, objects=[
          [(0, 7, 3, 4)],
          [(2, 2, 3, 3)],
          [(4, 6, 3, 3), (6, 6, 3, 3)],
      ]),
  ]
  test = [
      generate(width=17, height=15, objects=[
          [(1, 2, 3, 4), (3, 4, 3, 3), (3, 6, 3, 3), (2, 8, 4, 3)],
          [(1, 13, 3, 3), (3, 13, 4, 3), (6, 12, 3, 4)],
          [(9, 2, 4, 6)],
          [(11, 10, 4, 4), (11, 13, 4, 4)],
      ]),
  ]
  return {"train": train, "test": test}
