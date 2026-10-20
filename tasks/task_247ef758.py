# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC task 247ef758: stamp legend motifs at marker-row x marker-column crossings.

The grid has three parts. On the left is a legend of small single-colour
motifs on background 0. Next is a full-height divider column. On the right is
a rectangular frame: its border has one dominant colour, a few marker cells of
other colours sit on the border, and its interior is empty (0).

* A marker on the left or right border at row r marks row r for its colour.
* A marker on the top or bottom border at column x marks column x for its
  colour. Corners are ignored.

For every legend motif whose colour has at least one marker row and at least
one marker column, the motif is copied into the frame. One copy is centred on
each (marker row, marker column) crossing. The centre is the floor-centre of
the motif's bounding box. The motif is then erased from the legend.

Copies are painted from the lowest legend motif to the highest, so where
copies overlap the motif that sits higher in the legend stays on top. Motifs
with no row marker, or no column marker, stay in the legend unchanged.

Scope: the random scenes vary the legend width (3-5), the grid height, the
frame width, and the divider, frame and motif colours. They use catalogue and
random 3x3 motifs, 1 or 2 marker rows and columns per stamped colour, and
unstamped motifs that have no markers, row markers only or column markers
only. They also add distractor marker colours that have no motif, sometimes
on just one edge. Overlapping copies are allowed and follow the legend order.
"""

import random

import common


PLUS = ("010", "111", "010")
DIAMOND = ("010", "101", "010")
CROSS = ("101", "010", "101")
BLOCK = ("111", "111", "111")
DIAG = ("100", "010", "001")
ANTI = ("001", "010", "100")
HBAR = ("111",)

CATALOG = [
    PLUS, DIAMOND, CROSS, BLOCK, DIAG, ANTI, HBAR,
    ("1", "1", "1"),
    ("111", "010", "010"),
    ("010", "010", "111"),
    ("011", "010", "110"),
    ("110", "010", "011"),
    ("111", "111", "101"),
    ("111", "101", "111"),
    ("10000", "01000", "00100", "00010", "00001"),
    ("00001", "00010", "00100", "01000", "10000"),
    ("11111",),
    ("00100", "00100", "11111", "00100", "00100"),
]


def _cells(pattern):
  return [(r, c) for r, row in enumerate(pattern)
          for c, ch in enumerate(row) if ch == "1"]


def _random_mask():
  for _ in range(100):
    m = [[random.randint(0, 1) for _ in range(3)] for _ in range(3)]
    if sum(map(sum, m)) < 4:
      continue
    if not all(any(row) for row in m):
      continue
    if not all(any(m[r][c] for r in range(3)) for c in range(3)):
      continue
    return tuple("".join(str(v) for v in row) for row in m)
  return PLUS


def _pick_shape(legend_width):
  if legend_width >= 3 and random.random() < 0.3:
    return _random_mask()
  pool = [p for p in CATALOG if len(p[0]) <= legend_width]
  return random.choice(pool)


def _build(height, legend_width, frame_width, divider_color, frame_color,
           motifs, top_marks, bottom_marks, left_marks, right_marks):
  """Draws the input from latent parameters and derives the output."""
  width = legend_width + 1 + frame_width
  f0 = legend_width + 1
  grid = common.grid(width, height, 0)
  for r in range(height):
    grid[r][legend_width] = divider_color
    grid[r][f0] = frame_color
    grid[r][width - 1] = frame_color
  for c in range(f0, width):
    grid[0][c] = frame_color
    grid[height - 1][c] = frame_color
  for r, colour in left_marks.items():
    grid[r][f0] = colour
  for r, colour in right_marks.items():
    grid[r][width - 1] = colour
  for o, colour in top_marks.items():
    grid[0][f0 + o] = colour
  for o, colour in bottom_marks.items():
    grid[height - 1][f0 + o] = colour
  for colour, top, left, pattern in motifs:
    for r, c in _cells(pattern):
      grid[top + r][left + c] = colour

  output = [row[:] for row in grid]
  rows_of, cols_of = {}, {}
  for marks in (left_marks, right_marks):
    for r, colour in marks.items():
      if 1 <= r <= height - 2:
        rows_of.setdefault(colour, set()).add(r)
  for marks in (top_marks, bottom_marks):
    for o, colour in marks.items():
      if 1 <= o <= frame_width - 2:
        cols_of.setdefault(colour, set()).add(f0 + o)

  def top_row(m):
    return m[1] + min(r for r, _ in _cells(m[3]))

  # Paint the lowest legend motif first so higher motifs end up on top.
  for colour, top, left, pattern in sorted(motifs, key=lambda m: -top_row(m)):
    if colour not in rows_of or colour not in cols_of:
      continue
    cells = _cells(pattern)
    y0 = min(r for r, _ in cells)
    y1 = max(r for r, _ in cells)
    x0 = min(c for _, c in cells)
    x1 = max(c for _, c in cells)
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    for rr in sorted(rows_of[colour]):
      for cc in sorted(cols_of[colour]):
        for r, c in cells:
          y, x = rr + r - cy, cc + c - cx
          if not (1 <= y <= height - 2 and f0 + 1 <= x <= width - 2):
            raise ValueError("stamp leaves the frame interior")
          output[y][x] = colour
    for r, c in cells:
      output[top + r][left + c] = 0
  return grid, output, rows_of, cols_of


def _sample_scene(height=None, legend_width=None, frame_width=None,
                  divider_color=None, frame_color=None):
  for _ in range(500):
    lw = legend_width if legend_width is not None else random.choice(
        [3, 3, 4, 4, 5])
    h = height if height is not None else random.randint(9, 30)
    fw = frame_width if frame_width is not None else random.randint(
        9, 29 - lw)
    if lw+fw+1>30:continue
    fc = frame_color if frame_color is not None else random.randint(1, 9)
    if divider_color is not None:
      dc = divider_color
    else:
      dc = random.choice([c for c in range(1, 10) if c != fc])
    if dc == fc:
      continue
    free = [c for c in range(1, 10) if c not in (fc, dc)]
    random.shuffle(free)
    n_motifs = random.randint(2, 5 if h>=18 else 4)
    motif_colours = free[:n_motifs]
    spare = free[n_motifs:] + [dc]
    shapes = [_pick_shape(lw) for _ in range(n_motifs)]
    gaps = [random.randint(0, 1) for _ in range(n_motifs - 1)]
    need = sum(len(s) for s in shapes) + sum(gaps)
    if need > h:
      continue
    r = random.randint(0, min(2, h - need))
    motifs = []
    for i, s in enumerate(shapes):
      left = random.randint(0, lw - len(s[0]))
      motifs.append((motif_colours[i], r, left, s))
      r += len(s) + (gaps[i] if i < len(gaps) else 0)
    stamped = set(random.sample(range(n_motifs),
                                random.randint(1, min(4, n_motifs))))
    used_rows, used_cols = set(), set()
    side, top_marks, bottom_marks = {}, {}, {}
    ok = True
    for i, (colour, _, _, s) in enumerate(motifs):
      if i in stamped:
        mh, mw = len(s), len(s[0])
        cy, cx = (mh - 1) // 2, (mw - 1) // 2
        row_pool = [y for y in range(1 + cy, h - 1 - (mh - 1 - cy))
                    if y not in used_rows]
        col_pool = [o for o in range(1 + cx, fw - 1 - (mw - 1 - cx))
                    if o not in used_cols]
        nr = 2 if random.random() < 0.35 else 1
        nc = 2 if random.random() < 0.35 else 1
        if len(row_pool) < nr or len(col_pool) < nc:
          ok = False
          break
        for y in random.sample(row_pool, nr):
          used_rows.add(y)
          side[y] = colour
        for o in random.sample(col_pool, nc):
          used_cols.add(o)
          top_marks[o] = colour
          bottom_marks[o] = colour
      else:
        mode = random.choice(["none", "none", "rows", "cols"])
        if mode == "rows":
          pool = [y for y in range(1, h - 1) if y not in used_rows]
          if pool:
            y = random.choice(pool)
            used_rows.add(y)
            side[y] = colour
        elif mode == "cols":
          pool = [o for o in range(1, fw - 1) if o not in used_cols]
          if pool:
            o = random.choice(pool)
            used_cols.add(o)
            top_marks[o] = colour
            bottom_marks[o] = colour
    if not ok:
      continue
    n_d = random.randint(0, min(2, len(spare)))
    for colour in random.sample(spare, n_d):
      mode = random.choice(["rows", "cols", "both", "top", "bottom"])
      if mode in ("rows", "both"):
        pool = [y for y in range(1, h - 1) if y not in used_rows]
        if pool:
          y = random.choice(pool)
          used_rows.add(y)
          side[y] = colour
      if mode in ("cols", "both", "top", "bottom"):
        pool = [o for o in range(1, fw - 1) if o not in used_cols]
        if pool:
          o = random.choice(pool)
          used_cols.add(o)
          if mode != "bottom":
            top_marks[o] = colour
          if mode != "top":
            bottom_marks[o] = colour
    params = dict(height=h, legend_width=lw, frame_width=fw,
                  divider_color=dc, frame_color=fc, motifs=motifs,
                  top_marks=top_marks, bottom_marks=bottom_marks,
                  left_marks=dict(side), right_marks=dict(side))
    grid, output, _, _ = _build(**params)
    width = lw + 1 + fw
    # Background 0 must be the most common colour.
    counts = {}
    for row in grid:
      for v in row:
        counts[v] = counts.get(v, 0) + 1
    if any(v != 0 and n >= counts[0] for v, n in counts.items()):
      continue
    # The frame colour must dominate the frame border.
    f0 = lw + 1
    border = (grid[0][f0:] + grid[h - 1][f0:] +
              [grid[y][f0] for y in range(h)] +
              [grid[y][width - 1] for y in range(h)])
    bc = {}
    for v in border:
      bc[v] = bc.get(v, 0) + 1
    if any(v != fc and n >= bc[fc] for v, n in bc.items()):
      continue
    # Every stamped colour must remain visible in the frame interior.
    visible = True
    for i in stamped:
      colour = motifs[i][0]
      if not any(output[y][x] == colour for y in range(1, h - 1)
                 for x in range(f0 + 1, width - 1)):
        visible = False
    if not visible:
      continue
    return params
  raise ValueError("could not sample a valid scene")


def generate(height=None, legend_width=None, frame_width=None,
             divider_color=None, frame_color=None, motifs=None,
             top_marks=None, bottom_marks=None, left_marks=None,
             right_marks=None):
  """Returns an input/output pair.

  If motifs is None, a fresh random scene is sampled. Any given height,
  legend_width, frame_width, divider_color and frame_color are kept.

  Args:
    height: grid height (number of rows).
    legend_width: number of legend columns left of the divider.
    frame_width: width of the frame, including both border columns.
    divider_color: colour of the full-height divider column.
    frame_color: dominant colour of the frame border.
    motifs: list of (colour, top, left, pattern) legend motifs. Each pattern
      is a tuple of '0'/'1' strings with a tight bounding box.
    top_marks: {frame column offset: colour} cells on the top border.
    bottom_marks: {frame column offset: colour} cells on the bottom border.
    left_marks: {row: colour} cells on the left frame border.
    right_marks: {row: colour} cells on the right frame border.
  """
  if motifs is None:
    if any(v is not None for v in (top_marks,bottom_marks,left_marks,right_marks)):
      raise ValueError('explicit border markers require explicit motifs')
    if height is not None and not 9<=height<=30:
      raise ValueError('height must be 9..30')
    if legend_width is not None and not 3<=legend_width<=5:
      raise ValueError('legend_width must be 3..5')
    if frame_width is not None and not 9<=frame_width<=26:
      raise ValueError('frame_width must be 9..26')
    if legend_width is not None and frame_width is not None and legend_width+frame_width+1>30:
      raise ValueError('total width must not exceed 30')
    if any(v is not None and v not in range(1,10) for v in (divider_color,frame_color)):
      raise ValueError('frame and divider colours must be 1..9')
    if divider_color is not None and divider_color==frame_color:
      raise ValueError('frame and divider colours must differ')
    params = _sample_scene(height, legend_width, frame_width, divider_color,
                           frame_color)
  else:
    params = dict(height=height, legend_width=legend_width,
                  frame_width=frame_width, divider_color=divider_color,
                  frame_color=frame_color, motifs=motifs,
                  top_marks=top_marks or {}, bottom_marks=bottom_marks or {},
                  left_marks=left_marks or {}, right_marks=right_marks or {})
  grid, output, _, _ = _build(**params)
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the original task pairs from explicit latent parameters."""
  s1 = {4: 4, 6: 7, 9: 6}
  t1 = {2: 6, 5: 4, 6: 7}
  s2 = {2: 7, 5: 5, 7: 7}
  t2 = {2: 7, 4: 5, 6: 7}
  s3 = {3: 3, 6: 6}
  t3 = {3: 3, 7: 6}
  s4 = {3: 1, 6: 3, 7: 4, 8: 4, 9: 6, 12: 1}
  s5 = {2: 7, 4: 3, 5: 4, 8: 6}
  train = [
      generate(height=12, legend_width=3, frame_width=14, divider_color=2,
               frame_color=3,
               motifs=[(4, 0, 0, PLUS), (7, 8, 0, BLOCK)],
               top_marks=dict(t1), bottom_marks=dict(t1),
               left_marks=dict(s1), right_marks=dict(s1)),
      generate(height=10, legend_width=4, frame_width=10, divider_color=3,
               frame_color=4,
               motifs=[(5, 0, 0, DIAMOND), (8, 3, 0, DIAG), (7, 6, 0, PLUS)],
               top_marks=dict(t2), bottom_marks=dict(t2),
               left_marks=dict(s2), right_marks=dict(s2)),
      generate(height=10, legend_width=3, frame_width=10, divider_color=1,
               frame_color=2,
               motifs=[(3, 0, 0, PLUS), (6, 4, 0, DIAMOND), (7, 8, 0, HBAR)],
               top_marks=dict(t3), bottom_marks=dict(t3),
               left_marks=dict(s3), right_marks=dict(s3)),
  ]
  test = [
      generate(height=15, legend_width=4, frame_width=15, divider_color=3,
               frame_color=9,
               motifs=[(1, 0, 0, PLUS), (4, 4, 0, DIAG),
                       (6, 8, 0, ("111", "111", "101")),
                       (7, 12, 1, CROSS)],
               top_marks={2: 1, 5: 3, 9: 4, 10: 6, 13: 8},
               bottom_marks={1: 8, 2: 1, 5: 3, 9: 4, 10: 6},
               left_marks=dict(s4), right_marks=dict(s4)),
      generate(height=12, legend_width=5, frame_width=12, divider_color=2,
               frame_color=1,
               motifs=[(6, 0, 0, ("10000", "01000", "00100", "00010",
                                  "00001")),
                       (8, 4, 0, HBAR),
                       (4, 6, 1, ("011", "010", "110")),
                       (7, 9, 1, PLUS)],
               top_marks={0: 9, 2: 7, 4: 7, 5: 3, 7: 4, 8: 6},
               bottom_marks={2: 7, 4: 7, 5: 3, 7: 4, 8: 6},
               left_marks=dict(s5), right_marks=dict(s5)),
  ]
  return {"train": train, "test": test}
