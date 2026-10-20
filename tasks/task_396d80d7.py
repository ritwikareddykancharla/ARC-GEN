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

"""ARC-GEN style generator for task 396d80d7.

Rule: a single compact two-colour figure sits on a background of colour 7.
Every background cell that touches the figure only diagonally (at least one
figure cell among its 4 diagonal neighbours and none among its 4 orthogonal
neighbours) is painted with the inner colour. The inner colour is the figure
colour with the strictly smallest bounding box.

Scope: random grids of 10..30 cells per side, a figure box of 4..28 cells per
side placed with a one-cell margin, an outer colour whose cells touch all four
edges of the figure box, and an inner colour confined to a smaller interior
box (so its bounding box is always strictly smaller). Figures are drawn with
four-fold, left/right, up/down or no mirror symmetry. The background stays 7,
as in every original pair. The answer is computed from the latent figure cells
and the latent inner colour.
"""

import random

import common


def _render(width, height, pixels, inner_color, background):
  """Builds the input and output grids from latent pixels."""
  grid = common.grid(width, height, background)
  for r, c, col in pixels:
    grid[r][c] = col
  fig = set((r, c) for r, c, _ in pixels)
  output = [row[:] for row in grid]
  orth = ((1, 0), (-1, 0), (0, 1), (0, -1))
  diag = ((1, 1), (1, -1), (-1, 1), (-1, -1))
  for r in range(height):
    for c in range(width):
      if (r, c) in fig:
        continue
      if any((r + dr, c + dc) in fig for dr, dc in orth):
        continue
      if any((r + dr, c + dc) in fig for dr, dc in diag):
        output[r][c] = inner_color
  return {"input": grid, "output": output}


