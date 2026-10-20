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

"""ARC task 38007db0: odd-one-out panel in each row of panels.

Rule: the input is a lattice of equal rectangular panels separated by one-cell
frame lines. Every panel has a one-cell background margin around an h x w motif
drawn in an ink colour. Within each row of panels, every panel shows the same
motif except one, the odd one out. The output keeps the full input height and
is one panel wide plus its two frame lines. Each row of panels is replaced by
its odd-one-out panel.

Scope: motif heights 2..11 and widths 2..6, with at least two panel rows
and three panel columns, all within 30x30. A one-cell background margin
surrounds each motif. Frame, background and ink colours are distinct.
The base motif is shared across rows or chosen per row; each odd motif is a
small edit or an unrelated mask. Rectangular variants are a synthetic
extension; validate() preserves the original square panels.
"""

import random

import common


def _parse(motif):
  return [[1 if ch == "1" else 0 for ch in row] for row in motif]


def _fmt(m):
  return ["".join("1" if v else "0" for v in row) for row in m]


def _random_motif(h, w):
  dens = random.uniform(0.35, 0.7)
  for _ in range(100):
    m = [[1 if random.random() < dens else 0 for _ in range(w)] for _ in range(h)]
    if 2 <= sum(map(sum,m)) < h*w:
      return m
  raise RuntimeError("Could not sample a varied motif")


def _odd_motif(base, h, w):
  for _ in range(100):
    if random.random() < 0.65:
      m = [row[:] for row in base]
      cells = random.sample([(r,c) for r in range(h) for c in range(w)],random.randint(1,3))
      for r,c in cells:m[r][c]=1-m[r][c]
    else:
      m = _random_motif(h,w)
    if m != base and sum(map(sum,m)) > 0:return m
  raise RuntimeError("Could not sample a distinct nonempty odd motif")


