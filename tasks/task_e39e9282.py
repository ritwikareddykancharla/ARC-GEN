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


def _sample_markers(size, brows, bcols, bcolors):
  """Choose legal side markers with unique output destinations per block."""
  ids = common.grid(size, size, -1)
  for idx, (r, c) in enumerate(zip(brows, bcols)):
    common.rect(ids, 3, 3, r, c, idx)
  prows, pcols, pidxs = [], [], []
  for idx, (brow, bcol, color) in enumerate(zip(brows, bcols, bcolors)):
    options = []
    for prow, pcol in [(r, c) for r in (-1, 3) for c in range(3)] + [
        (r, c) for r in range(3) for c in (-1, 3)]:
      r, c = brow + prow, bcol + pcol
      if not (0 <= r < size and 0 <= c < size): continue
      neighbors = {common.get_pixel(ids, r+dr, c+dc)
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1)} - {-1}
      if neighbors != {idx}: continue
      if color == 6:
        destination = (1 if prow in (-1, 3) else prow,
                       1 if pcol in (-1, 3) else pcol)
      else:
        destination = (max(0, min(2, prow)), max(0, min(2, pcol)))
      options.append((prow, pcol, destination))
    wanted = common.randint(1, 5)
    chosen, destinations = [], set()
    for prow, pcol, destination in common.shuffle(options):
      if destination in destinations: continue
      destinations.add(destination)
      chosen.append((prow, pcol))
      if len(chosen) == wanted: break
    if len(chosen) != wanted: return None
    for prow, pcol in chosen:
      prows.append(prow)
      pcols.append(pcol)
      pidxs.append(idx)
  return prows, pcols, pidxs


def generate(size=None, brows=None, bcols=None, bcolors=None, prows=None,
             pcols=None, pidxs=None):
  """Returns input and output grids according to the given parameters.

  Args:
    size: The size of the grids.
    brows: The row indices of the blocks.
    bcols: The column indices of the blocks.
    bcolors: The colors of the blocks.
    prows: The row indices of the pixels.
    pcols: The column indices of the pixels.
    pidxs: The block indices of the pixels.
  """

  def draw():
    grid, output = common.grids(size, size, 8)
    ids = common.grid(size, size, -1)
    for idx, (brow, bcol, bcolor) in enumerate(zip(brows, bcols, bcolors)):
      common.rect(grid, 3, 3, brow, bcol, bcolor)
      common.rect(ids, 3, 3, brow, bcol, idx)
      if bcolor == 6:
        common.rect(output, 3, 3, brow, bcol, bcolor)
    for prow, pcol, pidx in zip(prows, pcols, pidxs):
      brow, bcol, bcolor = brows[pidx], bcols[pidx], bcolors[pidx]
      nr, nc = brow + prow, bcol + pcol
      if nr < 0 or nr >= size or nc < 0 or nc >= size: return None, None
      grid[brow + prow][bcol + pcol] = 9
      if bcolor == 6:
        if prow in [-1, 3]: prow = 1
        if pcol in [-1, 3]: pcol = 1
        if output[brow + prow][bcol + pcol] == 9: return None, None  # Clobbers.
        output[brow + prow][bcol + pcol] = 9
      else:
        output[brow + prow][bcol + pcol] = 9
        if prow == -1: prow += 1
        if prow == 3: prow -= 1
        if pcol == -1: pcol += 1
        if pcol == 3: pcol -= 1
        if output[brow + prow][bcol + pcol] == 9: return None, None  # Clobbers.
        output[brow + prow][bcol + pcol] = 9
    # Verify that the pixels align with exactly one block.
    for r in range(size):
      for c in range(size):
        if grid[r][c] != 9: continue
        neighbors = set()
        for dr in [-1, 0, 1]:
          for dc in [-1, 0, 1]:
            idx = common.get_pixel(ids, r + dr, c + dc)
            if idx != -1: neighbors.add(idx)
        if len(neighbors) != 1: return None, None
    return grid, output

  if size is None:
    size = 2 * common.randint(4, 7) + 1
    num_blocks = common.randint(1, 3)
    if size >= 13: num_blocks = common.randint(2, 7)
    for _ in range(2000):
      placement = common.place_rectangles(
          size, size, [3] * num_blocks, [3] * num_blocks, spacing=1)
      if placement is None: continue
      brows, bcols = placement
      bcolors = [common.randint(5, 6) for _ in range(num_blocks)]
      markers = _sample_markers(size, brows, bcols, bcolors)
      if markers is None: continue
      prows, pcols, pidxs = markers
      grid, _ = draw()
      if grid: break
    else:
      raise RuntimeError("bounded sampler failed to place all blocks and markers")

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=11, brows=[1, 2, 7], bcols=[1, 6, 3], bcolors=[6, 5, 6],
               prows=[2, 1, -1, 3], pcols=[-1, 3, 0, 1], pidxs=[0, 1, 2, 2]),
      generate(size=9, brows=[4], bcols=[2], bcolors=[6], prows=[2], pcols=[3],
               pidxs=[0]),
      generate(size=15, brows=[2, 4, 7, 10, 12], bcols=[2, 10, 4, 8, 4],
               bcolors=[5, 6, 6, 5, 5], prows=[0, 2, -1, -1, 1, 3, -1, 3, 2],
               pcols=[3, 3, 0, 1, -1, 0, 1, 2, -1],
               pidxs=[0, 0, 1, 1, 2, 2, 3, 3, 4]),
  ]
  test = [
      generate(size=13, brows=[0, 2, 5, 6, 9, 10, 10],
               bcols=[5, 0, 4, 9, 1, 5, 10], bcolors=[5, 6, 6, 6, 5, 6, 5],
               prows=[2, 2, 3, 3, 3, 3, 0, 2, 3, -1, -1, 0, 1, 2, 1, 2, 3, -1, 1],
               pcols=[-1, 3, 1, 0, 1, 2, 3, -1, 1, 0, 2, 3, -1, 3, -1, -1, 2, 2, -1],
               pidxs=[0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 5, 6]),
  ]
  return {"train": train, "test": test}
