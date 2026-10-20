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

_GAP = 2
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_ANGLE_DIRS = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
_MAX_SIZE_TRIES = 64
_MAX_SCENE_TRIES = 5000
_NODE_BUDGET = 200000


def _cell(a, dy, dx, d, s):
  if dy != 0:
    return (a[0] + dy * d, a[1] + s)
  return (a[0] + s, a[1] + dx * d)


def _box(a, dy, dx, e):
  if dy != 0:
    r_end = a[0] + dy * e
    return (min(a[0], r_end), max(a[0], r_end), a[1] - e, a[1] + e)
  c_end = a[1] + dx * e
  return (a[0] - e, a[0] + e, min(a[1], c_end), max(a[1], c_end))


def _separated(b1, b2):
  return (b1[1] + _GAP < b2[0] or b2[1] + _GAP < b1[0] or
          b1[3] + _GAP < b2[2] or b2[3] + _GAP < b1[2])


def _candidates(pts, height, width):
  """Visible cone candidates: apex, dir, extent, members, unclipped box."""
  ptset = set(pts)
  out = []
  for a in pts:
    for dy, dx in _DIRS:
      for e in range(1, max(height, width) + 1):
        members = {a}
        neg = pos = last = False
        for d in range(1, e + 1):
          for s in (-d, d):
            p = _cell(a, dy, dx, d, s)
            if p in ptset:
              members.add(p)
              if s < 0:
                neg = True
              else:
                pos = True
              if d == e:
                last = True
        if not (neg and pos and last):
          continue
        box = _box(a, dy, dx, e)
        ok = True
        for p in pts:
          if (box[0] - _GAP <= p[0] <= box[1] + _GAP and
              box[2] - _GAP <= p[1] <= box[3] + _GAP and p not in members):
            ok = False
            break
        if ok:
          out.append((a, dy, dx, e, frozenset(members), box))
  return out


def _visible_outputs(grid, marker=3, fill=8):
  height, width = len(grid), len(grid[0])
  pts = sorted((r,c) for r in range(height) for c in range(width) if grid[r][c]==marker)
  if not pts:
    return set()
  cands = _candidates(pts, height, width)
  by_pt = {p: [] for p in pts}
  for i,cand in enumerate(cands):
    for p in cand[4]: by_pt[p].append(i)
  answers, chosen, covered = set(), [], set()
  nodes = 0

  def rec():
    nonlocal nodes
    if len(answers)>1: return
    nodes += 1
    if nodes>_NODE_BUDGET:
      raise RuntimeError('Cone exact-cover search budget exhausted')
    remaining=[p for p in pts if p not in covered]
    if not remaining:
      out=[list(row) for row in grid]
      for i in chosen:
        a,dy,dx,e,_,_ = cands[i]
        for d in range(1,e+1):
          for s in range(-d,d+1):
            r,c=_cell(a,dy,dx,d,s)
            if 0<=r<height and 0<=c<width and grid[r][c]!=marker: out[r][c]=fill
      answers.add(tuple(map(tuple,out)))
      return
    first=min(remaining,key=lambda p:len(by_pt[p]))
    for i in by_pt[first]:
      cand=cands[i]
      if cand[4]&covered: continue
      if not all(_separated(cand[5],cands[j][5]) for j in chosen): continue
      chosen.append(i);covered.update(cand[4]);rec()
      covered.difference_update(cand[4]);chosen.pop()
      if len(answers)>1:return
  rec()
  return answers


