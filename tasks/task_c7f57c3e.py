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

"""ARC task c7f57c3e: swap the decorations between the two figure groups.

Rule: a background holds several figures that all share one colour-1 frame
shape. Some figures are drawn at 2x or 3x scale. Every figure carries a
decoration in other colours: its centre cell(s), plus an attachment such as
a cell above or below, a stem with a base, or a side cell. Measured in frame
units, exactly two decoration templates occur. One figure (the odd one) has
template A and the rest have template B. In the output every frame stays put.
Each figure loses its decoration and receives the other group's template,
redrawn at the figure's own scale.

Scope: five frame shapes (T-plus, plus, X, wide plus and tall plus), six
attachment kinds, 3-5 figures, scales 1-3 with at least one unit-scale
figure, random background and decoration colours, and grids of 10-30 per
side. Not supported: several frame shapes in one scene, templates without a
centre cell, and more than two templates.
"""

import random

import common


FRAME = 1

# name -> ((h, w) of frame bbox, frame cells, centre cells), unit coords.
SHAPES = {
    "tplus": ((2, 3), [(0, 1), (1, 0), (1, 2)], [(1, 1)]),
    "plus": ((3, 3), [(0, 1), (1, 0), (1, 2), (2, 1)], [(1, 1)]),
    "x": ((3, 3), [(0, 0), (0, 2), (2, 0), (2, 2)], [(1, 1)]),
    "wplus": ((3, 4), [(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 2)],
              [(1, 1), (1, 2)]),
    "hplus": ((4, 3), [(0, 1), (1, 0), (2, 0), (1, 2), (2, 2), (3, 1)],
              [(1, 1), (2, 1)]),
}

KINDS = ["above", "below", "left", "right", "below_base", "above_cap"]


def template_cells(shape, spec):
  """Return {(dy, dx): colour} for a decoration spec in frame units."""
  (h, w), _, centre = SHAPES[shape]
  c, kind, cols = spec
  rows = sorted({r for r, _ in centre})
  ccols = sorted({q for _, q in centre})
  d = {p: c for p in centre}
  if kind == "above":
    for q in ccols:
      d[(-1, q)] = cols[0]
  elif kind == "below":
    for q in ccols:
      d[(h, q)] = cols[0]
  elif kind == "left":
    for r in rows:
      d[(r, -1)] = cols[0]
  elif kind == "right":
    for r in rows:
      d[(r, w)] = cols[0]
  elif kind == "below_base":
    for q in ccols:
      d[(h, q)] = cols[0]
    for q in range(w):
      d[(h + 1, q)] = cols[1]
  elif kind == "above_cap":
    for q in ccols:
      d[(-1, q)] = cols[0]
    for q in range(w):
      d[(-2, q)] = cols[1]
  return d


def _stamp(g, y0, x0, s, cells, colour=None):
  for (dy, dx), c in cells:
    for a in range(s):
      for b in range(s):
        g[y0 + dy * s + a][x0 + dx * s + b] = c if colour is None else colour


def _paint(height, width, bg, shape, figures, odd_t, com_t, swap):
  g = common.grid(width, height, bg)
  _, frame, _ = SHAPES[shape]
  for (y0, x0, s, odd) in figures:
    _stamp(g, y0, x0, s, [(p, FRAME) for p in frame])
    t = odd_t if odd != swap else com_t
    _stamp(g, y0, x0, s, sorted(t.items()))
  return g


def _box(shape, s, y0, x0, ta, tb):
  (h, w), _, _ = SHAPES[shape]
  keys = list(ta) + list(tb)
  rmin = min([0] + [r for r, _ in keys])
  rmax = max([h - 1] + [r for r, _ in keys])
  cmin = min([0] + [q for _, q in keys])
  cmax = max([w - 1] + [q for _, q in keys])
  return (y0 + rmin * s, y0 + (rmax + 1) * s - 1,
          x0 + cmin * s, x0 + (cmax + 1) * s - 1)


def _sample_spec(palette, kind=None):
  if kind is None:
    kind = random.choice(KINDS)
  c = random.choice(palette)
  if kind in ("below_base", "above_cap"):
    a = random.choice(palette)
    b = a if random.random() < 0.3 else random.choice(palette)
    cols = (a, b)
  else:
    cols = (random.choice(palette),)
  return (c, kind, cols)