def generate(width=None, height=None, pixels=None, inner_color=None,
             background=7, figure_height=None, figure_width=None, symmetry=None):
  """Returns an input/output pair.

  Args:
    width: grid width (random 10..30 if None; 16 if pixels are given).
    height: grid height (random 10..30 if None; 16 if pixels are given).
    pixels: optional explicit list of (row, col, colour) figure cells.
    inner_color: colour used for the new ring (required with pixels).
    background: background colour (7 in the task).
    figure_height, figure_width: exact random figure-box sides, 4..28.
    symmetry: quad, lr, ud, or none; random when omitted.
  """
  for dimension in (width,height):
    if dimension is not None and (not isinstance(dimension,int) or not 1 <= dimension <= 30):
      raise ValueError("Dimensions must be in 1..30")
  if background not in range(10) or (inner_color is not None and (inner_color not in range(10) or inner_color==background)):
    raise ValueError("Invalid background or inner colour")
  if symmetry not in (None,"quad","lr","ud","none"):
    raise ValueError("Unknown symmetry")
  for size in (figure_height,figure_width):
    if size is not None and (not isinstance(size,int) or not 4 <= size <= 28):
      raise ValueError("Figure sides must be in 4..28")
  if pixels is not None:
    if inner_color is None or not pixels:
      raise ValueError("Explicit pixels require inner_color and nonempty pixels")
    if any(v is not None for v in (figure_height,figure_width,symmetry)):
      raise ValueError("Random shape controls cannot accompany explicit pixels")
    W,H=width if width is not None else 16,height if height is not None else 16
    if any(not (0 <= r < H and 0 <= c < W and col in range(10) and col!=background) for r,c,col in pixels):
      raise ValueError("Pixel outside canvas or invalid colour")
    if len({(r,c) for r,c,col in pixels})!=len(pixels):raise ValueError("Duplicate pixel coordinates")
    areas={}
    for colour in {col for r,c,col in pixels}:
      points=[(r,c) for r,c,col in pixels if col==colour]
      areas[colour]=(max(r for r,c in points)-min(r for r,c in points)+1)*(max(c for r,c in points)-min(c for r,c in points)+1)
    if inner_color not in areas or any(area <= areas[inner_color] for col,area in areas.items() if col!=inner_color):
      raise ValueError("inner_color must have the unique smallest bounding box")
    return _render(W,H,pixels,inner_color,background)
  if any(d is not None and d < 6 for d in (width,height)):
    raise ValueError("Random canvas sides must be at least 6")
  if (figure_height is not None and height is not None and figure_height+2 > height) or (figure_width is not None and width is not None and figure_width+2 > width):
    raise ValueError("Requested figure needs a one-cell margin")
  for _ in range(500):
    H = height if height is not None else random.randint(10, 30)
    W = width if width is not None else random.randint(10, 30)
    if H < 6 or W < 6:
      continue
    fh = figure_height if figure_height is not None else random.randint(4,H-2)
    fw = figure_width if figure_width is not None else random.randint(4,W-2)
    if fh+2 > H or fw+2 > W:continue
    r0 = random.randint(1, H - fh - 1)
    c0 = random.randint(1, W - fw - 1)
    sym = symmetry if symmetry is not None else random.choice(["quad", "quad", "quad", "lr", "ud", "none"])
    mirror_ud = sym in ("quad", "ud")
    mirror_lr = sym in ("quad", "lr")
    ih_opts = [k for k in range(1, min(max(4,fh//2), fh - 2) + 1)
               if not mirror_ud or k % 2 == fh % 2]
    iw_opts = [k for k in range(1, min(max(4,fw//2), fw - 2) + 1)
               if not mirror_lr or k % 2 == fw % 2]
    ih, iw = random.choice(ih_opts), random.choice(iw_opts)
    it = (fh - ih) // 2 if mirror_ud else random.randint(1, fh - 1 - ih)
    il = (fw - iw) // 2 if mirror_lr else random.randint(1, fw - 1 - iw)
    colours = [k for k in range(10) if k != background]
    inner = inner_color if inner_color is not None else random.choice(colours)
    outer = random.choice([c for c in colours if c!=inner])
    density = random.uniform(0.3, 0.65)
    p_inner = random.uniform(0.5, 0.9)
    cells = {}
    for r in range(fh):
      for c in range(fw):
        if (r, c) in cells:
          continue
        orbit = {(r, c)}
        if mirror_ud:
          orbit |= {(fh - 1 - a, b) for a, b in list(orbit)}
        if mirror_lr:
          orbit |= {(a, fw - 1 - b) for a, b in list(orbit)}
        in_box = it <= r < it + ih and il <= c < il + iw
        x = random.random()
        if in_box:
          col = inner if x < p_inner else (outer if x < p_inner + 0.1 else None)
        else:
          col = outer if x < density else None
        for cell in orbit:
          cells[cell] = col
    inn = [(r, c) for (r, c), v in cells.items() if v == inner]
    out = [(r, c) for (r, c), v in cells.items() if v == outer]
    if not inn or not out:
      continue
    rows = [r for r, _ in out]
    cols = [c for _, c in out]
    if min(rows) != 0 or max(rows) != fh - 1:
      continue
    if min(cols) != 0 or max(cols) != fw - 1:
      continue
    ir = [r for r, _ in inn]
    ic = [c for _, c in inn]
    a_in = (max(ir) - min(ir) + 1) * (max(ic) - min(ic) + 1)
    if a_in >= fh * fw:
      continue
    pix = [(r0 + r, c0 + c, v) for (r, c), v in sorted(cells.items())
           if v is not None]
    if 2 * len(pix) >= H * W:
      continue
    pair = _render(W, H, pix, inner, background)
    if pair["input"] == pair["output"]:
      continue
    return pair
  raise ValueError("could not construct a scene")


def _px(spec):
  """Expands {colour: [(row, [cols]), ...]} into a pixel list."""
  out = []
  for col, rows in spec.items():
    for r, cs in rows:
      for c in cs:
        out.append((r, c, col))
  return out


def validate():
  """Reconstructs the canonical fixtures through explicit generate calls."""
  t1 = _px({6: [(4, [5, 6, 8, 9]), (5, [4, 7, 10]), (6, [5, 6, 8, 9]),
                (7, [4, 7, 10]), (8, [5, 6, 8, 9]), (9, [4, 7, 10])],
            2: [(6, [7]), (8, [7])]})
  t2 = _px({4: [(5, [7, 8]), (6, [6, 9]), (7, [5, 10]), (8, [5, 10]),
                (9, [6, 9]), (10, [7, 8])],
            1: [(7, [7, 8]), (8, [7, 8])]})
  te = _px({1: [(6, [6, 9]), (9, [6, 9])],
            9: [(7, [7, 8]), (8, [7, 8])]})
  return {
      "train": [
          generate(width=16, height=16, pixels=t1, inner_color=2),
          generate(width=16, height=16, pixels=t2, inner_color=1),
      ],
      "test": [
          generate(width=16, height=16, pixels=te, inner_color=9),
      ],
  }
