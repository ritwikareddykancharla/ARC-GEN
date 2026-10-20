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

import sys

import common


def _unique_output(grid, max_nodes=20000):
  """Find the unique complete key-placement painting from visible input.

  Reject multiple paintings or search exhaustion. Identical paintings from
  equivalent rotations are allowed. No generator coordinates/answers are read.
  """
  height, width = len(grid), len(grid[0])
  remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
  groups = []
  while remaining:
    cells = {remaining.pop()}
    stack = list(cells)
    while stack:
      r, c = stack.pop()
      for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
        if p in remaining:
          remaining.remove(p)
          cells.add(p)
          stack.append(p)
    groups.append(cells)
  if not groups: return None
  board = max(groups, key=len)
  top, bottom = min(r for r, c in board), max(r for r, c in board)
  left, right = min(c for r, c in board), max(c for r, c in board)
  canvas = [row[left:right+1] for row in grid[top:bottom+1]]
  tall, wide = len(canvas), len(canvas[0])
  total = frozenset((r, c) for r in range(tall)
                    for c in range(wide) if canvas[r][c] == 0)
  candidate_lists = []
  for cells in groups:
    if all(top <= r <= bottom and left <= c <= right for r, c in cells): continue
    y0, y1 = min(r for r, c in cells), max(r for r, c in cells)
    x0, x1 = min(c for r, c in cells), max(c for r, c in cells)
    patch = tuple(tuple(grid[r][c] if (r, c) in cells else 0
                        for c in range(x0, x1+1)) for r in range(y0, y1+1))
    variants, candidates = set(), []
    for _ in range(4):
      variants.add(patch)
      patch = tuple(zip(*patch[::-1]))
    for patch in variants:
      h, w = len(patch), len(patch[0])
      if not any(v == 2 for row in patch for v in row): continue
      for r in range(tall-h+1):
        for c in range(wide-w+1):
          if any((canvas[r+y][c+x] == 0) != (patch[y][x] == 2)
                 for y in range(h) for x in range(w)):
            continue
          holes = frozenset((r+y, c+x) for y in range(h) for x in range(w)
                            if patch[y][x] == 2)
          paint = tuple((r+y, c+x, patch[y][x]) for y in range(h) for x in range(w)
                        if patch[y][x] != 0)
          footprint = frozenset((y, x) for y, x, ink in paint)
          candidates.append((holes, footprint, paint))
    candidate_lists.append(candidates)
  answers, nodes, exhausted = set(), 0, False
  order = sorted(range(len(candidate_lists)), key=lambda i: len(candidate_lists[i]))

  def search(depth, covered, occupied, paints):
    nonlocal nodes, exhausted
    if nodes >= max_nodes:
      exhausted = True
      return
    nodes += 1
    if depth == len(order):
      if covered == total:
        out = [row[:] for row in canvas]
        for paint in paints:
          for r, c, ink in paint: out[r][c] = ink
        answers.add(tuple(tuple(row) for row in out))
      return
    for holes, footprint, paint in candidate_lists[order[depth]]:
      if holes & covered or footprint & occupied: continue
      search(depth+1, covered | holes, occupied | footprint, paints + [paint])
      if exhausted or len(answers) > 1: return

  search(0, frozenset(), frozenset(), [])
  return next(iter(answers)) if len(answers) == 1 and not exhausted else None


