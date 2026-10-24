# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator."""

import random

import common


MAX_ATTEMPTS = 200


def _dimension(value, name):
  """Returns a validated canvas dimension."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not 1 <= value <= 30:
    raise ValueError(f"{name} must be in 1..30, got {value}")
  return value


def window_capacity(width, height):
  """Most disjoint 3x3 seed windows that fit inside the canvas."""
  return (width // 3) * (height // 3)


def default_max_boxes(width, height):
  """The legacy maximum of 8 windows on 15x15, scaled with area.

  Capped at half the packing capacity so random placement stays easy.
  """
  return max(2, min(window_capacity(width, height) // 2,
                    round(8 * width * height / 225)))


def _scattered_windows(width, height, count):
  """Random sequential placement of disjoint 3x3 windows (top-left corners).

  Each window takes a uniformly random free corner; windows may touch, as in
  the legacy common.overlaps check. Returns None if the free corners run out.
  """
  free = {(r, c) for r in range(height - 2) for c in range(width - 2)}
  corners = []
  for _ in range(count):
    if not free: return None
    r, c = random.choice(sorted(free))
    corners.append((r, c))
    free -= {(r + dr, c + dc) for dr in range(-2, 3) for dc in range(-2, 3)}
  return corners


def _lattice_windows(width, height, count):
  """Random disjoint windows on a jittered lattice; succeeds for any count up
  to window_capacity. Used for dense requests (above half the capacity)."""
  def starts(length):
    bands = length // 3
    gaps = [0] * (bands + 1)
    for _ in range(length - 3 * bands):
      gaps[random.randrange(bands + 1)] += 1
    out, at = [], 0
    for b in range(bands):
      at += gaps[b]
      out.append(at)
      at += 3
    return out
  slots = [(r, c) for r in starts(height) for c in starts(width)]
  return random.sample(slots, count)


def generate(colors=None, width=None, height=None, num_boxes=None,
             density=None, num_confetti_colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A list of colors to use, row by row (width * height values). 1
      marks a seed; seeds must be interior with disjoint 3x3 windows, and
      every window must end up with at least 3 blue cells.
    width: Canvas width, 1..30. None samples 6..30, or uses the legacy 15
      when colors is given.
    height: Canvas height, 1..30. None samples 6..30, or uses the legacy 15
      when colors is given.
    num_boxes: Number of seeds for sampled scenes, 1..window_capacity. None
      samples 2..default_max_boxes (the legacy 2..8 at 15x15).
    density: Confetti probability per cell for sampled scenes, 0 < d < 1.
      None samples 0.3..0.5 once per call (legacy 0.5).
    num_confetti_colors: Number of distinct non-background, non-seed colours
      actually used. None samples 1..8, bounded by the number of available
      cells after retaining each seed and at least two background cells in
      its window. Explicit requests keep the requested count or fail.

  Sampled scenes redraw layout and confetti at most MAX_ATTEMPTS times.
  Windows are placed by random sequential placement, or on a randomly
  jittered lattice when num_boxes exceeds half of window_capacity.
  """

  def draw(cells):
    grid, output = common.grids(width, height)
    # First, draw blue squares.
    for i, color in enumerate(cells):
      if color == 1: common.rect(output, 3, 3, i // width - 1, i % width - 1, 1)
    # Second, draw confetti.
    for i, color in enumerate(cells):
      if color: output[i // width][i % width] = grid[i // width][i % width] = color
    return grid, output

  def seeds(cells):
    return [(i // width, i % width) for i, color in enumerate(cells) if color == 1]

  def visible(output, cells):
    """At least three blue cells showing in every seed window."""
    return all(sum(output[r + dr][c + dc] == 1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)) >= 3
               for r, c in seeds(cells))

  explicit = colors is not None
  if explicit and (num_boxes is not None or density is not None or num_confetti_colors is not None):
    raise ValueError("num_boxes, density and num_confetti_colors apply only to sampled scenes")
  if width is None:
    width = 15 if explicit else common.randint(6, 30)
  if height is None:
    height = 15 if explicit else common.randint(6, 30)
  width, height = _dimension(width, "width"), _dimension(height, "height")

  if explicit:
    if len(colors) != width * height:
      raise ValueError(f"colors has {len(colors)} values; width * height is {width * height}")
    if any(isinstance(c, bool) or not isinstance(c, int) or not 0 <= c <= 9 for c in colors):
      raise ValueError("colors must be ints in 0..9")
    points = seeds(colors)
    if any(not (1 <= r <= height - 2 and 1 <= c <= width - 2) for r, c in points):
      raise ValueError("seeds on the canvas edge are outside the demonstrated domain")
    if any(abs(r1 - r2) < 3 and abs(c1 - c2) < 3
           for i, (r1, c1) in enumerate(points) for r2, c2 in points[:i]):
      raise ValueError("overlapping seed windows are outside the demonstrated domain")
    grid, output = draw(colors)
    if not visible(output, colors):
      raise ValueError("a seed window shows fewer than 3 blue cells")
    return {"input": grid, "output": output}

  capacity = window_capacity(width, height)
  if not capacity:
    raise ValueError(f"a {width}x{height} canvas cannot hold a 3x3 seed window")
  if num_boxes is None:
    num_boxes = common.randint(min(2, capacity),
                               min(capacity, default_max_boxes(width, height)))
  if isinstance(num_boxes, bool) or not isinstance(num_boxes, int):
    raise ValueError(f"num_boxes must be an int, got {num_boxes!r}")
  if not 1 <= num_boxes <= capacity:
    raise ValueError(f"num_boxes must be in 1..{capacity} on {width}x{height}, got {num_boxes}")
  colour_capacity = min(8, width * height - 3 * num_boxes)
  if num_confetti_colors is None:
    num_confetti_colors = common.randint(1, colour_capacity)
  if type(num_confetti_colors) is not int or not 1 <= num_confetti_colors <= colour_capacity:
    raise ValueError(f"num_confetti_colors must be in 1..{colour_capacity} on this canvas")
  subset = common.sample(list(range(2, 10)), num_confetti_colors)
  if density is None:
    density = random.uniform(0.3, 0.5)
  if isinstance(density, bool) or not isinstance(density, (int, float)) or not 0 < density < 1:
    raise ValueError(f"density must be a number strictly between 0 and 1, got {density!r}")
  dense = num_boxes > capacity // 2
  for _ in range(MAX_ATTEMPTS):
    # Windows fully inside the canvas keep every seed interior.
    corners = (_lattice_windows if dense else _scattered_windows)(width, height, num_boxes)
    if corners is None: continue
    cells = [common.choice(subset) if random.random() < density else 0
             for _ in range(width * height)]
    for brow, bcol in corners:
      cells[(brow + 1) * width + bcol + 1] = 1
    # Require the requested distinct palette, including the seven noise
    # colours present in canonical examples but unreachable by six old draws.
    if set(cells) - {0, 1} != set(subset):
      continue
    grid, output = draw(cells)
    if visible(output, cells):
      return {"input": grid, "output": output}
  raise RuntimeError(f"No {width}x{height} scene with {num_boxes} visible seed windows "
                     f"in {MAX_ATTEMPTS} attempts")


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[0, 0, 6, 2, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 4,
                       0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 6, 0, 4, 0, 0,
                       6, 3, 0, 1, 0, 4, 0, 0, 0, 0, 0, 6, 0, 0, 0,
                       0, 0, 4, 0, 6, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0,
                       6, 0, 3, 0, 0, 0, 0, 0, 0, 3, 2, 2, 0, 0, 4,
                       4, 2, 0, 2, 0, 2, 0, 0, 0, 0, 6, 0, 0, 6, 0,
                       0, 0, 0, 0, 2, 6, 0, 6, 0, 0, 4, 0, 0, 0, 0,
                       0, 6, 0, 0, 0, 0, 4, 0, 0, 0, 4, 6, 0, 0, 0,
                       0, 0, 0, 6, 0, 6, 0, 0, 3, 3, 4, 0, 6, 6, 0,
                       4, 6, 0, 3, 1, 3, 0, 0, 4, 0, 0, 2, 6, 0, 0,
                       0, 0, 3, 2, 0, 4, 0, 6, 0, 0, 4, 3, 6, 0, 0,
                       0, 4, 0, 0, 0, 0, 0, 2, 0, 0, 0, 4, 0, 0, 0,
                       0, 0, 0, 1, 0, 0, 0, 3, 0, 3, 0, 0, 2, 2, 0,
                       6, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 4, 3,
                       0, 0, 0, 0, 0, 3, 4, 0, 0, 2, 0, 0, 0, 0, 0]),
      generate(colors=[3, 0, 0, 0, 0, 0, 0, 9, 2, 3, 0, 2, 3, 3, 0,
                       2, 2, 2, 3, 0, 0, 3, 5, 7, 0, 0, 0, 2, 7, 0,
                       0, 3, 2, 2, 0, 0, 0, 7, 0, 5, 0, 0, 0, 5, 0,
                       0, 0, 0, 0, 2, 0, 0, 0, 0, 9, 0, 0, 2, 9, 2,
                       8, 0, 0, 3, 0, 0, 1, 2, 8, 2, 0, 0, 0, 0, 0,
                       3, 0, 0, 3, 2, 0, 0, 0, 7, 0, 2, 0, 3, 0, 0,
                       0, 0, 3, 0, 0, 0, 3, 0, 0, 5, 6, 0, 2, 0, 0,
                       0, 1, 0, 2, 3, 6, 0, 0, 2, 3, 0, 2, 0, 6, 0,
                       0, 2, 8, 0, 3, 0, 0, 0, 6, 0, 7, 0, 0, 3, 0,
                       0, 2, 3, 0, 8, 0, 0, 3, 0, 1, 0, 0, 6, 0, 0,
                       7, 0, 3, 0, 0, 2, 0, 0, 0, 0, 0, 0, 6, 7, 0,
                       0, 0, 2, 0, 5, 2, 0, 0, 0, 7, 0, 0, 0, 0, 0,
                       0, 9, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 3, 0, 0,
                       0, 0, 2, 0, 2, 3, 3, 0, 0, 0, 1, 0, 0, 6, 2,
                       0, 2, 9, 0, 0, 5, 2, 3, 0, 0, 0, 0, 2, 0, 0]),
      generate(colors=[3, 9, 0, 0, 0, 0, 0, 0, 0, 8, 3, 9, 3, 0, 8,
                       0, 0, 0, 4, 0, 4, 0, 0, 3, 0, 2, 7, 7, 0, 2,
                       0, 3, 3, 0, 9, 0, 9, 0, 0, 0, 0, 2, 0, 0, 0,
                       0, 0, 0, 0, 9, 0, 4, 0, 3, 0, 3, 3, 0, 1, 0,
                       0, 1, 0, 0, 8, 8, 0, 3, 0, 2, 9, 3, 0, 0, 0,
                       0, 9, 0, 8, 0, 0, 0, 0, 3, 0, 0, 7, 0, 0, 3,
                       0, 0, 7, 2, 2, 4, 7, 0, 9, 0, 0, 0, 0, 0, 8,
                       0, 4, 0, 0, 7, 0, 0, 0, 8, 0, 3, 3, 2, 7, 0,
                       0, 3, 3, 0, 2, 0, 1, 0, 2, 3, 3, 0, 0, 0, 4,
                       0, 0, 0, 3, 0, 8, 0, 0, 0, 7, 0, 3, 0, 1, 0,
                       0, 8, 0, 0, 3, 0, 9, 9, 0, 0, 7, 3, 9, 0, 0,
                       4, 4, 3, 0, 3, 0, 7, 8, 0, 4, 0, 7, 3, 0, 9,
                       7, 0, 1, 3, 3, 0, 7, 0, 1, 7, 0, 0, 4, 0, 9,
                       3, 0, 0, 0, 7, 8, 8, 0, 0, 8, 0, 9, 0, 0, 0,
                       0, 0, 7, 0, 0, 9, 8, 0, 0, 4, 8, 3, 0, 0, 0]),
  ]
  test = [
      generate(colors=[0, 0, 0, 7, 0, 0, 6, 0, 7, 0, 0, 0, 0, 0, 3,
                       2, 0, 4, 0, 3, 7, 0, 0, 7, 0, 7, 0, 0, 0, 8,
                       0, 0, 0, 7, 8, 0, 6, 2, 7, 0, 1, 0, 2, 7, 2,
                       0, 1, 0, 0, 2, 0, 0, 2, 6, 0, 0, 0, 0, 7, 8,
                       6, 0, 0, 6, 0, 1, 0, 0, 0, 2, 0, 0, 8, 6, 4,
                       0, 0, 4, 6, 6, 0, 0, 4, 8, 0, 0, 8, 0, 8, 7,
                       8, 7, 6, 0, 0, 0, 0, 7, 7, 4, 4, 8, 0, 0, 7,
                       3, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 7, 0, 8, 0,
                       0, 0, 8, 6, 8, 6, 7, 6, 1, 6, 6, 0, 4, 0, 7,
                       0, 8, 7, 0, 7, 8, 0, 7, 0, 8, 0, 0, 8, 0, 4,
                       4, 4, 0, 0, 0, 3, 0, 0, 2, 0, 0, 3, 8, 4, 8,
                       0, 0, 8, 0, 1, 0, 8, 3, 7, 6, 7, 8, 0, 8, 7,
                       0, 0, 0, 0, 8, 0, 0, 6, 0, 3, 0, 0, 3, 0, 0,
                       0, 6, 0, 0, 0, 0, 6, 3, 1, 0, 3, 0, 0, 1, 3,
                       4, 6, 0, 0, 0, 0, 8, 0, 0, 0, 2, 2, 0, 0, 6]),
  ]
  return {"train": train, "test": test}
