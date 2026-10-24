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

TOTAL = 5            # lock + key width per row, constant in every fixture
BAND_ROWS = 3        # rows per band, constant in every fixture
MIN_BANDS, MAX_BANDS = 2, 7   # 4n+1 <= 30 rows; seven colours exclude 7 and 8
KEY_COLOURS = (1, 2, 3, 4, 5, 6, 9)


def _int(value, name, low, high):
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{name} must be an int, got {value!r}")
  if not low <= value <= high:
    raise ValueError(f"{name}={value} outside {low}..{high}")
  return value


def _colours(colors):
  colors = list(colors)
  _int(len(colors), "len(colors)", MIN_BANDS, MAX_BANDS)
  for c in colors:
    if _int(c, "colour", 0, 9) not in KEY_COLOURS:
      raise ValueError(f"key colour {c} must not be background 7, lock 8 or 0")
  if len(set(colors)) != len(colors):
    raise ValueError("key colours must be distinct")
  return colors


def _legacy_draw(lefts, rights, colors):
  """The pre-expansion explicit path, kept verbatim so its labels are unchanged.

  It accepts anything the old code drew (repeated or 0/7 key colours, any
  band count, unused trailing lengths). Only cases where the old code
  returned None grids, crashed, or left ARC bounds now raise ValueError.
  These scenes lie outside the certified random domain.
  """

  def get_values(i):
    values = []
    for j in range(len(colors)):
      lengths = []
      for k in range(3):
        lengths.append(lefts[3 * i + k] + rights[3 * j + k])
      if list(set(lengths)) == [5]: values.append(j)
    return values

  try:
    grid, output = common.grids(11, 4 * len(colors) + 1, 7)
    for i, color in enumerate(colors):
      values = get_values(i)
      if len(values) != 1:
        raise ValueError(f"band {i}: {len(values)} keys complete its lock")
      common.rect(output, 5, 3, 4 * i + 1, 0, colors[values[0]])
      for j in range(3):
        for k in range(rights[3 * i + j]):
          grid[4 * i + j + 1][10 - k] = color
        for k in range(lefts[3 * i + j]):
          output[4 * i + j + 1][k] = grid[4 * i + j + 1][k] = 8
  except (IndexError, TypeError) as exc:
    raise ValueError(f"explicit lengths/colours not drawable: {exc!r}") from exc
  for g in (grid, output):
    if not 1 <= len(g) <= 30 or any(
        isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9
        for row in g for v in row):
      raise ValueError("explicit scene is not a valid ARC grid")
  return grid, output


def generate(lefts=None, rights=None, colors=None, num_bands=None):
  """Returns input and output grids according to the given parameters.

  Args:
    lefts: Lengths of the left (lock, colour 8) lines, three per band.
    rights: Lengths of the right (key) lines, three per band.
    colors: The colors of the groups (the key colour of each band).
    num_bands: Number of bands, 2..7 (random when omitted).

  Complete explicit lefts, rights and colors use the legacy drawing path
  unchanged (num_bands, if also given, must equal len(colors)). Partial
  lengths raise ValueError rather than being ignored. Explicit colors (or
  num_bands) with omitted lengths fix the band count of a random scene.
  """

  if num_bands is not None:
    _int(num_bands, "num_bands", MIN_BANDS, MAX_BANDS)
  if lefts is not None or rights is not None:
    if lefts is None or rights is None or colors is None:
      raise ValueError("explicit lefts need explicit rights and colors")
    if num_bands is not None and num_bands != len(colors):
      raise ValueError("num_bands disagrees with len(colors)")
    grid, output = _legacy_draw(lefts, rights, colors)
    return {"input": grid, "output": output}

  if colors is not None:
    colors = _colours(colors)
    if num_bands is not None and num_bands != len(colors):
      raise ValueError("num_bands disagrees with len(colors)")
  else:
    count = num_bands if num_bands is not None else common.randint(
        MIN_BANDS, MAX_BANDS)
    colors = common.random_colors(count, exclude=[7, 8])
  # A key completes a lock iff its row lengths are the lock's complements,
  # and keys are a permutation of the complements. So the matching is
  # unique (a bijection) iff the lock profiles are distinct: sample n
  # distinct profiles of (1..4)^3 directly instead of rejecting.
  profiles = common.sample(range(4 ** BAND_ROWS), len(colors))
  locks = [[1 + (p // 4 ** k) % 4 for k in range(BAND_ROWS)] for p in profiles]
  keys = common.shuffle([[TOTAL - v for v in lock] for lock in locks])
  grid, output = _legacy_draw(common.flatten(locks), common.flatten(keys), colors)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(lefts=[2, 2, 2, 1, 3, 1, 3, 1, 3],
               rights=[4, 2, 4, 2, 4, 2, 3, 3, 3], colors=[9, 3, 1]),
      generate(lefts=[3, 1, 2, 3, 2, 1], rights=[2, 4, 3, 2, 3, 4],
               colors=[9, 2]),
      generate(lefts=[1, 1, 2, 2, 3, 2, 1, 4, 3, 1, 3, 4],
               rights=[4, 4, 3, 4, 2, 1, 3, 2, 3, 4, 1, 2],
               colors=[2, 4, 3, 6]),
  ]
  test = [
      generate(lefts=[2, 4, 1, 2, 3, 1, 3, 4, 1, 3, 4, 2],
               rights=[2, 1, 4, 2, 1, 3, 3, 1, 4, 3, 2, 4],
               colors=[1, 2, 9, 5]),
  ]
  return {"train": train, "test": test}
