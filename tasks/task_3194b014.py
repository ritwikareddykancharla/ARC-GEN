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

"""Generator for ARC task 3194b014.

Rule: the input is a noisy grid (background 0 plus two or three scattered
noise colours) with a few solid single-colour blobs sitting on top.  The
output is a 3x3 grid filled with the colour of the LARGEST connected
single-colour object.  Total colour frequency is a deliberate distractor:
noise colours usually have more cells overall than the winning blob, but
they are split into many tiny pieces.

Scope of the random generator:
  * grid sizes 15..30 per side (originals are 20x20),
  * 3..5 blobs, each a rectangle 3..7 per side with optional corner
    staircase chips, sheared bands or connected polyominoes, pairwise separated by at least one cell,
  * distinct blob colours, a unique largest blob (margin >= 2 cells),
  * 2..3 noise colours disjoint from blob colours scattered at density
    0.3..0.5, with every noise cluster (even 8-connected) strictly smaller
    than the winning blob and colour 0 remaining the most frequent colour.
Original fixtures are replayed through the input_grid option because their
noise fields cannot be reconstructed from a handful of latent parameters.
"""

import collections
import random

import common


def _staircase_shape(h, w):
  """Returns cells of an h x w rectangle with optional chipped corners."""
  cells = set((r, c) for r in range(h) for c in range(w))
  maxd = 2 if min(h, w) >= 5 else 1
  for corner in range(4):
    if random.random() < 0.3:
      d = random.randint(1, maxd)
      for i in range(d):
        for j in range(d - i):
          r = i if corner < 2 else h - 1 - i
          c = j if corner % 2 == 0 else w - 1 - j
          cells.discard((r, c))
  return sorted(cells)


def _varied_shape(h, w, family=None):
  """Connected shapes with rectangular, sheared and irregular topology."""
  family = family or random.choice(('staircase', 'sheared', 'polyomino'))
  if family == 'staircase':
    return _staircase_shape(h, w)
  if family == 'sheared':
    thickness = random.randint(2, max(2, w - 1))
    shifts = [round(r * (w - thickness) / max(1, h - 1)) for r in range(h)]
    if random.random() < 0.5:
      shifts.reverse()
    return [(r, c) for r, shift in enumerate(shifts)
            for c in range(shift, shift + thickness)]
  if family != 'polyomino':
    raise ValueError('shape_family must be staircase, sheared or polyomino')
  cells = {(random.randrange(h), random.randrange(w))}
  target = random.randint(max(h, w), h * w)
  while len(cells) < target:
    frontier = {(r+dr, c+dc) for r,c in cells
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1))
                if 0 <= r+dr < h and 0 <= c+dc < w} - cells
    cells.add(random.choice(sorted(frontier)))
  return sorted(cells)


def _largest_component(grid, colors, eight):
  """Largest same-colour component among cells whose colour is in colors."""
  height, width = len(grid), len(grid[0])
  seen = [[False] * width for _ in range(height)]
  if eight:
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if dr or dc]
  else:
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
  best_size, best_color = 0, None
  for r in range(height):
    for c in range(width):
      if seen[r][c] or grid[r][c] not in colors:
        continue
      color = grid[r][c]
      queue = collections.deque([(r, c)])
      seen[r][c] = True
      size = 0
      while queue:
        y, x = queue.popleft()
        size += 1
        for dr, dc in steps:
          ny, nx = y + dr, x + dc
          if 0 <= ny < height and 0 <= nx < width and not seen[ny][nx] \
              and grid[ny][nx] == color:
            seen[ny][nx] = True
            queue.append((ny, nx))
      if size > best_size:
        best_size, best_color = size, color
  return best_size, best_color


