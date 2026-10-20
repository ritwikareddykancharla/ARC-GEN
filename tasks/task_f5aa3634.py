"""Generator for ARC task f5aa3634: crop the cluster that appears twice.

Rule
----
The input has a 0 background and several small multicoloured clusters. A
cluster is an 8-connected group of non-zero cells. Diagonal touches count, and
any mix of the colours 1..9 is allowed. Every cluster picture is unique except
one, which is painted twice at two different places, identical pixel for
pixel. The output is the bounding-box crop of that repeated cluster.
Background cells inside the box stay 0.

Scope
-----
Random generation samples these latent variables:
  * the number of distinct pictures: 3..7 by default, 2..10 on request. The
    count is reduced when the sampled grid cannot hold it;
  * the grid height and width. The default floor depends on the number of
    pictures (max(8, 2 + 2n)). Explicit sizes may be 2..30 per side when
    sampling. Sides outside the fixture range 10..15 are synthetic extensions;
  * random 8-connected blobs, 2..5 cells per side. Each blob spans its own
    bounding box and uses 2..4 colours. Fill density varies, so some blobs are
    joined only through a diagonal, matching the reference's 8-connectivity.
    The `diagonal` control can force this for the repeated picture, or forbid
    it for every picture;
  * placements whose bounding boxes are at least one empty row or column
    apart. A full empty row or column also rules out diagonal contact;
  * an optional hard-negative distractor derived from the answer. It is one
    of three kinds: a one-cell recolour (any other colour 1..9), a one-cell
    silhouette edit (add or remove a cell), or a rotation/reflection of the
    answer. A forced kind is always realised; it is never silently swapped
    for a different kind. The distractor is always distinct from every other
    picture, so the only exact repeat is the true answer.

Not supported:
  * duplicates that are equal only up to rotation, reflection or recolouring.
    These appear only as distractors and never count as repeats;
  * more than one repeated picture;
  * clusters whose bounding boxes touch or overlap;
  * non-zero backgrounds;
  * 1 x N clusters in random sampling. Explicit mode accepts them, with sides
    1..30.

The fixtures themselves only contain 4-connected clusters. 8-connectivity is
assumed from the reference rule, and this generator exercises it.

Copyright 2026 Ritwika Kancharla
Licensed under the Apache License, Version 2.0.
"""

import random

import common

_KINDS = ("recolour", "silhouette", "transform")


def _box_separated(a, b):
  """True if boxes (r0, c0, r1, c1) leave a gap of >= 1 empty row or column."""
  ar0, ac0, ar1, ac1 = a
  br0, bc0, br1, bc1 = b
  rows_apart = ar1 + 1 < br0 or br1 + 1 < ar0
  cols_apart = ac1 + 1 < bc0 or bc1 + 1 < ac0
  return rows_apart or cols_apart


def _neighbours(r, c, height, width, diag=True):
  """Yields the in-bounds 8-neighbours (or 4-neighbours) of (r, c)."""
  for dr in (-1, 0, 1):
    for dc in (-1, 0, 1):
      if dr == 0 and dc == 0:
        continue
      if not diag and dr != 0 and dc != 0:
        continue
      rr, cc = r + dr, c + dc
      if 0 <= rr < height and 0 <= cc < width:
        yield rr, cc


def _cells(shape):
  """Set of filled (row, col) cells of a picture."""
  return set((r, c) for r, row in enumerate(shape)
             for c, v in enumerate(row) if v)


def _connected(cells, height, width, diag):
  """True if the cell set is one component under the chosen adjacency."""
  if not cells:
    return False
  start = min(cells)
  seen = {start}
  stack = [start]
  while stack:
    r, c = stack.pop()
    for nb in _neighbours(r, c, height, width, diag):
      if nb in cells and nb not in seen:
        seen.add(nb)
        stack.append(nb)
  return seen == cells


def _is_4connected(shape):
  """True if the picture is a single 4-connected component."""
  return _connected(_cells(shape), len(shape), len(shape[0]), False)


