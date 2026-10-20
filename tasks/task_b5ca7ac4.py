# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ARC-GEN style generator for task b5ca7ac4.

Rule: the grid holds 5x5 squares. Each square is a one-cell frame of colour 8
or colour 2 around a 3x3 core of another colour. Squares framed in 8 slide
left and squares framed in 2 slide right, like gravity, and every square
keeps its rows. Within one frame colour, the square nearest its wall moves
first. Each later square stops against the row-overlapping squares of its
own colour that are already placed. Squares of the other frame colour never
block it.

Scope: the canvas size, background colour (never 2 or 8), number of squares,
square positions, frame colours and core colours are all sampled. Input
squares may touch, but they never overlap. Any scene is rejected when its
row-major 5x5 window parse would not recover exactly the latent squares, when
the slid squares would overlap or leave the grid, or when nothing moves.
"""

import random

import common

FRAMES = (8, 2)
BACKGROUNDS = (0, 1, 3, 4, 5, 6, 7, 9)


def _overlap(a, b):
  return abs(a[0] - b[0]) < 5 and abs(a[1] - b[1]) < 5


def _slide(squares, width):
  """Returns the output x position of every square, or None if one leaves the grid."""
  out_x = [s[1] for s in squares]
  for frame, direction in ((8, 'left'), (2, 'right')):
    idx = [i for i, s in enumerate(squares) if s[2] == frame]
    idx.sort(key=lambda i: squares[i][1], reverse=(direction == 'right'))
    placed = []
    for i in idx:
      y = squares[i][0]
      blockers = [p for p in placed if abs(p[0] - y) < 5]
      if direction == 'left':
        nx = max([p[1] + 5 for p in blockers], default=0)
      else:
        nx = min([p[1] - 5 for p in blockers], default=width - 5)
      if nx < 0 or nx + 5 > width:
        return None
      placed.append((y, nx))
      out_x[i] = nx
  return out_x


def _paint(grid, y, x, frame, core):
  for r in range(5):
    for c in range(5):
      edge = r in (0, 4) or c in (0, 4)
      grid[y + r][x + c] = frame if edge else core


def _parse_ok(grid, squares, bg):
  """Checks that a row-major window scan recovers exactly the latent squares."""
  height, width = len(grid), len(grid[0])
  used = [[False] * width for _ in range(height)]
  found = set()
  for y in range(height - 4):
    for x in range(width - 4):
      if any(used[y + r][x + c] for r in range(5) for c in range(5)):
        continue
      border = [grid[y + r][x + c] for r in range(5) for c in range(5)
                if r in (0, 4) or c in (0, 4)]
      inner = [grid[y + r][x + c] for r in range(1, 4) for c in range(1, 4)]
      col, ic = border[0], inner[0]
      if col == bg or any(v != col for v in border):
        continue
      if any(v != ic for v in inner) or ic == col or ic == bg:
        continue
      for r in range(5):
        for c in range(5):
          used[y + r][x + c] = True
      found.add((y, x))
  return found == set((s[0], s[1]) for s in squares)


def _build(width, height, bg, squares):
  out_x = _slide(squares, width)
  if out_x is None:
    return None
  for i in range(len(squares)):
    for j in range(i + 1, len(squares)):
      if _overlap((squares[i][0], out_x[i]), (squares[j][0], out_x[j])):
        return None
  grid = common.grid(width, height, bg)
  output = common.grid(width, height, bg)
  for s, nx in zip(squares, out_x):
    _paint(grid, s[0], s[1], s[2], s[3])
    _paint(output, s[0], nx, s[2], s[3])
  return {'input': grid, 'output': output}, out_x


def generate(width=None, height=None, background=None, squares=None):
  """Generates one input/output pair.

  Args:
    width: grid width (sampled in 14..26 when None).
    height: grid height (sampled in 12..26 when None).
    background: background colour, never 2 or 8 (sampled when None).
    squares: optional list of (row, col, frame_colour, core_colour). Each
      entry is the top-left corner of a 5x5 square in the input. If given,
      the scene is built exactly from it.
  """
  if squares is not None:
    width = 22 if width is None else width
    height = 22 if height is None else height
    bg = 0 if background is None else background
    squares = [tuple(s) for s in squares]
    built = _build(width, height, bg, squares)
    if built is None:
      raise ValueError('explicit squares slide off-grid or collide')
    return built[0]

  for _ in range(500):
    w = width if width is not None else random.randint(14, 26)
    h = height if height is not None else random.randint(12, 26)
    bg = background if background is not None else random.choice(BACKGROUNDS)
    cap = max(3, min(10, (w * h) // 55))
    target = random.randint(3, cap)
    sq = []
    for _ in range(300):
      if len(sq) >= target:
        break
      y = random.randint(0, h - 5)
      x = random.randint(0, w - 5)
      if any(_overlap((y, x), (s[0], s[1])) for s in sq):
        continue
      frame = random.choice(FRAMES)
      core = random.choice([c for c in range(10) if c not in (frame, bg)])
      sq.append((y, x, frame, core))
    if len(sq) < 3:
      continue
    if not any(s[2] == 8 for s in sq) or not any(s[2] == 2 for s in sq):
      continue
    built = _build(w, h, bg, sq)
    if built is None:
      continue
    pair, out_x = built
    if all(out_x[i] == sq[i][1] for i in range(len(sq))):
      continue
    if not _parse_ok(pair['input'], sq, bg):
      continue
    return pair
  raise RuntimeError('failed to sample a valid scene')


def validate():
  """Reconstructs the canonical fixtures from explicit latent squares."""
  train = [
      generate(width=22, height=22, background=0, squares=[
          (1, 1, 8, 5), (2, 9, 2, 1), (3, 15, 8, 3), (7, 4, 2, 3),
          (9, 13, 2, 9), (13, 0, 2, 6), (15, 12, 8, 4), (16, 5, 2, 4)]),
      generate(width=22, height=22, background=4, squares=[
          (0, 8, 2, 5), (2, 2, 8, 9), (2, 14, 2, 3), (8, 0, 8, 3),
          (8, 16, 2, 6), (14, 2, 8, 1), (14, 14, 2, 1), (16, 8, 8, 6)]),
      generate(width=22, height=22, background=1, squares=[
          (0, 12, 2, 3), (1, 3, 8, 2), (5, 12, 8, 6), (8, 2, 2, 5),
          (12, 14, 2, 4), (14, 7, 8, 3)]),
  ]
  test = [
      generate(width=22, height=22, background=9, squares=[
          (0, 1, 2, 4), (2, 10, 2, 3), (3, 16, 8, 4), (7, 2, 8, 1),
          (8, 10, 8, 7), (13, 9, 2, 6), (15, 3, 2, 3), (16, 15, 8, 3)]),
  ]
  return {'train': train, 'test': test}
