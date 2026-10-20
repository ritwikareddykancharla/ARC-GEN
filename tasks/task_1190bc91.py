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


def generate(size=None, prow=None, spacing=None, tcolor=None, lcolor=None,
             flip=None, xpose=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    size: The size of the grid.
    prow: The row of the pillar.
    spacing: The spacing between the corner and the pairs.
    tcolor: The color of the top pair.
    lcolor: The color of the left pair.
    flip: Whether to flip the grid.
    xpose: Whether to transpose the grid.
    colors: A list of colors to use.
  """

  random_mode = size is None

  def draw():
    grid, output = common.grids(size, size)
    def put(r, c, color):
      if not color: return True
      if common.get_pixel(output, r, c) not in [-1, 0, color]:
        return False
      common.draw(output, r, c, color)
      return True
    # Floodfill the output.
    offset = 0
    for c in range(size - len(colors) - 1, -1, -1):
      for r in range(prow - offset, prow + offset + 1):
        if not put(r, c, lcolor): return None, None
      offset += 1
    offset = 0
    for r in range(prow - 2, -1, -1):
      lb_col = size - len(colors) - 1 - offset + 1
      ub_col = size - len(colors) - 1 + offset + 3
      for c in range(lb_col, ub_col):
        if not put(r, c, tcolor): return None, None
      offset += 1
    # Draw the lines.
    for i, color in enumerate(colors):
      pcol = size - 1 - i
      grid[prow][pcol] = color
      offset = 0
      for c in range(size - 1 - i, size):
        if not put(prow - offset, c, color): return None, None
        if not put(prow + offset, c, color): return None, None
        offset += 1
      if i + 2 < len(colors): continue
      offset = 0
      for c in range(pcol, -1, -1):
        if not put(prow - offset, c, color): return None, None
        if not put(prow + offset, c, color): return None, None
        offset += 1
    # Draw the little pairs.  Each visible pair must sit inside the region
    # that its colour floods (tcolor: the triangle above the head; lcolor:
    # the wedge beyond the head).  Otherwise the label would colour a region
    # the pair does not touch and leave the pair's own region background.
    if random_mode:
      for r, c in [(0, spacing), (0, spacing + 1)]:
        if common.get_pixel(output, r, c) != tcolor: return None, None
      if lcolor:
        for r, c in [(spacing, 0), (spacing + 1, 0)]:
          if common.get_pixel(output, r, c) != lcolor: return None, None
    grid[0][spacing] = grid[0][spacing + 1] = tcolor
    grid[spacing][0] = grid[spacing + 1][0] = lcolor
    if not put(0, spacing, tcolor) or not put(0, spacing + 1, tcolor):
      return None, None
    if not put(spacing, 0, lcolor) or not put(spacing + 1, 0, lcolor):
      return None, None
    if flip: grid, output = common.flip(grid), common.flip(output)
    if xpose: grid, output = common.transpose(grid), common.transpose(output)
    return grid, output

  if size is None:
    size = common.randint(4, 10)
    flip, xpose = common.randint(0, 1), common.randint(0, 1)
    num_colors = common.randint(3, size - 1)
    num_colors = min(num_colors, 7)
    # Whether a scene can be drawn depends only on its geometry and on whether
    # lcolor is 0, because all colours are distinct.  So enumerate the
    # geometry with placeholder colours instead of using unbounded rejection.
    # Weights 1:9 match the original chance that lcolor == 0, so the result
    # equals the original rejection sampler conditioned on validity.
    tcolor, colors = 2, list(range(3, 3 + num_colors))
    options = []
    for lzero in [True, False]:
      lcolor = 0 if lzero else 1
      for prow in range(2, size - 1):
        for spacing in range(1, size - 1):
          trial, _ = draw()
          if trial: options.append((1 if lzero else 9, lzero, prow, spacing))
    pick = common.randint(1, sum(option[0] for option in options))
    for weight, lzero, prow, spacing in options:
      pick -= weight
      if pick <= 0: break
    palette = common.shuffle(list(range(1, 10)))
    lcolor = 0 if lzero else palette.pop()
    tcolor = palette.pop()
    colors = palette[:num_colors]

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=10, prow=3, spacing=4, tcolor=6, lcolor=4, flip=False,
               xpose=False, colors=[8, 1, 5, 9, 7, 3, 2]),
      generate(size=10, prow=5, spacing=4, tcolor=9, lcolor=7, flip=True,
               xpose=True, colors=[1, 2, 3, 6, 4, 8]),
      generate(size=4, prow=2, spacing=1, tcolor=8, lcolor=0, flip=False,
               xpose=True, colors=[4, 2, 3]),
  ]
  test = [
      generate(size=8, prow=5, spacing=3, tcolor=7, lcolor=9, flip=True,
               xpose=True, colors=[3, 6, 8, 4, 2]),
  ]
  return {"train": train, "test": test}
