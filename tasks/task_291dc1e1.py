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

"""ARC-GEN style generator for task 291dc1e1.

Rule: the input has a 0 in one corner with two full border lines leaving it,
one of colour 1 and one of colour 2. The rest is a background-8 field with multiple
lanes, each two cells thick, running parallel to the 1-line. Each lane holds
2-by-L blocks (L even) separated by two background cells. A block is solid or
carries a small accent pattern.

If the 1-line is vertical, the grid is first turned 90 degrees
counter-clockwise. That makes the lanes horizontal. Lanes are read nearest to
the 1-line first. Within a lane, blocks are read nearest to the 2-line first.
Each block is copied as it appears in the turned frame. The blocks are stacked
vertically, each centred in a strip as wide as the longest block.

Original fixtures have two lanes; random scenes have 2-4 lanes and an optional
num_lanes supports 2-5. Additional lanes are a synthetic mechanism extrapolation,
not extra original evidence. Total output height is capped at 30.

Scope: all four corners, both choices of which border line is the 1-line, and
2-5 blocks per lane with lengths 2/4/6/8. Blocks are solid or carry 1-3 accent
cells, sometimes in two accent colours. Gaps between blocks are always two
cells, and the first block sits one cell from the 2-line, as in every fixture.
The frame is built in the solver's normalised frame (1-line horizontal). It is
turned clockwise to produce a vertical-1-line input.
"""

import random

import common

BG = 8
SOLID = [3, 4, 5, 6, 7, 9]
ACCENT = [1, 2, 3, 4, 5, 6, 7, 9]
LENGTHS = [2, 2, 2, 2, 4, 4, 4, 6, 6, 8]
SHAPES = [
    [(0, 0), (1, 1)],
    [(1, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1)],
    [(1, 0), (1, 1)],
    [(0, 0)],
    [(1, 1)],
    [(0, 1), (1, 0), (1, 1)],
]


def _solid(color, length):
  return [[color] * length for _ in range(2)]


def _patterned(length):
  base = random.choice(SOLID)
  accents = [c for c in ACCENT if c != base]
  a1 = random.choice(accents)
  a2 = a1
  if random.random() < 0.25:
    a2 = random.choice([c for c in accents if c != a1])
  block = _solid(base, length)
  x = random.randint(0, length - 2)
  shape = random.choice(SHAPES)
  for k, (r, dx) in enumerate(shape):
    block[r][x + dx] = a1 if k == 0 else random.choice([a1, a2])
  return block


def _sample_lane():
  n = random.randint(2, 5)
  lane = []
  for _ in range(n):
    length = random.choice(LENGTHS)
    if random.random() < 0.3:
      lane.append(_patterned(length))
    else:
      lane.append(_solid(random.choice(SOLID), length))
  return lane


def _extent(lane):
  return 1 + sum(len(b[0]) for b in lane) + 2 * (len(lane) - 1)