def _random_scene(height=None, width=None, background=None, frame_shape=None):
  for _ in range(500):
    bg = background if background is not None else random.choice([0, 2, 3, 4, 5, 6, 7, 8, 9])
    palette = [c for c in range(10) if c not in (FRAME, bg)]
    shape = frame_shape if frame_shape is not None else random.choice(sorted(SHAPES))
    com = _sample_spec(palette)
    same_kind = random.random() < 0.35
    odd = _sample_spec(palette, com[1] if same_kind else None)
    if random.random() < 0.5:
      odd = (com[0], odd[1], odd[2])
    odd_t = template_cells(shape, odd)
    com_t = template_cells(shape, com)
    if odd_t == com_t:
      continue
    n = random.randint(3, 5)
    scales = []
    for _ in range(n):
      r = random.random()
      scales.append(1 if r < 0.62 else (2 if r < 0.88 else 3))
    if 1 not in scales:
      scales[random.randrange(n)] = 1
    while sum(1 for s in scales if s > 1) > 2:
      scales[[i for i, s in enumerate(scales) if s > 1][0]] = 1
    odd_idx = random.randrange(n)
    h = height if height is not None else random.randint(10, 30)
    w = width if width is not None else random.randint(10, 30)
    order = sorted(range(n), key=lambda i: -scales[i])
    boxes, placed, ok = [], {}, True
    for i in order:
      s = scales[i]
      b0 = _box(shape, s, 0, 0, odd_t, com_t)
      ylo, yhi = -b0[0], h - 1 - b0[1]
      xlo, xhi = -b0[2], w - 1 - b0[3]
      if ylo > yhi or xlo > xhi:
        ok = False
        break
      found = False
      for _ in range(150):
        y0 = random.randint(ylo, yhi)
        x0 = random.randint(xlo, xhi)
        bx = _box(shape, s, y0, x0, odd_t, com_t)
        if all(bx[0] > o[1] + 1 or o[0] > bx[1] + 1 or
               bx[2] > o[3] + 1 or o[2] > bx[3] + 1 for o in boxes):
          boxes.append(bx)
          placed[i] = (y0, x0, s, i == odd_idx)
          found = True
          break
      if not found:
        ok = False
        break
    if not ok:
      continue
    figures = [placed[i] for i in range(n)]
    g = _paint(h, w, bg, shape, figures, odd_t, com_t, False)
    nonbg = sum(1 for row in g for v in row if v != bg)
    if 2 * nonbg >= h * w:
      continue
    return h, w, bg, shape, figures, odd, com
  raise RuntimeError("could not place figures within the requested canvas")


def generate(height=None, width=None, background=None, shape=None,
             figures=None, odd_template=None, common_template=None):
  """Build one input/output pair.

  Args:
    height, width: grid size in cells.
    background: background colour (never 1).
    shape: frame shape name, a key of SHAPES.
    figures: list of (row, col, scale, is_odd). (row, col) is the top-left
      of the figure's frame bounding box.
    odd_template: (centre colour, attachment kind, attachment colours) worn
      by the odd figure in the input.
    common_template: the same kind of spec, worn by every other figure.
  Without explicit figures, a fresh scene respects any supplied canvas,
  background and frame shape. Explicit figures require both templates and
  every scene parameter; incomplete latent requests are rejected.
  """
  if background is not None and background not in (0, 2, 3, 4, 5, 6, 7, 8, 9):
    raise ValueError("background must be an ARC colour other than frame colour 1")
  if shape is not None and shape not in SHAPES:
    raise ValueError("unknown frame shape")
  if any(v is not None and not 10 <= v <= 30 for v in (height, width)):
    raise ValueError("canvas sides must be 10..30")
  if figures is None:
    if odd_template is not None or common_template is not None:
      raise ValueError("explicit templates require explicit figures")
    (height, width, background, shape, figures, odd_template,
     common_template) = _random_scene(height, width, background, shape)
  elif any(v is None for v in (height, width, background, shape, odd_template, common_template)):
    raise ValueError("explicit figures require complete latent parameters")
  odd_t = template_cells(shape, odd_template)
  com_t = template_cells(shape, common_template)
  inp = _paint(height, width, background, shape, figures, odd_t, com_t, False)
  out = _paint(height, width, background, shape, figures, odd_t, com_t, True)
  return {"input": inp, "output": out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(18, 18, 4, "tplus",
               [(1, 12, 1, True), (5, 3, 1, False), (9, 8, 2, False)],
               (2, "below_base", (8, 8)), (2, "below_base", (2, 3))),
      generate(18, 18, 3, "x",
               [(1, 1, 1, False), (6, 8, 2, False), (11, 2, 1, True)],
               (2, "above", (6,)), (2, "below", (4,))),
  ]
  test = [
      generate(28, 28, 8, "wplus",
               [(2, 1, 1, False), (6, 9, 1, True), (14, 2, 3, False),
                (17, 19, 1, False)],
               (6, "below", (4,)), (3, "above", (2,))),
  ]
  return {"train": train, "test": test}
