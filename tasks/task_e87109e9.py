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

"""ARC task e87109e9: legend-steered beams from an 8 square.

Rule:
  The top six rows form a legend strip framed by colour 5. It holds four
  panels, and each panel is a 4x3 block of 0s with one coloured marker column
  on its left or right side. Below the strip is a canvas with a background
  colour, several solid coloured blocks and one s x s square of colour 8.
  The output is the canvas alone. From the 8 square, four beams of width s
  start: up, down, left and right. A beam advances one cell at a time and
  paints 8. When its next position would overlap a coloured block, it turns in
  place instead. The turn is to the left of its travel direction if that
  colour's legend marker is on the left of its 0s, and to the right otherwise.
  A beam stops when it would leave the grid, or when it hits a colour that is
  not in the legend. Collision tests use the original canvas, so beams cross
  each other and the start square freely.

Scope:
  The width is fixed at 24 because four 6-column legend panels define it. The
  canvas height varies from 14 to 24, so the grid has 20 to 30 rows. The
  background colour, the legend colours, their order and their sides are
  sampled. The square size is 2 or 3. There are 3 or 4 distinct-colour
  rectangular blocks, often snapped to the grid edges. Each beam's path is
  computed from these latent objects.
"""

import collections
import random

import common

PALETTE = [1, 2, 3, 4, 6, 7, 9]
WIDTH = 24
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _header(legend):
  rows = [[5] * WIDTH]
  for _ in range(4):
    row = []
    for colour, side in legend:
      panel = [colour, 0, 0, 0] if side == "L" else [0, 0, 0, colour]
      row += [5] + panel + [5]
    rows.append(row)
  rows.append([5] * WIDTH)
  return rows


def _build_body(height, bg, square, blocks):
  body = common.grid(WIDTH, height, bg)
  for top, left, bh, bw, colour in blocks:
    for i in range(max(0, top), min(height, top + bh)):
      for j in range(max(0, left), min(WIDTH, left + bw)):
        body[i][j] = colour
  r, c, s = square
  for i in range(r, r + s):
    for j in range(c, c + s):
      body[i][j] = 8
  return body


def _trace(body, bg, square, legend):
  """Shoots the four beams; returns painted canvas and diagnostic stats."""
  r, c, s = square
  h, w = len(body), len(body[0])
  turn = {colour: side for colour, side in legend}
  out = [row[:] for row in body]
  stats = {"turns": 0, "turned_beams": 0, "mixed": False, "loop": False,
           "stopped": False}
  for d in DIRS:
    y, x = r, c
    dy, dx = d
    seen = set()
    turned = False
    for _ in range(2000):
      state = (y, x, dy, dx)
      if state in seen:
        stats["loop"] = True
        break
      seen.add(state)
      ny, nx = y + dy, x + dx
      if ny < 0 or nx < 0 or ny + s > h or nx + s > w:
        break
      vals = [body[i][j] for i in range(ny, ny + s) for j in range(nx, nx + s)
              if body[i][j] != bg and body[i][j] != 8]
      if not vals:
        y, x = ny, nx
        for i in range(y, y + s):
          for j in range(x, x + s):
            out[i][j] = 8
        continue
      counts = collections.Counter(vals)
      if len(counts) > 1:
        stats["mixed"] = True
      colour = counts.most_common(1)[0][0]
      side = turn.get(colour)
      if side is None:
        stats["stopped"] = True
        break
      if side == "L":
        dy, dx = -dx, dy
      else:
        dy, dx = dx, -dy
      stats["turns"] += 1
      turned = True
    if turned:
      stats["turned_beams"] += 1
  return out, stats


def _apart(a, b, gap):
  t1, l1, h1, w1 = a
  t2, l2, h2, w2 = b
  return (t1 + h1 + gap <= t2 or t2 + h2 + gap <= t1 or
          l1 + w1 + gap <= l2 or l2 + w2 + gap <= l1)


def _sample_block(height, colour):
  bh = random.randint(2, max(2, min(12, height - 4)))
  bw = random.randint(2, 14)
  top = random.randint(0, height - bh)
  left = random.randint(0, WIDTH - bw)
  snap = random.random()
  if snap < 0.25:
    left = 0
  elif snap < 0.45:
    left = WIDTH - bw
  elif snap < 0.6:
    top = 0
  elif snap < 0.75:
    top = height - bh
  return (top, left, bh, bw, colour)


