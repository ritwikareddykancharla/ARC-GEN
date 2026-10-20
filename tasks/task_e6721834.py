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


def _unique_placement(width, height, shapes, dots, max_states=100000):
  """Require one painted region across all legal marker-matching placements.

  Shapes are (width, height, [(row, col, colour), ...]). A shape may be
  omitted from the target panel, but cannot be used twice. This enumerator
  uses the visible marker constraints, not the constructor's chosen answer.
  """
  candidates = []
  for wide, tall, markers in shapes:
    first_r, first_c, first_color = markers[0]
    options = []
    for (r, c), color in dots.items():
      if color != first_color: continue
      top, left = r - first_r, c - first_c
      if top < 0 or left < 0 or top + tall > height or left + wide > width:
        continue
      marked = {(top + y, left + x): ink for y, x, ink in markers}
      if any(dots.get(p) != ink for p, ink in marked.items()): continue
      cells = frozenset((y, x) for y in range(top, top + tall)
                        for x in range(left, left + wide))
      if any(p in dots and p not in marked for p in cells): continue
      options.append((frozenset(marked), cells,
                      (top, top + tall, left, left + wide)))
    candidates.append(options)

  target, solutions, states = frozenset(dots), set(), 0

  def search(index, covered, painted, boxes):
    nonlocal states
    states += 1
    if states > max_states or len(solutions) > 1: return
    if index == len(candidates):
      if covered == target: solutions.add(painted)
      return
    search(index + 1, covered, painted, boxes)
    for marked, cells, box in candidates[index]:
      if covered & marked: continue
      if any(not (box[1] < other[0] or other[1] < box[0] or
                  box[3] < other[2] or other[3] < box[2]) for other in boxes):
        continue
      search(index + 1, covered | marked, painted | cells, boxes + [box])

  search(0, frozenset(), frozenset(), [])
  return states <= max_states and len(solutions) == 1


