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

"""ARC task 36a08778: magenta streams flow down and wrap around red bars.

Rule: the background is orange (7). Short magenta (6) marks hang from the top
edge. Each mark is the source of a stream that falls straight down through the
background. When the cell beneath a stream is red (2), the stream wraps the
horizontal run of red cells in that row that contains the hit cell. Call the
ends of that run c0 and c1. The stream paints the row just above the run from
c0-1 to c1+1, clipped to the grid. It then splits into two streams that fall
from both ends of that painted row. A stream that never meets red runs to the
bottom edge. Streams paint background cells only. Start cells that have
already been processed are skipped.

Scope: the grid size is sampled from 6..30 wide and 8..30 tall. Between 1 and
4 sources are sampled, each 1-2 cells long. The obstacles are horizontal red
bars, some of which touch the grid edges so that branches are clipped. There
are also optional vertical red bars, which a stream wraps as runs one cell
wide. Separated mode keeps bars apart. Clustered mode attaches vertical legs to
horizontal bars, producing touching L-shaped obstacles. Source cells remain
separate. Wraps use the horizontal red run at the collision row in both modes. Fixtures are rebuilt from explicit
latent segment lists. Those lists may contain touching or L-shaped
combinations, such as test 2 and pair 3.
"""

import random

import common

BG = 7
WALL = 2
FLOW = 6


def _simulate(width, height, sources, segments):
  """Builds the input and output grids from the latent scene.

  Returns (input, output, wraps), where wraps is the number of wrap events.
  """
  g = common.grid(width, height, BG)
  for (r0, c0, r1, c1) in segments:
    for r in range(r0, r1 + 1):
      for c in range(c0, c1 + 1):
        g[r][c] = WALL
  starts = []
  for (col, length) in sources:
    for r in range(length):
      g[r][col] = FLOW
    starts.append((length - 1, col))
  inp = [row[:] for row in g]
  out = [row[:] for row in g]
  queue = list(starts)
  head = 0
  seen = set()
  wraps = 0
  while head < len(queue):
    y, x = queue[head]
    head += 1
    if (y, x) in seen or not (0 <= x < width) or not (0 <= y < height):
      continue
    seen.add((y, x))
    if out[y][x] == BG:
      out[y][x] = FLOW
    while y + 1 < height and out[y + 1][x] != WALL:
      y += 1
      if out[y][x] == BG:
        out[y][x] = FLOW
    if y + 1 >= height:
      continue
    r = y + 1
    c0 = x
    while c0 - 1 >= 0 and out[r][c0 - 1] == WALL:
      c0 -= 1
    c1 = x
    while c1 + 1 < width and out[r][c1 + 1] == WALL:
      c1 += 1
    for c in range(max(0, c0 - 1), min(width - 1, c1 + 1) + 1):
      if out[r - 1][c] == BG:
        out[r - 1][c] = FLOW
    wraps += 1
    for c in (c0 - 1, c1 + 1):
      if 0 <= c < width:
        queue.append((r - 1, c))
  return inp, out, wraps


def _free(cells, used, width, height):
  """True if every cell and all of its 8-neighbours are absent from used."""
  for (r, c) in cells:
    if not (0 <= r < height and 0 <= c < width):
      return False
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        if (r + dr, c + dc) in used:
          return False
  return True


