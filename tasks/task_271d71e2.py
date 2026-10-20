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

"""ARC task 271d71e2: boxes push their 9 walls toward a far wall.

Rule: the background is 6. Each box is a rectangle with a 0 frame and an
interior of 5s and 7s. A line of 9s (the near wall) lies flush against one
side of the box and spans exactly that side. Further along the same direction
there is a second 9 line spanning the same rows or columns (the far wall).
The box slides toward the far wall, pushing the near wall ahead of it, by
move = min(#5s in the box, gap + 1). Here gap is the number of empty lines
between the two walls. When the full move is made, the pushed wall lands on
the far wall and the two merge. Each step converts one 5 into a 7. To find
which 5s convert, rotate the interior so the motion points right. Then scan
columns from the front column backwards, each column top to bottom. The
existing 7s are always a prefix of this scan order, so the next `move` cells
of the order become 7.

Scope: 1-4 boxes on grids of 10-30 cells per side. Each box has a random
motion direction (4 options), interior size 1-12 x 1-12, wall gap 0-14 and a
prefix of already-converted 7s. Boxes may be all-7 (they do not move). Boxes
may also have fewer 5s than gap + 1 (they stop short) or more (they reach
the far wall). Each box's footprint runs from the box itself to its far
wall. Footprints are separated by at least one background cell.
"""

import random

import common

BG, WALL, FRAME, FIVE, SEVEN = 6, 9, 0, 5, 7
DIRS = {"right": (0, 1), "left": (0, -1), "up": (-1, 0), "down": (1, 0)}


def _scan_order(ih, iw, direction):
  """Interior cells in conversion order (front column first)."""
  if direction == "right":
    return [(r, c) for c in reversed(range(iw)) for r in range(ih)]
  if direction == "left":
    return [(r, c) for c in range(iw) for r in reversed(range(ih))]
  if direction == "up":
    return [(r, c) for r in range(ih) for c in range(iw)]
  return [(r, c) for r in reversed(range(ih)) for c in reversed(range(iw))]


def _line(top, left, ih, iw, direction, k):
  """Cells of the line at distance k beyond the moving side of a box."""
  bottom, right = top + ih + 1, left + iw + 1
  if direction == "right":
    return [(r, right + k) for r in range(top, bottom + 1)]
  if direction == "left":
    return [(r, left - k) for r in range(top, bottom + 1)]
  if direction == "up":
    return [(top - k, c) for c in range(left, right + 1)]
  return [(bottom + k, c) for c in range(left, right + 1)]


def _draw_box(g, top, left, ih, iw, sevens):
  for r in range(ih + 2):
    for c in range(iw + 2):
      if r in (0, ih + 1) or c in (0, iw + 1):
        v = FRAME
      else:
        v = SEVEN if (r - 1, c - 1) in sevens else FIVE
      g[top + r][left + c] = v


def _paint(g, cells, color):
  for (r, c) in cells:
    g[r][c] = color


def _footprint(box):
  """Bounding rect (y0, x0, y1, x1) covering box, path and far wall."""
  top, left, ih, iw, direction, gap, _ = box
  cells = _line(top, left, ih, iw, direction, gap + 2)
  ys = [top, top + ih + 1] + [r for r, _ in cells]
  xs = [left, left + iw + 1] + [c for _, c in cells]
  return min(ys), min(xs), max(ys), max(xs)


def _sample_box(width, height):
  for _ in range(200):
    direction = random.choice(list(DIRS))
    ih, iw = random.randint(1, 12), random.randint(1, 12)
    gap = random.randint(0, 14)
    horizontal = direction in ("left", "right")
    along = (iw if horizontal else ih) + 2 + gap + 2
    perp = (ih if horizontal else iw) + 2
    fw, fh = (along, perp) if horizontal else (perp, along)
    if fw > width or fh > height:
      continue
    n = ih * iw
    mode = random.random()
    if mode < 0.15:
      pre7 = n
    elif mode < 0.45:
      pre7 = 0
    else:
      pre7 = random.randint(0, n - 1)
    fy = random.randint(0, height - fh)
    fx = random.randint(0, width - fw)
    top, left = fy, fx
    if direction == "left":
      left = fx + gap + 2
    elif direction == "up":
      top = fy + gap + 2
    return (top, left, ih, iw, direction, gap, pre7)
  return None


def _separated(a, b):
  return (a[2] + 1 < b[0] or b[2] + 1 < a[0] or
          a[3] + 1 < b[1] or b[3] + 1 < a[1])


