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


def generate(colors=None, height=None, width=None, marker_row=None,
             num_colors=None, style=None):
  """Remove the left control strip and roll the picture by its marker index.

  ``width`` is picture width; the input is one column wider. Explicit legacy
  ``colors`` calls retain the original 6x7 default and exact labels. Default
  scenes broaden dimensions and content; there is no exact-colour-count filter.
  """
  explicit = colors is not None
  if height is None and width is None:
    if explicit or common.randint(0, 3) == 0:
      height, width = 6, 6
    else:
      height, width = common.randint(2, 30), common.randint(1, 29)
  else:
    height = 6 if height is None else height
    width = 6 if width is None else width
  if (type(height) is not int or type(width) is not int
      or not 2 <= height <= 30 or not 1 <= width <= 29):
    raise ValueError("height must be 2..30 and picture width 1..29")
  if explicit:
    if len(colors) != height * (width + 1):
      raise ValueError("Explicit colours must fill the entire input")
    if any(type(c) is not int or not 0 <= c <= 9 for c in colors):
      raise ValueError("Invalid ARC colour")
    grid = [list(colors[r * (width + 1):(r + 1) * (width + 1)])
            for r in range(height)]
    hits = [r for r in range(height) if grid[r][0] == 2]
    if len(hits) != 1:
      raise ValueError("Control strip must contain exactly one marker")
    offset = hits[0]
    if marker_row is not None and marker_row != offset:
      raise ValueError("marker_row conflicts with explicit control strip")
    picture = [row[1:] for row in grid]
  else:
    offset = common.randint(0, height - 1) if marker_row is None else marker_row
    if type(offset) is not int or not 0 <= offset < height:
      raise ValueError("marker_row outside control strip")
    available = [0, 1, 3, 4, 5, 7, 8, 9]
    count = common.randint(1, min(8, height * width)) if num_colors is None else num_colors
    if type(count) is not int or not 1 <= count <= min(8, height * width):
      raise ValueError("Impossible number of picture colours")
    palette = []
    for _ in range(count):
      colour = common.choice(available)
      available.remove(colour)
      palette.append(colour)
    mode = common.choice(['bars', 'blocks', 'pixels']) if style is None else style
    if mode not in ('bars', 'blocks', 'pixels'):
      raise ValueError("Unknown picture style")
    picture = [[palette[0] for _ in range(width)] for _ in range(height)]
    if mode == 'pixels':
      picture = [[common.choice(palette) for _ in range(width)] for _ in range(height)]
    else:
      for _ in range(common.randint(1, max(10, height * width // 2))):
        r, c = common.randint(0, height - 1), common.randint(0, width - 1)
        if mode == 'bars':
          vertical = common.randint(0, 1)
          hh = common.randint(1, height - r) if vertical else 1
          ww = 1 if vertical else common.randint(1, width - c)
        else:
          hh, ww = common.randint(1, height - r), common.randint(1, width - c)
        colour = common.choice(palette)
        for y in range(r, r + hh):
          for x in range(c, c + ww):
            picture[y][x] = colour
    # Distinct anchor cells ensure requested colours are actually used. This
    # does not constrain occupancy, connectivity or require a modal background.
    positions = list(range(height * width))
    for colour in palette:
      pos = common.choice(positions)
      positions.remove(pos)
      picture[pos // width][pos % width] = colour
    grid = [[2 if r == offset else 6] + picture[r] for r in range(height)]
  output = [list(picture[(r - offset) % height]) for r in range(height)]
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(colors=[2, 1, 1, 1, 1, 9, 8,
                       6, 4, 3, 9, 9, 9, 8,
                       6, 4, 3, 9, 3, 8, 8,
                       6, 4, 3, 3, 3, 8, 8,
                       6, 4, 8, 8, 5, 5, 5,
                       6, 4, 5, 5, 5, 3, 3]),
      generate(colors=[6, 8, 8, 8, 4, 4, 4,
                       6, 9, 9, 8, 3, 4, 4,
                       2, 9, 9, 8, 3, 3, 3,
                       6, 9, 1, 1, 1, 5, 3,
                       6, 4, 4, 1, 5, 5, 5,
                       6, 4, 4, 1, 5, 5, 5]),
      generate(colors=[6, 8, 8, 8, 4, 4, 4,
                       6, 8, 9, 8, 4, 9, 1,
                       6, 8, 9, 9, 9, 9, 1,
                       2, 5, 5, 3, 3, 3, 1,
                       6, 5, 5, 3, 4, 3, 1,
                       6, 5, 5, 3, 4, 4, 4]),
  ]
  test = [
      generate(colors=[6, 5, 8, 8, 8, 9, 9,
                       2, 5, 4, 4, 4, 4, 9,
                       6, 5, 3, 1, 1, 4, 9,
                       6, 5, 3, 1, 1, 4, 8,
                       6, 1, 3, 3, 3, 8, 8,
                       6, 1, 1, 3, 8, 8, 9]),
  ]
  return {"train": train, "test": test}
