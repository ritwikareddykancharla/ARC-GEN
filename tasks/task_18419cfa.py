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

"""ARC-GEN style generator for task 18419cfa.

Rule: the grid holds one or more light-blue (8) hollow rectangular frames.
Each frame has a pair of matching 3-cell bumps centred on two opposite walls.
The bumps sit either on the left and right walls or on the top and bottom
walls, and each bump opens a one-cell gap in its wall. Inside every frame a
red (2) motif fills one half of the interior. The motif touches the centre
line and is centred on the bump line. The output reflects the motif across
the interior centre, along the axis the bumps point along, and keeps both
copies. Frames, bumps and background are unchanged.

Scope: 1-3 frames per grid. Each frame is independently oriented. Its
interior extent along the mirror axis is even or odd, with a wall gap of 1-2.
Its perpendicular extent is odd and centred on the bumps. Motifs are random
8-connected red shapes. They are 2-3 cells deep and 3 or 5 cells wide, and
symmetric about the bump line, as in all examples. The motif may lie in
either half. Grid sizes are 12-30 per side. Colours are fixed at 0, 8 and 2.
"""

import random

import common


def _connected8(cells):
  cells = set(cells)
  if not cells:
    return False
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    y, x = stack.pop()
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        n = (y + dy, x + dx)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _random_motif(d, s):
  """Return cells (a, p): a along mirror axis (0..d-1), p perpendicular."""
  half = (s + 1) // 2
  for _ in range(300):
    cells = set()
    for a in range(d):
      for p in range(half):
        if random.random() < 0.5:
          cells.add((a, p))
          cells.add((a, s - 1 - p))
    if not cells or len(cells) == d * s:
      continue
    if any(all((a, p) not in cells for p in range(s)) for a in range(d)):
      continue
    if any(all((a, p) not in cells for a in range(d)) for p in range(s)):
      continue
    if not _connected8(cells):
      continue
    return cells
  cells = {(0, p) for p in range(s)}
  for a in range(d):
    cells.add((a, 0))
    cells.add((a, s - 1))
  return cells


def _bbox(f):
  top, left, ih, iw = f["top"], f["left"], f["ih"], f["iw"]
  if f["orient"] == "h":
    return top, left - 1, top + ih + 1, left + iw + 2
  return top - 1, left, top + ih + 2, left + iw + 1


def _draw(grid, f, with_mirror):
  top, left, ih, iw = f["top"], f["left"], f["ih"], f["iw"]
  for x in range(left, left + iw + 2):
    grid[top][x] = 8
    grid[top + ih + 1][x] = 8
  for y in range(top, top + ih + 2):
    grid[y][left] = 8
    grid[y][left + iw + 1] = 8
  if f["orient"] == "h":
    c = top + 1 + ih // 2
    for y in range(c - 1, c + 2):
      grid[y][left - 1] = 8
      grid[y][left + iw + 2] = 8
    grid[c][left] = 0
    grid[c][left + iw + 1] = 0
  else:
    c = left + 1 + iw // 2
    for x in range(c - 1, c + 2):
      grid[top - 1][x] = 8
      grid[top + ih + 2][x] = 8
    grid[top][c] = 0
    grid[top + ih + 1][c] = 0
  cells = []
  for r, row in enumerate(f["motif"]):
    for k, ch in enumerate(row):
      if ch == "2":
        cells.append((top + 1 + f["dy"] + r, left + 1 + f["dx"] + k))
  for y, x in cells:
    grid[y][x] = 2
  if with_mirror:
    for y, x in cells:
      if f["orient"] == "h":
        grid[y][2 * left + iw + 1 - x] = 2
      else:
        grid[2 * top + ih + 1 - y][x] = 2


def _sample_frame_shape():
  orient = random.choice(["h", "v"])
  d = random.choice([2, 2, 3, 3])
  centre = random.choice([0, 1])
  wall_gap = random.choice([1, 1, 1, 2])
  length = 2 * (d + wall_gap) + centre
  s = random.choice([3, 3, 5])
  pg = random.choice([1, 1, 2])
  span = s + 2 * pg
  cells = _random_motif(d, s)
  far_half = random.random() < 0.5
  start = (length + 1) // 2 if far_half else length // 2 - d
  if orient == "h":
    motif = ["".join("2" if (a, p) in cells else "." for a in range(d))
             for p in range(s)]
    shape = dict(orient="h", ih=span, iw=length, dy=pg, dx=start,
                 motif=motif)
    bh, bw = span + 2, length + 4
  else:
    motif = ["".join("2" if (a, p) in cells else "." for p in range(s))
             for a in range(d)]
    shape = dict(orient="v", ih=length, iw=span, dy=start, dx=pg,
                 motif=motif)
    bh, bw = length + 4, span + 2
  return shape, bh, bw


