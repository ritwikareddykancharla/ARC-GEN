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

# The output is (H*H) x (W*W), so each input axis is limited to 2..5 (25 <= 30).
MIN_SIZE, MAX_SIZE = 2, 5
LEGACY_SIZE = 3            # explicit colours with an omitted dimension
MIN_COLORS, MAX_COLORS = 3, 5
MAX_ATTEMPTS = 200


def _int(value, name):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int")
  return value


def _modal(colors):
  """The unique most frequent colour; None when tied or only one colour."""
  counts = sorted(((colors.count(c), c) for c in set(colors)), reverse=True)
  if len(counts) < 2 or counts[0][0] == counts[1][0]: return None
  return counts[0][1]


def generate(colors=None, height=None, width=None, num_colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A row-major list of the input colours (0..9). At least two colours
      must be present and the most frequent one must be unique (the legacy
      generator returned None grids for ties and failed on one colour). Random
      inputs never contain 0, the output fill.
    height: Input height, 2..5. Sampled when omitted and colours are random;
      3 (legacy) when colours are explicit.
    width: Input width, 2..5, with the same defaults as height.
    num_colors: Sampling only: how many distinct colours (3..5) the input
      uses. A unique maximum needs height * width >= num_colors + 1.
  """
  for name, value in (("height", height), ("width", width)):
    if value is not None and not MIN_SIZE <= _int(value, name) <= MAX_SIZE:
      raise ValueError(f"{name} must be in {MIN_SIZE}..{MAX_SIZE}")
  if colors is not None:
    if num_colors is not None:
      raise ValueError("num_colors is a sampling argument; omit it with explicit colors")
    height = LEGACY_SIZE if height is None else height
    width = LEGACY_SIZE if width is None else width
    colors = list(colors)
    if len(colors) != height * width:
      raise ValueError("colors must have height * width entries")
    for color in colors:
      if not 0 <= _int(color, "color") <= 9:
        raise ValueError("colors must be in 0..9")
    if _modal(colors) is None:
      raise ValueError("needs two or more colours with a unique most frequent one")
  else:
    if num_colors is not None:
      if not MIN_COLORS <= _int(num_colors, "num_colors") <= MAX_COLORS:
        raise ValueError(f"num_colors must be in {MIN_COLORS}..{MAX_COLORS}")
      # Sample omitted dimensions only among canvases that can hold the request.
      sizes = range(MIN_SIZE, MAX_SIZE + 1)
      shapes = [(h, w) for h in ([height] if height is not None else sizes)
                for w in ([width] if width is not None else sizes)
                if h * w >= num_colors + 1]
      if not shapes:
        raise ValueError("infeasible: a unique most frequent colour among "
                         f"{num_colors} used colours needs at least {num_colors + 1} cells")
      if height is None or width is None:
        height, width = common.choice(shapes)
    height = common.randint(MIN_SIZE, MAX_SIZE) if height is None else height
    width = common.randint(MIN_SIZE, MAX_SIZE) if width is None else width
    area = height * width
    if num_colors is None:
      num_colors = common.randint(MIN_COLORS, min(MAX_COLORS, area - 1))
    subset = common.random_colors(num_colors)
    for _ in range(MAX_ATTEMPTS):
      colors = common.choices(subset, area)
      if len(set(colors)) == num_colors and _modal(colors) is not None: break
    else:
      raise RuntimeError("attempt budget exhausted before a unique modal colour")

  modal = _modal(colors)
  grid, output = common.grid(width, height), common.grid(width * width, height * height)
  for row in range(height):
    for col in range(width):
      grid[row][col] = colors[row * width + col]
      if grid[row][col] != modal: continue
      for r in range(height):
        for c in range(width):
          output[row * height + r][col * width + c] = colors[r * width + c]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[4, 5, 4, 2, 2, 5, 5, 5, 4]),
      generate(colors=[7, 7, 1, 4, 7, 1, 3, 3, 7]),
      generate(colors=[1, 2, 3, 9, 9, 1, 2, 9, 4]),
      generate(colors=[8, 8, 1, 8, 6, 1, 4, 9, 6]),
  ]
  test = [
      generate(colors=[9, 6, 7, 8, 7, 7, 2, 8, 7]),
  ]
  return {"train": train, "test": test}
