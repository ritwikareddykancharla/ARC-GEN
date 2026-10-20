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

"""ARC task 25c199f5: Tetris-style stacking of three panel shapes.

Rule: the 5x17 input holds three 5x5 panels on background 7. The panels
are separated by columns of 6. Each panel contains one monochrome shape
in colour 1 or 5, and consecutive panels alternate colours. The output is
an empty 5x5 canvas. The shapes are dropped into it in order: left panel
first, then middle, then right. Each shape keeps its columns, enters with
its top row at canvas row 0, and falls as a rigid piece. It stops when
the next row down would leave the grid or hit a cell that is already
filled.

Scope: original fixtures retain three 5x5 panels. Random scenes extrapolate
this ordered falling-piece mechanism to square panels of side 4..9 (default
three panels). Optional panel counts 2..4 and sizes up to 14 are supported
when the concatenated input fits within 30 columns. These extra sizes/counts
are synthetic extensions, not observed original configurations. Background 7,
separator 6 and alternating colours 1/5 are preserved. Shapes include bars,
rectangles, plus signs, T/L shapes, rings and random connected polyominoes.
Every random piece must enter the stack without collision; failed sampling
raises rather than substituting a fixed stack.
"""

import random

import common

SIZE = 5
BG = 7
SEP = 6
NUM_PANELS = 3


def _cells(rows):
  """Return the (r, c) cells marked '#' in a list of mask strings."""
  return [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row)
          if ch == "#"]


def _random_poly(max_h, max_w, size):
  """Grow a random 4-connected polyomino inside a max_h x max_w box."""
  cells = {(random.randrange(max_h), random.randrange(max_w))}
  for _ in range(60):
    if len(cells) >= size:
      break
    r, c = random.choice(sorted(cells))
    dr, dc = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
    nr, nc = r + dr, c + dc
    if 0 <= nr < max_h and 0 <= nc < max_w:
      cells.add((nr, nc))
  r0 = min(r for r, _ in cells)
  c0 = min(c for _, c in cells)
  h = max(r for r, _ in cells) - r0 + 1
  w = max(c for _, c in cells) - c0 + 1
  rows = []
  for r in range(h):
    rows.append("".join("#" if (r + r0, c + c0) in cells else "."
                        for c in range(w)))
  return rows


def _random_shape(size=SIZE):
  """Sample one piece mask from several shape families."""
  kind = random.choice(["hbar", "hbar", "vbar", "rect", "plus", "tee",
                        "ell", "ring", "poly", "poly"])
  if kind == "hbar":
    return ["#" * random.randint(1, size)]
  if kind == "vbar":
    return ["#"] * random.randint(2, 3)
  if kind == "rect":
    h, w = random.randint(2, min(4,size-1)), random.randint(2, min(5,size))
    return ["#" * w] * h
  if kind == "plus":
    return [".#.", "###", ".#."]
  if kind == "tee":
    return random.choice([["###", ".#."], [".#.", "###"],
                          ["#.", "##", "#."], [".#", "##", ".#"]])
  if kind == "ell":
    return random.choice([["#.", "##"], [".#", "##"], ["##", "#."],
                          ["##", ".#"], ["#..", "###"], ["..#", "###"],
                          ["###", "#.."], ["###", "..#"]])
  if kind == "ring":
    w = random.randint(3, size)
    return ["#" * w, "#" + "." * (w - 2) + "#", "#" * w]
  return _random_poly(random.randint(1, min(4,size-1)), random.randint(2, min(6,size)),
                      random.randint(2, 9))


def _simulate(pieces, size=SIZE):
  """Drop the pieces into the canvas.

  Returns (canvas, clean). clean is False if a piece collided on entry.
  """
  canvas = common.grid(size, size, BG)
  clean = True
  for color, row, col, rows in pieces:
    cells = [(r, c + col) for r, c in _cells(rows)]
    if not cells:
      continue
    top = min(r for r, _ in cells)
    cells = [(r - top, c) for r, c in cells]
    if any(canvas[r][c] != BG for r, c in cells):
      clean = False
    dy = 0
    while all(r + dy + 1 < size and canvas[r + dy + 1][c] == BG
              for r, c in cells):
      dy += 1
    for r, c in cells:
      canvas[r + dy][c] = color
  return canvas, clean


