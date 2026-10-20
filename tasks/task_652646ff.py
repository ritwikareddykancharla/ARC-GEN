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


from itertools import permutations as _ring_permutations

_RING_TEMPLATE = [(0,2),(0,3),(1,1),(1,4),(2,0),(2,5),(3,0),(3,5),(4,1),(4,4),(5,2),(5,3)]


def _ring_orders(grid):
    h, w = len(grid), len(grid[0])
    counts = {}
    cells = {}
    for y,row in enumerate(grid):
        for x,c in enumerate(row):
            counts[c] = counts.get(c,0)+1
            cells.setdefault(c,set()).add((y,x))
    bg = max(counts,key=counts.get)
    colours = set(counts)-{bg}
    strong = {c for c in colours if counts[c]>=8}
    weak = colours-strong

    def placements(c):
        anchor = min(cells[c])
        found = []
        for ty,tx in _RING_TEMPLATE:
            oy,ox = anchor[0]-ty,anchor[1]-tx
            if not (-1 <= oy <= h-5 and -1 <= ox <= w-5):
                continue
            full = {(oy+dy,ox+dx) for dy,dx in _RING_TEMPLATE}
            if cells[c] <= full:
                found.append(full)
        return found

    fixed = {}
    for c in strong:
        candidates = placements(c)
        if len(candidates)!=1:
            return bg,set()
        fixed[c] = candidates[0]
    variants = [dict(fixed)]
    # Only the top ring may show fewer than eight pixels. A candidate must
    # explain its entire visible colour; the remaining colours are noise.
    for c in weak:
        for pos in placements(c):
            if any(grid[y][x]==bg or grid[y][x] in strong
                   for y,x in pos if 0<=y<h and 0<=x<w):
                continue
            variant = dict(fixed)
            variant[c] = pos
            variants.append(variant)
    answers = set()
    for masks in variants:
        n = len(masks)
        if n not in ((3,4) if h>15 else (2,3)):
            continue
        noise = colours-set(masks)
        if not 1 <= len(noise) <= 2 or not 1 <= sum(counts[c] for c in noise) <= 7:
            continue
        if len({frozenset(p) for p in masks.values()}) != n:
            continue
        for order in _ring_permutations(masks):
            if any(counts[c]<8 for c in order[1:]):
                continue
            # Every lower ring must visibly be covered by its immediate
            # predecessor, exactly as the construction's chain rule requires.
            if any(not any(0<=y<h and 0<=x<w and grid[y][x]==order[i-1]
                           for y,x in masks[c]) for i,c in enumerate(order) if i):
                continue
            predicted = {}
            for c in reversed(order):
                for y,x in masks[c]:
                    if 0<=y<h and 0<=x<w:
                        predicted[y,x] = c
            if all(c in noise or predicted.get((y,x),bg)==c
                   for y,row in enumerate(grid) for x,c in enumerate(row)):
                answers.add(tuple(order))
    return bg,answers




def generate(size=None, bgcolor=None, brows=None, bcols=None, bcolors=None,
             prows=None, pcols=None, pcolors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    size: The size of the grid.
    bgcolor: The background color.
    brows: The row indices of the blobs.
    bcols: The column indices of the blobs.
    bcolors: The colors of the blobs.
    prows: The row indices of the pixels.
    pcols: The column indices of the pixels.
    pcolors: The colors of the pixels.
  """

  def draw():
    if common.overlaps(brows, bcols, [1] * len(brows), [1] * len(bcols)):
      return None, None
    grid = common.grid(size, size, bgcolor)
    output = common.grid(6, 6 * len(bcolors), bgcolor)
    drs = [0, 1, 2, 3, 4, 5, 5, 4, 3, 2, 1, 0]
    dcs = [3, 4, 5, 5, 4, 3, 2, 1, 0, 0, 1, 2]
    for i, (brow, bcol, bcolor) in enumerate(reversed(list(zip(brows, bcols, bcolors)))):
      for dr, dc in zip(drs, dcs):
        common.draw(grid, brow + dr, bcol + dc, bcolor)
        output[(len(bcolors) - i - 1) * 6 + dr][dc] = bcolor
    for prow, pcol, pcolor in zip(prows, pcols, pcolors):
      grid[prow][pcol] = pcolor
    # Check that each blob is (a) covered by the one above it, and (b) shows at
    # least 8 pixels.
    for i in range(1, len(bcolors)):
      covered = False
      num_showing = 0
      for dr, dc in zip(drs, dcs):
        color = common.get_pixel(grid, brows[i] + dr, bcols[i] + dc)
        if color == bcolors[i - 1]: covered = True
        if color == bcolors[i]: num_showing += 1
      if not covered or num_showing < 8: return None, None
    return grid, output

  if size is None:
    size = common.randint(10, 20)
    num_blobs = common.randint(2, 3)
    if size > 15: num_blobs += 1
    num_pixels = common.randint(3, 7)
    colors = common.shuffle(list(range(10)))
    bgcolor = colors.pop()
    bcolors = [colors.pop() for _ in range(num_blobs)]
    pixel_colors = [colors.pop() for _ in range(2)]
    for _ in range(200000):
      brows = [common.randint(-1, size - 5) for _ in range(num_blobs)]
      bcols = [common.randint(-1, size - 5) for _ in range(num_blobs)]
      prows = [common.randint(0, size - 1) for _ in range(num_pixels)]
      pcols = [common.randint(0, size - 1) for _ in range(num_pixels)]
      pcolors = common.choices(pixel_colors, num_pixels)
      grid, _ = draw()
      if not grid: continue
      _, possible_orders = _ring_orders(grid)
      if possible_orders == {tuple(bcolors)}: break
    else:
      raise RuntimeError("652646ff: unique visible ring order sampling exhausted")

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=20, bgcolor=2, brows=[7, 7, 8], bcols=[1, 6, 10],
               bcolors=[4, 8, 3], prows=[2, 2, 9, 10, 10, 16, 19],
               pcols=[3, 17, 7, 3, 13, 10, 0], pcolors=[5, 5, 5, 9, 9, 5, 5]),
      generate(size=10, bgcolor=3, brows=[1, 2, 4], bcols=[1, 2, 0],
               bcolors=[4, 8, 1], prows=[1, 7, 9], pcols=[0, 2, 6],
               pcolors=[5, 5, 5]),
      generate(size=13, bgcolor=4, brows=[8, 5, 2], bcols=[6, 3, 0],
               bcolors=[3, 8, 2], prows=[0, 1, 4, 5, 10, 11, 11],
               pcols=[5, 11, 3, 9, 1, 2, 9], pcolors=[5, 7, 7, 5, 5, 7, 5]),
      generate(size=10, bgcolor=8, brows=[2, 2], bcols=[1, 4], bcolors=[4, 3],
               prows=[0, 4, 8, 9], pcols=[8, 2, 1, 7], pcolors=[5, 2, 5, 2]),
  ]
  test = [
      generate(size=17, bgcolor=1, brows=[3, 6, 8, 7], bcols=[5, 8, 4, 5],
               bcolors=[8, 4, 3, 7], prows=[1, 2, 8, 11, 15, 16],
               pcols=[14, 2, 3, 16, 11, 0],
               pcolors=[0, 0, 5, 5, 0, 5]),
  ]
  return {"train": train, "test": test}
