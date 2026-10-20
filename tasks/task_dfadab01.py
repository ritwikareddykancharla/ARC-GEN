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

"""ARC task dfadab01: stamp a fixed 4x4 motif at every single-pixel marker.

Rule:
  Single-pixel markers of colours 2, 3, 5 and 8 lie on a background of 0.
  Each marker becomes the top-left corner of a 4x4 motif, clipped to the grid:
    2 -> hollow square in colour 4   (1111/1001/1001/1111)
    3 -> ring in colour 1            (0110/1001/1001/0110)
    5 -> diagonal 2x2 blocks, col 6  (1100/1100/0011/0011)
    8 -> X in colour 7               (1001/0110/0110/1001)
  An optional legend is a full 4x4 motif drawn in its motif colour. Its key
  marker sits one cell diagonally past the motif's bottom-right corner. The
  output erases both the legend shape and its key marker; neither is stamped.
  The output starts from a blank canvas, so nothing else survives.

Scope:
  Random scenes place markers on a lattice. The lattice is either regular
  (one step shared by rows and columns: a random choice of 4..6 by default,
  or a requested step in 4..7) or irregular (each row and column gap drawn
  independently from 4..gmax, gmax in 5..7, as in training pair 1). It has a
  random offset (any value below the step or gmax), random density and a
  random palette subset. Markers may lie in the last row or column, where
  their stamps are clipped. Random-scene sides are 10..30. Sides above 20 and
  non-square grids are synthetic extensions. Marker gaps of at least 4 keep
  the 4x4 stamp boxes disjoint.

  With probability 0.75 a legend is placed, either on a lattice point or at
  a free position. Every lattice marker inside the one-cell margin around the
  legend and its key is removed. One exception copies training pair 2: a
  ring legend (key 3) may keep a 3-marker in its empty top-left corner,
  whether or not that corner is a lattice point, provided its stamp box is
  disjoint from every other marker's box. That marker is stamped normally,
  so the ring reappears in the output. The legend key colour always occurs
  among the ordinary markers in random scenes.

  Fixtures are rebuilt from explicit marker lists and legend tuples. The
  explicit path forbids markers inside the legend's 5x5 box (motif plus key)
  except the pair-2 ring-corner 3, and it requires 0 to be the majority
  colour so that the background is unambiguous.
"""

import random

import common


_TABLE = {
    2: (4, [[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]]),
    3: (1, [[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]]),
    5: (6, [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]]),
    8: (7, [[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1]]),
}

_MIN_RANDOM_SIDE = 10


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _seq(v, name):
  """Returns v as a tuple, raising ValueError for non-sequences."""
  if not isinstance(v, (list, tuple)):
    raise ValueError(name + " must be a list or tuple")
  return tuple(v)


def _stamp_cells(r, c, key, width, height):
  col, pat = _TABLE[key]
  cells = []
  for dy in range(4):
    for dx in range(4):
      if pat[dy][dx] and r + dy < height and c + dx < width:
        cells.append((r + dy, c + dx, col))
  return cells


def _build(width, height, markers, legend):
  """Draws the input and derives the output from the latent scene."""
  if not (_is_int(width) and _is_int(height)):
    raise ValueError("grid sides must be integers")
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid sides must be in 1..30")
  if not markers:
    raise ValueError("at least one ordinary marker is required")
  grid = common.grid(width, height, 0)
  legend_cells = set()
  if legend is not None:
    lr, lc, key = legend
    if key not in _TABLE:
      raise ValueError("bad legend key colour")
    if lr < 0 or lc < 0 or lr + 4 >= height or lc + 4 >= width:
      raise ValueError("legend does not fit")
    for r, c, col in _stamp_cells(lr, lc, key, width, height):
      grid[r][c] = col
      legend_cells.add((r, c))
    grid[lr + 4][lc + 4] = key
  for r, c, col in markers:
    if not (_is_int(r) and _is_int(c) and _is_int(col)):
      raise ValueError("marker entries must be integers")
    if col not in _TABLE:
      raise ValueError("bad marker colour")
    if not (0 <= r < height and 0 <= c < width):
      raise ValueError("marker out of bounds")
    if legend is not None:
      in_box = (legend[0] <= r <= legend[0] + 4 and
                legend[1] <= c <= legend[1] + 4)
      ring_corner = ((r, c) == (legend[0], legend[1]) and legend[2] == 3
                     and col == 3)
      if in_box and not ring_corner:
        raise ValueError("only a 3-marker in the ring legend corner may sit "
                         "inside the legend box")
    if grid[r][c] != 0:
      raise ValueError("marker overlaps another object")
    grid[r][c] = col
  # Stamp boxes of distinct markers must be disjoint, as in every fixture.
  for i in range(len(markers)):
    for j in range(i + 1, len(markers)):
      if (abs(markers[i][0] - markers[j][0]) < 4 and
          abs(markers[i][1] - markers[j][1]) < 4):
        raise ValueError("marker stamp boxes overlap")
  # Markers must be isolated single pixels. The only permitted contact is a
  # 3-marker in the empty top-left corner of a ring legend (training pair 2).
  for r, c, col in markers:
    corner = legend is not None and (r, c) == (legend[0], legend[1])
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if dr == 0 and dc == 0:
          continue
        rr, cc = r + dr, c + dc
        if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 0:
          if not (corner and (rr, cc) in legend_cells):
            raise ValueError("marker touches another object")
  # The background must be the unambiguous majority colour.
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  zeros = counts.get(0, 0)
  if any(n >= zeros for v, n in counts.items() if v != 0):
    raise ValueError("background 0 must be the most common colour")
  output = common.grid(width, height, 0)
  painted = set()
  for r, c, col in sorted(markers):
    for rr, cc, val in _stamp_cells(r, c, col, width, height):
      if (rr, cc) in painted:
        raise ValueError("stamps overlap")
      painted.add((rr, cc))
      output[rr][cc] = val
  return {"input": grid, "output": output}


