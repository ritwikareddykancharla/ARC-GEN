# Copyright 2026 Ritwika Kancharla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generator for ARC task 2de01db2: per-row complement of the main colour.

Rule: every row carries one "main" colour (the most frequent nonzero colour of
that row) plus a few noise cells of other colours and zeros.  The output row
contains the main colour exactly on the cells where the input row did NOT
hold it, and 0 on every cell where it did.  Noise is discarded.

Scope: rows are built from a latent pattern (contiguous run, run with an
interior gap, alternating parity, or scattered subset), a main colour and a
noise map.  The random path guarantees the main colour strictly outnumbers all
noise cells of its row and that each row is neither empty nor full, so the
rule is unambiguous and no example is an identity.  Grid width and height are
sampled (original fixtures are 10x3).  Rows with a frequency tie between the
main colour and a noise colour are never sampled; one canonical train row
(pair 2, row 1: three 4s vs three 7s) contains such a tie, which the archived
reference resolves to the lower colour value; validate() reproduces that row
by explicit latent arguments only.
"""

import random

import common


def _build(width, rows):
  """Builds input/output grids from explicit row specs.

  Args:
    width: number of columns.
    rows: list of (colour, positions, noise) triples; positions is an iterable
      of x coordinates holding the main colour, noise is a dict x -> colour.
  """
  height = len(rows)
  grid = common.grid(width, height, 0)
  output = common.grid(width, height, 0)
  for y, (colour, positions, noise) in enumerate(rows):
    pos = set(positions)
    for x in range(width):
      if x in pos:
        grid[y][x] = colour
        output[y][x] = 0
      else:
        grid[y][x] = noise.get(x, 0)
        output[y][x] = colour
  return {"input": grid, "output": output}


def _sample_positions(width, pattern):
  """Samples the x coordinates of the main colour for one row."""
  if pattern == "run":
    length = random.randint(width // 2 + 1, width - 1)
    start = random.randint(0, width - length)
    return list(range(start, start + length))
  if pattern == "gap":
    gap = random.randint(1, (width - 1) // 2)
    start = random.randint(1, width - gap - 1)
    return [x for x in range(width) if x < start or x >= start + gap]
  if pattern == "alternate":
    parity = random.randint(0, 1)
    return [x for x in range(width) if x % 2 == parity]
  count = random.randint(width // 2 + 1, width - 1)
  return sorted(random.sample(range(width), count))


def _row_valid(width, colour, positions, noise):
  """Main colour must strictly outnumber every other nonzero colour."""
  pos = set(positions)
  if not pos or len(pos) >= width:
    return False
  if any(x in pos for x in noise):
    return False
  counts = {}
  for x, c in noise.items():
    if c == colour or c == 0:
      return False
    counts[c] = counts.get(c, 0) + 1
  return all(v < len(pos) for v in counts.values())


def generate(width=None, height=None, rows=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: number of columns (required when rows is given).
    height: number of rows (ignored when rows is given).
    rows: list of (colour, positions, noise) latent row specs; positions is a
      list of x coordinates holding the main colour and noise maps x -> colour
      for the distractor cells.  If None, a fresh scene is sampled.
  """
  if rows is not None:
    return _build(width, rows)

  if width is None:
    width = random.randint(6, 20)
  if height is None:
    height = random.randint(2, 8)

  patterns = ["run", "gap", "alternate", "scatter"]
  for _ in range(200):
    palette = list(range(1, 10))
    random.shuffle(palette)
    mains = [palette[y % 9] for y in range(height)]
    noise_pool = [c for c in range(1, 10) if c not in mains]
    specs = []
    ok = True
    for y in range(height):
      colour = mains[y]
      pattern = random.choice(patterns)
      positions = _sample_positions(width, pattern)
      empties = [x for x in range(width) if x not in set(positions)]
      pool = noise_pool if noise_pool else [c for c in range(1, 10) if c != colour]
      max_noise = min(len(empties), len(positions) - 1, (len(empties) + 1) // 2 + 1)
      k = 0 if random.random() < 0.3 else random.randint(0, max(0, max_noise))
      noise_colours = random.sample(pool, min(len(pool), random.randint(1, 2)))
      noise = {}
      for x in random.sample(empties, k):
        noise[x] = random.choice(noise_colours)
      if not _row_valid(width, colour, positions, noise):
        ok = False
        break
      specs.append((colour, positions, noise))
    if not ok:
      continue
    scene = _build(width, specs)
    if scene["input"] != scene["output"]:
      return scene
  raise RuntimeError("failed to sample a valid scene")


def validate():
  """Validates the generator against the canonical ARC-AGI fixtures."""
  train = [
      generate(width=10, rows=[
          (6, [0, 1, 2, 3, 4, 5, 6], {8: 7, 9: 7}),
          (8, [0, 1, 2, 3, 7, 8, 9], {5: 7}),
          (4, [4, 5, 6, 7, 8, 9], {1: 2, 2: 7}),
      ]),
      generate(width=10, rows=[
          (6, [0, 1, 2, 3, 4], {6: 7, 8: 7}),
          (4, [0, 1, 2], {5: 7, 6: 7, 7: 7}),
          (8, [0, 1, 2, 3], {6: 7, 8: 7}),
      ]),
      generate(width=10, rows=[
          (4, [1, 3, 5, 7, 9], {}),
          (6, [0, 2, 4, 6, 8], {}),
          (8, [1, 3, 5, 7, 9], {}),
      ]),
  ]
  test = [
      generate(width=10, rows=[
          (8, [0, 1, 2, 7, 8, 9], {5: 3}),
          (4, [2, 3, 4, 5, 6, 7], {0: 3}),
          (6, [1, 3, 5, 7, 9], {4: 3}),
      ]),
  ]
  return {"train": train, "test": test}
