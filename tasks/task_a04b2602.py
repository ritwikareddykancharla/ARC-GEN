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

import common

# Native domain (sampled when `colors` is None):
# * canvas height and width independently in MIN_DIM..MAX_DIM;
# * 2..3 green rectangles, each side 4..(canvas side - 6);
# * rectangles separated by at least SPACING background cells along some axis.
#   The legacy spacing of 2 excluded canonical train[0], whose rectangles are
#   one row apart. Gap 0 would merge rectangles, so 1 is the minimum;
# * every cell turns red with probability 1/k, k drawn once per scene from
#   RED_PERIODS (the legacy constant was k = 20; the canonical red densities
#   0.055..0.067 are all consistent with it). The rule is per red cell, so
#   the noise rate is incidental to it.
# A scene is accepted only if the reds with >= 2 orthogonal green neighbours
# are exactly the reds inside rectangles (and there is at least one). This is
# what makes the neighbour rule and the inside-rectangle rule agree. With
# spacing 1 it also rejects reds in a one-cell gap that touch two rectangles.
# Retries are bounded by ATTEMPTS; there is no fallback scene.
MIN_DIM, MAX_DIM = 10, 30
SPACING = 1
RED_PERIODS = (12, 30)
ATTEMPTS = 10000


def _dimension(value, name):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int")
  if not MIN_DIM <= value <= MAX_DIM:
    raise ValueError(f"{name} must be in {MIN_DIM}..{MAX_DIM}")
  return value


def generate(width=None, height=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: Width of the grid.
    height: Height of the grid.
    colors: Colors of the grid. If given, width and height are required and
      the scene is drawn exactly as given. If omitted, a random scene is
      sampled, at the given width and height when both are supplied.
  """

  def draw():
    grid, output = common.grids(width, height)
    for i, color in enumerate(colors):
      output[i // width][i % width] = grid[i // width][i % width] = color
    outlined = []
    for it in range(2):
      for row in range(height):
        for col in range(width):
          if grid[row][col] != 2: continue
          greens = 0
          if common.get_pixel(grid, row - 1, col) == 3: greens += 1
          if common.get_pixel(grid, row + 1, col) == 3: greens += 1
          if common.get_pixel(grid, row, col - 1) == 3: greens += 1
          if common.get_pixel(grid, row, col + 1) == 3: greens += 1
          if greens < 2: continue
          if it == 0:  # In the first iteration, we draw the blue squares.
            for r in [-1, 0, 1]:
              for c in [-1, 0, 1]:
                common.draw(output, row + r, col + c, 1)
          if it == 1:  # In the second iteration, we redraw the red pixels.
            output[row][col] = 2
            outlined.append((row, col))
    return grid, output, outlined

  if colors is not None:
    if width is None or height is None:
      raise ValueError("explicit colors need both width and height")
    if (isinstance(width, bool) or isinstance(height, bool)
        or not isinstance(width, int) or not isinstance(height, int)
        or not 1 <= width <= 30 or not 1 <= height <= 30):
      raise ValueError("explicit width and height must be ints in 1..30")
    if len(colors) != width * height:
      raise ValueError("explicit colors must have width * height entries")
  else:
    if (width is None) != (height is None):
      raise ValueError("give both width and height, or neither")
    if width is None:
      width, height = common.randint(MIN_DIM, MAX_DIM), common.randint(MIN_DIM, MAX_DIM)
    else:
      width, height = _dimension(width, "width"), _dimension(height, "height")
    num_boxes = common.randint(2, 3)
    period = common.randint(*RED_PERIODS)
    for _ in range(ATTEMPTS):
      wides = [common.randint(4, width - 6) for _ in range(num_boxes)]
      talls = [common.randint(4, height - 6) for _ in range(num_boxes)]
      brows = [common.randint(0, height - t) for t in talls]
      bcols = [common.randint(0, width - w) for w in wides]
      if common.overlaps(brows, bcols, wides, talls, SPACING): continue
      grid = common.grid(width, height)
      for wide, tall, brow, bcol in zip(wides, talls, brows, bcols):
        common.rect(grid, wide, tall, brow, bcol, 3)
      expected_outlined = []
      for r in range(height):
        for c in range(width):
          if common.randint(0, period - 1): continue
          grid[r][c] = 2
          for wide, tall, brow, bcol in zip(wides, talls, brows, bcols):
            if r >= brow and r < brow + tall and c >= bcol and c < bcol + wide:
              expected_outlined.append((r, c))
      colors = common.flatten(grid)
      _, _, outlined = draw()
      if outlined and outlined == expected_outlined: break
    else:
      raise RuntimeError(f"no scene within {ATTEMPTS} attempts at {height}x{width}")

  grid, output, _ = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=20, height=20,
               colors=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 3, 3, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 2, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 2, 3, 3, 3, 3, 3, 3, 2, 3, 0, 0, 0, 2, 3, 3, 2, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 2, 3, 3, 3, 0, 2, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 2,
                       0, 0, 3, 2, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 3, 3, 3, 3, 3, 2, 3, 3, 3, 0, 0, 2, 0, 2, 3, 3, 3, 3,
                       0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 0, 2, 0, 0, 3, 3, 3, 3, 3,
                       0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3,
                       0, 2, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 0, 2, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 0, 0, 0, 0, 0, 0, 0]),
      generate(width=20, height=20,
               colors=[0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0, 0, 0, 0,
                       2, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 2, 0, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 2, 0, 0, 0, 0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 2, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 2, 0, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 2, 3, 3, 3, 3, 3, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 2, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 2, 0, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0]),
      generate(width=17, height=10,
               colors=[0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0,
                       0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 3, 3, 3, 2, 0, 0, 0, 0, 3, 3, 3, 3, 3, 2, 0, 0,
                       0, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 3, 3, 3, 3, 0, 0, 0, 0, 3, 2, 2, 3, 3, 3, 0, 0,
                       0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0]),
  ]
  test = [
      generate(width=27, height=16,
               colors=[0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 0, 2,
                       0, 0, 0, 3, 3, 3, 3, 2, 3, 3, 3, 0, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 3, 3, 3, 2, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0, 0,
                       0, 0, 0, 3, 3, 2, 2, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0,
                       0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 2, 3, 2, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0,
                       0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 3, 2, 2, 3, 3, 3, 3, 3, 0, 0, 0, 2, 0]),
  ]
  return {"train": train, "test": test}
