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

# Bounded rejection sampling for the random path.
_MAX_ATTEMPTS = 1000


def _render(arows, acols, brows, bcols, crows, ccols, rows, cols, width,
            height):
  """Draws a scene exactly as the original generator body did."""
  grid, output = common.grids(width, height)
  awide, bwide, cwide = max(acols) + 1, max(bcols) + 1, max(ccols) + 1
  for idx in range(len(rows)):
    row, col = rows[idx], cols[idx]
    for c in range(0, col, awide):
      for ar, ac in zip(arows, acols):
        output[row + ar][c + ac] = grid[row + ar][c + ac] = common.cyan()
    for br, bc in zip(brows, bcols):
      output[row + br][col + bc] = grid[row + br][col + bc] = common.cyan()
    for c in range(col + bwide, width, cwide):
      for cr, cc in zip(crows, ccols):
        if not idx:
          common.draw(grid, row + cr, c + cc, common.cyan())
          common.draw(output, row + cr, c + cc, common.cyan())
        else:
          common.draw(output, row + cr, c + cc, common.blue())
  return {"input": grid, "output": output}


# ---------------------------------------------------------------------------
# Uniqueness check: enumerate every explanation of the visible input inside a
# relaxed latent space that contains all generator latents (patterns up to
# 2 wide, band window up to 3 tall, reference boundary at most4 (sampled awide1..2 times1..2), band 0 is the
# reference). The check is independent of any solver's search order.
# Coordinates: u = column, v = row.
# ---------------------------------------------------------------------------


def _profile(cells, v0, s, lu):
  prof = [set() for _ in range(lu)]
  for u, v in cells:
    if v0 <= v < v0 + s:
      prof[u].add(v - v0)
  return [frozenset(p) for p in prof]


def _parse_ref(prof, aw, bw, cw, col0, lu):
  if not prof[aw - 1]:
    return None
  for u in range(col0):
    if prof[u] != prof[u % aw]:
      return None
  if not prof[col0 + bw - 1]:
    return None
  e = col0 + bw
  if not prof[e + cw - 1]:
    return None
  for u in range(e, lu):
    if prof[u] != prof[e + (u - e) % cw]:
      return None
  return prof[0:aw], prof[col0:e], prof[e:e + cw]


def _fit_shorts(rest, a, b, c_pat, aw, bw, cw, v0, s, lu, lv):
  ab_min = min(d for col in list(a) + list(b) for d in col)
  remaining = set(rest)
  prev = v0
  paint = set()
  while remaining:
    mv = min(v for _, v in remaining)
    base = mv - ab_min
    if base < prev + s + 1:
      return None
    band = set(p for p in remaining if p[1] < base + s)
    col = max(u for u, _ in band) - (bw - 1)
    if col < aw or col % aw:
      return None
    render = set()
    for c in range(0, col, aw):
      for j in range(aw):
        for d in a[j]:
          render.add((c + j, base + d))
    for j in range(bw):
      for d in b[j]:
        render.add((col + j, base + d))
    if render != band:
      return None
    e = col + bw
    for u in range(e, lu):
      for d in c_pat[(u - e) % cw]:
        if 0 <= base + d < lv:
          paint.add((u, base + d))
    remaining -= band
    prev = base
  return frozenset(paint)


def _explanations(cells, lu, lv):
  outs = []
  if not cells:
    return outs
  occupied = set(v for _, v in cells)
  v0 = min(occupied)
  for s in (1, 2, 3):
    if (v0 + s - 1) not in occupied:
      continue
    prof = _profile(cells, v0, s, lu)
    rest = set(p for p in cells if p[1] >= v0 + s)
    for aw in (1, 2):
      for bw in (1, 2):
        for cw in (1, 2):
          col0 = aw
          while col0 <= 4 and col0 + bw + cw <= lu:
            parsed = _parse_ref(prof, aw, bw, cw, col0, lu)
            if parsed is not None:
              paint = _fit_shorts(rest, parsed[0], parsed[1], parsed[2], aw,
                                  bw, cw, v0, s, lu, lv)
              if paint is not None:
                outs.append(paint)
            col0 += aw
  return outs


def _unambiguous(example, width, height):
  """True iff every visible explanation predicts exactly the drawn output."""
  grid, output = example["input"], example["output"]
  cells, painted = set(), set()
  for r in range(height):
    for c in range(width):
      if grid[r][c] == common.cyan():
        cells.add((c, r))
      if output[r][c] != grid[r][c]:
        painted.add((c, r))
  outs = _explanations(cells, width, height)
  return bool(outs) and set(outs) == {frozenset(painted)}


def generate(arows=None, acols=None, brows=None, bcols=None, crows=None,
             ccols=None, rows=None, cols=None, width=10, height=15):
  """Returns input and output grids according to the given parameters.

  Args:
    arows: a list of vertical coordinates where A pixels should be placed
    acols: a list of horizontal coordinates where A pixels should be placed
    brows: a list of vertical coordinates where B pixels should be placed
    bcols: a list of horizontal coordinates where B pixels should be placed
    crows: a list of vertical coordinates where C pixels should be placed
    ccols: a list of horizontal coordinates where C pixels should be placed
    rows: a list of vertical coordinates where patterns should be placed
    cols: a list of horizontal coordinates where patterns should be placed
    width: the width of the grid
    height: the height of the grid
  """
  if arows is not None:
    return _render(arows, acols, brows, bcols, crows, ccols, rows, cols,
                   width, height)
  for _ in range(_MAX_ATTEMPTS):
    tall = min(3, common.randint(1, 5))
    awide = common.randint(1, 2)
    bwide = common.randint(1, 2)
    cwide = common.randint(1, 2)
    apixels = common.all_pixels(awide, tall)
    bpixels = common.all_pixels(bwide, tall)
    cpixels = common.all_pixels(cwide, tall)
    apixels = common.sample(apixels, common.randint(1, len(apixels)))
    bpixels = common.sample(bpixels, common.randint(1, len(bpixels)))
    cpixels = common.sample(cpixels, common.randint(1, len(cpixels)))
    arows, acols = zip(*apixels)
    brows, bcols = zip(*bpixels)
    crows, ccols = zip(*cpixels)
    rows, cols, r = [], [], common.randint(1, 2)
    while r + tall < height:
      rows.append(r)
      cols.append(awide * common.randint(1, 2))
      r += common.randint(tall + 1, tall + 3)
    example = _render(arows, acols, brows, bcols, crows, ccols, rows, cols,
                      width, height)
    if _unambiguous(example, width, height):
      return example
  raise RuntimeError("could not sample an unambiguous scene")


def validate():
  """Validates the generator."""
  train = [
      generate(arows=[0], acols=[0], brows=[1], bcols=[0], crows=[2], ccols=[0],
               rows=[1, 6, 10], cols=[2, 3, 2]),
      generate(arows=[0], acols=[0], brows=[0], bcols=[0], crows=[0], ccols=[0],
               rows=[2, 6, 11, 13], cols=[2, 2, 3, 1]),
      generate(arows=[0, 1], acols=[0, 1], brows=[0], bcols=[0], crows=[0, 1],
               ccols=[1, 0], rows=[1, 6, 10], cols=[2, 2, 4]),
  ]
  test = [
      generate(arows=[1], acols=[0], brows=[0, 0, 2, 2], bcols=[0, 1, 0, 1],
               crows=[0, 2], ccols=[0, 0], rows=[1, 8], cols=[2, 3]),
  ]
  return {"train": train, "test": test}