def _sample_scene(requested_width, requested_height, num_boxes):
  for _ in range(100):
    width = requested_width if requested_width is not None else random.randint(10, 30)
    height = requested_height if requested_height is not None else random.randint(10, 30)
    want = num_boxes if num_boxes is not None else random.choice([1, 2, 2, 3, 3, 4, 4])
    boxes, rects = [], []
    for _ in range(want * 30):
      if len(boxes) == want:
        break
      box = _sample_box(width, height)
      if box is None:
        continue
      rect = _footprint(box)
      if all(_separated(rect, o) for o in rects):
        boxes.append(box)
        rects.append(rect)
    if boxes and (num_boxes is None or len(boxes) == num_boxes) and any(b[2] * b[3] > b[6] for b in boxes):
      return width, height, boxes
  raise ValueError("Could not place requested boxes without overlapping paths")


def generate(width=None, height=None, boxes=None, num_boxes=None):
  """Build one input/output pair.

  Args:
    width: requested grid width; random construction accepts 10..30.
    height: requested grid height; random construction accepts 10..30.
    num_boxes: exact number of random boxes (1..4); default is adaptive.
    boxes: list of (top, left, ih, iw, direction, gap, pre7) tuples.
      (top, left) is the frame's top-left corner and ih x iw is the interior
      size. direction is one of right/left/up/down. gap is the number of
      empty lines between the near and far walls. pre7 is the number of
      interior cells, in scan order, that are already 7.
  """
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Grid dimensions must be integers in 1..30")
  if num_boxes is not None and (not isinstance(num_boxes, int) or not 1 <= num_boxes <= 4):
    raise ValueError("num_boxes must be in 1..4")
  if boxes is None:
    if any(d is not None and d < 10 for d in (width, height)):
      raise ValueError("Random scenes require dimensions in 10..30")
    width, height, boxes = _sample_scene(width, height, num_boxes)
  if width is None or height is None or not boxes:
    raise ValueError("Explicit boxes require width, height and a nonempty box list")
  if num_boxes is not None and len(boxes) != num_boxes:
    raise ValueError("Explicit boxes do not match num_boxes")
  for box in boxes:
    top, left, ih, iw, direction, gap, pre7 = box
    if direction not in DIRS or min(ih, iw) < 1 or gap < 0 or not 0 <= pre7 <= ih * iw:
      raise ValueError("Invalid box parameters")
    y0, x0, y1, x1 = _footprint(box)
    if not (0 <= y0 <= y1 < height and 0 <= x0 <= x1 < width):
      raise ValueError("Box or wall outside grid")
  grid_in = common.grid(width, height, BG)
  grid_out = common.grid(width, height, BG)
  for (top, left, ih, iw, direction, gap, pre7) in boxes:
    order = _scan_order(ih, iw, direction)
    n5 = ih * iw - pre7
    move = min(n5, gap + 1)
    far = _line(top, left, ih, iw, direction, gap + 2)
    # input scene
    _paint(grid_in, far, WALL)
    _paint(grid_in, _line(top, left, ih, iw, direction, 1), WALL)
    _draw_box(grid_in, top, left, ih, iw, set(order[:pre7]))
    # output scene
    dy, dx = DIRS[direction]
    nt, nl = top + dy * move, left + dx * move
    _paint(grid_out, far, WALL)
    _paint(grid_out, _line(nt, nl, ih, iw, direction, 1), WALL)
    _draw_box(grid_out, nt, nl, ih, iw, set(order[:pre7 + move]))
  return {"input": grid_in, "output": grid_out}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(8, 8, [(3, 0, 3, 2, "up", 0, 0), (4, 5, 2, 1, "up", 0, 1)]),
      generate(17, 17, [(1, 10, 1, 3, "left", 4, 0),
                        (6, 3, 2, 4, "right", 6, 0),
                        (12, 5, 2, 5, "left", 3, 3)]),
      generate(12, 12, [(2, 0, 3, 3, "right", 4, 2),
                        (8, 3, 2, 5, "left", 1, 10)]),
  ]
  test = [
      generate(26, 26, [(0, 11, 6, 3, "down", 14, 1),
                        (0, 22, 12, 2, "down", 10, 24),
                        (13, 1, 9, 5, "up", 8, 14),
                        (19, 17, 5, 1, "up", 3, 2)]),
  ]
  return {"train": train, "test": test}
