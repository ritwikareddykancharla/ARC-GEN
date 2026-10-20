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

"""ARC task 65b59efc: stamp motifs according to position maps.

The input is a lattice of k x k cells (period k+1) separated by dashed grey
(5) lines. Three rows of cells matter:
  * top row: cell j holds a one-colour k x k motif (colour M_j);
  * middle row: cell j holds a few pixels of one motif colour (a position map);
  * bottom strip (two rows): a paint colour P_j sits centred under column j
    (two pixels wide when k is even).
The output is a (k*k) x (k*k) grid of k x k blocks. Every pixel of colour c at
position (r, s) of any middle cell stamps the shape of the motif with colour c
into output block (r, s), painted with the paint colour of the column where
that motif lives. The column of the middle cell itself plays no role.

Scope: k in {3, 4, 5}; 2..6 columns, limited so the input width is at most 30
(more than four columns is a synthetic extension). Middle colours form a
random non-identity permutation of the motif colours, so the cross-column
lookup is always exercised. Position maps are nonempty and pairwise disjoint,
so the stamping order never matters. Optional trailing separator column,
zero padding on the right/bottom, and a few dropped separator dashes (never in
row 0) occur as in the original fixtures. Explicit arguments are checked for
consistency and rejected with ValueError if incompatible.
"""

import random

import common


COLORS = [1, 2, 3, 4, 6, 7, 8, 9]


