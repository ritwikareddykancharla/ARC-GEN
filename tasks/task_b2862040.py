# Copyright 2025 Google LLC
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

# Bounds on rejection loops. Exhaustion raises rather than silently reducing
# object count or returning an unchecked scene.
_MAX_SCENE_ATTEMPTS = 1000
_MAX_PLACEMENT_ATTEMPTS = 2000000
_MAX_CLOSED_ATTEMPTS = 10000


def _hole_rule_output(ingrid, bg, mark):
  """Visible rule: a non-bg 4-component that touches an enclosed bg region -> mark.

  An enclosed bg region is a 4-connected background component that never
  touches the grid border. This function depends only on the visible input.
  It does not use any generator latent.
  """
  height, width = len(ingrid), len(ingrid[0])
  seen = [[False] * width for _ in range(height)]
  hole = [[False] * width for _ in range(height)]
  steps = ((1, 0), (-1, 0), (0, 1), (0, -1))

  def flood(r0, c0, is_bg):
    stack, cells = [(r0, c0)], []
    seen[r0][c0] = True
    while stack:
      r, c = stack.pop()
      cells.append((r, c))
      for dr, dc in steps:
        nr, nc = r + dr, c + dc
        if 0 <= nr < height and 0 <= nc < width and not seen[nr][nc]:
          if (ingrid[nr][nc] == bg) == is_bg:
            seen[nr][nc] = True
            stack.append((nr, nc))
    return cells

  for r in range(height):
    for c in range(width):
      if ingrid[r][c] == bg and not seen[r][c]:
        cells = flood(r, c, True)
        if not any(y in (0, height - 1) or x in (0, width - 1) for y, x in cells):
          for y, x in cells:
            hole[y][x] = True
  output = [list(row) for row in ingrid]
  for r in range(height):
    for c in range(width):
      if ingrid[r][c] != bg and not seen[r][c]:
        cells = flood(r, c, False)
        enclosed = False
        for y, x in cells:
          for dr, dc in steps:
            ny, nx = y + dr, x + dc
            if 0 <= ny < height and 0 <= nx < width and hole[ny][nx]:
              enclosed = True
        if enclosed:
          for y, x in cells:
            output[y][x] = mark
  return output


def _sample_scene(num_boxes):
  """Sample geometry for the requested object count without reducing it."""
  # Choose some nonoverlapping box locations.
  for _ in range(_MAX_PLACEMENT_ATTEMPTS):
    width, height = common.randint(10, 16), common.randint(10, 16)
    wides = [common.randint(3, 5) for _ in range(num_boxes)]
    talls = [common.randint(3, 5) for _ in range(num_boxes)]
    brows = [common.randint(0, height - tall) for tall in talls]
    bcols = [common.randint(0, width - wide) for wide in wides]
    if not common.overlaps(brows, bcols, wides, talls, 2): break
  else:
    raise RuntimeError("box placement attempts exhausted")
  # Draw the boxes (subtracting pixels from open ones) and adding "barnacles".
  grid = common.grid(width, height, common.maroon())
  for _ in range(_MAX_CLOSED_ATTEMPTS):
    closeds = [common.randint(0, 1) for _ in range(num_boxes)]
    if len(set(closeds)) > 1: break
  else:
    raise RuntimeError("closed/open assignment attempts exhausted")
  all_barnacles = []
  barnacle_colors = {}
  for idx in range(num_boxes):
    brow, bcol, wide, tall = brows[idx], bcols[idx], wides[idx], talls[idx]
    closed = closeds[idx]
    color, perim = common.cyan() if closed else common.blue(), []
    for r in range(brow, brow + tall):
      for c in range(bcol, bcol + wide):
        h, v = r in [brow, brow + tall - 1], c in [bcol, bcol + wide - 1]
        if not h and not v: continue  # Anything inside the box.
        grid[r][c] = color  # Any part of the perimeter.
        if h != v: perim.append((r, c))  # Excludes edge pixels.
    # Draw little things around the edges.
    barnacles = []
    barnacles.append((brow - 1, bcol))
    barnacles.append((brow, bcol - 1))
    barnacles.append((brow - 1, bcol + wide - 1))
    barnacles.append((brow, bcol + wide))
    barnacles.append((brow + tall - 1, bcol + wide))
    barnacles.append((brow + tall, bcol + wide - 1))
    barnacles.append((brow + tall, bcol))
    barnacles.append((brow + tall - 1, bcol - 1))
    for barnacle in barnacles:
      if common.randint(0, 4): continue
      all_barnacles.append(barnacle)
      barnacle_colors[barnacle] = color
    if closed: continue
    pixel = common.choice(perim)
    grid[pixel[0]][pixel[1]] = common.maroon()
  all_barnacles = common.remove_neighbors(all_barnacles)
  for barnacle in all_barnacles:
    common.draw(grid, barnacle[0], barnacle[1], barnacle_colors[barnacle])
  rows, cols, colors = [], [], []
  for r in range(height):
    for c in range(width):
      if grid[r][c] == common.maroon(): continue
      rows.append(r)
      cols.append(c)
      colors.append(grid[r][c])
  return width, height, rows, cols, colors