def _place(shapes, width, height):
  boxes = []
  frames = []
  for shape, bh, bw in shapes:
    if bh > height or bw > width:
      return None
    ok = False
    for _ in range(80):
      r0 = random.randint(0, height - bh)
      c0 = random.randint(0, width - bw)
      r1, c1 = r0 + bh - 1, c0 + bw - 1
      if all(r0 > b[2] + 1 or r1 < b[0] - 1 or c0 > b[3] + 1 or
             c1 < b[1] - 1 for b in boxes):
        ok = True
        break
    if not ok:
      return None
    boxes.append((r0, c0, r1, c1))
    f = dict(shape)
    if f["orient"] == "h":
      f["top"], f["left"] = r0, c0 + 1
    else:
      f["top"], f["left"] = r0 + 1, c0
    frames.append(f)
  return frames


def generate(width=None, height=None, frames=None):
  """Build one input/output pair.

  Args:
    width: grid width (sampled 12..30 if None).
    height: grid height (sampled 12..30 if None).
    frames: optional list of frame dicts with keys orient ('h' = bumps on
      left/right walls, 'v' = bumps on top/bottom walls), top, left (corner
      of the rectangle excluding bumps), ih, iw (interior size; the dimension
      perpendicular to the bumps' axis must be odd), dy, dx (motif offset
      from interior top-left), motif (list of strings, '2' = red cell).
  """
  requested_width, requested_height = width, height
  if frames is None:
    if any(v is not None and not 12 <= v <= 30 for v in (width, height)):
      raise ValueError("grid dimensions must be 12..30")
    for _ in range(200):
      n = random.choices([1, 2, 3], weights=[3, 5, 3])[0]
      shapes = [_sample_frame_shape() for _ in range(n)]
      min_h = max(12, max(s[1] for s in shapes))
      min_w = max(12, max(s[2] for s in shapes))
      height = requested_height if requested_height is not None else random.randint(min_h, 30)
      width = requested_width if requested_width is not None else random.randint(min_w, 30)
      placed = _place(shapes, width, height)
      if placed is not None:
        frames = placed
        break
    if frames is None:
      raise RuntimeError("could not place frames in the requested canvas")
  grid_in = common.grid(width, height, 0)
  grid_out = common.grid(width, height, 0)
  for f in frames:
    _draw(grid_in, f, False)
    _draw(grid_out, f, True)
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstruct the canonical fixtures through explicit latent arguments."""
  train = [
      generate(width=17, height=18, frames=[
          dict(orient="h", top=3, left=2, ih=7, iw=6, dy=2, dx=1,
               motif=["22", "2.", "22"])]),
      generate(width=22, height=16, frames=[
          dict(orient="h", top=2, left=4, ih=5, iw=6, dy=1, dx=1,
               motif=["2.", "22", "2."]),
          dict(orient="v", top=6, left=15, ih=6, iw=5, dy=1, dx=1,
               motif=["2.2", "222"])]),
      generate(width=16, height=24, frames=[
          dict(orient="v", top=3, left=2, ih=8, iw=7, dy=1, dx=1,
               motif=["2.2.2", ".222.", "2.2.2"])]),
  ]
  test = [
      generate(width=26, height=28, frames=[
          dict(orient="h", top=3, left=3, ih=5, iw=7, dy=1, dx=1,
               motif=[".2", "22", ".2"]),
          dict(orient="v", top=2, left=17, ih=8, iw=7, dy=4, dx=1,
               motif=["..2..", ".222.", "2...2"]),
          dict(orient="v", top=15, left=6, ih=8, iw=9, dy=1, dx=2,
               motif=["2...2", ".222.", "2...2"])]),
  ]
  return {"train": train, "test": test}
