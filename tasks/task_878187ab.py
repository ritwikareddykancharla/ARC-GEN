# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator for ARC task 878187ab.

Rule: the input is a background-7 field with scattered single pixels in
exactly two non-background colours.  Pixel positions are irrelevant; only the
two colour counts matter.  The output is always a 16x16 background-7 canvas
with a solid block of colour 2 anchored at the bottom-left whose width is the
larger colour count and whose height is the smaller colour count.  Two
diagonals of colour 4 rise one step per row from the block's bottom-left and
bottom-right corners toward each other (overlapping where they cross).

Scope: input sizes 10..22 per side (fixtures use 16x16 and 15x15), any pair of
distinct non-7 colours, larger count 3..16 and smaller count 2..larger-1 so the
block always fits the fixed 16x16 canvas.  Equal counts are deliberately not
sampled, so width/height assignment is never ambiguous.
"""

import random

import common


CANVAS = 16
BG = 7
BLOCK = 2
DIAG = 4


def _draw_output(counts):
  """Builds the 16x16 answer from the two pixel counts."""
  small, big = sorted(counts)
  out = common.grid(CANVAS, CANVAS, BG)
  w, h = min(big, CANVAS), min(small, CANVAS)
  for y in range(CANVAS - h, CANVAS):
    for x in range(w):
      out[y][x] = BLOCK
  for k in range(h):
    y = CANVAS - 1 - k
    if k < w:
      out[y][k] = DIAG
      out[y][w - 1 - k] = DIAG
  return out


def generate(width=None, height=None, colors=None, counts=None, pixels=None):
  """Returns {'input': ..., 'output': ...} for one scene.

  Args:
    width: input grid width (10..22 when sampled).
    height: input grid height (10..22 when sampled).
    colors: list of the two distinct non-background colours.
    counts: list of the two pixel counts, aligned with `colors` and distinct.
    pixels: explicit list of (row, col, color) triples; when given it fully
      determines the input and `counts` is derived from it.
  """
  if width is None:
    width = random.randint(10, 22)
  if height is None:
    height = random.randint(10, 22)
  if colors is None:
    colors = random.sample([c for c in range(10) if c != BG], 2)
  if pixels is None:
    if counts is None:
      for _ in range(100):
        big = random.randint(3, 16)
        small = random.randint(2, big - 1)
        if big + small <= (width * height) // 3:
          break
      counts = [small, big]
      random.shuffle(counts)
    cells = [(r, c) for r in range(height) for c in range(width)]
    chosen = random.sample(cells, sum(counts))
    pixels = []
    idx = 0
    for color, n in zip(colors, counts):
      for _ in range(n):
        r, c = chosen[idx]
        idx += 1
        pixels.append((r, c, color))
  tally = {}
  for _, _, color in pixels:
    tally[color] = tally.get(color, 0) + 1
  grid = common.grid(width, height, BG)
  for r, c, color in pixels:
    grid[r][c] = color
  return {"input": grid, "output": _draw_output(list(tally.values()))}


def validate():
  """Reconstructs the canonical train/test fixtures via explicit calls."""
  train = [
      generate(width=16, height=16, colors=[8, 6], pixels=[
          (0, 1, 8), (1, 12, 8), (2, 6, 8), (4, 9, 8), (8, 6, 8),
          (10, 14, 8), (11, 3, 8), (12, 14, 8), (13, 8, 8), (15, 14, 8),
          (3, 1, 6), (3, 12, 6), (4, 3, 6), (11, 6, 6), (12, 9, 6)]),
      generate(width=15, height=15, colors=[4, 5], pixels=[
          (1, 1, 4), (2, 14, 4), (3, 8, 4), (7, 3, 4), (7, 14, 4),
          (12, 1, 4), (12, 6, 4),
          (3, 9, 5), (7, 5, 5), (8, 8, 5), (10, 11, 5), (11, 8, 5)]),
  ]
  test = [
      generate(width=16, height=16, colors=[5, 0], pixels=[
          (0, 11, 5), (2, 3, 5), (3, 5, 5), (5, 7, 5), (7, 1, 5),
          (7, 13, 5), (8, 10, 5), (10, 1, 5), (10, 12, 5), (11, 2, 5),
          (11, 11, 5), (13, 15, 5),
          (1, 10, 0), (1, 14, 0), (2, 10, 0), (2, 15, 0), (4, 9, 0),
          (4, 11, 0), (7, 8, 0), (7, 10, 0), (7, 12, 0), (8, 5, 0),
          (8, 15, 0), (10, 10, 0), (12, 2, 0), (13, 3, 0)]),
  ]
  return {"train": train, "test": test}