def generate(vertical=None, one_top=None, two_left=None, lanes=None,
             width=None, num_lanes=None):
  """Build one input/output pair.

  Args:
    vertical: True if the input's 1-line is a column. The input is then the
      normalised frame turned 90 degrees clockwise.
    one_top: in the normalised frame, True if the 1-line is the top row,
      False if it is the bottom row.
    two_left: in the normalised frame, True if the 2-line is the left column,
      False if it is the right column.
    lanes: ordered lanes, nearest the 1-line first. Each lists 2-row blocks in reading
      order (nearest the 2-line first), as displayed in the normalised frame.
    width: width of the normalised frame (border column included).
    num_lanes: exact random lane count 2..5; default samples 2..4.
  """
  if width is not None and (not isinstance(width, int) or not 11 <= width <= 30):
    raise ValueError("Normalised width must be in 11..30")
  if num_lanes is not None and (not isinstance(num_lanes, int) or not 2 <= num_lanes <= 5):
    raise ValueError("num_lanes must be in 2..5")
  if vertical is None:
    vertical = random.random() < 0.5
  if one_top is None:
    one_top = random.random() < 0.5
  if two_left is None:
    two_left = random.random() < 0.5
  if lanes is None:
    chosen = None
    count = num_lanes if num_lanes is not None else random.choice([2, 2, 3, 4])
    for _ in range(2000):
      cand = [_sample_lane() for _ in range(count)]
      lens = [len(b[0]) for lane in cand for b in lane]
      if len(set(lens)) < 2:
        continue
      if sum(len(l) for l in cand) > 15:
        continue
      if max(_extent(l) for l in cand) > (width - 2 if width is not None else 27):
        continue
      chosen = cand
      break
    if chosen is None:
      raise ValueError("Could not construct lanes within requested width/output size")
    lanes = chosen
  if not 2 <= len(lanes) <= 5 or any(not lane for lane in lanes):
    raise ValueError("Provide 2..5 nonempty lanes")
  if num_lanes is not None and len(lanes) != num_lanes:
    raise ValueError("Explicit lanes do not match num_lanes")
  if sum(len(lane) for lane in lanes) > 15:
    raise ValueError("Stacked output exceeds 30 rows")
  for lane in lanes:
    for block in lane:
      if (len(block) != 2 or not block[0] or len(block[0]) % 2 or
          len(block[0]) != len(block[1]) or
          any(v not in ACCENT for row in block for v in row)):
        raise ValueError("Blocks must have two equal even-length rows without background or zero")
  ext = max(_extent(lane) for lane in lanes)
  if width is None:
    width = 1 + ext + random.randint(1, max(1, min(3, 29 - ext)))
  if ext + 2 > width or width > 30:
    raise ValueError("Lanes and background margin do not fit requested width")
  height = 3 * len(lanes) + 2
  frame = common.grid(width, height, BG)
  one_row = 0 if one_top else height - 1
  two_col = 0 if two_left else width - 1
  for c in range(width):
    frame[one_row][c] = 1
  for r in range(height):
    frame[r][two_col] = 2
  frame[one_row][two_col] = 0
  starts = [2 + 3 * i if one_top else height - 4 - 3 * i for i in range(len(lanes))]
  lane_rows = [(r, r + 1) for r in starts]
  for lane, rows in zip(lanes, lane_rows):
    offset = 1
    for block in lane:
      length = len(block[0])
      if two_left:
        start = 1 + offset
      else:
        start = width - 2 - offset - length + 1
      for k in range(2):
        for dx in range(length):
          frame[rows[k]][start + dx] = block[k][dx]
      offset += length + 2
  # Output: blocks stacked in reading order, centred.
  wout = max(len(b[0]) for lane in lanes for b in lane)
  output = []
  for lane in lanes:
    for block in lane:
      length = len(block[0])
      off = (wout - length) // 2
      for k in range(2):
        row = [BG] * wout
        row[off:off + length] = block[k]
        output.append(row)
  if vertical:
    grid = [[frame[height - 1 - j][i] for j in range(height)] for i in range(width)]
  else:
    grid = [row[:] for row in frame]
  return {"input": grid, "output": output}


def _s(color, length):
  return _solid(color, length)


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(vertical=True, one_top=False, two_left=True, width=20,
               lanes=[[_s(4, 2), [[6, 6, 6, 6, 6, 6], [1, 2, 6, 6, 6, 6]],
                       [[6, 6, 3, 3], [3, 3, 3, 3]]],
                      [_s(9, 2), _s(4, 2),
                       [[7, 4, 7, 7, 7, 7], [4, 7, 7, 7, 7, 7]]]]),
      generate(vertical=False, one_top=True, two_left=True, width=11,
               lanes=[[_s(3, 2), _s(4, 4)], [_s(6, 2), _s(9, 2)]]),
      generate(vertical=False, one_top=True, two_left=True, width=28,
               lanes=[[_s(3, 8), _s(9, 2), _s(7, 4), _s(4, 4)],
                      [_s(9, 2), _s(6, 8), _s(4, 2)]]),
      generate(vertical=False, one_top=True, two_left=False, width=23,
               lanes=[[_s(4, 4), _s(3, 2), _s(7, 2), _s(3, 6)],
                      [_s(9, 2), _s(6, 6), _s(3, 4)]]),
  ]
  test = [
      generate(vertical=True, one_top=True, two_left=True, width=28,
               lanes=[[_s(4, 2), [[3, 3, 3, 3], [6, 6, 3, 3]], _s(6, 6),
                       _s(9, 2), _s(4, 2)],
                      [[[3, 3, 3, 3, 3, 7, 3, 3], [3, 3, 3, 3, 3, 3, 7, 7]],
                       _s(5, 2), [[7, 9, 7, 7], [7, 7, 9, 7]], _s(9, 4)]]),
  ]
  return {"train": train, "test": test}
