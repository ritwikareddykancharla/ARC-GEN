"""Generator for ARC task 97d7923e (legend rank -> fill the n-th tallest capped bar).

Rule
----
The input has two kinds of structure on a background of 0:

* A legend of short vertical strips hanging from row 0.  A strip of colour
  ``c`` that is ``n`` cells tall is an instruction "colour c, rank n".
* Bars standing on the bottom row.  Each bar is one column wide; its top
  and bottom cells carry a cap colour and the cells in between carry a body
  colour.

For every legend strip (colour ``c``, height ``n``) the bars whose cap
colour is ``c`` are ranked by total height, and the ``n``-th tallest one is
repainted entirely in colour ``c``.  Everything else is unchanged.

Scope
-----
Supported: grids of 8..20 rows and 9..26 columns, 1..4 legend colours,
legend heights 1..3, 1..5 bars per colour with pairwise distinct heights,
bars standing in adjacent columns, bars standing below a legend strip (with
at least one background cell of gap), adjacent or spaced legend strips, and
per-colour body colours.  Not supported: bars with cap colours absent from
the legend, non-zero backgrounds, bars of height < 3, and ties in height
within a colour group (these would make the rank ambiguous).

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common


def _build(width, height, legend, bars):
  """Renders the input/output pair from explicit latent parameters.

  Args:
    width: grid width.
    height: grid height.
    legend: list of (x, colour, n) legend strips hanging from row 0.
    bars: list of (x, cap_colour, bar_height, body_colour) bars standing on
        the bottom row.
  """
  grid = common.grid(width, height, 0)
  for x, c, n in legend:
    for y in range(n):
      grid[y][x] = c
  for x, c, h, body in bars:
    top = height - h
    for y in range(top, height):
      grid[y][x] = body
    grid[top][x] = c
    grid[height - 1][x] = c
  output = [row[:] for row in grid]
  for _, c, n in legend:
    group = sorted([b for b in bars if b[1] == c], key=lambda b: -b[2])
    if 1 <= n <= len(group):
      bx, _, bh, _ = group[n - 1]
      for y in range(height - bh, height):
        output[y][bx] = c
  return {"input": grid, "output": output}


def _sample_scene():
  """Samples a fresh random scene; returns (width, height, legend, bars)."""
  for _ in range(200):
    height = random.randint(8, 20)
    width = random.randint(9, 26)
    num_colours = random.choice([1, 1, 2, 2, 3, 4])
    colours = random.sample(range(1, 10), num_colours)
    body_pool = [c for c in range(1, 10) if c not in colours]
    spacing = random.choice([1, 2])
    legend = []
    for i, c in enumerate(colours):
      legend.append((i * spacing, c, random.randint(1, 3)))
    spaced = random.random() < 0.6
    cols = list(range(width))
    random.shuffle(cols)
    used = set()
    bars = []
    ok = True
    for _, c, n in legend:
      body = random.choice(body_pool)
      count = min(random.randint(n, n + 2), 5)
      heights = random.sample(range(3, height), count)
      for h in heights:
        placed = False
        for x in cols:
          if x in used:
            continue
          if spaced and ((x - 1) in used or (x + 1) in used):
            continue
          limit = height - 1
          for lx, _, ln in legend:
            if lx == x:
              limit = height - ln - 2
          if h > limit:
            continue
          used.add(x)
          bars.append((x, c, h, body))
          placed = True
          break
        if not placed:
          ok = False
          break
      if not ok:
        break
    if not ok:
      continue
    bars.sort()
    return width, height, legend, bars
  # Deterministic fallback (practically unreachable).
  return 12, 10, [(0, 2, 1)], [(3, 2, 4, 5), (7, 2, 7, 5)]


def generate(width=None, height=None, legend=None, bars=None):
  """Returns an input/output pair for task 97d7923e.

  Args:
    width: grid width (sampled when any argument is None).
    height: grid height.
    legend: list of (x, colour, n) legend strips hanging from row 0; n is
        the rank of the bar to fill for that colour.
    bars: list of (x, cap_colour, bar_height, body_colour) bars standing on
        the bottom row.  Heights within one cap colour must be distinct and
        a bar below a legend strip must leave at least one background cell.
  """
  if width is None or height is None or legend is None or bars is None:
    width, height, legend, bars = _sample_scene()
  return _build(width, height, legend, bars)


def validate():
  """Reconstructs the canonical train/test pairs with explicit parameters."""
  train = [
      generate(width=15, height=10, legend=[(0, 2, 2)],
               bars=[(2, 2, 4, 5), (4, 2, 9, 5), (7, 2, 7, 5)]),
      generate(width=10, height=10, legend=[(0, 2, 1)],
               bars=[(2, 2, 4, 3), (6, 2, 7, 3)]),
      generate(width=15, height=10, legend=[(0, 1, 1), (2, 3, 2)],
               bars=[(2, 1, 6, 7), (5, 1, 4, 7), (7, 1, 3, 7),
                     (10, 3, 6, 5), (13, 3, 4, 5)]),
  ]
  test = [
      generate(width=20, height=10,
               legend=[(0, 1, 2), (1, 2, 1), (2, 3, 3), (3, 4, 1)],
               bars=[(1, 2, 6, 5), (3, 4, 5, 5), (6, 3, 3, 5), (8, 3, 7, 5),
                     (10, 3, 4, 5), (13, 2, 3, 5), (15, 4, 3, 5),
                     (16, 1, 9, 5), (18, 1, 6, 5), (19, 1, 4, 5)]),
  ]
  return {"train": train, "test": test}
