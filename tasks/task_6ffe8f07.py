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


def _conflict(r1, c1, w1, t1, r2, c2, w2, t2):
  """True if two boxes overlap or touch (need at least one empty cell gap)."""
  return (r1 < r2 + t2 + 1 and r2 < r1 + t1 + 1 and
          c1 < c2 + w2 + 1 and c2 < c1 + w1 + 1)


def _sample_scene(width, height):
  """Bounded placement; retain the sampled box count across retries.

  Dimensions/layouts are conditioned on fitting. Exhaustion raises rather than
  quietly replacing a crowded scene with fewer objects.
  """
  num_boxes = common.randint(4, 12)
  for _ in range(2000):
    wides = [common.randint(2, 7) for _ in range(num_boxes)]
    talls = [common.randint(2, 7) for _ in range(num_boxes)]
    wides[-1] = common.randint(2, 13)  # Sometimes one of them is very long.
    order = sorted(range(num_boxes), key=lambda i: wides[i]*talls[i], reverse=True)
    pos = {}
    ok = True
    for i in order:
      placed = False
      for _ in range(80):
        r = common.randint(0, height - talls[i])
        c = common.randint(0, width - wides[i])
        good = True
        for j, (rj, cj) in pos.items():
          if _conflict(r, c, wides[i], talls[i], rj, cj, wides[j], talls[j]):
            good = False
            break
        if good:
          pos[i] = (r, c)
          placed = True
          break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    brows = [pos[i][0] for i in range(num_boxes)]
    bcols = [pos[i][1] for i in range(num_boxes)]
    if common.overlaps(brows, bcols, wides, talls, 1):
      continue
    colors = None
    for _ in range(100):
      cand = [common.randint(1, 2) for _ in range(num_boxes)]
      cand[0] = 8
      if len(set(cand)) == 3:
        colors = cand
        break
    if colors is None:
      continue
    return wides, talls, brows, bcols, colors
  raise RuntimeError("bounded sampler failed to place boxes")


def generate(width=None, height=None, wides=None, talls=None, brows=None, bcols=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: The width of the grid.
    height: The height of the grid.
    wides: The widths of the boxes.
    talls: The heights of the boxes.
    brows: The rows of the boxes.
    bcols: The columns of the boxes.
    colors: The colors of the boxes.
  """

  if width is None:
    width, height = common.randint(18, 19), common.randint(18, 19)
    wides, talls, brows, bcols, colors = _sample_scene(width, height)

  grid, output = common.grids(width, height)
  for wide, tall, brow, bcol, color in zip(wides, talls, brows, bcols, colors):
    common.rect(grid, wide, tall, brow, bcol, color)
    common.rect(output, wide, tall, brow, bcol, color)
  for wide, tall, brow, bcol, color in zip(wides, talls, brows, bcols, colors):
    if color != 8: continue
    for c in range(bcol, bcol + wide):
      for r in range(brow - 1, -1, -1):
        if output[r][c] == 1: break
        output[r][c] = 4
      for r in range(brow + tall, height, 1):
        if output[r][c] == 1: break
        output[r][c] = 4
    for r in range(brow, brow + tall):
      for c in range(bcol - 1, -1, -1):
        if output[r][c] == 1: break
        output[r][c] = 4
      for c in range(bcol + wide, width, 1):
        if output[r][c] == 1: break
        output[r][c] = 4
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=19, height=19, wides=[13, 4, 6, 5], talls=[3, 4, 4, 3], brows=[0, 5, 7, 12], bcols=[3, 6, 13, 2], colors=[2, 8, 2, 1]),
      generate(width=19, height=19, wides=[3, 5, 4, 2, 6, 4, 4, 2, 3, 5, 4], talls=[3, 6, 3, 2, 7, 3, 4, 3, 3, 3, 2], brows=[0, 0, 1, 5, 7, 8, 9, 12, 13, 16, 16], bcols=[6, 10, 1, 1, 5, 15, 0, 12, 16, 4, 10], colors=[1, 2, 2, 1, 8, 2, 2, 2, 1, 2, 1]),
      generate(width=19, height=19, wides=[3, 9, 3, 7, 7, 6, 7], talls=[2, 2, 5, 4, 2, 3, 2], brows=[1, 1, 2, 5, 10, 12, 14], bcols=[5, 10, 1, 6, 3, 12, 2], colors=[2, 1, 1, 8, 1, 2, 2]),
      generate(width=18, height=19, wides=[3, 5, 3, 2, 4, 3, 3, 5, 3, 2], talls=[2, 2, 3, 5, 4, 4, 2, 3, 3, 2], brows=[0, 0, 3, 4, 6, 8, 11, 13, 14, 15], bcols=[3, 7, 10, 0, 4, 13, 6, 10, 1, 6], colors=[1, 2, 2, 1, 8, 1, 2, 2, 2, 1]),
  ]
  test = [
      generate(width=19, height=19, wides=[7, 8, 5, 7, 4, 4], talls=[3, 3, 8, 5, 6, 2], brows=[0, 0, 4, 5, 7, 13], bcols=[0, 9, 14, 5, 0, 7], colors=[2, 1, 1, 8, 2, 2]),
      generate(width=19, height=19, wides=[5, 2, 4, 6, 5, 3, 5, 4], talls=[3, 2, 6, 5, 5, 3, 3, 2], brows=[0, 0, 0, 5, 8, 9, 14, 15], bcols=[2, 8, 13, 4, 13, 0, 6, 14], colors=[2, 1, 2, 8, 1, 2, 1, 2]),
  ]
  return {"train": train, "test": test}
