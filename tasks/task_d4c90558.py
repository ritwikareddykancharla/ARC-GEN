"""Generator for ARC task d4c90558 (frame grey-count bars).

Rule: the input holds several rectangular frames, each drawn in its own
colour (never 0 or 5) with borders that may be thicker on some sides.
Scattered grey (5) cells sit inside each frame.  For every frame colour the
number of grey cells inside its bounding box is counted.  The output has one
row per frame, sorted by count (smallest first), and is as wide as the
largest count; row i holds its frame's colour in the first `count` cells and
background 0 elsewhere.

Scope: 2..5 frames on a 12..30 canvas with per-side border thickness 1..3,
distinct frame colours, distinct grey counts (1..12), frames separated by at
least one background cell. Colour 0 strictly outnumbers each other colour;
scenes with a dominant thick frame are outside the sampled domain because the
archived checker infers background by frequency.  Background is always 0 and the marker colour is
always 5 (both intrinsic to the task).

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common


def _draw_frame(grid, color, r0, c0, r1, c1, thick):
  """Draws a rectangular frame with per-side thickness (top, bottom, left, right)."""
  t, b, l, r = thick
  for y in range(r0, r1 + 1):
    for x in range(c0, c1 + 1):
      if y < r0 + t or y > r1 - b or x < c0 + l or x > c1 - r:
        grid[y][x] = color


def _overlaps(box, boxes, gap=1):
  """True if box touches/overlaps any placed box (with a 1-cell gap)."""
  r0, c0, r1, c1 = box
  for (s0, d0, s1, d1) in boxes:
    if r0 <= s1 + gap and s0 <= r1 + gap and c0 <= d1 + gap and d0 <= c1 + gap:
      return True
  return False


def _random_frames(width, height):
  """Places 2..5 non-touching frames and fills them with distinct grey counts."""
  colors = [1, 2, 3, 4, 6, 7, 8, 9]
  for _ in range(40):
    target = random.randint(2, 5)
    boxes, specs = [], []
    for _ in range(300):
      if len(specs) == target:
        break
      t, b, l, r = [random.choice([1, 1, 1, 2, 2, 3]) for _ in range(4)]
      ih = random.randint(3, 8)
      iw = random.randint(3, 9)
      h = ih + t + b
      w = iw + l + r
      if h > height or w > width:
        continue
      r0 = random.randint(0, height - h)
      c0 = random.randint(0, width - w)
      box = (r0, c0, r0 + h - 1, c0 + w - 1)
      if _overlaps(box, boxes):
        continue
      boxes.append(box)
      specs.append((box, (t, b, l, r), ih * iw))
    if len(specs) < 2:
      continue
    # Assign distinct counts, smallest interiors first so a count always fits.
    specs.sort(key=lambda s: s[2])
    used = set()
    cols = random.sample(colors, len(specs))
    frames = []
    for ((r0, c0, r1, c1), thick, cells), color in zip(specs, cols):
      cap = min(cells, 12)
      options = [k for k in range(1, cap + 1) if k not in used]
      count = random.choice(options)
      used.add(count)
      t, b, l, r = thick
      interior = [(y, x) for y in range(r0 + t, r1 - b + 1)
                  for x in range(c0 + l, c1 - r + 1)]
      greys = random.sample(interior, count)
      frames.append((color, r0, c0, r1, c1, thick, greys))
    # The archived solver infers background by colour frequency. Keep that
    # inference unambiguous; thick frames can otherwise dominate a small grid.
    frame_pixels = []
    grey_pixels = 0
    for _, r0, c0, r1, c1, (t, b, l, r), greys in frames:
      h, w = r1 - r0 + 1, c1 - c0 + 1
      frame_pixels.append(h * w - (h - t - b) * (w - l - r))
      grey_pixels += len(greys)
    background_pixels = width * height - sum(frame_pixels) - grey_pixels
    if background_pixels <= max(frame_pixels + [grey_pixels]):
      continue
    random.shuffle(frames)
    return frames
  return None


def generate(width=None, height=None, frames=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the input grid
    height: the height of the input grid
    frames: list of (color, row0, col0, row1, col1, (top, bottom, left,
      right thickness), [(row, col) absolute grey cells]) describing each
      frame; counts of grey cells must be distinct across frames
  """
  requested_width, requested_height = width, height
  if frames is None:
    for _ in range(40):
      width = requested_width if requested_width is not None else random.randint(12, 30)
      height = requested_height if requested_height is not None else random.randint(12, 30)
      if not (1 <= width <= 30 and 1 <= height <= 30):
        raise ValueError("grid dimensions must lie in 1..30")
      if width < 5 or height < 5:
        raise ValueError("canvas cannot fit the minimum frame")
      frames = _random_frames(width, height)
      if frames is not None:
        break
    else:
      raise ValueError("could not fit separated frames in requested dimensions")
  elif width is None or height is None:
    raise ValueError("explicit frames require width and height")

  grid = common.grid(width, height)
  for color, r0, c0, r1, c1, thick, greys in frames:
    _draw_frame(grid, color, r0, c0, r1, c1, thick)
    for (y, x) in greys:
      grid[y][x] = 5

  info = sorted((len(greys), color) for color, _, _, _, _, _, greys in frames)
  out_w = max(n for n, _ in info)
  output = common.grid(out_w, len(info))
  for i, (n, color) in enumerate(info):
    for x in range(n):
      output[i][x] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator with the canonical train/test examples."""
  train = [
      generate(width=20, height=20, frames=[
          (6, 1, 5, 8, 16, (1, 2, 1, 2), [(3, 11), (4, 8), (4, 10), (6, 13)]),
          (2, 12, 1, 19, 9, (1, 1, 2, 1), [(14, 5), (16, 3), (16, 5)]),
      ]),
      generate(width=25, height=25, frames=[
          (8, 0, 1, 9, 11, (1, 2, 1, 3), [(3, 6), (4, 4), (5, 3), (6, 7)]),
          (1, 3, 16, 7, 21, (1, 1, 1, 1), [(4, 18), (6, 19)]),
          (7, 11, 4, 22, 22, (1, 1, 2, 2),
           [(14, 8), (14, 14), (14, 19), (16, 10), (16, 16), (18, 8),
            (19, 12), (19, 16)]),
      ]),
      generate(width=20, height=20, frames=[
          (3, 0, 2, 6, 10, (1, 1, 1, 1), [(2, 5), (3, 3), (3, 5), (4, 8)]),
          (8, 1, 13, 6, 17, (1, 1, 1, 1), [(3, 14), (4, 15)]),
          (4, 9, 11, 17, 19, (2, 1, 1, 1),
           [(12, 13), (12, 15), (13, 16), (13, 18), (15, 14), (15, 16)]),
          (2, 10, 1, 18, 8, (1, 3, 1, 1),
           [(11, 6), (12, 3), (13, 3), (13, 5), (14, 7)]),
      ]),
  ]
  test = [
      generate(width=21, height=21, frames=[
          (6, 2, 0, 8, 11, (2, 2, 2, 4), [(4, 6), (5, 2), (5, 4), (6, 6)]),
          (8, 6, 13, 16, 20, (1, 2, 1, 1),
           [(8, 17), (8, 18), (9, 15), (10, 15), (11, 17), (12, 19),
            (13, 15), (13, 17)]),
          (2, 12, 2, 20, 10, (2, 2, 2, 2), [(15, 5), (15, 8), (17, 7)]),
      ]),
  ]
  return {"train": train, "test": test}
