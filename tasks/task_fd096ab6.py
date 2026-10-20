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

"""ARC-GEN style generator for task fd096ab6.

Rule: the background is 1. One complete template figure is drawn in colour 4,
and colour 4 always has more cells than any fragment colour. Every other colour
is a fragment: a few cells of a copy of the template. The copy is translated
only, never rotated or mirrored. The output completes each fragment into a full
copy of the template in the fragment's colour. One colour may own two separate
fragments, and each one is completed into its own copy. Existing cells are
never erased.

Scope:
- Templates are random 8-connected shapes of 5..8 cells. Each shape fits in a
  box of 2..5 rows by 2..5 columns. Callers may supply their own shape, which
  must be normalised, 8-connected, two-dimensional and made of integer pairs.
- There are 1..7 fragment colours, drawn from {2,3,5,6,7,8,9}. Random scenes
  use 2..7 colours. One colour can optionally own two fragments.
- Each fragment has 2..4 cells, mostly 2..3. The fragment cells of any one
  colour total fewer than the template's cell count.
- Random grids are 14..30 per side. Larger-than-fixture and non-square sizes
  are synthetic extensions.
- Every object's bounding box is separated from the others by at least one
  background cell.
- Some copy boxes are deliberately placed against a grid border. Grid bounds
  can then be what rules out an otherwise equally good shift.
- In random scenes the four input corner cells stay background, as in every
  original example.
- The background (1) and the template colour (4) are fixed, as in every
  original example.
- A local check simulates greedy max-coverage completion. The scene is kept
  only if completion recovers exactly the intended copies, with ties allowed
  only between intended copies. It also requires count(1) > count(4) > every
  fragment colour's count.
- Explicit scenes (`copies=`) go through the same checks, except the corner
  rule, and invalid scenes raise ValueError.
"""

import random

import common

BG = 1
TEMPLATE_COLOR = 4
FRAG_COLORS = [2, 3, 5, 6, 7, 8, 9]


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _dims(shape):
  return (max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1)


def _connected(shape):
  cells = set(shape)
  start = next(iter(cells))
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        nb = (r + dr, c + dc)
        if nb in cells and nb not in seen:
          seen.add(nb)
          stack.append(nb)
  return len(seen) == len(cells)