def _shape_error(shape):
  """Returns None for a valid tight 8-connected picture, else a message."""
  if (not isinstance(shape, (list, tuple)) or not shape or
      not isinstance(shape[0], (list, tuple)) or not shape[0]):
    return "empty shape"
  h, w = len(shape), len(shape[0])
  for row in shape:
    if not isinstance(row, (list, tuple)) or len(row) != w:
      return "shape rows must have equal length"
    for v in row:
      if type(v) is not int or v < 0 or v > 9:
        return "shape values must be integers 0..9"
  if not any(shape[0]) or not any(shape[-1]):
    return "shape must fill its bounding box rows"
  if not any(row[0] for row in shape) or not any(row[-1] for row in shape):
    return "shape must fill its bounding box columns"
  if not _connected(_cells(shape), h, w, True):
    return "shape must be 8-connected"
  return None


def _check_shape(shape):
  """Raises ValueError unless shape is a valid tight 8-connected cluster."""
  err = _shape_error(shape)
  if err:
    raise ValueError(err)


def _colour(cells, height, width):
  """Paints a cell set with 2..4 colours, each colour used at least once."""
  ncol = random.randint(2, max(2, min(4, len(cells))))
  palette = random.sample(range(1, 10), ncol)
  shape = [[0] * width for _ in range(height)]
  order = sorted(cells)
  random.shuffle(order)
  for i, (r, c) in enumerate(order):
    shape[r][c] = palette[i] if i < ncol else random.choice(palette)
  return shape


def _random_shape(height, width):
  """Grows an 8-connected multicolour blob that spans a height x width box.

  Growth always terminates because each step adds one cell. In the worst case
  the whole box is filled, which spans it trivially. A sparse fill fraction
  makes diagonal-only junctions possible.
  """
  area = height * width
  frac = random.choice((0.3, 0.45, 0.6, 0.75))
  lo = min(area, max(3, int(area * frac + 0.999)))
  target = random.randint(lo, area)
  cells = {(random.randrange(height), random.randrange(width))}

  def spans():
    rows = set(r for r, _ in cells)
    cols = set(c for _, c in cells)
    return (0 in rows and height - 1 in rows and 0 in cols and
            width - 1 in cols)

  for _ in range(area):
    if spans() and len(cells) >= target:
      break
    frontier = set()
    for (r, c) in cells:
      for nb in _neighbours(r, c, height, width):
        if nb not in cells:
          frontier.add(nb)
    if not frontier:
      break
    cells.add(random.choice(sorted(frontier)))
  return _colour(cells, height, width)


def _staircase(height, width):
  """Spanning blob joined only diagonally at its start.

  The blob runs along the main or anti-diagonal, chosen at random.
  """
  k = min(height, width)
  cells = set((i, i) for i in range(k))
  if height > width:
    cells |= set((r, width - 1) for r in range(k, height))
  elif width > height:
    cells |= set((height - 1, c) for c in range(k, width))
  if random.random() < 0.5:
    cells = set((r, width - 1 - c) for r, c in cells)
  return _colour(cells, height, width)


def _make_shape(height, width, diagonal):
  """Random blob; diagonal True needs a diagonal-only link, False forbids it."""
  if diagonal is True and height == 2 and width == 2:
    # Any 3+ cells of a 2x2 box are 4-connected; only a diagonal pair works.
    return _staircase(height, width)
  for _ in range(60):
    sh = _random_shape(height, width)
    four = _is_4connected(sh)
    if (diagonal is None or (diagonal is True and not four) or
        (diagonal is False and four)):
      return sh
  if diagonal is True:
    return _staircase(height, width)
  full = set((r, c) for r in range(height) for c in range(width))
  return _colour(full, height, width)


def _transforms(shape):
  """All rotations and reflections of a picture (including itself)."""
  out = []
  cur = [list(row) for row in shape]
  for _ in range(4):
    out.append(cur)
    out.append([list(row)[::-1] for row in cur])
    cur = [list(row) for row in zip(*cur[::-1])]
  return out