def _max_cols(k):
  """Largest column count whose lattice fits in 30 columns."""
  return min(6, 31 // (k + 1))


def _dash(k, o):
  """Whether offset o inside a cell span carries a grey dash."""
  if k % 2:
    return o % 2 == 0
  return o == 0 or o == k - 1


def _to_mask(m):
  if isinstance(m, str):
    return [[int(ch) for ch in row] for row in m.split("/")]
  return [list(row) for row in m]


def _check_mask(m, k, what):
  if len(m) != k or any(len(row) != k for row in m):
    raise ValueError("%s must be %d x %d" % (what, k, k))
  if any(type(v) is not int or v not in (0, 1) for row in m for v in row):
    raise ValueError("%s must be binary" % what)
  if sum(map(sum, m)) == 0:
    raise ValueError("%s must be nonempty" % what)


def _random_mask(k):
  for _ in range(100):
    dens = random.uniform(0.45, 0.85)
    m = [[1 if random.random() < dens else 0 for _ in range(k)]
         for _ in range(k)]
    sym = random.random()
    if sym < 0.3:
      for r in range(k):
        for c in range(k // 2):
          m[r][k - 1 - c] = m[r][c]
    elif sym < 0.5:
      for r in range(k // 2):
        m[k - 1 - r] = list(m[r])
    if sum(map(sum, m)) >= 2:
      return m
  return [[1] * k for _ in range(k)]


def _random_motifs(k, n):
  masks = [_random_mask(k) for _ in range(n)]
  for _ in range(100):
    if len(set(str(m) for m in masks)) == n:
      break
    masks = [_random_mask(k) for _ in range(n)]
  return masks


def _random_maps(k, n):
  """Disjoint nonempty position maps, mostly 8-connected blobs."""
  allcells = [(r, c) for r in range(k) for c in range(k)]
  remaining = k * k - 1
  used = set()
  maps = []
  for i in range(n):
    hi = min(2 * k - 1, remaining - (n - i - 1))
    size = random.randint(1, max(1, hi))
    remaining -= size
    free = [rc for rc in allcells if rc not in used]
    start = random.choice(free)
    cells = [start]
    used.add(start)
    scatter = random.random() < 0.3
    while len(cells) < size:
      cand = []
      if not scatter:
        for (r, c) in cells:
          for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
              q = (r + dr, c + dc)
              if 0 <= q[0] < k and 0 <= q[1] < k and q not in used:
                if q not in cand:
                  cand.append(q)
      if not cand:
        cand = [rc for rc in allcells if rc not in used]
      q = random.choice(cand)
      cells.append(q)
      used.add(q)
    m = [[0] * k for _ in range(k)]
    for (r, c) in cells:
      m[r][c] = 1
    maps.append(m)
  return maps


def generate(k=None, n=None, motif_colors=None, motifs=None, paints=None,
             mid_colors=None, mid_maps=None, trailing=None, pad_w=None,
             pad_h=None, erased=None):
  """Build one input/output pair.

  Args:
    k: cell side (3, 4 or 5); inferred from masks if they are given.
    n: number of columns (2..max fitting in 30 columns).
    motif_colors: list of n distinct motif colours, one per column.
    motifs: list of n k x k masks (strings like "111/101/111" or lists).
    paints: list of n paint colours (bottom strip), one per column.
    mid_colors: colour of the pixels in each middle cell (motif colours).
    mid_maps: list of n nonempty, pairwise disjoint k x k position masks.
    trailing: whether a separator column follows the last column.
    pad_w: number of extra empty columns on the right.
    pad_h: number of extra empty rows at the bottom.
    erased: list of (row, col) separator dashes that are missing (row > 0).
  """
  if motifs is not None:
    motifs = [_to_mask(m) for m in motifs]
  if mid_maps is not None:
    mid_maps = [_to_mask(m) for m in mid_maps]
  if k is None:
    sizes = set(len(m) for m in (motifs or []) + (mid_maps or []))
    if len(sizes) > 1:
      raise ValueError("inconsistent mask sizes")
    k = sizes.pop() if sizes else random.choice([3, 4, 5])
  if type(k) is not int or k not in (3, 4, 5):
    raise ValueError("k must be 3, 4 or 5")
  p = k + 1
  cap = _max_cols(k)
  lengths = set(len(v) for v in (motif_colors, motifs, paints, mid_colors,
                                 mid_maps) if v is not None)
  if n is not None:
    if type(n) is not int:
      raise ValueError("n must be an integer")
    lengths.add(n)
  if len(lengths) > 1:
    raise ValueError("inconsistent column counts")
  if lengths:
    n = lengths.pop()
  else:
    n = min(cap, random.choice(list(range(2, cap + 1)) + [3, 3, 4]))
  if not 2 <= n <= cap:
    raise ValueError("column count must be in 2..%d for k=%d" % (cap, k))

  if motif_colors is None:
    motif_colors = random.sample(COLORS, n)
  motif_colors = list(motif_colors)
  if len(set(motif_colors)) != n or any(type(c) is not int or c not in COLORS
                                       for c in motif_colors):
    raise ValueError("motif colours must be distinct non-grey colours")
  if motifs is None:
    motifs = _random_motifs(k, n)
  for m in motifs:
    _check_mask(m, k, "motif")
  if paints is None:
    paints = random.sample(COLORS, n)
  paints = list(paints)
  if any(type(c) is not int or c not in COLORS for c in paints):
    raise ValueError("paint colours must be non-grey colours")
  if mid_colors is None:
    mid_colors = list(motif_colors)
    random.shuffle(mid_colors)
    if mid_colors == motif_colors:
      mid_colors = mid_colors[1:] + mid_colors[:1]
  mid_colors = list(mid_colors)
  if any(type(c) is not int or c not in motif_colors for c in mid_colors):
    raise ValueError("middle colours must be motif colours")
  if mid_maps is None:
    mid_maps = _random_maps(k, n)
  seen = set()
  for m in mid_maps:
    _check_mask(m, k, "position map")
    for r in range(k):
      for s in range(k):
        if m[r][s]:
          if (r, s) in seen:
            raise ValueError("position maps must be disjoint")
          seen.add((r, s))

  if trailing is None:
    trailing = n * p <= 30 and random.random() < 0.25
  elif type(trailing) is not bool:
    raise ValueError("trailing must be a boolean")
  struct_w = n * p - 1 + (1 if trailing else 0)
  if struct_w > 30:
    raise ValueError("lattice too wide")
  if pad_w is None:
    pad_w = 0
    if struct_w < 30 and random.random() < 0.35:
      pad_w = random.randint(1, min(8, 30 - struct_w))
  if pad_h is None:
    pad_h = random.choice([0, 0, 0, 1, 2])
  height = 2 * p + 2 + pad_h
  width = struct_w + pad_w
  if (type(pad_w) is not int or type(pad_h) is not int or
      pad_w < 0 or pad_h < 0 or width > 30 or height > 30):
    raise ValueError("padding out of range")

  g = common.grid(width, height, 0)
  for y in range(2 * p + 2):
    for x in range(struct_w):
      sep_col = x % p == k
      sep_row = y == k or y == 2 * p - 1
      if sep_col and sep_row:
        g[y][x] = 5
      elif sep_col:
        if _dash(k, y % p):
          g[y][x] = 5
      elif sep_row:
        if _dash(k, x % p):
          g[y][x] = 5
  if erased is None:
    erased = []
    if random.random() < 0.25:
      fives = [(y, x) for y in range(1, 2 * p + 2) for x in range(struct_w)
               if g[y][x] == 5]
      erased = random.sample(fives, random.randint(1, 2))
  for (y, x) in erased:
    if not (type(y) is int and type(x) is int and
            1 <= y < 2 * p + 2 and 0 <= x < struct_w) or g[y][x] != 5:
      raise ValueError("erased cells must be separator dashes below row 0")
  for (y, x) in erased:
    g[y][x] = 0
  for j in range(n):
    x0 = j * p
    for r in range(k):
      for s in range(k):
        if motifs[j][r][s]:
          g[r][x0 + s] = motif_colors[j]
        if mid_maps[j][r][s]:
          g[p + r][x0 + s] = mid_colors[j]
    if k % 2:
      g[2 * p + 1][x0 + k // 2] = paints[j]
    else:
      g[2 * p + 1][x0 + k // 2 - 1] = paints[j]
      g[2 * p + 1][x0 + k // 2] = paints[j]

  out = common.grid(k * k, k * k, 0)
  for j in range(n):
    mj = motif_colors.index(mid_colors[j])
    for r in range(k):
      for s in range(k):
        if not mid_maps[j][r][s]:
          continue
        for a in range(k):
          for b in range(k):
            if motifs[mj][a][b]:
              out[r * k + a][s * k + b] = paints[mj]
  return {"input": g, "output": out}


def validate():
  """Reconstruct the original fixtures from explicit latent parameters."""
  train = [
      generate(k=3, motif_colors=[2, 1, 4],
               motifs=["111/111/111", "111/101/111", "111/010/111"],
               paints=[6, 7, 1], mid_colors=[2, 4, 1],
               mid_maps=["000/000/100", "011/001/000", "100/010/001"],
               trailing=False, pad_w=0, pad_h=0, erased=[]),
      generate(k=3, motif_colors=[1, 2, 4],
               motifs=["010/111/010", "111/101/111", "101/111/010"],
               paints=[7, 9, 3], mid_colors=[2, 4, 1],
               mid_maps=["000/000/110", "100/100/000", "001/001/000"],
               trailing=False, pad_w=0, pad_h=0, erased=[]),
      generate(k=5, motif_colors=[1, 2, 4],
               motifs=["11101/10111/11101/10001/11111",
                       "11111/01010/10101/10101/11111",
                       "01001/11111/01001/01111/11011"],
               paints=[3, 8, 6], mid_colors=[4, 1, 2],
               mid_maps=["10000/10000/11000/01100/00100",
                         "00000/00000/00000/10000/11000",
                         "01111/01100/00000/00000/00000"],
               trailing=False, pad_w=0, pad_h=0, erased=[(8, 11)]),
  ]
  test = [
      generate(k=5, motif_colors=[8, 2, 7, 4],
               motifs=["11111/11001/10001/10011/11111",
                       "10101/11111/10101/11111/10101",
                       "11001/11111/01110/01111/11011",
                       "11111/11111/00100/01110/11111"],
               paints=[3, 4, 1, 6], mid_colors=[7, 2, 8, 4],
               mid_maps=["00011/00001/00000/00000/00000",
                         "00100/00110/00011/00000/00000",
                         "10000/10000/10000/10000/11111",
                         "00000/00000/01100/01100/00000"],
               trailing=False, pad_w=7, pad_h=2, erased=[]),
      generate(k=4, motif_colors=[6, 4, 3, 1],
               motifs=["1111/1011/1001/1111", "0110/1111/1111/0110",
                       "1100/1110/0111/0011", "1001/1111/1111/1001"],
               paints=[1, 9, 8, 7], mid_colors=[6, 3, 4, 1],
               mid_maps=["0110/0000/1111/0000", "1001/0110/0000/0000",
                         "0000/0000/0000/1111", "0000/1001/0000/0000"],
               trailing=True, pad_w=0, pad_h=0,
               erased=[(3, 19), (4, 18), (5, 19)]),
  ]
  return {"train": train, "test": test}