def _random_shape():
  """Grow a random 8-connected shape by frontier growth."""
  for _ in range(200):
    n = random.randint(5, 8)
    bh = random.randint(2, 5)
    bw = random.randint(2, 5)
    if bh * bw < n + 1:
      continue
    cells = {(random.randrange(bh), random.randrange(bw))}
    while len(cells) < n:
      frontier = set()
      for r, c in cells:
        for dr in (-1, 0, 1):
          for dc in (-1, 0, 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < bh and 0 <= nc < bw and (nr, nc) not in cells:
              frontier.add((nr, nc))
      cells.add(random.choice(sorted(frontier)))
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    shape = sorted((r - r0, c - c0) for r, c in cells)
    h, w = _dims(shape)
    if h >= 2 and w >= 2:
      return shape
  raise RuntimeError("could not grow a two-dimensional template")


def _build(width, height, shape, template_pos, copies):
  grid = common.grid(width, height, BG)
  if len(grid) != height or len(grid[0]) != width:
    raise RuntimeError("common.grid returned unexpected dimensions")
  ty, tx = template_pos
  for r, c in shape:
    grid[ty + r][tx + c] = TEMPLATE_COLOR
  for color, oy, ox, frag in copies:
    for r, c in frag:
      grid[oy + r][ox + c] = color
  output = [row[:] for row in grid]
  for color, oy, ox, _ in copies:
    for r, c in shape:
      output[oy + r][ox + c] = color
  return grid, output


def _boxes_separated(boxes, sh, sw):
  for i in range(len(boxes)):
    r, c = boxes[i]
    for j in range(i):
      br, bc = boxes[j]
      if not (r >= br + sh + 1 or br >= r + sh + 1 or
              c >= bc + sw + 1 or bc >= c + sw + 1):
        return False
  return True


def _counts_ok(grid, n, copies):
  """Require count(BG) > count(template) > every fragment colour's count."""
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  tc = counts.get(TEMPLATE_COLOR, 0)
  if tc != n:
    return False
  frag_max = max(counts.get(cp[0], 0) for cp in copies)
  return counts.get(BG, 0) > tc > frag_max


def _corners_clear(grid):
  """Keep the four input corner cells background, as in every fixture."""
  h, w = len(grid), len(grid[0])
  return all(grid[r][c] == BG for r in (0, h - 1) for c in (0, w - 1))


def _unambiguous(grid, shape, copies):
  """Check that greedy max-coverage completion yields exactly the intended copies."""
  height, width = len(grid), len(grid[0])
  by_color = {}
  for color, oy, ox, _ in copies:
    by_color.setdefault(color, []).append((oy, ox))
  for color, intended in by_color.items():
    remaining = set()
    for r in range(height):
      for c in range(width):
        if grid[r][c] == color:
          remaining.add((r, c))
    unused = set(intended)
    for _ in range(len(intended) + 1):
      if not remaining:
        break
      cand = set()
      for fy, fx in remaining:
        for ry, rx in shape:
          cand.add((fy - ry, fx - rx))
      scores = {}
      for oy, ox in cand:
        ok = True
        cov = 0
        for ry, rx in shape:
          y, x = oy + ry, ox + rx
          if not (0 <= y < height and 0 <= x < width):
            ok = False
            break
          v = grid[y][x]
          if v != BG and v != color:
            ok = False
            break
          if (y, x) in remaining:
            cov += 1
        if ok and cov > 0:
          scores[(oy, ox)] = cov
      if not scores:
        return False
      best = max(scores.values())
      tied = [s for s, v in scores.items() if v == best]
      if any(s not in unused for s in tied):
        return False
      oy, ox = tied[0]
      unused.discard((oy, ox))
      for ry, rx in shape:
        remaining.discard((oy + ry, ox + rx))
    if remaining or unused:
      return False
  return True


def _place_boxes(width, height, sh, sw, count, first=None, edge_prob=0.0):
  """Place equal-size boxes with a one-cell gap. Search is exhaustive per box.

  With probability edge_prob, a copy box (never the template box) is first
  tried at positions touching the grid border.
  """
  boxes = []
  if first is not None:
    boxes.append(tuple(first))
  positions = [(r, c) for r in range(height - sh + 1)
               for c in range(width - sw + 1)]
  if not positions:
    return None
  edge = [(r, c) for r, c in positions
          if r == 0 or c == 0 or r == height - sh or c == width - sw]
  while len(boxes) < count:
    pools = [positions]
    if boxes and random.random() < edge_prob:
      pools = [edge, positions]
    found = None
    for pool in pools:
      random.shuffle(pool)
      for r, c in pool:
        if all(r >= br + sh + 1 or br >= r + sh + 1 or
               c >= bc + sw + 1 or bc >= c + sw + 1 for br, bc in boxes):
          found = (r, c)
          break
      if found is not None:
        break
    if found is None:
      return None
    boxes.append(found)
  return boxes


def _int_cells(cells, what):
  out = set()
  for cell in cells:
    if len(cell) != 2 or not all(_is_int(v) for v in cell):
      raise ValueError("%s cells must be (row, col) integer pairs" % what)
    out.add((cell[0], cell[1]))
  return sorted(out)


def _check_shape(shape, min_cells):
  shape = _int_cells(shape, "shape")
  if len(shape) < min_cells:
    raise ValueError("shape needs at least %d cells" % min_cells)
  if min(r for r, _ in shape) != 0 or min(c for _, c in shape) != 0:
    raise ValueError("shape must be normalised to its bounding-box corner")
  h, w = _dims(shape)
  if h < 2 or w < 2:
    raise ValueError("shape must be two-dimensional")
  if h > 30 or w > 30:
    raise ValueError("shape is too large")
  if not _connected(shape):
    raise ValueError("shape must be 8-connected")
  return shape


def _check_size(name, value):
  if not _is_int(value) or not 1 <= value <= 30:
    raise ValueError("%s must be an integer in 1..30" % name)


def _check_copies(copies, shape):
  copies = list(copies)
  if not copies:
    raise ValueError("copies must be non-empty")
  sset = set(shape)
  out = []
  for cp in copies:
    if len(cp) != 4:
      raise ValueError("each copy is (color, row, col, fragment)")
    color, oy, ox, frag = cp
    if not _is_int(color) or color not in FRAG_COLORS:
      raise ValueError("fragment colour must be one of %s" % FRAG_COLORS)
    if not _is_int(oy) or not _is_int(ox):
      raise ValueError("copy corner must be integers")
    cells = _int_cells(frag, "fragment")
    if not cells or any(cell not in sset for cell in cells):
      raise ValueError("fragment cells must be a nonempty subset of shape")
    out.append((color, oy, ox, cells))
  return out


def _sample_scene(width, height, shape, template_pos, num_colors, split_color):
  for _ in range(300):
    w = width if width is not None else random.randint(14, 30)
    h = height if height is not None else random.randint(14, 30)
    shp = shape if shape is not None else _random_shape()
    n = len(shp)
    sh, sw = _dims(shp)
    if sh > h or sw > w:
      continue
    if template_pos is not None and (template_pos[0] + sh > h or
                                     template_pos[1] + sw > w):
      continue
    k = num_colors if num_colors is not None else random.randint(2, 7)
    split = (split_color if split_color is not None
             else random.random() < 0.35)
    colors = random.sample(FRAG_COLORS, k)
    slots = list(colors)
    if split:
      slots.append(random.choice(colors))
    random.shuffle(slots)
    boxes = _place_boxes(w, h, sh, sw, len(slots) + 1, template_pos,
                         edge_prob=0.35)
    if boxes is None:
      continue
    tpos = boxes[0]
    for _ in range(30):
      copies = []
      totals = {}
      for color, (oy, ox) in zip(slots, boxes[1:]):
        size = min(random.choice([2, 2, 3, 3, 4]), n - 1)
        frag = sorted(random.sample(shp, size))
        copies.append((color, oy, ox, frag))
        totals[color] = totals.get(color, 0) + size
      if max(totals.values()) >= n:
        continue
      grid, _ = _build(w, h, shp, tpos, copies)
      if not _corners_clear(grid):
        continue
      if not _counts_ok(grid, n, copies):
        continue
      if _unambiguous(grid, shp, copies):
        return w, h, shp, tpos, copies
  raise RuntimeError("could not construct an unambiguous scene for the "
                     "requested parameters")


def generate(width=None, height=None, shape=None, template_pos=None,
             copies=None, num_colors=None, split_color=None):
  """Generate one input/output pair.

  Args:
    width: grid width (columns), 1..30. Random scenes use 14..30.
    height: grid height (rows), 1..30. Random scenes use 14..30.
    shape: template cells, relative to the template's bounding-box corner.
      Must be normalised, 8-connected and two-dimensional. Needs at least 5
      cells when sampling and at least 3 in explicit mode.
    template_pos: (row, col) of the colour-4 template's bounding-box corner.
    copies: list of (color, row, col, fragment) tuples. (row, col) is the
      corner of a copy, and fragment lists the relative template cells that
      are visible in the input. When given, width, height, shape and
      template_pos are all required, and num_colors and split_color must be
      None. The scene is checked for separation, colour-count ordering and
      unambiguous completion, and raises ValueError on failure.
    num_colors: number of distinct fragment colours (1..7) when sampling.
    split_color: when sampling, whether one colour owns two fragments.
  """
  if width is not None:
    _check_size("width", width)
  if height is not None:
    _check_size("height", height)
  if template_pos is not None:
    if len(template_pos) != 2 or not all(_is_int(v) for v in template_pos):
      raise ValueError("template_pos must be two integers")
    template_pos = (template_pos[0], template_pos[1])
    if template_pos[0] < 0 or template_pos[1] < 0:
      raise ValueError("template_pos must be non-negative")
    max_h = height if height is not None else 30
    max_w = width if width is not None else 30
    if template_pos[0] + 2 > max_h or template_pos[1] + 2 > max_w:
      raise ValueError("template_pos leaves no room for a template")
  if copies is not None:
    if None in (width, height, shape, template_pos):
      raise ValueError("explicit copies require width, height, shape and "
                       "template_pos")
    if num_colors is not None or split_color is not None:
      raise ValueError("num_colors/split_color only apply when sampling")
    shape = _check_shape(shape, 3)
    copies = _check_copies(copies, shape)
    sh, sw = _dims(shape)
    corners = [template_pos] + [(cp[1], cp[2]) for cp in copies]
    for oy, ox in corners:
      if oy < 0 or ox < 0 or oy + sh > height or ox + sw > width:
        raise ValueError("object out of bounds")
    if not _boxes_separated(corners, sh, sw):
      raise ValueError("object bounding boxes must be gap-separated")
    grid, output = _build(width, height, shape, template_pos, copies)
    if not _counts_ok(grid, len(shape), copies):
      raise ValueError("need count(bg) > count(template) > fragment counts")
    if not _unambiguous(grid, shape, copies):
      raise ValueError("fragments do not complete unambiguously")
    return {"input": grid, "output": output}
  if shape is not None:
    shape = _check_shape(shape, 5)
  if num_colors is not None and (not _is_int(num_colors) or
                                 not 1 <= num_colors <= len(FRAG_COLORS)):
    raise ValueError("num_colors must be in 1..7")
  if split_color is not None and not isinstance(split_color, bool):
    raise ValueError("split_color must be a bool")
  if shape is not None and template_pos is not None:
    sh, sw = _dims(shape)
    if (template_pos[0] + sh > (height if height is not None else 30) or
        template_pos[1] + sw > (width if width is not None else 30)):
      raise ValueError("template does not fit at template_pos")
  w, h, shp, tpos, cps = _sample_scene(width, height, shape, template_pos,
                                       num_colors, split_color)
  grid, output = _build(w, h, shp, tpos, cps)
  return {"input": grid, "output": output}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  s1 = [(0, 1), (0, 2), (0, 3), (1, 0), (1, 4), (2, 1), (3, 1), (3, 2)]
  s2 = [(0, 2), (0, 3), (1, 0), (1, 1), (2, 2)]
  s3 = [(0, 2), (1, 1), (1, 3), (2, 0), (2, 1), (2, 3)]
  train = [
      generate(width=24, height=24, shape=s1, template_pos=(4, 5), copies=[
          (6, 2, 16, [(2, 1), (3, 1), (3, 2)]),
          (7, 11, 16, [(0, 2), (0, 3), (1, 4)]),
          (8, 13, 4, [(0, 1), (1, 0)]),
          (3, 17, 11, [(0, 1), (0, 2), (0, 3)]),
      ]),
      generate(width=22, height=22, shape=s2, template_pos=(3, 6), copies=[
          (6, 7, 13, [(0, 2), (2, 2)]),
          (8, 10, 2, [(1, 1), (2, 2)]),
          (2, 14, 14, [(0, 2), (0, 3), (1, 1)]),
          (3, 16, 7, [(0, 2), (1, 1)]),
      ]),
  ]
  test = [
      generate(width=30, height=30, shape=s3, template_pos=(3, 5), copies=[
          (8, 1, 21, [(0, 2), (1, 1), (2, 1)]),
          (2, 3, 11, [(0, 2), (1, 1), (2, 0)]),
          (2, 19, 21, [(2, 0), (2, 1)]),
          (5, 8, 24, [(1, 1), (2, 0), (2, 1)]),
          (6, 10, 4, [(1, 1), (2, 1), (2, 3)]),
          (3, 11, 13, [(0, 2), (1, 3), (2, 3)]),
          (7, 19, 9, [(0, 2), (1, 3)]),
          (9, 21, 2, [(1, 3), (2, 1)]),
      ]),
  ]
  return {"train": train, "test": test}