def generate(size=None, rows=None, cols=None, frame=None, background=None,
             ink=None, bases=None, odds=None, odd_cols=None,
             motif_height=None, motif_width=None):
  """Generate a framed lattice and the odd panel from each panel row.

  size is the backwards-compatible square motif side. motif_height/width
  allow rectangles (2..11 rows, 2..6 columns), subject to a 30x30 grid.
  The motif has a one-cell margin inside every panel. rows >= 2, cols >= 3.
  Explicit bases and odds are lists of per-row binary string arrays;
  odd_cols gives the exceptional panel column in each row. Missing colours
  are sampled without replacing colours already supplied.
  """
  if size is not None:
    if motif_height is not None or motif_width is not None:
      raise ValueError("Use size or rectangular dimensions, not both")
    motif_height=motif_width=size
  if bases is not None:
    if not bases or not bases[0] or not bases[0][0]:raise ValueError("Bases must be nonempty")
    if rows is None:rows=len(bases)
    if motif_height is None:motif_height=len(bases[0])
    if motif_width is None:motif_width=len(bases[0][0])
  for n,minimum in ((rows,2),(cols,3)):
    if n is not None and (not isinstance(n,int) or n < minimum):raise ValueError("At least two rows and three columns required")
  maxh=29//(rows if rows is not None else 2)-3
  maxw=29//(cols if cols is not None else 3)-3
  if maxh < 2 or maxw < 2:raise ValueError("Requested panel counts exceed 30x30")
  h=motif_height if motif_height is not None else random.randint(2,maxh)
  w=motif_width if motif_width is not None else random.randint(2,maxw)
  if not isinstance(h,int) or not isinstance(w,int) or not (2 <= h <= maxh and 2 <= w <= maxw):
    raise ValueError("Motif dimensions must fit panel counts within 30x30")
  rows=rows if rows is not None else random.randint(2,29//(h+3))
  cols=cols if cols is not None else random.randint(3,29//(w+3))
  supplied=[v for v in (frame,background,ink) if v is not None]
  if any(v not in range(10) for v in supplied) or len(set(supplied))!=len(supplied):
    raise ValueError("Frame, background and ink must be distinct valid colours")
  palette=[v for v in range(10) if v not in supplied];random.shuffle(palette)
  if frame is None:frame=palette.pop()
  if background is None:background=palette.pop()
  if ink is None:ink=palette.pop()
  if bases is None:
    if random.random() < 0.5:
      base=_fmt(_random_motif(h,w));bases=[base for _ in range(rows)]
    else:bases=[_fmt(_random_motif(h,w)) for _ in range(rows)]
  for motifs in (bases,odds):
    if motifs is not None and (len(motifs)!=rows or any(len(m)!=h or any(len(row)!=w or any(ch not in '01' for ch in row) for row in m) for m in motifs)):
      raise ValueError("Explicit motifs must be binary strings with requested dimensions and row count")
  bases=[_parse(b) for b in bases]
  if any(not any(v for row in b for v in row) for b in bases):raise ValueError("Base motifs must be nonempty")
  if odds is None:odds=[_fmt(_odd_motif(b,h,w)) for b in bases]
  odds=[_parse(o) for o in odds]
  if any(o==b or not any(v for row in o for v in row) for o,b in zip(odds,bases)):
    raise ValueError("Odd motif must be nonempty and differ from its base")
  if odd_cols is None:odd_cols=[random.randrange(cols) for _ in range(rows)]
  if len(odd_cols)!=rows or any(not isinstance(c,int) or not 0 <= c < cols for c in odd_cols):
    raise ValueError("Invalid odd-panel column indices")
  height=rows*(h+3)+1;width=cols*(w+3)+1
  grid=common.grid(width,height,frame);out=common.grid(w+4,height,frame)
  for pr in range(rows):
    y0=pr*(h+3)+1
    for pc in range(cols):
      x0=pc*(w+3)+1;m=odds[pr] if pc==odd_cols[pr] else bases[pr]
      for r in range(h+2):
        for c in range(w+2):grid[y0+r][x0+c]=background
      for r in range(h):
        for c in range(w):
          if m[r][c]:grid[y0+1+r][x0+1+c]=ink
    for r in range(h+2):
      for c in range(w+2):out[y0+r][1+c]=background
    for r in range(h):
      for c in range(w):
        if odds[pr][r][c]:out[y0+1+r][2+c]=ink
  return {"input":grid,"output":out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  b1 = ["100", "111", "010"]
  t1 = generate(size=3, rows=3, cols=3, frame=1, background=6, ink=4,
                bases=[b1, b1, b1],
                odds=[["101", "111", "010"], ["100", "110", "010"],
                      ["100", "111", "000"]],
                odd_cols=[2, 0, 1])
  b2 = ["111", "010", "110"]
  t2 = generate(size=3, rows=3, cols=4, frame=3, background=4, ink=1,
                bases=[b2, b2, b2],
                odds=[["111", "010", "111"], ["111", "010", "010"],
                      ["110", "011", "110"]],
                odd_cols=[2, 0, 3])
  b3 = ["1101", "1001", "1111", "1001"]
  e1 = generate(size=4, rows=4, cols=4, frame=4, background=8, ink=1,
                bases=[b3, b3, b3, b3],
                odds=[["1001", "1111", "1001", "1011"],
                      ["1011", "1001", "1111", "1001"],
                      ["1001", "1001", "1111", "1001"],
                      ["1101", "1001", "1011", "1101"]],
                odd_cols=[1, 2, 1, 3])
  b4 = ["111", "010", "111"]
  e2 = generate(size=3, rows=4, cols=4, frame=1, background=3, ink=8,
                bases=[b4, b4, b4, b4],
                odds=[["101", "010", "111"], ["111", "101", "111"],
                      ["111", "100", "111"], ["111", "010", "110"]],
                odd_cols=[2, 1, 0, 3])
  return {"train": [t1, t2], "test": [e1, e2]}