def _positions(n, start, gap_fn):
  pos = []
  p = start
  while p <= n - 1:
    pos.append(p)
    p += gap_fn()
  return pos


def _sample_scene(width, height, step, irregular, palette, legend,
                  with_legend):
  min_h, min_w = _MIN_RANDOM_SIDE, _MIN_RANDOM_SIDE
  if legend is not None:
    min_h = max(min_h, legend[0] + 5)
    min_w = max(min_w, legend[1] + 5)
  for _ in range(400):
    h = height if height is not None else random.randint(min_h, 30)
    w = width if width is not None else random.randint(min_w, 30)
    if step is not None:
      use_irregular = False
    elif irregular is not None:
      use_irregular = irregular
    else:
      use_irregular = random.random() < 0.35
    if use_irregular:
      gmax = random.choice([5, 6, 7])
      gap_fn = lambda: random.randint(4, gmax)
      r0 = random.randint(0, gmax - 1)
      c0 = random.randint(0, gmax - 1)
    else:
      st = step if step is not None else random.choice([4, 4, 5, 5, 6])
      gap_fn = lambda: st
      r0 = random.randint(0, st - 1)
      c0 = random.randint(0, st - 1)
    rows = _positions(h, r0, gap_fn)
    cols = _positions(w, c0, gap_fn)
    if not rows or not cols:
      continue
    if palette is not None:
      pal = list(palette)
    else:
      pal = random.sample([2, 3, 5, 8], random.randint(1, 4))
      if legend is not None and legend[2] not in pal:
        pal.append(legend[2])
    density = random.uniform(0.5, 1.0)
    markers = []
    for r in rows:
      for c in cols:
        if random.random() < density:
          markers.append((r, c, random.choice(pal)))
    if legend is not None:
      use_legend = True
    elif with_legend is not None:
      use_legend = with_legend
    else:
      use_legend = random.random() < 0.75
    legend_t = None
    if use_legend:
      if legend is not None:
        pr, pc, key = legend
        if pr + 4 >= h or pc + 4 >= w:
          continue
      else:
        key = None
        cands = [(r, c) for r in rows for c in cols
                 if r + 4 <= h - 1 and c + 4 <= w - 1]
        if cands and random.random() < 0.6:
          pr, pc = random.choice(cands)
        else:
          pr = random.randint(0, h - 5)
          pc = random.randint(0, w - 5)
      kept = [(r, c, col) for r, c, col in markers
              if not (pr - 1 <= r <= pr + 5 and pc - 1 <= c <= pc + 5)]
      if not kept:
        continue
      colours = sorted({col for _, _, col in kept})
      if key is None:
        key = random.choice(colours)
      elif key not in colours:
        idx = random.randrange(len(kept))
        kept[idx] = (kept[idx][0], kept[idx][1], key)
      if key == 3 and random.random() < 0.5:
        # Pair-2 exception: an ordinary 3 in the ring's empty corner. Only
        # allowed when its stamp box is disjoint from every kept marker.
        clash = any(abs(r - pr) < 4 and abs(c - pc) < 4
                    for r, c, _ in kept)
        if not clash:
          kept.append((pr, pc, 3))
      markers = kept
      legend_t = (pr, pc, key)
      if not markers:
        continue
    elif len(markers) < 2:
      continue
    return w, h, markers, legend_t
  raise RuntimeError("could not sample a scene with the requested controls")


