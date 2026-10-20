"""Generator for ARC task e4888269 (sequential colour-substitution legend).

Rule: the grid holds a legend - a background-isolated block exactly two cells
wide whose rows read `a b` ("recolour a to b"). The rows are applied as
substitutions in top-to-bottom order, each acting on the colours produced by
the earlier rows, giving one composed colour map. Every non-legend cell is
recoloured through that map; colours that never appear as a source stay.

Scope: background colour, grid size, legend position/height (3..7 rows) and
three layouts are sampled: a vertical divider (legend on one side, scattered
pixels on the other, as in the training pairs), a horizontal divider (as in
test 2), or no divider at all with single-coloured distractor shapes around
the legend (as in test 1). Canvas content includes isolated pixels and
single-coloured shapes; some carry colours the legend changes, others carry
colours that stay. Multicoloured non-legend components are never generated.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common


def _compose(legend):
  """Composes legend rows (applied top to bottom) into one colour map."""
  mapping = {c: c for c in range(10)}
  for src, dst in legend:
    for c in mapping:
      if mapping[c] == src:
        mapping[c] = dst
  return mapping


def _mark(occ, cells):
  """Marks cells plus their 8-neighbourhood as occupied."""
  h, w = len(occ), len(occ[0])
  for r, c in cells:
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
          occ[rr][cc] = True


def _free(occ, cells):
  h, w = len(occ), len(occ[0])
  return all(0 <= r < h and 0 <= c < w and not occ[r][c] for r, c in cells)


def _cells_to_runs(cells):
  """Converts a cell list to horizontal (row, c0, c1) runs."""
  by_row = {}
  for r, c in cells:
    by_row.setdefault(r, []).append(c)
  runs = []
  for r in sorted(by_row):
    cols = sorted(by_row[r])
    start = prev = cols[0]
    for c in cols[1:]:
      if c == prev + 1:
        prev = c
        continue
      runs.append((r, start, prev))
      start = prev = c
    runs.append((r, start, prev))
  return runs


def _shape_template():
  """Returns relative cells of a random single-coloured distractor shape."""
  kind = random.choices(["outline", "filled", "hline", "vline", "blob"],
                        [3, 2, 2, 1, 2])[0]
  if kind == "outline":
    w, h = random.randint(3, 7), random.randint(3, 7)
    return [(r, c) for r in range(h) for c in range(w)
            if r in (0, h - 1) or c in (0, w - 1)]
  if kind == "filled":
    w = random.choice([1, 3, 3, 4, 5])
    h = random.randint(1, 4)
    if w == 1 and h == 1:
      h = 2
    return [(r, c) for r in range(h) for c in range(w)]
  if kind == "hline":
    return [(0, c) for c in range(random.randint(3, 8))]
  if kind == "vline":
    return [(r, 0) for r in range(random.randint(2, 8))]
  cells = {(0, 0)}
  for _ in range(random.randint(3, 9)):
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
    cells.add((r + dr, c + dc))
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  return [(r - r0, c - c0) for r, c in cells]


def _build(width, height, bg, legend, legend_pos, divider, pixels, shapes):
  """Renders the scene and derives the output from the composed legend map."""
  grid = common.grid(width, height, bg)
  if divider is not None:
    axis, index, colour = divider
    if axis == "v":
      for r in range(height):
        grid[r][index] = colour
    else:
      for c in range(width):
        grid[index][c] = colour
  for colour, runs in shapes or []:
    for r, c0, c1 in runs:
      for c in range(c0, c1 + 1):
        grid[r][c] = colour
  for r, c, colour in pixels or []:
    grid[r][c] = colour
  lr, lc = legend_pos
  for i, (a, b) in enumerate(legend):
    grid[lr + i][lc] = a
    grid[lr + i][lc + 1] = b
  mapping = _compose(legend)
  out = [row[:] for row in grid]
  for r in range(height):
    for c in range(width):
      if lr <= r < lr + len(legend) and lc <= c <= lc + 1:
        continue
      out[r][c] = mapping[grid[r][c]]
  return {"input": grid, "output": out}


def _sample_scene(width, height, bg):
  """Samples one latent scene; returns None if the attempt is unusable."""
  if bg is None:
    bg = 0 if random.random() < 0.6 else random.randint(1, 9)
  w = width if width is not None else random.randint(10, 30)
  h = height if height is not None else random.randint(8, 30)
  mode = random.choice(["v", "v", "h", "none", "none"])
  # A vertical divider needs >= 10 columns (3 + 1 + 1 + ... layout below);
  # a horizontal divider needs >= 12 rows so both bands fit a 3-row legend
  # and a canvas band with a gap of one row on each side of the divider.
  if mode == "v" and w < 10:
    mode = "none"
  if mode == "h" and h < 12:
    mode = "none"
  non_bg = [c for c in range(10) if c != bg]
  divider = None
  if mode == "v":
    colour = random.choice(non_bg)
    if random.random() < 0.5:
      dx = random.randint(3, w - 7)
      legend_region = (0, h - 1, 0, dx - 2)
      canvas_region = (0, h - 1, dx + 2, w - 1)
    else:
      dx = random.randint(6, w - 4)
      legend_region = (0, h - 1, dx + 2, w - 1)
      canvas_region = (0, h - 1, 0, dx - 2)
    divider = ("v", dx, colour)
  elif mode == "h":
    colour = random.choice(non_bg)
    if random.random() < 0.5:
      dy = random.randint(4, h - 7)
      legend_region = (0, dy - 2, 0, w - 1)
      canvas_region = (dy + 2, h - 1, 0, w - 1)
    else:
      dy = random.randint(6, h - 5)
      legend_region = (dy + 2, h - 1, 0, w - 1)
      canvas_region = (0, dy - 2, 0, w - 1)
    divider = ("h", dy, colour)
  else:
    legend_region = (0, h - 1, 0, w - 1)
    canvas_region = (0, h - 1, 0, w - 1)
  pool = [c for c in non_bg if divider is None or c != divider[2]]

  # Legend rows: chained substitutions so composition order matters.
  lr0, lr1, lc0, lc1 = legend_region
  if lr1 - lr0 + 1 < 3 or lc1 - lc0 + 1 < 2:
    return None
  n = random.randint(3, min(7, lr1 - lr0 + 1))
  rows = []
  for _ in range(n):
    pair = None
    for _ in range(50):
      if rows and random.random() < 0.6:
        a = random.choice([d for _, d in rows])
      else:
        a = random.choice(pool)
      b = random.choice([c for c in pool if c != a])
      if (a, b) not in rows:
        pair = (a, b)
        break
    if pair is None:
      return None
    rows.append(pair)
  mapping = _compose(rows)
  sources = sorted({a for a, _ in rows})
  changing = [c for c in non_bg if mapping[c] != c]
  if not changing:
    return None

  occ = [[False] * w for _ in range(h)]
  if divider is not None:
    axis, index, _ = divider
    if axis == "v":
      _mark(occ, [(r, index) for r in range(h)])
    else:
      _mark(occ, [(index, c) for c in range(w)])
  legend_pos = (random.randint(lr0, lr1 - n + 1), random.randint(lc0, lc1 - 1))
  legend_cells = [(legend_pos[0] + i, legend_pos[1] + d)
                  for i in range(n) for d in (0, 1)]
  if not _free(occ, legend_cells):
    return None
  _mark(occ, legend_cells)

  cr0, cr1, cc0, cc1 = canvas_region
  # Distractor shapes (single-coloured).
  shapes = []
  n_shapes = random.randint(2, 5) if mode == "none" else random.choice(
      [0, 0, 0, 1, 2])
  for _ in range(n_shapes):
    template = _shape_template()
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    if th > cr1 - cr0 + 1 or tw > cc1 - cc0 + 1:
      continue
    for _ in range(30):
      r = random.randint(cr0, cr1 - th + 1)
      c = random.randint(cc0, cc1 - tw + 1)
      cells = [(r + dr, c + dc) for dr, dc in template]
      if _free(occ, cells):
        _mark(occ, cells)
        colour = random.choice(pool if random.random() < 0.6 else non_bg)
        shapes.append((colour, _cells_to_runs(cells)))
        break

  # Isolated canvas pixels.
  area = (cr1 - cr0 + 1) * (cc1 - cc0 + 1)
  n_pixels = random.randint(3, max(3, min(12, area // 12)))
  candidates = [(r, c) for r in range(cr0, cr1 + 1) for c in range(cc0, cc1 + 1)]
  random.shuffle(candidates)
  pixels = []
  for r, c in candidates:
    if len(pixels) >= n_pixels:
      break
    if not _free(occ, [(r, c)]):
      continue
    _mark(occ, [(r, c)])
    if not pixels:
      colour = random.choice(changing)
    else:
      roll = random.random()
      if roll < 0.7:
        colour = random.choice(changing)
      elif roll < 0.85:
        colour = random.choice(sources)
      else:
        colour = random.choice(non_bg)
    pixels.append((r, c, colour))
  if not pixels:
    return None

  scene = {"width": w, "height": h, "bg": bg, "legend": rows,
           "legend_pos": legend_pos, "divider": divider, "pixels": pixels,
           "shapes": shapes}
  # Background must dominate; output must differ from input.
  built = _build(**scene)
  counts = {}
  for row in built["input"]:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  if max(counts, key=counts.get) != bg:
    return None
  if counts[bg] <= max(v for k, v in counts.items() if k != bg):
    return None
  if built["input"] == built["output"]:
    return None
  return scene


def generate(width=None, height=None, bg=None, legend=None, legend_pos=None,
             divider=None, pixels=None, shapes=None):
  """Returns an input/output pair for the sequential legend task.

  Args:
    width: grid width (sampled 10..30 if None).
    height: grid height (sampled 8..30 if None).
    bg: background colour (sampled if None).
    legend: list of (source, destination) rows, top to bottom. When given,
      the scene is built explicitly from the remaining arguments.
    legend_pos: (row, col) of the legend's top-left cell.
    divider: None or (axis, index, colour) with axis 'v' (column) or 'h' (row).
    pixels: list of (row, col, colour) isolated canvas pixels.
    shapes: list of (colour, runs) where runs are (row, c0, c1) segments.
  """
  if legend is not None:
    return _build(width, height, bg, legend, legend_pos, divider, pixels,
                  shapes)
  for _ in range(300):
    scene = _sample_scene(width, height, bg)
    if scene is not None:
      return _build(**scene)
  raise RuntimeError("could not sample a valid scene")


def validate():
  """Reconstructs the original train/test pairs via explicit generate calls."""
  train_pixels = [(2, 14, 6), (6, 11, 3), (7, 18, 1)]
  train = [
      generate(width=20, height=10, bg=0,
               legend=[(1, 4), (3, 5), (4, 6), (6, 7)], legend_pos=(0, 0),
               divider=("v", 9, 2), pixels=train_pixels),
      generate(width=20, height=10, bg=0,
               legend=[(1, 4), (6, 7), (3, 5), (4, 6)], legend_pos=(0, 0),
               divider=("v", 9, 2), pixels=train_pixels),
      generate(width=20, height=10, bg=0,
               legend=[(1, 4), (6, 7), (3, 5)], legend_pos=(0, 0),
               divider=("v", 9, 2), pixels=train_pixels),
  ]
  test1_shapes = [
      (6, [(1, 6, 7), (2, 6, 7), (3, 6, 7)]),
      (5, [(1, 22, 24)]),
      (5, [(2, 1, 3), (3, 1, 3), (4, 2, 3)]),
      (4, [(2, 15, 16), (3, 15, 16)]),
      (8, [(6, 5, 5), (7, 5, 5), (8, 1, 1), (8, 5, 5), (9, 1, 1), (9, 5, 5),
           (10, 1, 1), (10, 5, 5), (11, 1, 5), (12, 3, 4)]),
      (9, [(7, 13, 13), (8, 10, 13), (9, 9, 11), (10, 9, 9), (10, 11, 13),
           (11, 9, 9), (11, 13, 13), (12, 9, 13)]),
      (7, [(9, 17, 21), (9, 23, 26)]),
      (3, [(13, 24, 29), (14, 24, 24), (15, 24, 24), (16, 24, 24),
           (17, 24, 24), (18, 24, 24), (19, 24, 24), (20, 20, 24),
           (21, 14, 22), (16, 7, 14), (17, 7, 7), (17, 14, 14), (18, 7, 7),
           (18, 14, 14), (19, 7, 7), (19, 14, 14), (20, 7, 7), (20, 14, 14),
           (21, 7, 7), (22, 4, 7), (16, 1, 4), (17, 1, 1), (17, 4, 4),
           (18, 0, 1), (18, 4, 4), (19, 4, 4), (20, 4, 4), (21, 4, 4)]),
      (6, [(14, 19, 21), (15, 19, 19), (15, 21, 21), (16, 19, 21)]),
  ]
  test = [
      generate(width=30, height=30, bg=1,
               legend=[(7, 9), (2, 3), (4, 2), (6, 7), (2, 9), (7, 8), (9, 2)],
               legend_pos=(18, 9), divider=None, pixels=[],
               shapes=test1_shapes),
      generate(width=13, height=24, bg=0,
               legend=[(1, 2), (5, 3), (6, 7), (9, 1), (1, 3), (5, 1), (2, 4)],
               legend_pos=(1, 10), divider=("h", 11, 4),
               pixels=[(14, 1, 1), (14, 4, 6), (15, 7, 2), (16, 10, 6),
                       (18, 0, 8), (18, 5, 5), (19, 8, 3), (22, 3, 9)]),
  ]
  return {"train": train, "test": test}
