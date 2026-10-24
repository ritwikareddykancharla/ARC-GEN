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


def generate(size=None, colors=None, height=None, width=None,
             num_colors=None, style=None):
  """Colour-matched self-tiling on independently sized rectangular inputs.

  Block (r,c) keeps exactly the input cells matching input[r][c]. The output
  is H**2 by W**2, so both input axes are limited to 2..5. The old explicit
  size/colors interface and all canonical labels are preserved. Random inputs
  vary aspect ratio, palette size and line/block/pixel structure.
  """
  if size is not None and (height is not None or width is not None):
    raise ValueError("Use size or height/width, not both")
  if size is not None:
    height = width = size
  elif colors is not None and (height is None or width is None):
    raise ValueError("Explicit colors require size or both height and width")
  else:
    height = common.randint(2, 5) if height is None else height
    width = common.randint(2, 5) if width is None else width
  for value in (height, width):
    if type(value) is not int or not 2 <= value <= 5:
      raise ValueError("Each input dimension must be an integer in 2..5")
  if colors is not None:
    if num_colors is not None or style is not None:
      raise ValueError("num_colors/style apply only to random generation")
    if len(colors) != height * width or any(
        type(c) is not int or not 0 <= c <= 9 for c in colors):
      raise ValueError("Expected H*W colour integers in 0..9")
    colors = list(colors)
  else:
    n = common.randint(2, min(5, height * width)) if num_colors is None else num_colors
    if type(n) is not int or not 2 <= n <= min(9, height * width):
      raise ValueError("Requested palette does not fit the input")
    style = common.choice(("lines", "blocks", "pixels")) if style is None else style
    if style not in ("lines", "blocks", "pixels"):
      raise ValueError("Unknown pattern style")
    hues = common.random_colors(n)
    # Bounded rejection keeps the requested palette intact; never substitutes
    # a fixed example or silently relaxes the requested number of colours.
    for attempt in range(5000):
      if style == "pixels":
        colors = [common.choice(hues) for _ in range(height * width)]
      else:
        colors = [0] * (height * width)
        for stroke in range(4 * height * width):
          hue = common.choice(hues)
          if style == "blocks":
            top, bottom = sorted((common.randint(0, height-1), common.randint(0, height-1)))
            left, right = sorted((common.randint(0, width-1), common.randint(0, width-1)))
          elif common.randint(0, 1):
            top, bottom = sorted((common.randint(0, height-1), common.randint(0, height-1)))
            left = right = common.randint(0, width-1)
          else:
            left, right = sorted((common.randint(0, width-1), common.randint(0, width-1)))
            top = bottom = common.randint(0, height-1)
          for r in range(top, bottom+1):
            for c in range(left, right+1):
              colors[r * width + c] = hue
          if set(colors) == set(hues):
            break
      if set(colors) == set(hues):
        break
    else:
      raise RuntimeError("Palette/structure rejection budget exhausted")
  grid = [colors[r * width:(r+1) * width] for r in range(height)]
  output = common.grid(width * width, height * height)
  for r in range(height):
    for c in range(width):
      for y in range(height):
        for x in range(width):
          if grid[y][x] == grid[r][c]:
            output[r * height + y][c * width + x] = grid[r][c]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=3, colors=[6, 6, 6, 6, 8, 8, 8, 8, 6]),
      generate(size=3, colors=[2, 4, 4, 3, 2, 4, 3, 3, 2]),
      generate(size=5, colors=[1, 1, 1, 1, 1, 1, 8, 8, 8, 1, 1, 1, 1, 8, 1, 1, 8, 1, 8, 1, 1, 8, 1, 1, 1]),
  ]
  test = [
      generate(size=5, colors=[1, 1, 1, 1, 4, 1, 4, 4, 4, 4, 1, 4, 1, 1, 1, 2, 2, 2, 2, 1, 4, 1, 1, 2, 1]),
      generate(size=4, colors=[3, 3, 3, 3, 4, 3, 3, 6, 4, 4, 6, 6, 4, 3, 3, 6]),
  ]
  return {"train": train, "test": test}
