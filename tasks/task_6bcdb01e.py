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


def _sample_obstacles(size, expected_bounces, max_nodes=4096):
  """Construct constraints for a valid ray, then add unconstrained noise.

  Preserve the requested turn count. A bounded search returns None on
  exhaustion, never a simpler path. This is not uniform sampling of fields
  conditioned on the requested number of turns.
  """
  nodes = 0

  def inside(p):
    return 0 <= p[0] < size and 0 <= p[1] < size

  def constrain(known, assignments):
    result = known.copy()
    for cell, obstacle in assignments:
      if not inside(cell):
        if obstacle: return None
        continue
      if cell in result and result[cell] != obstacle: return None
      result[cell] = obstacle
    return result

  def search(row, col, dr, dc, turns, known):
    nonlocal nodes
    if nodes >= max_nodes: return None
    nodes += 1
    if not inside((row, col)):
      return known if turns == expected_bounces else None
    # Every incoming step has already been constrained to be unobstructed.
    ahead = row + dr, col + dc
    choices = [(dr, dc, turns, [(ahead, 0)])]
    if turns < expected_bounces:
      for nr, nc in ((dc, -dr), (-dc, dr)):
        choices.append((nr, nc, turns + 1, [
            (ahead, 1), ((row - nr, col - nc), 1),
            ((row + nr, col + nc), 0)]))
    for nr, nc, count, assignments in common.shuffle(choices):
      extended = constrain(known, assignments)
      if extended is None: continue
      result = search(row + nr, col + nc, nr, nc, count, extended)
      if result is not None: return result
    return None

  known = search(1, 2, 0, 1, 0, {(1, 0): 0, (1, 1): 0, (1, 2): 0})
  if known is None: return None
  return [known[(r, c)] if (r, c) in known else int(common.randint(0, 4) == 0)
          for r in range(size) for c in range(size)]


def generate(size=None, flip=None, flop=None, xpose=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    size: The size of the grid.
    flip: Whether to flip the grid.
    flop: Whether to flop the grid.
    xpose: Whether to transpose the grid.
    colors: The colors of the grid.
  """

  def draw():
    grid, output = common.grids(size, size, 7)
    for i, color in enumerate(colors):
      if color: output[i // size][i % size] = grid[i // size][i % size] = 8
    output[1][0] = output[1][1] = grid[1][0] = grid[1][1] = 3
    row, col, rdir, cdir, bounces = 1, 2, 0, 1, 0
    while True:
      if bounces > 10: return None, None, None  # avoid an infinite loop
      if row < 0 or col < 0 or row >= size or col >= size: break
      output[row][col] = 3
      if common.get_pixel(output, row + rdir, col + cdir) == 8:
        bounces += 1
        alt_row = row if abs(rdir) else (row - 1)
        alt_col = col if abs(cdir) else (col - 1)
        increase = common.get_pixel(output, alt_row, alt_col) == 8
        alt_row = row if abs(rdir) else (row + 1)
        alt_col = col if abs(cdir) else (col + 1)
        decrease = common.get_pixel(output, alt_row, alt_col) == 8
        if increase == decrease: return None, None, None
        if decrease: rdir, cdir = 0 if abs(rdir) else -1, 0 if abs(cdir) else -1
        if increase: rdir, cdir = 0 if abs(rdir) else 1, 0 if abs(cdir) else 1
      row, col = row + rdir, col + cdir
    if flip: grid, output = common.flip(grid), common.flip(output)
    if flop: grid, output = common.flop(grid), common.flop(output)
    if xpose: grid, output = common.transpose(grid), common.transpose(output)
    return grid, output, bounces

  if size is None:
    flip, flop = common.randint(0, 1), common.randint(0, 1)
    xpose = common.randint(0, 1)
    expected_bounces = common.randint(3, 6)
    for _ in range(256):
      size = common.randint(5, 10)
      colors = _sample_obstacles(size, expected_bounces)
      if colors is None: continue
      grid, _, bounces = draw()
      if grid is not None and bounces == expected_bounces: break
    else:
      raise RuntimeError("bounded ray construction exhausted")

  grid, output, _ = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(size=7, flip=True, flop=False, xpose=False,
               colors=[0, 0, 0, 1, 0, 0, 0,
                       0, 0, 0, 0, 1, 0, 0,
                       0, 0, 0, 0, 0, 1, 0,
                       0, 0, 0, 0, 0, 0, 1,
                       0, 0, 0, 0, 0, 0, 0,
                       0, 1, 1, 0, 0, 0, 1,
                       1, 0, 0, 1, 0, 1, 0]),
      generate(size=5, flip=False, flop=True, xpose=True,
               colors=[0, 0, 0, 1, 0,
                       0, 0, 0, 0, 1,
                       0, 0, 0, 0, 0,
                       1, 0, 0, 0, 1,
                       0, 1, 0, 1, 0]),
  ]
  test = [
      generate(size=8, flip=False, flop=True, xpose=False,
               colors=[0, 0, 0, 0, 0, 1, 0, 0,
                       0, 0, 0, 0, 0, 0, 1, 0,
                       0, 1, 0, 1, 0, 0, 0, 0,
                       1, 0, 0, 0, 1, 0, 1, 0,
                       0, 0, 0, 0, 1, 0, 0, 1,
                       0, 0, 0, 0, 0, 1, 0, 0,
                       0, 0, 1, 0, 0, 0, 0, 1,
                       0, 0, 0, 1, 0, 0, 1, 0]),
  ]
  return {"train": train, "test": test}
