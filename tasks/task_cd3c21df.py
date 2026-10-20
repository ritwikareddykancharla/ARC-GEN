"""Generator for ARC task cd3c21df (odd-one-out object crop).

Rule: the black canvas holds several small (possibly multicoloured) 4-connected
shapes.  Grouping the shapes by exact appearance (cell layout plus colours,
no rotation or reflection), every appearance occurs exactly twice except for
one shape that occurs only once.  The output is the bounding-box crop of that
unique shape.

Scope: canvases of 9..18 cells per side, 1..3 duplicated appearances plus the
single unique one (3, 5 or 7 objects in total), sprite types covering single
colour lines, filled rectangles and random polyominoes, each coloured with
1..3 colours.  Objects never touch and their bounding boxes are kept at least
one empty row or column apart so the crop is exactly the latent sprite.
Appearances are compared exactly: a rotated or recoloured copy counts as a
different shape.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import collections
import random

import common


def _trim(sprite):
  """Returns the sprite cropped to the bounding box of its non-zero cells."""
  cells = [(r, c) for r, row in enumerate(sprite) for c, v in enumerate(row) if v]
  r0 = min(r for r, _ in cells)
  r1 = max(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  c1 = max(c for _, c in cells)
  return [list(row[c0:c1 + 1]) for row in sprite[r0:r1 + 1]]


def _connected(sprite):
  """True when the non-zero cells of the sprite form one 4-connected piece."""
  cells = {(r, c) for r, row in enumerate(sprite) for c, v in enumerate(row) if v}
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
      n = (r + dr, c + dc)
      if n in cells and n not in seen:
        seen.add(n)
        stack.append(n)
  return len(seen) == len(cells)


def _random_mask():
  """Samples a small 4-connected binary mask (list of rows of 0/1)."""
  kind = random.choice(["line", "line", "rect", "poly", "poly", "poly"])
  if kind == "line":
    length = random.randint(2, 5)
    if random.random() < 0.5:
      return [[1] * length]
    return [[1] for _ in range(length)]
  if kind == "rect":
    h, w = random.choice([(2, 2), (2, 3), (3, 2), (2, 2)])
    return [[1] * w for _ in range(h)]
  size = random.randint(3, 6)
  cells = {(0, 0)}
  while len(cells) < size:
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    cells.add((r + dr, c + dc))
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  cells = {(r - r0, c - c0) for r, c in cells}
  h = max(r for r, _ in cells) + 1
  w = max(c for _, c in cells) + 1
  mask = [[0] * w for _ in range(h)]
  for r, c in cells:
    mask[r][c] = 1
  if h > 5 or w > 5:
    return _random_mask()
  return mask


def _random_sprite():
  """Samples a coloured sprite: a connected mask painted with 1..3 colours."""
  mask = _random_mask()
  ncol = random.choice([1, 1, 1, 2, 2, 3])
  palette = random.sample(range(1, 10), ncol)
  cells = [(r, c) for r, row in enumerate(mask) for c, v in enumerate(row) if v]
  ncol = min(ncol, len(cells))
  palette = palette[:ncol]
  sprite = [[0] * len(mask[0]) for _ in mask]
  # Every palette colour is used at least once; the rest are random.
  random.shuffle(cells)
  for i, (r, c) in enumerate(cells):
    sprite[r][c] = palette[i] if i < ncol else random.choice(palette)
  return sprite


def _separated(box, boxes):
  """True when box has an empty row or column between it and every other box."""
  r0, c0, r1, c1 = box
  for (s0, d0, s1, d1) in boxes:
    row_gap = r1 + 1 < s0 or s1 + 1 < r0
    col_gap = c1 + 1 < d0 or d1 + 1 < c0
    if not (row_gap or col_gap):
      return False
  return True


def _sample_scene(width, height):
  """Samples sprites and placements; returns None when placement fails."""
  n_pairs = random.choice([1, 2, 2, 2, 3])
  sprites = []
  keys = set()
  guard = 0
  while len(sprites) < n_pairs + 1 and guard < 200:
    guard += 1
    s = _trim(_random_sprite())
    if not _connected(s):
      continue
    k = tuple(tuple(row) for row in s)
    if k in keys:
      continue
    keys.add(k)
    sprites.append(s)
  if len(sprites) < n_pairs + 1:
    return None
  unique = random.randrange(len(sprites))
  items = [unique]
  for i in range(len(sprites)):
    if i != unique:
      items.extend([i, i])
  random.shuffle(items)
  boxes = []
  placements = []
  for idx in items:
    sh, sw = len(sprites[idx]), len(sprites[idx][0])
    if sh + 2 > height or sw + 2 > width:
      return None
    placed = False
    for _ in range(120):
      r = random.randint(0, height - sh)
      c = random.randint(0, width - sw)
      box = (r, c, r + sh - 1, c + sw - 1)
      if _separated(box, boxes):
        boxes.append(box)
        placements.append([idx, r, c])
        placed = True
        break
    if not placed:
      return None
  # Background must remain the dominant colour.
  filled = sum(sum(1 for v in row for _ in [0] if v) for i in items for row in sprites[i])
  if filled * 2 >= width * height:
    return None
  return sprites, placements


def generate(width=None, height=None, sprites=None, placements=None):
  """Returns an input/output pair for task cd3c21df.

  Args:
    width: canvas width (sampled 9..18 when None).
    height: canvas height (sampled 9..18 when None).
    sprites: list of trimmed sprite grids (0 = empty cell) describing each
      distinct appearance.  Exactly one index must be used once in placements
      and every other index exactly twice.
    placements: list of [sprite_index, row, col] top-left positions.  Sprites
      must not touch and their bounding boxes must not intrude on each other.
  """
  if sprites is None or placements is None:
    scene = None
    for attempt in range(300):
      w = width if width is not None else random.randint(9, 18)
      h = height if height is not None else random.randint(9, 18)
      if attempt > 150:
        if width is None:
          w = max(w, 14)
        if height is None:
          h = max(h, 14)
      scene = _sample_scene(w, h)
      if scene is not None:
        width, height = w, h
        break
    if scene is None:
      raise ValueError("could not place sprites in requested dimensions")
    sprites, placements = scene
  canvas = common.grid(width, height, 0)
  for idx, r, c in placements:
    sprite = sprites[idx]
    for dr, row in enumerate(sprite):
      for dc, v in enumerate(row):
        if v:
          canvas[r + dr][c + dc] = v
  counts = collections.Counter(idx for idx, _, _ in placements)
  unique = [idx for idx, n in counts.items() if n == 1][0]
  output = _trim(sprites[unique])
  return {"input": canvas, "output": output}


def validate():
  """Reconstructs the canonical train/test fixtures from latent parameters."""
  train = [
      generate(width=12, height=12,
               sprites=[[[8, 2], [2, 8]], [[6, 6, 6]], [[7, 7], [7, 7]]],
               placements=[[0, 1, 2], [1, 1, 8], [0, 5, 8], [1, 6, 0],
                           [2, 8, 4]]),
      generate(width=11, height=11,
               sprites=[[[5], [5], [5], [5], [5]], [[4], [4], [4]],
                        [[2], [2], [2], [2]]],
               placements=[[0, 1, 2], [1, 2, 7], [2, 3, 9], [0, 6, 4],
                           [1, 8, 0]]),
      generate(width=13, height=13,
               sprites=[[[6, 6, 6], [0, 6, 0]], [[2, 2, 2], [2, 3, 2]],
                        [[2, 1, 2], [1, 1, 1]]],
               placements=[[0, 1, 2], [1, 2, 8], [2, 5, 9], [1, 7, 1],
                           [0, 9, 6]]),
  ]
  test = [
      generate(width=13, height=13,
               sprites=[[[5, 5, 5]], [[4, 4], [4, 4]],
                        [[4, 8], [8, 8], [8, 4]]],
               placements=[[0, 1, 1], [2, 2, 7], [1, 4, 1], [1, 8, 2],
                           [0, 10, 9]]),
  ]
  return {"train": train, "test": test}