def _sample_scene(height=None, width=None, shape_family=None):
  """Samples height, width, blobs, noise colours and density."""
  for _ in range(300):
    height = height if height is not None else random.randint(15, 30)
    width = width if width is not None else random.randint(15, 30)
    if not (10 <= height <= 30 and 10 <= width <= 30):
      raise ValueError("height and width must be 10..30")
    count = random.randint(3, 5)
    palette = list(range(1, 10))
    random.shuffle(palette)
    blob_colors = palette[:count]
    noise_colors = palette[count:count + random.randint(2, 3)]
    blobs, boxes, ok = [], [], True
    for color in blob_colors:
      placed = False
      for _ in range(100):
        h = random.randint(3, 7)
        w = random.randint(3, 7)
        top = random.randint(0, height - h)
        left = random.randint(0, width - w)
        clash = False
        for (t, l, b, r) in boxes:
          if top - 1 <= b and top + h >= t and left - 1 <= r \
              and left + w >= l:
            clash = True
            break
        if clash:
          continue
        boxes.append((top, left, top + h - 1, left + w - 1))
        blobs.append((color, top, left, _varied_shape(h, w, shape_family)))
        placed = True
        break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    areas = sorted(len(cells) for _, _, _, cells in blobs)
    if areas[-1] - areas[-2] < 2:
      continue
    density = random.uniform(0.3, 0.5)
    return height, width, blobs, noise_colors, density
  raise RuntimeError("could not sample a blob layout")


def generate(height=None, width=None, blobs=None, noise_colors=None,
             density=None, input_grid=None, shape_family=None):
  """Returns input and output grids according to the given parameters.

  Args:
    height: grid height (10..30); explicit requests are honored.
    width: grid width (10..30); explicit requests are honored.
    shape_family: staircase, sheared, polyomino, or None for a mixture.
    blobs: list of (color, top, left, cells) tuples; cells are (dr, dc)
      offsets of a connected single-colour blob.  The blob with the most
      cells must be unique; its colour is the answer.
    noise_colors: list of colours scattered as noise (disjoint from blobs).
    density: probability that a free cell receives a noise colour.
    input_grid: optional full input grid used to replay the original
      fixtures; the answer is then the colour of the largest 4-connected
      non-background object of that grid.
  """
  if input_grid is not None:
    grid = [list(row) for row in input_grid]
    counts = collections.Counter(v for row in grid for v in row)
    background = counts.most_common(1)[0][0]
    colors = set(counts) - {background}
    _, winner = _largest_component(grid, colors, eight=False)
    return {"input": grid, "output": common.grid(3, 3, winner)}

  for _ in range(300):
    if height is None or width is None or blobs is None:
      h, w, bl, nc, dn = _sample_scene(height, width, shape_family)
      if noise_colors is not None: nc = noise_colors
      if density is not None: dn = density
    else:
      h, w, bl, nc, dn = height, width, blobs, noise_colors, density
    if nc is None:
      used = {color for color, _, _, _ in bl}
      nc = [c for c in range(1, 10) if c not in used][:2]
    if dn is None:
      dn = 0.4
    grid = common.grid(w, h, 0)
    occupied = set()
    for color, top, left, cells in bl:
      for dr, dc in cells:
        grid[top + dr][left + dc] = color
        occupied.add((top + dr, left + dc))
    areas = sorted(((len(cells), color) for color, _, _, cells in bl),
                   reverse=True)
    win_size, win_color = areas[0]
    for r in range(h):
      for c in range(w):
        if (r, c) not in occupied and random.random() < dn:
          grid[r][c] = random.choice(nc)
    counts = collections.Counter(v for row in grid for v in row)
    if any(counts[v] >= counts[0] for v in counts if v != 0):
      continue
    noise_max, _ = _largest_component(grid, set(nc), eight=True)
    if noise_max >= win_size - 1:
      continue
    return {"input": grid, "output": common.grid(3, 3, win_color)}
  raise RuntimeError("could not sample a valid noise field")