def _sample_scene(requested_height=None, requested_bg=None):
  for _ in range(1000):
    height = requested_height if requested_height is not None else random.randint(14, 24)
    bg = requested_bg if requested_bg is not None else random.choice(PALETTE)
    colours = [bg] + random.sample([c for c in PALETTE if c != bg], 4)
    legend = [(col, random.choice(["L", "R"])) for col in colours[1:]]
    s = random.choice([2, 2, 3])
    r = random.randint(2, height - s - 2)
    c = random.randint(2, WIDTH - s - 2)
    sq_rect = (r, c, s, s)
    nblocks = random.randint(3, 4)
    block_colours = random.sample(colours[1:], nblocks)
    blocks = []
    ok = True
    for colour in block_colours:
      placed = False
      for _ in range(60):
        blk = _sample_block(height, colour)
        rect = blk[:4]
        if not _apart(rect, sq_rect, 1):
          continue
        if all(_apart(rect, b[:4], 1) for b in blocks):
          blocks.append(blk)
          placed = True
          break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    area = sum(b[2] * b[3] for b in blocks) + s * s
    if area * 2 >= height * WIDTH:
      continue
    body = _build_body(height, bg, (r, c, s), blocks)
    _, stats = _trace(body, bg, (r, c, s), legend)
    if stats["mixed"] or stats["loop"] or stats["stopped"]:
      continue
    if stats["turns"] < 2 or stats["turned_beams"] < 2:
      continue
    return legend, bg, height, (r, c, s), blocks
  raise RuntimeError("could not sample beams satisfying turn and separation constraints")


def generate(legend=None, bg=None, height=None, square=None, blocks=None):
  """Generates one input/output pair.

  Args:
    legend: four (colour, side) tuples in panel order, with side "L" or "R"
      giving the marker position (and turn direction) for that colour.
    bg: canvas background colour.
    height: canvas height (the input has 6 extra legend rows).
    square: (row, col, size) of the 8 square within the canvas.
    blocks: list of (top, left, height, width, colour) canvas rectangles.
  """
  if height is not None and not 14 <= height <= 24:
    raise ValueError("canvas height must be 14..24")
  if bg is not None and bg not in PALETTE:
    raise ValueError("background must avoid legend frame, source and empty colours")
  if legend is None and square is None and blocks is None:
    legend, bg, height, square, blocks = _sample_scene(height, bg)
  elif any(v is None for v in (legend, bg, height, square, blocks)):
    raise ValueError("explicit scenes require legend, background, height, square and blocks")
  body = _build_body(height, bg, square, blocks)
  out, _ = _trace(body, bg, square, legend)
  grid = _header(legend) + [row[:] for row in body]
  return {"input": grid, "output": out}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(legend=[(1, "L"), (6, "L"), (4, "L"), (2, "L")], bg=3,
               height=19, square=(7, 8, 2),
               blocks=[(3, 0, 9, 4, 1), (4, 18, 7, 4, 4),
                       (16, 4, 3, 11, 2)]),
      generate(legend=[(2, "R"), (4, "L"), (6, "R"), (3, "L")], bg=1,
               height=19, square=(8, 8, 2),
               blocks=[(0, 13, 2, 5, 6), (5, 0, 7, 4, 2), (5, 16, 6, 4, 3),
                       (16, 5, 3, 8, 4)]),
      generate(legend=[(4, "R"), (6, "L"), (3, "L"), (2, "R")], bg=7,
               height=19, square=(11, 12, 2),
               blocks=[(0, 8, 4, 10, 3), (3, 20, 11, 4, 6),
                       (7, 0, 12, 3, 2), (16, 8, 3, 14, 4)]),
  ]
  test = [
      generate(legend=[(1, "L"), (3, "R"), (2, "L"), (4, "L")], bg=9,
               height=24, square=(7, 8, 3),
               blocks=[(0, 0, 3, 21, 2), (0, 21, 13, 3, 3),
                       (6, 0, 10, 3, 1), (17, 7, 3, 9, 4)]),
  ]
  return {"train": train, "test": test}