def generate(width=None, height=None, rows=None, cols=None, idxs=None,
             colors=None, brows=None, bcols=None, bidxs=None, bsides=None,
             wides=None, talls=None, backs=None, forecolor=None, horiz=None,
             foreside=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the (square) grid
    height: the height of the (square) grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    idxs: a list of indicies into the sprite list
    colors: a list of digit representing the color to be used
    brows: a list of vertical coordinates where boxes should be placed
    bcols: a list of horizontal coordinates where boxes should be placed
    bidxs: a list of box indices into the sprite list
    bsides: a list of sides (either 0 or 1)
    wides: a list of widths of boxes
    talls: a list of heights of boxes
    backs: a list of background colors
    forecolor: a foreground color
    horiz: whether the two grids are horitonally positioned
    foreside: which side has the foreground colors
  """
  if width is None:
    # Choose grid dimensions, colors, # of boxes, and foreground side / horiz.
    height = common.randint(10, 15)
    width = height + common.randint(-2, 2)
    backs = common.sample(range(10), 2)
    forecolor = common.random_color(exclude=backs)
    num_boxes = 2 if height < 12 else 3
    foreside, horiz = common.randint(0, 1), common.randint(0, 1)
    # Two horizontal panels share one ARC grid; vertical panels may retain
    # the wider native widths because their total width is not doubled.
    if horiz: width = min(width, 15)
    # Choose box sizes and positions.
    while True:
      wides = [common.randint(2, 7) for _ in range(num_boxes)]
      talls = [common.randint(2, 7) for _ in range(num_boxes)]
      brows, bcols, bidxs, bsides = [], [], [], []
      for side in range(2):
        for idx in range(num_boxes):
          if side != foreside and idx and not common.randint(0, 2): continue
          brows.append(common.randint(0, height - talls[idx]))
          bcols.append(common.randint(0, width - wides[idx]))
          bidxs.append(idx)
          bsides.append(side)
      overlaps = False
      for j in range(len(bidxs)):
        for i in range(j):
          if bsides[i] != bsides[j]: continue
          if brows[i] + talls[bidxs[i]] < brows[j]: continue
          if brows[j] + talls[bidxs[j]] < brows[i]: continue
          if bcols[i] + wides[bidxs[i]] < bcols[j]: continue
          if bcols[j] + wides[bidxs[j]] < bcols[i]: continue
          overlaps = True
      if not overlaps: break
    # Repeated marker colours are allowed, but the visible markers must
    # determine one target painting rather than a hidden random assignment.
    for _ in range(128):
      rows, cols, idxs, colors, shapes = [], [], [], [], []
      for idx in range(num_boxes):
        wide, tall = wides[idx], talls[idx]
        pixels = common.sample(common.all_pixels(wide, tall), idx + 1)
        row_list, col_list = zip(*pixels)
        color = common.random_color(exclude=backs + [forecolor])
        rows.extend(row_list)
        cols.extend(col_list)
        idxs.extend([idx for _ in pixels])
        colors.extend([color for _ in pixels])
        shapes.append((wide, tall, [(r, c, color) for r, c in pixels]))
      dots = {}
      for brow, bcol, bidx, bside in zip(brows, bcols, bidxs, bsides):
        if bside == foreside: continue
        for row, col, color in shapes[bidx][2]:
          dots[brow + row, bcol + col] = color
      if _unique_placement(width, height, shapes, dots): break
    else:
      raise ValueError("Could not sample unambiguous marker placements")

  inwidth, inheight = width * (2 if horiz else 1), height * (1 if horiz else 2)
  grid = common.grid(inwidth, inheight, backs[0 if foreside else 1])
  output = common.grid(width, height, backs[0 if foreside else 1])
  # Draw the appropriate background colors.
  for row in range(height):
    for col in range(width):
      r, c = row, col
      if foreside and horiz: c += width
      if foreside and not horiz: r += height
      grid[r][c] = backs[1 if foreside else 0]
  for brow, bcol, bidx, bside in zip(brows, bcols, bidxs, bsides):
    # Draw the foreground colors.
    wide, tall = wides[bidx], talls[bidx]
    for row in range(brow, brow + tall):
      for col in range(bcol, bcol + wide):
        r, c = row, col
        if bside != foreside:
          output[r][c] = forecolor
        else:
          if bside and horiz: c += width
          if bside and not horiz: r += height
          grid[r][c] = forecolor
    # Draw the dots.
    for row, col, idx, color in zip(rows, cols, idxs, colors):
      if idx != bidx: continue
      r, c = brow + row, bcol + col
      if bside != foreside: output[r][c] = color
      if bside and horiz: c += width
      if bside and not horiz: r += height
      grid[r][c] = color
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=17, height=15, rows=[1, 0, 1, 0, 1, 3, 4, 0, 1, 1, 2],
               cols=[1, 3, 5, 2, 1, 1, 2, 3, 1, 3, 1],
               idxs=[0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2],
               colors=[2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2],
               brows=[4, 7, 8, 1, 9], bcols=[2, 2, 10, 8, 2],
               bidxs=[0, 1, 2, 0, 1], bsides=[0, 0, 0, 1, 1],
               wides=[7, 4, 5], talls=[2, 5, 3], backs=[8, 0], forecolor=1,
               horiz=0, foreside=0),
      generate(width=10, height=11, rows=[1, 1, 0, 1],
               cols=[0, 2, 3, 1],
               idxs=[0, 0, 1, 1],
               colors=[8, 8, 2, 2],
               brows=[2, 8, 0, 6], bcols=[2, 4, 5, 1],
               bidxs=[0, 1, 0, 1], bsides=[0, 0, 1, 1],
               wides=[3, 4], talls=[4, 3], backs=[6, 1], forecolor=3,
               horiz=1, foreside=0),
      generate(width=8, height=10, rows=[1, 3, 0],
               cols=[0, 0, 2],
               idxs=[0, 0, 1],
               colors=[2, 2, 6],
               brows=[1, 8, 1, 7], bcols=[4, 0, 1, 2],
               bidxs=[0, 1, 0, 1], bsides=[0, 0, 1, 1],
               wides=[3, 3], talls=[4, 2], backs=[4, 8], forecolor=1,
               horiz=1, foreside=1),
  ]
  test = [
      generate(width=12, height=12, rows=[1, 2, 1, 0, 1, 2],
               cols=[3, 4, 0, 2, 0, 2],
               idxs=[0, 0, 1, 2, 2, 2],
               colors=[1, 1, 1, 1, 1, 1],
               brows=[2, 6, 3, 7, 8], bcols=[4, 1, 3, 1, 6],
               bidxs=[0, 2, 0, 1, 2], bsides=[0, 0, 1, 1, 1],
               wides=[5, 2, 5], talls=[3, 4, 3], backs=[4, 2], forecolor=8,
               horiz=0, foreside=1),
  ]
  return {"train": train, "test": test}