def _variant(shape, kind, height, width):
  """Hard-negative copy of shape of the given kind, or None if impossible."""
  h, w = len(shape), len(shape[0])
  cells = sorted(_cells(shape))
  if kind == "transform":
    cands = [t for t in _transforms(shape)
             if t != shape and len(t) <= height and len(t[0]) <= width]
    return random.choice(cands) if cands else None
  if kind == "silhouette":
    palette = sorted(set(v for row in shape for v in row if v))
    empties = [(r, c) for r in range(h) for c in range(w) if not shape[r][c]]
    for _ in range(40):
      new = [list(row) for row in shape]
      if empties and (len(cells) <= 3 or random.random() < 0.5):
        r, c = random.choice(empties)
        new[r][c] = random.choice(palette)
      else:
        r, c = random.choice(cells)
        new[r][c] = 0
      if new != shape and len(_cells(new)) >= 2 and _shape_error(new) is None:
        return new
    return None
  new = [list(row) for row in shape]
  r, c = random.choice(cells)
  new[r][c] = random.choice([k for k in range(1, 10) if k != shape[r][c]])
  return new


def _max_pictures(height, width):
  """Upper bound on distinct pictures (placements - 1) for a grid size.

  Each placement, padded by its one-cell gap, occupies a disjoint box of at
  least 3x3 inside a (height+1) x (width+1) area. A line sweep bounds the
  packing. Each placement also needs at least two cells, and the sampler
  keeps filled*3 <= height*width.
  """
  a, b = height + 1, width + 1
  slots = min((a // 3) * b, (b // 3) * a) // 3
  dens = (height * width) // 6
  return min(slots, dens) - 1


def _place(order, shapes, height, width):
  """Places shapes in order; returns a (shape_index, row, col) list or None."""
  boxes = []
  placements = []
  for idx in order:
    sh = shapes[idx]
    h, w = len(sh), len(sh[0])
    if h > height or w > width:
      return None
    placed = False
    for _ in range(80):
      r = random.randint(0, height - h)
      c = random.randint(0, width - w)
      box = (r, c, r + h - 1, c + w - 1)
      if all(_box_separated(box, other) for other in boxes):
        boxes.append(box)
        placements.append((idx, r, c))
        placed = True
        break
    if not placed:
      return None
  return placements


def _sample_scene(width, height, num_shapes, distractor, diagonal):
  """Samples dims, distinct pictures (one duplicated) and placements.

  Honours any of width, height, num_shapes, distractor and diagonal given.
  """
  if (height is not None and height < 2) or (width is not None and width < 2):
    raise ValueError("sampled scenes need width and height >= 2")
  cap_h = height if height is not None else 30
  cap_w = width if width is not None else 30
  n_cap = _max_pictures(cap_h, cap_w)
  if n_cap < 2:
    raise ValueError("requested width/height too small for any scene")
  if num_shapes is not None and num_shapes > n_cap:
    raise ValueError("num_shapes cannot fit in the requested width/height")

  for _ in range(400):
    n0 = num_shapes if num_shapes is not None else random.randint(3, 7)
    lo = min(30, max(8, 2 + 2 * n0))
    hi = min(30, lo + 12)
    if height is not None:
      h = height
    else:
      h = random.randint(lo, 30 if (width is not None and width < lo) else hi)
    if width is not None:
      w = width
    else:
      w = random.randint(lo, 30 if (height is not None and height < lo) else hi)
    fit = _max_pictures(h, w)
    if num_shapes is not None:
      if fit < num_shapes:
        continue
      n = num_shapes
    else:
      n = min(n0, fit)
      if n < 2:
        continue
    if distractor is None:
      kind = random.choice(_KINDS) if random.random() < 0.45 else None
    elif distractor is True:
      kind = random.choice(_KINDS)
    elif distractor is False:
      kind = None
    else:
      kind = distractor
    others_diag = False if diagonal is False else None
    n_base = n - 1 if kind else n
    shapes = []
    keys = set()
    for _ in range(40 * n):
      if len(shapes) >= n_base:
        break
      mode = diagonal if not shapes else others_diag
      sh = _make_shape(random.randint(2, min(5, h)),
                       random.randint(2, min(5, w)), mode)
      key = tuple(map(tuple, sh))
      if key in keys:
        continue
      keys.add(key)
      shapes.append(sh)
    if len(shapes) < n_base:
      continue
    dup = 0
    if kind:
      near = _variant(shapes[dup], kind, h, w)
      if near is None:
        continue
      key = tuple(map(tuple, near))
      if key in keys:
        continue
      if diagonal is False and not _is_4connected(near):
        continue
      keys.add(key)
      shapes.append(near)
    order = list(range(len(shapes))) + [dup]
    random.shuffle(order)
    placements = _place(order, shapes, h, w)
    if placements is None:
      continue
    filled = 0
    for idx, _, _ in placements:
      filled += sum(1 for row in shapes[idx] for v in row if v != 0)
    if filled * 3 > h * w:
      continue
    return h, w, shapes, placements
  raise ValueError("could not fit a valid f5aa3634 scene with the requested "
                   "width/height/num_shapes")


def generate(width=None, height=None, shapes=None, placements=None,
             num_shapes=None, distractor=None, diagonal=None):
  """Returns {"input": grid, "output": grid} for one f5aa3634 scene.

  Args:
    width: grid width (columns). Integer 2..30 when sampling, 1..30 in
      explicit mode. Required when shapes/placements are given.
    height: grid height (rows). Same rules as width.
    shapes: list of at least two pairwise distinct cluster pictures. Each
      picture is a list of rows, with 0 for holes. Every picture must be
      8-connected and tight to its bounding box. Must be given together with
      placements.
    placements: list of (shape_index, row, col) integer triples. Exactly one
      index appears twice and every other index appears once. Placed bounding
      boxes must be separated by at least one empty row or column.
    num_shapes: number of distinct pictures to sample, integer 2..10. It
      counts the distractor if there is one. If given with explicit shapes,
      it must equal len(shapes).
    distractor: when sampling, None means random. True forces a hard negative
      of a random kind, and False forbids one. The string 'recolour',
      'silhouette' or 'transform' forces that kind. Only None, a real bool or
      one of those strings is accepted. Not allowed with explicit shapes.
    diagonal: when sampling, None means natural random shapes. True forces the
      repeated picture to be joined somewhere only through a diagonal. False
      makes every picture 4-connected. Must be None or a real bool. Not
      allowed with explicit shapes.
  With all arguments None, a fresh random scene is sampled.
  """
  for name, v in (("width", width), ("height", height)):
    if v is not None and (type(v) is not int or v < 1 or v > 30):
      raise ValueError(name + " must be an integer in 1..30")
  if num_shapes is not None and (type(num_shapes) is not int or
                                 num_shapes < 2 or num_shapes > 10):
    raise ValueError("num_shapes must be an integer in 2..10")
  if not (distractor is None or type(distractor) is bool or
          (isinstance(distractor, str) and distractor in _KINDS)):
    raise ValueError("distractor must be None, a bool or one of " +
                     ", ".join(_KINDS))
  if not (diagonal is None or type(diagonal) is bool):
    raise ValueError("diagonal must be None or a bool")
  if (shapes is None) != (placements is None):
    raise ValueError("shapes and placements must be given together")

  if shapes is None:
    height, width, shapes, placements = _sample_scene(
        width, height, num_shapes, distractor, diagonal)
  else:
    if width is None or height is None:
      raise ValueError("explicit shapes need explicit width and height")
    if distractor is not None or diagonal is not None:
      raise ValueError("distractor/diagonal only apply to random sampling")
    if not isinstance(shapes, (list, tuple)) or len(shapes) < 2:
      raise ValueError("shapes must be a list of at least two pictures")
    if num_shapes is not None and num_shapes != len(shapes):
      raise ValueError("num_shapes disagrees with len(shapes)")
    for sh in shapes:
      _check_shape(sh)
    if not isinstance(placements, (list, tuple)):
      raise ValueError("placements must be a list")
    for p in placements:
      if (not isinstance(p, (list, tuple)) or len(p) != 3 or
          any(type(x) is not int for x in p)):
        raise ValueError("each placement must be (index, row, col) ints")

  counts = {}
  for idx, _, _ in placements:
    if not 0 <= idx < len(shapes):
      raise ValueError("placement shape index out of range")
    counts[idx] = counts.get(idx, 0) + 1
  repeated = [idx for idx, n in counts.items() if n == 2]
  if len(repeated) != 1 or any(n > 2 for n in counts.values()):
    raise ValueError("exactly one shape must be placed twice")
  if len(counts) != len(shapes):
    raise ValueError("every shape must be placed")
  keys = set(tuple(map(tuple, sh)) for sh in shapes)
  if len(keys) != len(shapes):
    raise ValueError("shapes must be pairwise distinct")

  boxes = []
  filled = 0
  for idx, r, c in placements:
    sh = shapes[idx]
    box = (r, c, r + len(sh) - 1, c + len(sh[0]) - 1)
    if r < 0 or c < 0 or box[2] >= height or box[3] >= width:
      raise ValueError("placement outside the grid")
    if not all(_box_separated(box, other) for other in boxes):
      raise ValueError("placements must not touch")
    boxes.append(box)
    filled += sum(1 for row in sh for v in row if v != 0)
  if filled * 2 >= height * width:
    raise ValueError("background 0 must remain the majority colour")

  grid = common.grid(width, height, 0)
  for idx, r, c in placements:
    sh = shapes[idx]
    for dr, row in enumerate(sh):
      for dc, v in enumerate(row):
        if v != 0:
          grid[r + dr][c + dc] = v

  output = [list(row) for row in shapes[repeated[0]]]
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical train/test pairs through explicit calls."""
  train = [
      generate(
          width=13, height=15,
          shapes=[
              [[0, 1, 1], [2, 2, 8], [3, 2, 8], [3, 0, 0]],
              [[0, 1, 1], [1, 2, 0], [0, 2, 0]],
              [[0, 8, 0], [8, 8, 8], [5, 5, 5]],
              [[0, 0, 8], [0, 6, 8], [6, 6, 8], [0, 4, 4], [0, 4, 0]],
          ],
          placements=[(0, 1, 1), (1, 4, 6), (2, 6, 2), (2, 11, 2),
                      (3, 10, 8)]),
      generate(
          width=13, height=10,
          shapes=[
              [[0, 5, 8, 8], [3, 5, 3, 8], [0, 3, 3, 0]],
              [[0, 7, 0], [7, 7, 2], [0, 2, 2]],
              [[3, 5, 2], [2, 2, 0], [3, 2, 0]],
          ],
          placements=[(0, 0, 1), (1, 2, 9), (2, 5, 2), (0, 6, 8)]),
      generate(
          width=15, height=15,
          shapes=[
              [[0, 2, 8], [0, 8, 2], [8, 8, 0]],
              [[0, 0, 5, 9], [7, 7, 5, 9], [0, 5, 7, 0]],
              [[0, 0, 6], [0, 6, 6], [3, 3, 3]],
              [[0, 4, 0], [3, 4, 3], [0, 4, 0]],
          ],
          placements=[(0, 0, 1), (1, 0, 9), (2, 4, 6), (3, 9, 1),
                      (1, 11, 10)]),
  ]
  test = [
      generate(
          width=15, height=15,
          shapes=[
              [[0, 0, 8, 8], [8, 5, 5, 8]],
              [[5, 5, 5], [5, 9, 5], [0, 9, 0]],
              [[3, 8, 3], [3, 4, 3], [0, 4, 0], [0, 4, 0]],
              [[2, 2, 0], [7, 2, 0], [0, 7, 7], [0, 0, 7]],
              [[0, 2], [1, 2], [1, 1]],
          ],
          placements=[(0, 1, 10), (1, 2, 3), (2, 5, 7), (3, 8, 1),
                      (2, 9, 11), (4, 11, 7)]),
  ]
  return {"train": train, "test": test}
