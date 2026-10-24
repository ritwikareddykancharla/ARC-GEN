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
LEGACY_SIZE = 4            # explicit colours with an omitted dimension
MAX_ATTEMPTS = 200


def _int(value, name):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int")
  return value


def generate(colors=None, height=None, width=None, color=None):
  """Returns input and output grids according to the given parameters.

  Args:
    colors: A row-major list of the input pixels (0..9), labelled with the
      legacy construction. Random inputs are non-empty one-ink masks. Explicit
      empty or several-ink inputs are still accepted for legacy compatibility,
      but they are outside the certified domain: with several inks, block j is
      colour j painted on the mask, not a copy of the input.
    height: Input height, 2..5. Sampled when omitted and colours are random;
      4 (legacy) when colours are explicit.
    width: Input width, 2..5, with the same defaults as height.
    color: Sampling only: the ink colour (1..9); sampled when omitted.
  """
  for name, value in (("height", height), ("width", width)):
    if value is not None and not MIN_SIZE <= _int(value, name) <= MAX_SIZE:
      raise ValueError(f"{name} must be in {MIN_SIZE}..{MAX_SIZE}")
  if colors is not None:
    if color is not None:
      raise ValueError("color is a sampling argument; omit it with explicit colors")
    height = LEGACY_SIZE if height is None else height
    width = LEGACY_SIZE if width is None else width
    colors = list(colors)
    if len(colors) != height * width:
      raise ValueError("colors must have height * width entries")
    for value in colors:
      if not 0 <= _int(value, "color") <= 9:
        raise ValueError("colors must be in 0..9")
  else:
    height = common.randint(MIN_SIZE, MAX_SIZE) if height is None else height
    width = common.randint(MIN_SIZE, MAX_SIZE) if width is None else width
    if color is None:
      color = common.randint(1, 9)
    elif not 1 <= _int(color, "color") <= 9:
      raise ValueError("color must be in 1..9")
    for _ in range(MAX_ATTEMPTS):
      colors = [color if common.randint(0, 1) else 0 for _ in range(height * width)]
      if any(colors): break
    else:
      raise RuntimeError("attempt budget exhausted before a non-empty mask")

  grid, output = common.grid(width, height), common.grid(width * width, height * height)
  for i, value in enumerate(colors):
    grid[i // width][i % width] = value
    if not value: continue
    for j, value2 in enumerate(colors):
      output[height * (j // width) + i // width][width * (j % width) + i % width] = value2
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[3, 3, 0, 3, 3, 0, 0, 3, 0, 0, 0, 3, 3, 3, 0, 3]),
      generate(colors=[0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
      generate(colors=[0, 0, 0, 0, 4, 4, 4, 4, 0, 4, 4, 0, 4, 4, 0, 0]),
      generate(colors=[1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1]),
      generate(colors=[2, 0, 0, 2, 2, 2, 2, 2, 2, 0, 0, 2, 0, 2, 0, 2]),
  ]
  test = [
      generate(colors=[0, 2, 0, 2, 2, 2, 0, 2, 2, 2, 0, 0, 0, 0, 0, 2]),
  ]
  return {"train": train, "test": test}