def _random_scene(width, height, sources, obstacle_mode):
  """Samples sources and 8-separated red segments."""
  if width is None:
    width = random.randint(6, 30)
  if height is None:
    height = random.randint(8, 30)
  if sources is None:
    count = random.randint(1, max(1, min(4, width // 6)))
    cols = []
    for _ in range(50):
      if len(cols) >= count:
        break
      c = random.randint(0, width - 1)
      if all(abs(c - o) >= 3 for o in cols):
        cols.append(c)
    cols.sort()
    sources = [(c, random.randint(1, 2)) for c in cols]
  used = set()
  for (col, length) in sources:
    for r in range(length):
      used.add((r, col))
  segments = []
  target = random.randint(max(2, height // 4), max(3, height // 2 + 1))
  max_len = max(2, min(width - 1, (width * 2) // 3))
  for _ in range(target * 40):
    if len(segments) >= target:
      break
    r = random.randint(1, height - 1)
    length = random.randint(2, max_len)
    mode = random.random()
    if mode < 0.15:
      c0 = 0
    elif mode < 0.3:
      c0 = width - length
    elif mode < 0.65 and sources:
      # Bias the bar to cross a source column so streams interact.
      col = random.choice(sources)[0] + random.randint(-3, 3)
      c0 = col - random.randint(0, length - 1)
    else:
      c0 = random.randint(0, width - length)
    c0 = max(0, min(width - length, c0))
    cells = [(r, c) for c in range(c0, c0 + length)]
    if _free(cells, used, width, height):
      used.update(cells)
      segments.append((r, c0, r, c0 + length - 1))
  if random.random() < 0.35:
    for _ in range(random.randint(1, 2) * 30):
      length = random.randint(2, min(5, height - 3))
      r0 = random.randint(2, height - length)
      c = random.randint(0, width - 1)
      cells = [(r, c) for r in range(r0, r0 + length)]
      if _free(cells, used, width, height):
        used.update(cells)
        segments.append((r0, c, r0 + length - 1, c))
        if random.random() < 0.5:
          break
  if obstacle_mode == "clustered":
    added = 0
    candidates=[seg for seg in segments if seg[0]==seg[2] and seg[3]>seg[1]]
    random.shuffle(candidates)
    for r,c0,_,c1 in candidates:
      own={(r,c) for c in range(c0,c1+1)}
      for _ in range(20):
        c=random.choice((c0,c1));direction=random.choice((-1,1));length=random.randint(2,min(6,height-1))
        end=r+direction*(length-1)
        if not 1 <= end < height:continue
        extension={(y,c) for y in range(min(r,end),max(r,end)+1)}
        if not _free(extension,used-own,width,height):continue
        segments.append((min(r,end),c,max(r,end),c));used.update(extension);added+=1;break
      if added >= 3:break
    if not added:return width,height,sources,[]
  return width, height, sources, segments


def generate(width=None, height=None, sources=None, segments=None,
             obstacle_mode=None):
  """Returns an input/output pair for the stream-wrapping task.

  Args:
    width: grid width (number of columns), 1..30.
    height: grid height (number of rows), 1..30.
    sources: list of (column, length) magenta marks that touch the top edge.
    segments: list of (r0, c0, r1, c1) inclusive red rectangles. These are
      horizontal bars (r0 == r1) or vertical bars (c0 == c1). If omitted, a
      fresh random scene is sampled.
    obstacle_mode: "separated" or "clustered"; clustered adds touching L-shapes.
  """
  for dimension in (width,height):
    if dimension is not None and (not isinstance(dimension,int) or not 1 <= dimension <= 30):
      raise ValueError("Dimensions must be in 1..30")
  if obstacle_mode not in (None,"separated","clustered"):
    raise ValueError("Unknown obstacle_mode")
  if sources is not None:
    if width is None or height is None or not sources:
      raise ValueError("Explicit sources require width, height and nonempty sources")
    if any(not (0 <= col < width and 1 <= length <= height) for col,length in sources) or len({col for col,length in sources})!=len(sources):
      raise ValueError("Invalid or repeated source columns")
  if segments is not None:
    if sources is None or obstacle_mode is not None:
      raise ValueError("Explicit segments require sources and no sampling mode")
    for r0,c0,r1,c1 in segments:
      if not (0 <= r0 <= r1 < height and 0 <= c0 <= c1 < width) or (r0!=r1 and c0!=c1):
        raise ValueError("Segments must be in-bounds horizontal or vertical bars")
      if any(c0 <= col <= c1 and r0 < length for col,length in sources):
        raise ValueError("Obstacles must not overwrite sources")
    inp, out, _ = _simulate(width, height, sources, segments)
    return {"input": inp, "output": out}
  if (width is not None and width < 6) or (height is not None and height < 8):
    raise ValueError("Random scenes require width >= 6 and height >= 8")
  mode=obstacle_mode if obstacle_mode is not None else random.choice(("separated","clustered"))
  for _ in range(200):
    w, h, src, segs = _random_scene(width, height, sources, mode)
    if not src or not segs:
      continue
    inp, out, wraps = _simulate(w, h, src, segs)
    if wraps >= 2 and inp != out:
      return {"input": inp, "output": out}
  raise RuntimeError("Could not construct requested stream scene with two wrap events")


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(14, 14, [(4, 2), (12, 2)],
               [(3, 3, 3, 5), (3, 11, 3, 13), (5, 0, 5, 4), (8, 7, 8, 13),
                (10, 2, 10, 6), (12, 5, 12, 10)]),
      generate(13, 16, [(4, 2), (11, 2)],
               [(4, 9, 4, 12), (9, 1, 9, 4), (13, 4, 13, 7)]),
      generate(9, 8, [(2, 2)],
               [(0, 7, 0, 8), (1, 7, 1, 7), (2, 1, 2, 3), (5, 3, 5, 6),
                (7, 0, 7, 5)]),
      generate(5, 14, [(3, 2)],
               [(1, 0, 1, 2), (1, 4, 1, 4), (3, 2, 3, 2), (3, 4, 3, 4),
                (5, 2, 5, 4), (10, 0, 10, 2), (10, 4, 10, 4),
                (12, 2, 12, 4)]),
      generate(20, 8, [(0, 2)],
               [(2, 0, 2, 17), (4, 6, 4, 9), (4, 16, 4, 19), (5, 2, 5, 5),
                (6, 13, 6, 17)]),
      generate(16, 15, [(6, 2)],
               [(1, 0, 1, 5), (1, 9, 1, 15), (4, 4, 4, 12), (7, 0, 7, 9),
                (10, 7, 10, 14), (13, 0, 13, 1), (13, 4, 13, 13)]),
  ]
  test = [
      generate(16, 16, [(2, 2), (12, 2)],
               [(4, 0, 4, 1), (4, 3, 4, 4), (4, 11, 4, 15), (6, 8, 6, 12),
                (8, 6, 8, 9), (11, 4, 11, 7), (14, 6, 14, 9)]),
      generate(30, 30, [(4, 2), (22, 2)],
               [(2, 2, 2, 5), (2, 17, 2, 25), (7, 9, 7, 12), (9, 23, 9, 26),
                (10, 11, 12, 11), (12, 2, 16, 2), (17, 2, 17, 7),
                (13, 19, 17, 19), (22, 10, 22, 19), (27, 14, 27, 17),
                (27, 25, 27, 28)]),
  ]
  return {"train": train, "test": test}