def _sample_pieces(size=SIZE, num_panels=NUM_PANELS):
  """Sample alternating-colour pieces that stack cleanly."""
  for _ in range(500):
    first = random.choice([1, 5])
    colors = [first if i%2==0 else 6-first for i in range(num_panels)]
    pieces = []
    for i in range(num_panels):
      rows = _random_shape(size)
      h, w = len(rows), len(rows[0])
      pieces.append((colors[i], random.randint(0, size - h),
                     random.randint(0, size - w), rows))
    _, clean = _simulate(pieces,size)
    counts = {1:0,5:0}
    for colour,_,_,rows in pieces:counts[colour]+=len(_cells(rows))
    background_cells = num_panels*size*size-sum(counts.values())
    if clean and background_cells>max(*counts.values(),size*(num_panels-1)):
      return pieces
  raise RuntimeError('could not construct a clean stack for the requested panels')


def generate(pieces=None, size=None, num_panels=None):
  """Generate one input/output pair.

  Args:
    pieces: optional list of tuples (color, row, col, rows). Each
      tuple describes the shape in one panel, from left to right. row and
      col give the top-left corner of the mask inside its panel. rows
      is a list of mask strings that use '#' for filled cells. If omitted,
      a fresh random scene is sampled.
    size: square panel side, 4..14 if the input width stays <=30.
    num_panels: 2..4 panels; defaults to three, or len(pieces) in explicit mode.
  """
  explicit = pieces is not None
  if num_panels is None:
    num_panels = len(pieces) if explicit else NUM_PANELS
  if num_panels not in range(2,5):
    raise ValueError('num_panels must be 2..4')
  if size is None:
    size = SIZE if explicit else random.choice([s for s in [4,5,5,6,7,8,9] if num_panels*s+num_panels-1<=30])
  if not 4<=size<=14 or num_panels*size+num_panels-1>30:
    raise ValueError('panel configuration must fit within 30 columns')
  if pieces is None:
    pieces = _sample_pieces(size,num_panels)
  if len(pieces)!=num_panels:
    raise ValueError('piece count must equal panel count')
  width = num_panels*size+num_panels-1
  grid = common.grid(width,size,BG)
  for p in range(1,num_panels):
    for r in range(size):
      grid[r][p*(size+1)-1]=SEP
  for i,(color,row,col,rows) in enumerate(pieces):
    if color not in (1,5) or not _cells(rows):
      raise ValueError('each piece must be nonempty with colour 1 or 5')
    x0=i*(size+1)
    for r,c in _cells(rows):
      if not(0<=row+r<size and 0<=col+c<size):
        raise ValueError('piece must lie inside its input panel')
      grid[row+r][x0+col+c]=color
  output,_ = _simulate(pieces,size)
  return {"input": grid, "output": output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent pieces."""
  train = [
      generate(pieces=[(1, 1, 1, [".#.", "###"]), (5, 2, 2, ["#"]),
                       (1, 3, 1, ["###"])]),
      generate(pieces=[(1, 0, 0, ["#####", "#...#", "#####"]),
                       (5, 1, 2, ["##"]), (1, 4, 1, ["##"])]),
      generate(pieces=[(1, 3, 0, ["#####"]), (5, 1, 1, ["####"]),
                       (1, 2, 1, ["###"])]),
      generate(pieces=[(5, 1, 1, ["###", "#.#", "###"]),
                       (1, 2, 2, ["##"]), (5, 1, 3, ["#"])]),
      generate(pieces=[(5, 2, 1, ["###"]),
                       (1, 1, 1, [".#.", "###", ".#."]),
                       (5, 2, 2, ["#"])]),
  ]
  test = [
      generate(pieces=[(1, 3, 1, ["##", "##"]), (5, 2, 2, ["##", "##"]),
                       (1, 3, 3, ["#"])]),
      generate(pieces=[(5, 2, 0, [".#.", "###", ".#."]),
                       (1, 4, 1, ["#"]), (5, 4, 0, ["#####"])]),
  ]
  return {"train": train, "test": test}