def _render(width, height, rows, cols, colors):
  grid, output = common.grids(width, height, common.maroon())
  for r, c, color in zip(rows, cols, colors):
    grid[r][c] = color if color != common.cyan() else common.blue()
    output[r][c] = color
  return {"input": grid, "output": output}


def generate(width=None, height=None, rows=None, cols=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the grid
    height: the height of the grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    colors: a list of digits representing the colors to be used
  """
  if width is None:
    # Rejection sampling. The latent closed/open label must agree with the
    # visible hole rule for every object. Otherwise barnacles can seal an open
    # box's leak, or seal a corridor pocket between two boxes, and the latent
    # label would contradict what is visible. Such scenes are discarded and
    # resampled with the same object count.
    num_boxes = common.randint(2, 5)
    for _ in range(_MAX_SCENE_ATTEMPTS):
      width, height, rows, cols, colors = _sample_scene(num_boxes)
      pair = _render(width, height, rows, cols, colors)
      expected = _hole_rule_output(pair["input"], common.maroon(), common.cyan())
      if expected == pair["output"]:
        return pair
    raise RuntimeError("no label-consistent scene found")
  return _render(width, height, rows, cols, colors)


def validate():
  """Validates the generator."""
  train = [
      generate(width=11, height=9,
               cols=[1, 2, 3, 7, 1, 3, 7, 1, 3, 6, 7, 8, 9, 1, 2, 3, 7, 7],
               rows=[2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 6],
               colors=[8, 8, 8, 1, 8, 8, 1, 8, 8, 1, 1, 1, 1, 8, 8, 8, 1, 1]),
      generate(width=11, height=12,
               cols=[1, 2, 3, 4, 5, 8, 1, 5, 8, 10, 1, 2, 3, 4, 5, 8, 9, 10, 3,
                     2, 3, 4, 5, 6, 3, 5, 3, 4, 5, 8, 9, 10, 8, 10, 0, 1, 8, 9,
                     10],
               rows=[1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 6, 7,
                     7, 7, 7, 7, 8, 8, 9, 9, 9, 9, 9, 9, 10, 10, 11, 11, 11, 11,
                     11],
               colors=[8, 8, 8, 8, 8, 1, 8, 8, 1, 1, 8, 8, 8, 8, 8, 1, 1, 1, 8,
                       8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 1, 1, 8, 8,
                       8]),
      generate(width=13, height=12,
               cols=[5, 8, 2, 7, 8, 9, 10, 1, 2, 3, 4, 8, 1, 4, 8, 1, 2, 3, 4,
                     8, 9, 10, 4, 4, 1, 7, 8, 9, 0, 1, 2, 9, 1, 6, 8, 9, 0, 1,
                     6, 7, 8],
               rows=[0, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5,
                     5, 5, 6, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11,
                     11, 11, 11],
               colors=[1, 1, 8, 1, 1, 1, 1, 8, 8, 8, 8, 1, 8, 8, 1, 8, 8, 8, 8,
                       1, 1, 1, 8, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1]),
      generate(width=15, height=14,
               cols=[1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 2, 6, 11, 14, 2, 3, 4, 6,
                     10, 11, 12, 14, 4, 5, 6, 14, 4, 8, 9, 10, 8, 10, 11, 8, 9,
                     10, 0, 1, 2, 3, 0, 3, 7, 9, 0, 1, 2, 3, 7, 8, 9, 10, 11, 0,
                     9, 5, 4, 5, 12, 13],
               rows=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3,
                     3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 8,
                     9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 12,
                     13, 13, 13, 13],
               colors=[8, 8, 8, 8, 8, 8, 1, 1, 1, 1, 8, 8, 1, 1, 8, 8, 8, 8, 1,
                       1, 1, 1, 8, 8, 8, 1, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
                       8, 8, 8, 8, 1, 1, 8, 8, 8, 8, 1, 1, 1, 1, 1, 8, 1, 1, 1,
                       1, 1, 1]),
  ]
  test = [
      generate(width=15, height=16,
               cols=[0, 1, 11, 3, 4, 5, 6, 7, 11, 4, 7, 11, 4, 7, 11, 4, 5, 6,
                     7, 11, 14, 7, 11, 12, 13, 14, 0, 1, 2, 3, 7, 11, 14, 0, 3,
                     14, 0, 3, 13, 14, 0, 1, 3, 4, 5, 6, 7, 8, 12, 13, 3, 8, 13,
                     3, 8, 13, 3, 4, 5, 6, 7, 8, 9, 13],
               rows=[0, 0, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5,
                     5, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 9,
                     10, 10, 12, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 14, 14,
                     14, 15, 15, 15, 15, 15, 15, 15, 15],
               colors=[1, 1, 1, 8, 8, 8, 8, 8, 1, 8, 8, 1, 8, 8, 1, 8, 8, 8, 8,
                       1, 1, 8, 1, 1, 1, 1, 1, 1, 1, 1, 8, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 8, 8, 8, 8, 8, 8, 1, 1, 8, 8, 1, 8, 8, 1, 8,
                       8, 8, 8, 8, 8, 8, 1]),
  ]
  return {"train": train, "test": test}