def generate(width=None, height=None, markers=None, legend=None, step=None,
             palette=None, with_legend=None, irregular=None):
  """Generate an input/output pair.

  Args:
    width: grid width (int). With markers it is required (1..30). Otherwise
      it fixes the width of a random scene (10..30).
    height: grid height (int). With markers it is required (1..30).
      Otherwise it fixes the height of a random scene (10..30).
    markers: non-empty list of (row, col, colour) ordinary markers, colour in
      2/3/5/8. When given, the scene is built exactly with no random
      sampling. Stamp boxes must be disjoint, markers must be isolated, and
      only the pair-2 ring-corner 3 may lie inside the legend box.
    legend: optional (row, col, key) giving the top-left of the legend motif.
      Its key marker sits at (row + 4, col + 4). With markers=None, a random
      lattice is sampled around this legend.
    step: regular lattice spacing for random scenes (int, 4..7). The default
      is a random choice of 4..6 or an irregular lattice.
    palette: non-empty list of distinct colours from [2, 3, 5, 8] used for
      random markers. Must contain an explicit legend's key colour.
    with_legend: None, True or False. Forces legend presence in random
      scenes. The default is a 75% chance.
    irregular: None, True or False. True forces independent gaps of 4..gmax
      for every row and column; False forces a regular lattice. True cannot
      be combined with an explicit step.
  """
  for name, v in (("width", width), ("height", height), ("step", step)):
    if v is not None and not _is_int(v):
      raise ValueError(name + " must be an integer")
  for name, v in (("with_legend", with_legend), ("irregular", irregular)):
    if v is not None and not isinstance(v, bool):
      raise ValueError(name + " must be None, True or False")
  if legend is not None:
    legend = _seq(legend, "legend")
    if (len(legend) != 3 or not all(_is_int(v) for v in legend)
        or legend[2] not in _TABLE):
      raise ValueError("legend must be (row, col, key) with key in 2/3/5/8")
    if legend[0] < 0 or legend[1] < 0:
      raise ValueError("legend position must be non-negative")
  if markers is not None:
    if width is None or height is None:
      raise ValueError("width and height are required with explicit markers")
    if (step is not None or palette is not None or with_legend is not None
        or irregular is not None):
      raise ValueError("step/palette/with_legend/irregular apply only to "
                       "random scenes")
    mk = []
    for m in _seq(markers, "markers"):
      m = _seq(m, "marker")
      if len(m) != 3 or not all(_is_int(v) for v in m):
        raise ValueError("markers must be (row, col, colour) integer tuples")
      mk.append(m)
    return _build(width, height, mk, legend)
  if step is not None and not 4 <= step <= 7:
    raise ValueError("step must be in 4..7")
  if step is not None and irregular:
    raise ValueError("step defines a regular lattice; irregular=True "
                     "contradicts it")
  if palette is not None:
    palette = list(_seq(palette, "palette"))
    if not palette or any(not _is_int(p) or p not in _TABLE for p in palette):
      raise ValueError("palette must be a non-empty subset of [2, 3, 5, 8]")
    if len(set(palette)) != len(palette):
      raise ValueError("palette must not contain duplicates")
    if legend is not None and legend[2] not in palette:
      raise ValueError("legend key colour must belong to the palette")
  if with_legend is False and legend is not None:
    raise ValueError("with_legend=False contradicts an explicit legend")
  for side in (width, height):
    if side is not None and not _MIN_RANDOM_SIDE <= side <= 30:
      raise ValueError("random-scene sides must be in 10..30")
  if legend is not None:
    if (height is not None and legend[0] + 4 >= height) or (
        width is not None and legend[1] + 4 >= width):
      raise ValueError("legend does not fit in the requested grid")
    if legend[0] + 5 > 30 or legend[1] + 5 > 30:
      raise ValueError("legend cannot fit in a 30x30 grid")
  w, h, mk, lg = _sample_scene(width, height, step, irregular, palette,
                               legend, with_legend)
  return _build(w, h, mk, lg)


def validate():
  """Rebuild the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=20, height=20, legend=(1, 1, 5), markers=[
          (1, 8, 2), (1, 13, 2), (6, 8, 2), (6, 13, 2),
          (11, 2, 3), (11, 8, 5), (11, 13, 5),
          (16, 2, 3), (16, 8, 3), (16, 13, 3)]),
      generate(width=10, height=10, legend=(5, 5, 3), markers=[
          (1, 1, 3), (1, 5, 2), (5, 1, 2), (5, 5, 3)]),
      generate(width=10, height=10, legend=(0, 0, 2), markers=[
          (0, 6, 2), (6, 0, 2), (6, 6, 2)]),
  ]
  rows4 = [[2, 2, 5, 8, 8], [2, 3, 2, 3, 8], [5, 3, 5, 2, 5],
           [8, 3, 2, 3, 2], [8, 8, 5, 2, 2]]
  m4 = []
  for i, row in enumerate(rows4):
    for j, col in enumerate(row):
      m4.append((4 * i, 4 * j, col))
  train.append(generate(width=20, height=20, legend=None, markers=m4))
  test_cols = {1: [0, 4, 8, 12, 16], 5: [0, 16], 9: [0, 16],
               13: [0, 12, 16], 17: [0, 4, 8, 12, 16]}
  mt = []
  for r in sorted(test_cols):
    for c in test_cols[r]:
      mt.append((r, c, 8))
  test = [generate(width=20, height=20, legend=(5, 4, 8), markers=mt)]
  return {"train": train, "test": test}
