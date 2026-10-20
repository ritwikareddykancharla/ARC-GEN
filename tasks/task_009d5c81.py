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

"""Generator for ARC task 009d5c81 (legend symbol recolours a drawing).

Rule: the input holds a colour-8 drawing in the upper part of the grid and a
small 3x3 colour-1 legend symbol below it.  The symbol's shape selects a
colour from a fixed lookup table (chalice `111/101/010` -> 7, inverted
chalice `101/010/111` -> 3, plus `010/111/010` -> 2).  The output repaints
every drawing cell with that colour and erases the legend symbol.

Scope: grid size, drawing shape/position and symbol position are sampled.
The drawing colour (8), symbol colour (1) and the three legend glyphs with
their colours are intrinsic to the task and kept fixed.  The drawing's
bounding box is always strictly larger than the 3x3 symbol so the two
objects are unambiguous.
"""

import random

import common


GLYPHS = [
    (["111", "101", "010"], 7),
    (["101", "010", "111"], 3),
    (["010", "111", "010"], 2),
]
DRAW_COLOR = 8
SYMBOL_COLOR = 1


def _random_drawing(dh, dw):
  """Grows a connected blob inside a dh x dw box and returns it as strings.

  Args:
    dh: box height
    dw: box width
  """
  target = max(dh + dw, int(dh * dw * random.uniform(0.35, 0.6)))
  cells = {(random.randrange(dh), random.randrange(dw))}
  frontier = list(cells)
  attempts = 0
  while len(cells) < target and attempts < 500:
    attempts += 1
    r, c = random.choice(frontier)
    dr, dc = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
    nr, nc = r + dr, c + dc
    if 0 <= nr < dh and 0 <= nc < dw and (nr, nc) not in cells:
      cells.add((nr, nc))
      frontier.append((nr, nc))
  rows = [r for r, _ in cells]
  cols = [c for _, c in cells]
  r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
  return ["".join("#" if (r, c) in cells else "." for c in range(c0, c1 + 1))
          for r in range(r0, r1 + 1)]


def generate(width=None, height=None, drawing=None, draw_row=None,
             draw_col=None, glyph=None, sym_row=None, sym_col=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: grid width
    height: grid height
    drawing: list of strings ('#' = drawing cell, '.' = empty) giving the
      drawing cropped to its bounding box
    draw_row: top row of the drawing
    draw_col: left column of the drawing
    glyph: index into GLYPHS of the legend symbol
    sym_row: top row of the 3x3 legend symbol
    sym_col: left column of the 3x3 legend symbol
  """
  if width is None:
    width = random.randint(12, 20)
  if height is None:
    height = random.randint(12, 20)
  if drawing is None:
    for _ in range(100):
      dh = random.randint(3, min(8, height - 6))
      dw = random.randint(4, min(10, width))
      cand = _random_drawing(dh, dw)
      ch, cw = len(cand), len(cand[0])
      # Bounding box must dominate the 3x3 symbol's bounding box.
      if ch * cw >= 12 and max(ch, cw) >= 4 and ch <= height - 6:
        drawing = cand
        break
    if drawing is None:
      drawing = ["####", "#..#", "####"]
  dh, dw = len(drawing), len(drawing[0])
  if draw_row is None:
    draw_row = random.randint(0, height - dh - 5)
  if draw_col is None:
    draw_col = random.randint(0, width - dw)
  if glyph is None:
    glyph = random.randrange(len(GLYPHS))
  if sym_row is None:
    sym_row = random.randint(draw_row + dh + 1, height - 3)
  if sym_col is None:
    sym_col = random.randint(0, width - 3)

  shape, new_color = GLYPHS[glyph]
  grid, output = common.grid(width, height), common.grid(width, height)
  for r in range(dh):
    for c in range(dw):
      if drawing[r][c] == "#":
        grid[draw_row + r][draw_col + c] = DRAW_COLOR
        output[draw_row + r][draw_col + c] = new_color
  for r in range(3):
    for c in range(3):
      if shape[r][c] == "1":
        grid[sym_row + r][sym_col + c] = SYMBOL_COLOR
  return {"input": grid, "output": output}


def validate():
  """Validates the generator against the canonical ARC examples."""
  train = [
      generate(width=14, height=14,
               drawing=["...##.....", "....###...", "......#.#.",
                        ".####.###.", "##..###.##", "...##...#.",
                        "..##...##.", ".....###.."],
               draw_row=0, draw_col=4, glyph=0, sym_row=10, sym_col=4),
      generate(width=14, height=14,
               drawing=["##.#.##", "#.#.#.#", "##.#.##"],
               draw_row=2, draw_col=4, glyph=1, sym_row=10, sym_col=3),
      generate(width=14, height=14,
               drawing=["..#...#..", "#.#.#.#.#", "#########",
                        "#.#.#.#.#", "#...#...#"],
               draw_row=0, draw_col=1, glyph=2, sym_row=9, sym_col=7),
      generate(width=14, height=14,
               drawing=["...#...", "###.##.", ".#.##..", "..#..##",
                        "...##.#", ".....#."],
               draw_row=1, draw_col=5, glyph=1, sym_row=8, sym_col=2),
      generate(width=14, height=14,
               drawing=["...##.##.", "....###..", ".####....", "##.#..##.",
                        "...####..", "....#.#..", "..###.###", "..#.....#"],
               draw_row=1, draw_col=4, glyph=2, sym_row=9, sym_col=1),
  ]
  test = [
      generate(width=14, height=14,
               drawing=["#########", "#...#.#.#", "#.#.#...#", "#########"],
               draw_row=1, draw_col=5, glyph=0, sym_row=8, sym_col=6),
  ]
  return {"train": train, "test": test}