def generate(width=None, height=None, brows=None, bcols=None, angles=None,
             lengths=None, colors=None):
  """Returns input and output grids according to the given parameters.

  Args:
    width: The width of the grids.
    height: The height of the grids.
    brows: The row indices of the sprite points.
    bcols: The column indices of the sprite points.
    angles: The angles of the sprites.
    lengths: The lengths of the sprites.
    colors: The colors of the input grid.
  """

  def draw():
    talls, wides, rows, cols = [], [], [], []
    for brow, bcol, angle, length in zip(brows, bcols, angles, lengths):
      talls.append(length if angle in [0, 2] else (2 * length - 1))
      wides.append(length if angle in [1, 3] else (2 * length - 1))
      rows.append(brow)
      cols.append(bcol)
      if angle == 0:
        rows[-1] -= length - 1
        cols[-1] -= length - 1
      if angle == 1:
        rows[-1] -= length - 1
      if angle == 2:
        cols[-1] -= length - 1
      if angle == 3:
        rows[-1] -= length - 1
        cols[-1] -= length - 1
    if common.overlaps(rows, cols, wides, talls, 2): return None, None
    grid, output = common.grids(width, height)
    for i, color in enumerate(colors):
      output[i // width][i % width] = grid[i // width][i % width] = color
    for brow, bcol, angle, length in zip(brows, bcols, angles, lengths):
      left, right = False, False
      for i in range(length):
        good = False
        for j in range(-i, i + 1):
          if angle == 0: r, c = -i, j
          elif angle == 1: r, c = j, i
          elif angle == 2: r, c = i, j
          else: r, c = j, -i
          if common.get_pixel(output, r + brow, c + bcol) == 3:
            if j < 0: left = True
            if j > 0: right = True
            good = True
          else:
            common.draw(output, r + brow, c + bcol, 8)
        if i in [0, length - 1] and not good: return None, None
      if not left or not right: return None, None
    return grid, output

  if width is None:
    accepted = False
    for _ in range(_MAX_SIZE_TRIES):
      width, height = common.randint(10, 20), common.randint(10, 20)
      num_sprites = 1
      if width * height >= 150: num_sprites = 2
      if width * height >= 200: num_sprites = 3
      if width * height >= 250: num_sprites = 4
      for _ in range(_MAX_SCENE_TRIES):
        # Rows index height and columns index width (fixes swapped bounds).
        brows = common.randints(1, height - 2, num_sprites)
        bcols = common.randints(1, width - 2, num_sprites)
        angles = common.randints(0, 3, num_sprites)
        lengths = common.randints(3, 4, num_sprites)
        grid = common.grid(width, height)
        for row in range(height):
          for col in range(width):
            grid[row][col] = common.randint(0, 1)
        for brow, bcol, angle, length in zip(brows, bcols, angles, lengths):
          for i in range(length):
            for j in [-i, i]:
              if angle == 0:
                r, c = -i, j
              elif angle == 1:
                r, c = j, i
              elif angle == 2:
                r, c = i, j
              else:
                r, c = j, -i
              if common.randint(0, 4): common.draw(grid, r + brow, c + bcol, 3)
        colors = common.flatten(grid)
        grid, expected = draw()
        if not grid: continue
        try:
          answers = _visible_outputs(grid)
        except RuntimeError:
          continue
        if answers != {tuple(map(tuple, expected))}: continue
        accepted = True
        break
      if accepted: break
    if not accepted:
      raise RuntimeError("Bounded sampling failed to find an unambiguous scene")

  grid, output = draw()
  return {"input": grid, "output": output}


def validate():
  """Validates the generator."""
  train = [
      generate(width=12, height=15, brows=[5, 12], bcols=[3, 4], angles=[1, 2],
               lengths=[4, 3],
               colors=[1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0,
                       1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1,
                       1, 0, 0, 0, 0, 0, 3, 0, 1, 0, 1, 1,
                       1, 0, 0, 1, 0, 3, 0, 1, 1, 1, 1, 1,
                       1, 1, 1, 0, 3, 1, 0, 0, 1, 0, 1, 1,
                       0, 1, 1, 3, 1, 1, 1, 1, 0, 1, 0, 0,
                       0, 1, 0, 0, 3, 1, 0, 0, 1, 0, 0, 1,
                       1, 1, 1, 1, 1, 3, 0, 0, 1, 0, 0, 1,
                       0, 0, 1, 0, 0, 1, 3, 0, 1, 0, 1, 1,
                       1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0,
                       1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0,
                       1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0,
                       0, 1, 0, 0, 3, 1, 1, 0, 0, 0, 0, 1,
                       0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1,
                       0, 1, 3, 0, 0, 0, 3, 0, 0, 1, 1, 1]),
      generate(width=12, height=13, brows=[2, 8], bcols=[4, 5], angles=[2, 2],
               lengths=[3, 4],
               colors=[0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1,
                       1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1,
                       1, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 0,
                       0, 0, 1, 3, 1, 3, 0, 0, 0, 0, 0, 0,
                       1, 0, 3, 1, 1, 1, 3, 0, 1, 0, 1, 0,
                       1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0,
                       1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0,
                       0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0,
                       0, 0, 0, 0, 0, 3, 0, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 3, 0, 3, 0, 1, 0, 1, 0,
                       0, 0, 0, 3, 1, 0, 1, 1, 0, 0, 1, 0,
                       1, 0, 3, 1, 0, 1, 0, 0, 1, 0, 0, 1,
                       0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1]),
      generate(width=16, height=15, brows=[2, 10, 11], bcols=[5, 14, 5],
               angles=[2, 0, 1], lengths=[3, 3, 4],
               colors=[1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1,
                       1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                       1, 1, 1, 0, 0, 3, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0,
                       0, 0, 0, 0, 3, 1, 3, 0, 1, 1, 0, 0, 1, 1, 1, 0,
                       0, 1, 0, 3, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0,
                       1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1,
                       0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1,
                       1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0,
                       1, 0, 0, 1, 0, 0, 1, 1, 3, 0, 0, 0, 3, 1, 1, 0,
                       0, 1, 0, 1, 1, 0, 1, 3, 1, 1, 1, 0, 0, 3, 1, 3,
                       1, 0, 0, 0, 0, 1, 3, 0, 0, 0, 0, 1, 0, 0, 3, 0,
                       0, 0, 1, 0, 1, 3, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
                       1, 1, 0, 1, 1, 1, 3, 0, 0, 1, 1, 1, 1, 0, 0, 0,
                       0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1,
                       0, 1, 1, 1, 0, 0, 1, 1, 3, 1, 0, 1, 0, 1, 1, 1]),
  ]
  test = [
      generate(width=18, height=15, brows=[1, 5, 11, 12], bcols=[3, 15, 3, 6],
               angles=[2, 0, 3, 1], lengths=[3, 3, 3, 4],
               colors=[0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0,
                       1, 0, 1, 3, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0,
                       0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0,
                       0, 3, 0, 1, 0, 3, 1, 0, 1, 1, 0, 1, 0, 3, 1, 0, 0, 3,
                       0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 3, 0, 3, 0,
                       0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 3, 1, 0,
                       0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0,
                       1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0,
                       1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0,
                       1, 3, 0, 0, 1, 1, 0, 1, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 1, 3, 0, 0, 0, 1, 1, 3, 0, 1, 1, 0, 1, 0, 0, 1, 0,
                       0, 0, 0, 3, 0, 1, 1, 3, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0,
                       0, 0, 3, 1, 1, 0, 3, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0,
                       0, 1, 1, 0, 0, 1, 1, 3, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0,
                       1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1]),
  ]
  return {"train": train, "test": test}