def validate():
  """Validates the generator against the original fixtures."""
  train = [
      generate(input_grid=[
          [8, 8, 8, 8, 8, 0, 1, 0, 1, 1, 8, 1, 1, 1, 0, 0, 0, 0, 0, 1],
          [1, 0, 0, 0, 0, 8, 1, 1, 0, 0, 0, 8, 0, 5, 5, 5, 5, 5, 8, 1],
          [0, 0, 0, 0, 0, 8, 1, 0, 0, 8, 1, 1, 1, 5, 5, 5, 5, 5, 8, 0],
          [1, 8, 0, 1, 8, 0, 0, 8, 8, 8, 8, 1, 8, 5, 5, 5, 5, 5, 1, 0],
          [0, 8, 0, 9, 9, 9, 9, 8, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 8, 0],
          [8, 1, 8, 9, 9, 9, 9, 8, 1, 1, 0, 1, 1, 0, 8, 0, 8, 8, 0, 8],
          [0, 0, 0, 9, 9, 9, 9, 0, 1, 1, 8, 8, 3, 3, 8, 1, 1, 0, 0, 1],
          [8, 1, 1, 8, 1, 8, 0, 1, 0, 0, 0, 3, 3, 3, 1, 0, 8, 1, 8, 8],
          [0, 1, 8, 8, 1, 1, 0, 8, 8, 3, 3, 3, 3, 3, 8, 0, 0, 8, 1, 0],
          [0, 1, 1, 0, 1, 0, 0, 0, 8, 3, 3, 3, 3, 3, 1, 1, 8, 8, 1, 0],
          [8, 0, 8, 0, 8, 0, 0, 0, 0, 3, 3, 3, 3, 3, 1, 1, 1, 0, 8, 8],
          [0, 0, 0, 0, 8, 1, 1, 1, 1, 3, 3, 3, 3, 3, 1, 1, 0, 1, 8, 1],
          [0, 8, 8, 0, 8, 8, 1, 8, 0, 3, 3, 3, 8, 1, 1, 0, 0, 0, 0, 0],
          [0, 0, 8, 8, 0, 0, 8, 0, 1, 0, 0, 1, 0, 0, 0, 8, 1, 1, 1, 0],
          [0, 0, 1, 0, 1, 0, 1, 8, 8, 1, 0, 0, 8, 0, 1, 0, 1, 1, 0, 0],
          [0, 4, 4, 4, 4, 4, 8, 4, 0, 0, 0, 1, 0, 8, 0, 8, 0, 1, 8, 0],
          [1, 4, 4, 4, 4, 4, 4, 4, 0, 1, 1, 0, 8, 0, 0, 0, 0, 8, 1, 8],
          [1, 4, 4, 4, 4, 4, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 8],
          [0, 1, 0, 0, 0, 1, 8, 1, 0, 8, 0, 1, 0, 0, 8, 0, 0, 8, 1, 0],
          [8, 0, 1, 0, 0, 1, 0, 8, 0, 1, 1, 0, 1, 8, 0, 8, 0, 0, 1, 0],
      ]),
      generate(input_grid=[
          [6, 6, 6, 7, 7, 7, 0, 0, 6, 0, 0, 6, 0, 0, 6, 6, 0, 0, 6, 6],
          [0, 0, 0, 0, 6, 0, 0, 0, 7, 0, 0, 7, 0, 0, 6, 7, 6, 0, 7, 0],
          [6, 0, 0, 7, 6, 0, 0, 0, 0, 7, 0, 0, 6, 6, 0, 0, 0, 6, 7, 6],
          [7, 0, 7, 2, 2, 2, 2, 0, 7, 0, 7, 7, 0, 7, 0, 0, 6, 7, 0, 6],
          [0, 7, 0, 2, 2, 2, 2, 7, 6, 7, 0, 0, 6, 7, 6, 0, 7, 0, 6, 0],
          [7, 0, 0, 2, 2, 2, 2, 7, 0, 0, 0, 0, 6, 7, 0, 0, 0, 0, 0, 0],
          [6, 6, 6, 2, 2, 2, 2, 0, 7, 0, 0, 9, 9, 9, 7, 7, 0, 7, 7, 0],
          [7, 0, 0, 0, 7, 0, 0, 7, 6, 0, 6, 9, 9, 9, 7, 0, 6, 0, 0, 0],
          [7, 6, 0, 6, 6, 7, 0, 6, 0, 6, 7, 9, 9, 9, 6, 0, 0, 0, 0, 0],
          [0, 0, 7, 7, 6, 0, 7, 6, 6, 7, 6, 9, 9, 9, 0, 0, 0, 0, 0, 0],
          [0, 7, 7, 6, 0, 0, 0, 0, 7, 0, 6, 0, 6, 0, 0, 7, 0, 7, 0, 0],
          [0, 6, 7, 7, 0, 7, 7, 7, 0, 0, 0, 6, 6, 6, 0, 0, 0, 0, 6, 6],
          [6, 7, 7, 0, 7, 6, 0, 6, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 7],
          [7, 6, 6, 0, 6, 7, 0, 6, 0, 6, 7, 6, 0, 0, 6, 7, 0, 0, 7, 6],
          [6, 0, 0, 6, 0, 7, 4, 4, 4, 4, 4, 0, 0, 7, 6, 0, 6, 0, 0, 0],
          [7, 0, 7, 0, 0, 0, 4, 4, 4, 4, 4, 7, 0, 7, 6, 0, 0, 0, 0, 7],
          [6, 6, 0, 0, 0, 0, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 6, 0, 0],
          [6, 7, 6, 6, 6, 0, 4, 4, 4, 4, 4, 6, 7, 7, 6, 7, 0, 0, 0, 6],
          [7, 0, 0, 0, 6, 6, 4, 4, 4, 4, 4, 6, 0, 6, 0, 0, 0, 0, 6, 7],
          [0, 0, 7, 7, 6, 0, 0, 6, 7, 6, 6, 0, 6, 0, 6, 0, 7, 7, 0, 0],
      ]),
      generate(input_grid=[
          [0, 3, 2, 0, 0, 0, 0, 0, 2, 0, 3, 2, 2, 3, 3, 2, 0, 0, 0, 0],
          [2, 2, 0, 0, 2, 0, 0, 0, 3, 3, 2, 2, 0, 3, 0, 0, 3, 2, 2, 3],
          [0, 2, 8, 8, 8, 8, 8, 8, 0, 0, 0, 2, 3, 3, 0, 2, 6, 6, 0, 2],
          [3, 8, 8, 8, 8, 8, 8, 8, 3, 0, 0, 3, 2, 3, 6, 6, 6, 6, 6, 2],
          [0, 8, 8, 8, 8, 8, 8, 8, 3, 2, 0, 2, 3, 9, 6, 6, 6, 6, 6, 3],
          [2, 0, 8, 8, 8, 8, 8, 8, 8, 0, 0, 2, 0, 0, 6, 6, 6, 6, 6, 0],
          [0, 2, 0, 8, 8, 8, 8, 8, 8, 2, 2, 0, 6, 6, 6, 6, 6, 6, 6, 2],
          [0, 0, 2, 3, 8, 8, 8, 8, 8, 8, 0, 3, 0, 6, 6, 6, 6, 6, 6, 3],
          [0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 0, 3, 3, 6, 6, 6, 0, 0, 0, 0],
          [0, 0, 2, 2, 0, 3, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
          [0, 2, 3, 2, 2, 3, 3, 2, 2, 0, 2, 2, 0, 2, 0, 0, 2, 0, 2, 2],
          [3, 0, 0, 3, 2, 0, 3, 0, 0, 2, 4, 4, 4, 0, 0, 0, 2, 0, 2, 3],
          [0, 0, 0, 0, 2, 0, 2, 0, 0, 4, 4, 4, 4, 0, 0, 3, 0, 2, 0, 2],
          [3, 2, 0, 0, 0, 3, 0, 0, 4, 4, 4, 4, 4, 3, 2, 3, 2, 0, 2, 0],
          [3, 2, 2, 0, 2, 0, 0, 0, 4, 4, 4, 4, 4, 3, 2, 0, 3, 0, 2, 2],
          [2, 3, 0, 0, 2, 2, 0, 3, 0, 4, 4, 4, 4, 3, 2, 0, 0, 0, 3, 2],
          [2, 2, 0, 3, 0, 2, 0, 3, 0, 2, 3, 2, 2, 2, 0, 2, 2, 3, 0, 3],
          [2, 2, 0, 0, 0, 0, 0, 3, 2, 3, 0, 2, 0, 0, 0, 2, 0, 2, 2, 2],
          [0, 0, 0, 0, 0, 0, 3, 3, 2, 3, 3, 3, 2, 0, 0, 3, 0, 2, 3, 3],
          [0, 0, 3, 2, 0, 0, 2, 2, 2, 0, 3, 0, 0, 2, 0, 3, 0, 3, 0, 0],
      ]),
  ]
  test = [
      generate(input_grid=[
          [0, 9, 9, 7, 0, 0, 9, 7, 7, 7, 0, 7, 0, 0, 7, 0, 9, 0, 0, 0],
          [0, 0, 7, 3, 3, 3, 3, 0, 7, 7, 0, 0, 0, 0, 6, 6, 6, 6, 0, 9],
          [0, 7, 9, 3, 3, 3, 3, 3, 3, 0, 9, 9, 7, 0, 6, 6, 6, 6, 0, 7],
          [0, 9, 0, 3, 3, 3, 3, 3, 3, 3, 7, 0, 7, 6, 6, 6, 6, 6, 0, 0],
          [9, 0, 0, 7, 0, 9, 7, 7, 0, 7, 7, 0, 0, 0, 9, 6, 6, 6, 7, 7],
          [0, 0, 9, 7, 0, 9, 9, 0, 0, 7, 0, 0, 9, 0, 0, 6, 6, 6, 0, 7],
          [0, 9, 0, 9, 0, 0, 7, 0, 0, 9, 0, 0, 0, 0, 0, 9, 9, 0, 0, 0],
          [0, 9, 0, 0, 9, 7, 0, 0, 0, 9, 7, 0, 9, 9, 0, 7, 0, 0, 0, 0],
          [0, 7, 8, 8, 8, 8, 9, 9, 0, 7, 0, 0, 9, 7, 7, 0, 0, 9, 7, 7],
          [9, 0, 9, 8, 8, 8, 7, 7, 0, 7, 0, 0, 9, 0, 0, 9, 0, 7, 0, 0],
          [0, 0, 9, 8, 8, 8, 0, 9, 0, 9, 0, 0, 7, 5, 5, 0, 0, 9, 0, 9],
          [0, 0, 9, 8, 8, 8, 9, 0, 0, 0, 0, 9, 5, 5, 5, 7, 0, 0, 0, 9],
          [9, 0, 0, 8, 8, 8, 0, 7, 9, 9, 7, 0, 5, 5, 5, 5, 0, 0, 0, 7],
          [9, 9, 9, 7, 9, 8, 8, 0, 9, 7, 0, 5, 5, 5, 5, 5, 9, 0, 7, 0],
          [0, 0, 7, 7, 0, 7, 8, 0, 0, 0, 7, 5, 5, 5, 5, 5, 5, 9, 0, 9],
          [9, 7, 7, 0, 9, 0, 7, 9, 7, 0, 9, 5, 5, 5, 5, 5, 5, 0, 0, 9],
          [0, 7, 7, 0, 0, 7, 9, 0, 7, 0, 9, 7, 5, 5, 5, 5, 5, 9, 7, 9],
          [0, 0, 7, 7, 7, 0, 0, 9, 0, 9, 0, 0, 5, 5, 5, 5, 5, 0, 0, 0],
          [0, 0, 0, 0, 0, 7, 9, 0, 0, 0, 9, 9, 5, 5, 5, 0, 9, 0, 9, 0],
          [0, 0, 9, 0, 7, 0, 0, 9, 7, 0, 0, 7, 0, 0, 7, 9, 0, 0, 0, 0],
      ]),
  ]
  return {"train": train, "test": test}
