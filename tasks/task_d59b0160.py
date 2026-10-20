"""Generator for ARC task d59b0160.

Rule: the top-left corner holds a legend enclosed by a colour-3 frame (row 3
and column 3).  Coloured dots inside the frame are the legend colours.  The
rest of the canvas (background 7) holds several rectangles of fill colour 0
sprinkled with coloured dots, separated from each other by background.  Every
rectangle whose dot colours include ALL legend colours is erased (painted 7);
all other rectangles stay untouched.

Scope: grid sizes 12..26 per side (fixtures are 16x16), legend of 2..4 distinct
colours at random positions in the 3x3 legend box, 3..7 rectangles of varying
shape with random dot density, a mix of erased rectangles (superset of legend)
and kept distractors that carry some but not all legend colours plus extra
colours.  Background 7, frame 3, fill 0 and the legend box location are fixed
properties of the task and are not varied.

Copyright 2026 Ritwika Kancharla.  Licensed under the Apache License 2.0.
"""

import common
import random

BG = 7
FRAME = 3
FILL = 0
PALETTE = [1, 2, 4, 5, 6, 8, 9]


def _legend_colours(legend):
  """Returns the set of non-background, non-frame colours in the legend box."""
  return set(c for row in legend for c in row if c not in (BG, FRAME))


def _rect_colours(cells):
  """Returns the set of dot colours (non-fill) inside a rectangle."""
  return set(c for row in cells for c in row if c != FILL)


def _fits(taken, h, w, y, x, rh, rw):
  """Checks the rectangle plus a one-cell margin against the occupancy map."""
  for yy in range(max(0, y - 1), min(h, y + rh + 1)):
    for xx in range(max(0, x - 1), min(w, x + rw + 1)):
      if taken[yy][xx]:
        return False
  return True