def generate(width=None, height=None, rows=None, cols=None, idxs=None,
             srows=None, scols=None, colors=None, irows=None, icols=None,
             rotates=None, wide=None, tall=None, brow=None, bcol=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: the width of the input grid
    height: the height of the input grid
    rows: a list of vertical coordinates where pixels should be placed
    cols: a list of horizontal coordinates where pixels should be placed
    idxs: a list of indices into the sprites list
    srows: a list of vertical coordinates where the sprites should be placed
    scols: a list of horizontal coordinates where the sprites should be placed
    colors: a list of colors to be used for the sprites
    irows: a list of vertical coordinates insides the red box
    icols: a list of horizontal coordinates insides the red box
    rotates: a list of rotations to be applied to the sprites
    wide: the width of the output grid
    tall: the height of the output grid
    brow: the vertical coordinate of the top left corner of the red box
    bcol: the horizontal coordinate of the top left corner of the red box
  """

  def draw(grid, output):
    # Draw the big red boxes.
    for r in range(tall):
      for c in range(wide):
        output[r][c] = grid[r + brow][c + bcol] = common.red()
    # Draw the sprite background colors (outside for input, inside for output)
    for idx, color in enumerate(colors):
      for dr in range(3):
        for dc in range(3):
          grid[srows[idx] + dr][scols[idx] + dc] = color
          output[irows[idx] + dr][icols[idx] + dc] = color
    # Draw sprites (black inside + red outside for input, red inside for output)
    # Along the way, check that we're not touching edges of another sprite.
    illegal = False
    for sprite_idx in set(idxs):
      for row, col, idx in zip(rows, cols, idxs):
        if idx != sprite_idx: continue
        r, c = row, col
        if rotates[idx] == 1: r, c = c, 2 - r
        if rotates[idx] == 2: r, c = 2 - r, 2 - c
        if rotates[idx] == 3: r, c = 2 - c, r
        for dr in [-1, 0, 1]:
          for dc in [-1, 0, 1]:
            v = grid[brow + irows[idx] + r + dr][bcol + icols[idx] + c + dc]
            if v == common.black(): illegal = True
      for row, col, idx in zip(rows, cols, idxs):
        if idx != sprite_idx: continue
        r, c = row, col
        if rotates[idx] == 1: r, c = c, 2 - r
        if rotates[idx] == 2: r, c = 2 - r, 2 - c
        if rotates[idx] == 3: r, c = 2 - c, r
        grid[srows[idx] + row][scols[idx] + col] = common.red()
        grid[brow + irows[idx] + r][bcol + icols[idx] + c] = common.black()
        output[irows[idx] + r][icols[idx] + c] = common.red()
    return not illegal

  if width is None:
    num_sprites = common.randint(1, 5)
    # Choose positions until everything fits and nothing overlaps.
    for _ in range(2000):
      wide, tall = common.randint(8, 20), common.randint(8, 20)
      width, height = wide + common.randint(2, 10), tall + common.randint(2, 10)
      brow = common.randint(1, height - tall - 1)
      bcol = common.randint(1, width - wide - 1)
      lens = [3] * num_sprites
      outside = common.place_rectangles(
          width, height, [wide] + lens, [tall] + lens, spacing=1,
          fixed_positions={0: (brow, bcol)})
      if outside is None: continue
      inside = common.place_rectangles(wide - 2, tall - 2, lens, lens)
      if inside is None: continue
      srows, scols = outside[0][1:], outside[1][1:]
      irows, icols = [r + 1 for r in inside[0]], [c + 1 for c in inside[1]]
      counts = common.sample(range(4, 9), num_sprites)
      rows, cols, idxs = [], [], []
      for idx in range(num_sprites):
        for _ in range(256):  # Avoid sprites where rotation might be ambiguous.
          pixels = common.sample(common.all_pixels(3, 3), counts[idx])
          num_blank = 0
          for r in range(3):
            blank = True
            for c in range(3):
              if (r, c) in pixels: blank = False
            if blank: num_blank += 1
          for c in range(3):
            blank = True
            for r in range(3):
              if (r, c) in pixels: blank = False
            if blank: num_blank += 1
          if counts[idx] == 4 and num_blank >= 2: continue  # Avoid 2x2
          if counts[idx] == 6 and num_blank >= 1: continue  # Avoid 2x3
          break
        else:
          raise RuntimeError("bounded sampler failed to draw key silhouette")
        rows.extend(p[0] for p in pixels)
        cols.extend(p[1] for p in pixels)
        idxs.extend([idx] * len(pixels))
      # Exercise the relative rotations already present in supplied fixtures,
      # rather than teaching only keys that happen to be pre-aligned.
      rotates = [common.randint(0, 3) for _ in range(num_sprites)]
      colors = common.random_colors(num_sprites, exclude=[common.red()])
      grid, output = common.grid(width, height), common.grid(wide, tall)
      if draw(grid, output) and _unique_output(grid) is not None: break
    else:
      raise RuntimeError("bounded sampler failed to place board and all keys")

  grid, output = common.grid(width, height), common.grid(wide, tall)
  draw(grid, output)
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=19, height=24,
               rows=[0, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 2, 2, 1, 2, 2, 0, 1, 1, 1,
                     2],
               cols=[1, 0, 1, 2, 1, 0, 1, 2, 0, 2, 0, 1, 2, 1, 0, 1, 2, 0, 1, 2,
                     2],
               idxs=[0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4,
                     4],
               srows=[2, 7, 17, 20, 20], scols=[13, 14, 14, 3, 8],
               irows=[6, 1, 13, 1, 13], icols=[3, 6, 0, 1, 5],
               rotates=[0, 1, 3, 1, 1], colors=[1, 3, 8, 4, 5], wide=9, tall=17,
               brow=1, bcol=2),
      generate(width=10, height=20,
               rows=[0, 1, 1, 2, 0, 0, 1, 1, 2, 2],
               cols=[1, 0, 1, 1, 0, 1, 0, 2, 1, 2],
               idxs=[0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
               srows=[11, 13], scols=[1, 5], irows=[1, 4], icols=[1, 4],
               rotates=[1, 0], colors=[4, 3], wide=8, tall=8, brow=1, bcol=1),
      generate(width=12, height=16,
               rows=[0, 1, 1, 1, 2], cols=[1, 0, 1, 2, 1], idxs=[0, 0, 0, 0, 0],
               srows=[1], scols=[5], irows=[2], icols=[2], rotates=[0],
               colors=[8], wide=9, tall=9, brow=6, bcol=1),
  ]
  test = [
      generate(width=15, height=19,
               rows=[1, 0, 1, 1, 2, 0, 1, 1, 2, 2, 0, 1, 2],
               cols=[1, 0, 0, 1, 0, 2, 1, 2, 0, 1, 1, 1, 1],
               idxs=[0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3],
               srows=[11, 11, 15, 16], scols=[1, 8, 11, 3], irows=[0, 1, 1, 5],
               icols=[9, 4, 1, 7], rotates=[0, 2, 1, 1], colors=[1, 3, 8, 4],
               wide=12, tall=8, brow=1, bcol=2),
  ]
  return {"train": train, "test": test}