def _fill_rect(rh, rw, colours):
  """Builds a rectangle of fill 0 whose dot colours are exactly `colours`."""
  area = rh * rw
  cells = common.grid(rw, rh, FILL)
  if not colours:
    return cells
  density = random.uniform(0.1, 0.35)
  n_dots = max(len(colours), int(round(area * density)))
  n_dots = min(n_dots, area - 1 if area > len(colours) else area)
  spots = random.sample(range(area), n_dots)
  order = list(colours)
  random.shuffle(order)
  for i, spot in enumerate(spots):
    c = order[i] if i < len(order) else random.choice(order)
    cells[spot // rw][spot % rw] = c
  return cells


def _sample_scene(h, w):
  """Samples legend and rectangles; returns (legend, rects) or None."""
  n_legend = random.choice([2, 3, 3, 3, 4])
  legend_set = random.sample(PALETTE, n_legend)
  legend = common.grid(3, 3, BG)
  for pos, c in zip(random.sample(range(9), n_legend), legend_set):
    legend[pos // 3][pos % 3] = c
  extras_pool = [c for c in PALETTE if c not in legend_set]

  taken = [[False] * w for _ in range(h)]
  for y in range(4):
    for x in range(4):
      taken[y][x] = True
  target = random.randint(4, 7)
  boxes = []
  for _ in range(300):
    if len(boxes) >= target:
      break
    rh = random.randint(2, min(12, h))
    rw = random.randint(2, min(12, w))
    area = rh * rw
    if area < 6 or area > 80:
      continue
    y = random.randint(0, h - rh)
    x = random.randint(0, w - rw)
    if not _fits(taken, h, w, y, x, rh, rw):
      continue
    boxes.append((y, x, rh, rw))
    for yy in range(y, y + rh):
      for xx in range(x, x + rw):
        taken[yy][xx] = True
  if len(boxes) < 3:
    return None

  erase = [random.random() < 0.5 for _ in boxes]
  if not any(erase):
    erase[random.randrange(len(boxes))] = True
  if all(erase):
    erase[random.randrange(len(boxes))] = False

  rects = []
  for (y, x, rh, rw), is_erased in zip(boxes, erase):
    area = rh * rw
    if is_erased:
      base = list(legend_set)
    else:
      k = random.randint(0, n_legend - 1)
      base = random.sample(legend_set, k)
    room = max(0, area - 1 - len(base))
    n_extra = random.randint(0, min(len(extras_pool), room))
    colours = base + random.sample(extras_pool, n_extra)
    rects.append((y, x, _fill_rect(rh, rw, colours)))
  return legend, rects


def generate(width=None, height=None, legend=None, rects=None):
  """Returns an input/output pair for the legend-superset erasure task.

  Args:
    width: grid width (12..26 when sampled).
    height: grid height (12..26 when sampled).
    legend: 3x3 list of colours for the legend box (7 marks empty cells).
    rects: list of (y, x, cells) where cells is a 2D list describing one
      rectangle (fill 0 with coloured dots) placed with top-left at (y, x).
  """
  if width is None:
    width = random.randint(12, 26)
  if height is None:
    height = random.randint(12, 26)
  if legend is None or rects is None:
    scene = None
    for _ in range(50):
      scene = _sample_scene(height, width)
      if scene is not None:
        break
    if scene is None:
      raise ValueError('could not place rectangles')
    legend, rects = scene

  grid = common.grid(width, height, BG)
  for y in range(4):
    grid[y][3] = FRAME
  for x in range(4):
    grid[3][x] = FRAME
  for y in range(3):
    for x in range(3):
      grid[y][x] = legend[y][x]
  output = [row[:] for row in grid]

  legend_set = _legend_colours(legend)
  for y, x, cells in rects:
    erased = legend_set <= _rect_colours(cells)
    for dy, row in enumerate(cells):
      for dx, c in enumerate(row):
        grid[y + dy][x + dx] = c
        output[y + dy][x + dx] = BG if erased else c
  return {'input': grid, 'output': output}


def validate():
  """Reconstructs the canonical train and test fixtures."""
  train = [
      generate(width=16, height=16,
               legend=[[4, 7, 1], [7, 7, 7], [2, 7, 7]],
               rects=[
                   (0, 7, [[9, 6, 4], [4, 5, 9], [0, 0, 0], [0, 0, 0],
                           [6, 5, 0]]),
                   (1, 12, [[0, 0, 0], [0, 4, 0], [0, 0, 1], [0, 2, 0],
                            [0, 0, 0]]),
                   (6, 3, [[0, 0, 0, 0, 9, 0, 0, 5], [0, 0, 9, 0, 2, 9, 0, 0],
                           [2, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 1, 0, 4, 0, 0, 8]]),
                   (7, 14, [[0, 0], [1, 4], [0, 0], [1, 0], [0, 0], [6, 0],
                            [0, 0], [0, 0], [0, 8]]),
                   (11, 0, [[0, 0, 0, 0, 0, 0, 0, 1], [9, 5, 0, 9, 0, 0, 8, 6],
                            [0, 4, 2, 6, 0, 0, 0, 0],
                            [2, 0, 0, 0, 6, 0, 0, 0]]),
                   (11, 9, [[0, 0, 0, 0], [9, 0, 0, 8], [0, 6, 0, 5],
                            [0, 0, 0, 0], [0, 2, 2, 0]]),
               ]),
      generate(width=16, height=16,
               legend=[[7, 9, 7], [7, 7, 7], [5, 7, 6]],
               rects=[
                   (1, 6, [[0, 0, 0], [1, 0, 0], [0, 5, 0], [0, 0, 0],
                           [2, 0, 6], [0, 0, 0]]),
                   (1, 12, [[0, 0, 0], [6, 0, 4], [0, 0, 0], [0, 9, 0],
                            [0, 0, 0], [0, 8, 0], [0, 0, 0]]),
                   (9, 1, [[0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 5, 0],
                           [0, 9, 0, 8, 0, 0, 0], [0, 0, 0, 0, 0, 4, 0],
                           [0, 2, 0, 4, 0, 0, 0]]),
                   (11, 11, [[0, 0, 0, 0, 9], [0, 6, 0, 0, 0], [0, 0, 0, 0, 0],
                             [0, 0, 5, 1, 0], [8, 0, 0, 0, 0]]),
               ]),
      generate(width=16, height=16,
               legend=[[7, 6, 7], [1, 7, 7], [7, 7, 8]],
               rects=[
                   (1, 7, [[0, 8, 0, 0, 0, 5, 0, 0, 0],
                           [0, 5, 0, 0, 6, 0, 0, 0, 0],
                           [4, 0, 0, 0, 0, 0, 8, 0, 0],
                           [9, 0, 0, 6, 0, 0, 0, 4, 0],
                           [0, 0, 0, 0, 5, 9, 0, 5, 0],
                           [9, 0, 0, 0, 0, 8, 0, 0, 0],
                           [1, 0, 0, 2, 0, 0, 0, 0, 6]]),
                   (5, 1, [[0, 0, 0, 0, 0], [5, 2, 2, 0, 0], [0, 0, 1, 0, 0],
                           [0, 0, 5, 5, 0], [0, 0, 0, 9, 0], [0, 0, 0, 6, 0]]),
                   (9, 9, [[0, 9, 0, 0], [0, 0, 0, 0], [8, 0, 0, 0],
                           [0, 0, 0, 0], [0, 0, 0, 0]]),
                   (12, 2, [[6, 1, 0, 0, 0, 0], [0, 2, 0, 0, 0, 0],
                            [0, 8, 0, 0, 0, 0]]),
                   (12, 14, [[0, 0], [0, 0], [0, 0], [0, 0]]),
               ]),
  ]
  test = [
      generate(width=16, height=16,
               legend=[[7, 2, 7], [7, 7, 5], [7, 4, 7]],
               rects=[
                   (0, 6, [[0, 0, 0], [0, 0, 6], [0, 0, 1], [0, 0, 0],
                           [0, 0, 0], [0, 0, 0], [0, 5, 0], [2, 0, 4],
                           [0, 0, 0], [0, 1, 0], [0, 0, 9], [0, 0, 1],
                           [0, 9, 0], [0, 9, 8], [0, 0, 0], [0, 0, 5]]),
                   (1, 10, [[0, 0, 0, 0, 0], [4, 0, 5, 0, 0],
                            [4, 0, 8, 0, 0]]),
                   (5, 0, [[9, 0], [0, 8], [0, 0], [0, 0], [0, 0], [6, 0],
                           [0, 0], [5, 0], [0, 0], [5, 0], [0, 0]]),
                   (5, 10, [[9, 0, 0, 0, 0, 0], [0, 0, 0, 6, 5, 0],
                            [0, 2, 0, 0, 0, 0], [0, 0, 4, 0, 8, 0],
                            [0, 9, 4, 0, 5, 0]]),
                   (6, 3, [[0, 0], [0, 0], [0, 0], [0, 5], [0, 5], [5, 0],
                           [5, 0], [0, 5], [0, 4], [0, 2]]),
                   (11, 11, [[0, 0, 0, 0, 0], [0, 0, 9, 0, 1],
                             [1, 0, 4, 0, 0]]),
               ]),
  ]
  return {'train': train, 'test': test}
