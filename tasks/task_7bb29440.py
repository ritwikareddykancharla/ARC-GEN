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

"""ARC task 7bb29440: crop the rectangle with the fewest special cells.

Rule:
  The input is a black (0) canvas holding several solid blue (1) rectangles.
  No two rectangles touch, not even diagonally. Each rectangle contains a few
  single "special" cells coloured yellow (4) or magenta (6). The output is an
  exact crop of the rectangle with the fewest special cells. Cells are counted
  individually: two special cells that touch still count as two.

Scope:
  Canvas width and height are each sampled from 10..30. Either can be set
  explicitly to 3..30, but the canvas must be able to hold the requested number
  of separated rectangles while staying mostly black. Infeasible requests
  raise ValueError early. Rare tight requests can also exhaust the bounded
  sampler, which then raises ValueError. Scenes hold 2..7 rectangles, each
  3..10 cells per side. Rectangles may touch the canvas border.

  Each random rectangle holds at most floor(area / 3) specials. This reaches
  the fixture density of 3 specials in a 3x3 rectangle and keeps blue strictly
  dominant inside every rectangle. Random specials are usually not
  4-adjacent. Some scenes contain touching specials, as the canvas test input
  does. Some scenes also include a "blob decoy": a runner-up with one more
  special cell than the winner, three of which form a straight run. That
  decoy has fewer connected special blobs than the winner, so counting blobs
  instead of cells picks the wrong rectangle.

  Black stays strictly the most frequent canvas colour, as in every
  demonstration. Random scenes cover strictly less than half the canvas with
  rectangles. The winning count is always a strict unique minimum. When
  rectangles are passed explicitly, a tied minimum is rejected, because the
  training pairs never show how a tie is broken. About half of the other
  random scenes contain a runner-up with exactly one more special. Background
  black, main colour blue and the special colours {4, 6} are fixed, as in
  the task.
"""

import random

import common


_SPECIAL_COLORS = (4, 6)
_NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_EIGHT = tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)


def _is_int(value):
  return isinstance(value, int) and not isinstance(value, bool)


def _render(width, height, rects):
  """Draws the rectangles (top, left, h, w, specials) on a black canvas."""
  grid = common.grid(width, height, 0)
  for top, left, h, w, specials in rects:
    for r in range(top, top + h):
      for c in range(left, left + w):
        grid[r][c] = 1
    for dr, dc, color in specials:
      grid[top + dr][left + dc] = color
  return grid


def _separated(a, b):
  """True if boxes (top, left, h, w) leave a gap of at least one cell."""
  ta, la, ha, wa = a[:4]
  tb, lb, hb, wb = b[:4]
  row_gap = ta + ha < tb or tb + hb < ta
  col_gap = la + wa < lb or lb + wb < la
  return row_gap or col_gap


def _check_rects(width, height, rects):
  """Validates a latent scene and returns the index of the winning rectangle.

  Raises ValueError in these cases:
    the geometry or the specials are malformed or not integers;
    a rectangle is out of bounds;
    two rectangles touch or overlap, diagonal contact included;
    blue is not dominant in some rectangle;
    black is not strictly the most frequent canvas colour;
    the minimum special count is tied.
  """
  if len(rects) < 2:
    raise ValueError("need at least two rectangles")
  totals = {0: width * height, 1: 0, 4: 0, 6: 0}
  for rect in rects:
    if not isinstance(rect, (list, tuple)) or len(rect) != 5:
      raise ValueError("rectangle must be (top, left, h, w, specials)")
    top, left, h, w, specials = rect
    if not all(_is_int(v) for v in (top, left, h, w)):
      raise ValueError("rectangle geometry must be integers")
    if h < 1 or w < 1 or top < 0 or left < 0:
      raise ValueError("bad rectangle geometry")
    if top + h > height or left + w > width:
      raise ValueError("rectangle exceeds canvas")
    seen = set()
    for special in specials:
      if not isinstance(special, (list, tuple)) or len(special) != 3:
        raise ValueError("special must be (dr, dc, color)")
      dr, dc, color = special
      if not (_is_int(dr) and _is_int(dc) and _is_int(color)):
        raise ValueError("special offsets and colour must be integers")
      if not (0 <= dr < h and 0 <= dc < w):
        raise ValueError("special cell outside its rectangle")
      if (dr, dc) in seen:
        raise ValueError("duplicate special cell")
      if color not in _SPECIAL_COLORS:
        raise ValueError("special colour must be 4 or 6")
      seen.add((dr, dc))
      totals[color] += 1
    if h * w - len(specials) <= len(specials):
      raise ValueError("blue must dominate every rectangle")
    totals[0] -= h * w
    totals[1] += h * w - len(specials)
  if any(totals[0] <= totals[c] for c in (1, 4, 6)):
    raise ValueError("black must be the most frequent canvas colour")
  for i in range(len(rects)):
    for j in range(i + 1, len(rects)):
      if not _separated(rects[i], rects[j]):
        raise ValueError("rectangles overlap or touch")
  counts = [len(rect[4]) for rect in rects]
  low = min(counts)
  if counts.count(low) != 1:
    raise ValueError("minimum special count is tied (ambiguous)")
  return counts.index(low)


def _fit_bound(wd, ht):
  """Upper bound on how many separated 3x3+ rectangles a canvas can hold.

  Two constraints apply. The rectangles must cover strictly less than half
  the canvas, so 18 * n < wd * ht. Disjoint 4x4 footprints (one box plus its
  half-gap) must fit, so n <= floor((wd+1)/4)*floor((ht+1)/4). Two boxes also need
  one side of length 7 or more.
  """
  if min(wd, ht) < 3 or max(wd, ht) < 7:
    return 0
  n = 7
  while n >= 2 and not (18 * n < wd * ht
                        and n <= ((wd + 1) // 4) * ((ht + 1) // 4)):
    n -= 1
  return n if n >= 2 else 0


def _place_boxes(wd, ht, n):
  """Places n separated boxes covering under half the canvas, or None."""
  boxes = []
  covered = 0
  for _ in range(n):
    placed = False
    for t in range(80):
      shrink = t // 10
      h = random.randint(3, max(3, min(10, ht) - shrink))
      w = random.randint(3, max(3, min(10, wd) - shrink))
      if h > ht or w > wd:
        continue
      if 2 * (covered + h * w) >= wd * ht:
        continue
      top = random.randint(0, ht - h)
      left = random.randint(0, wd - w)
      box = (top, left, h, w)
      if all(_separated(box, other) for other in boxes):
        boxes.append(box)
        covered += h * w
        placed = True
        break
    if not placed:
      return None
  return boxes


def _place_specials(h, w, count, mode):
  """Picks `count` special cells in an h x w box, or returns None.

  Modes:
    sep: no two specials are 8-adjacent.
    free: if count >= 2, at least one 4-adjacent pair is forced; other cells
      are unconstrained.
    run3: a straight run of three specials (one blob), plus count - 3
      isolated specials. The box then has count - 2 blobs.
  """
  if mode == "run3" and count < 3:
    return None
  for _ in range(60):
    chosen = set()
    if mode == "run3":
      options = []
      if w >= 3:
        options.append((0, 1))
      if h >= 3:
        options.append((1, 0))
      if not options:
        return None
      sr, sc = random.choice(options)
      r0 = random.randint(0, h - 1 - 2 * sr)
      c0 = random.randint(0, w - 1 - 2 * sc)
      for i in range(3):
        chosen.add((r0 + i * sr, c0 + i * sc))
    elif mode == "free" and count >= 2:
      r0 = random.randrange(h)
      c0 = random.randrange(w)
      nbrs = [(r0 + dr, c0 + dc) for dr, dc in _NEIGHBOURS
              if 0 <= r0 + dr < h and 0 <= c0 + dc < w]
      chosen.add((r0, c0))
      chosen.add(random.choice(nbrs))
    cells = [(r, c) for r in range(h) for c in range(w)]
    random.shuffle(cells)
    for r, c in cells:
      if len(chosen) >= count:
        break
      if (r, c) in chosen:
        continue
      if mode != "free" and any((r + dr, c + dc) in chosen
                                for dr, dc in _EIGHT):
        continue
      chosen.add((r, c))
    if len(chosen) == count:
      return sorted(chosen)
  return None


def _sample_scene(width, height, num_rects):
  """Samples a fresh latent scene: (width, height, rects, winner index)."""
  for _ in range(400):
    wd = width if width is not None else random.randint(10, 30)
    ht = height if height is not None else random.randint(10, 30)
    bound = _fit_bound(wd, ht)
    if bound < 2:
      continue
    if num_rects is not None:
      if num_rects > bound:
        continue
      n = num_rects
    else:
      n = random.randint(2, bound)
    boxes = _place_boxes(wd, ht, n)
    if boxes is None:
      continue
    caps = [(h * w) // 3 for _, _, h, w in boxes]  # area >= 9, so cap >= 3.
    win = random.randrange(n)
    others = [i for i in range(n) if i != win]
    kmax = min(3, caps[win], min(caps[i] for i in others) - 1)
    if kmax < 1:
      continue
    k = random.randint(1, kmax)
    counts = []
    for i in range(n):
      if i == win:
        counts.append(k)
      else:
        counts.append(random.randint(k + 1, min(caps[i], k + 4)))
    modes = ["sep"] * n
    if random.random() < 0.35:
      for i in others:
        if random.random() < 0.5:
          modes[i] = "free"
      if random.random() < 0.2:
        modes[win] = "free"
    if k >= 2 and random.random() < 0.35:
      # Blob decoy: k + 1 cells but only k - 1 blobs, against the winner's
      # k isolated cells.
      decoy = random.choice(others)
      counts[decoy] = k + 1
      modes[decoy] = "run3"
      modes[win] = "sep"
    elif random.random() < 0.5:
      counts[random.choice(others)] = k + 1
    rects = []
    for (top, left, h, w), cnt, mode in zip(boxes, counts, modes):
      cells = _place_specials(h, w, cnt, mode)
      if cells is None:
        break
      specials = [(r, c, random.choice(_SPECIAL_COLORS)) for r, c in cells]
      rects.append((top, left, h, w, specials))
    if len(rects) == n:
      return wd, ht, rects, win
  raise ValueError("cannot fit the requested rectangles on this canvas")


def _check_dim(name, value, low):
  if value is None:
    return
  if not _is_int(value) or value < low or value > 30:
    raise ValueError("%s must be an int in %d..30" % (name, low))


def generate(width=None, height=None, num_rects=None, rects=None):
  """Returns an input/output pair for task 7bb29440.

  Args:
    width: canvas width (columns). If None it is sampled from 10..30. With
      random rects it must be 3..30. With explicit rects it must be 1..30.
    height: canvas height (rows). If None it is sampled from 10..30. With
      random rects it must be 3..30. With explicit rects it must be 1..30.
    num_rects: number of rectangles, 2..7. If None it is sampled from the
      range the canvas can hold. It is honoured exactly. ValueError is raised
      if the fixed canvas cannot hold it, or if no layout is found. With
      explicit rects it must be None or equal len(rects).
    rects: optional list of (top, left, h, w, specials). Each specials entry
      is a list of (dr, dc, color) offsets inside its rectangle, with color in
      {4, 6}. Explicit rects require explicit width and height. The minimum
      special count must be unique, blue must dominate every rectangle, and
      black must be strictly the most frequent colour. If None, a fresh random
      scene is built.
  """
  if num_rects is not None and not _is_int(num_rects):
    raise ValueError("num_rects must be an integer")
  if rects is not None:
    if not isinstance(rects, (list, tuple)) or any(not isinstance(rect, (list, tuple)) or len(rect) != 5 or not isinstance(rect[4], (list, tuple)) for rect in rects):
      raise ValueError("rects must contain (top, left, height, width, specials) sequences")
    if width is None or height is None:
      raise ValueError("explicit rects require width and height")
    _check_dim("width", width, 1)
    _check_dim("height", height, 1)
    if num_rects is not None and num_rects != len(rects):
      raise ValueError("num_rects disagrees with len(rects)")
    rects = [tuple(rect[:4]) + (list(rect[4]),) if len(rect) == 5 else rect
             for rect in rects]
    win = _check_rects(width, height, rects)
  else:
    _check_dim("width", width, 3)
    _check_dim("height", height, 3)
    if num_rects is not None and (not _is_int(num_rects)
                                  or not 2 <= num_rects <= 7):
      raise ValueError("num_rects must be an int in 2..7")
    if width is not None and height is not None:
      bound = _fit_bound(width, height)
      need = num_rects if num_rects is not None else 2
      if bound < need:
        raise ValueError("canvas too small for %d separated rectangles" % need)
    width, height, rects, win = _sample_scene(width, height, num_rects)
    if _check_rects(width, height, rects) != win:
      raise ValueError("internal error: sampled winner is not unique")
  grid = _render(width, height, rects)
  top, left, h, w, _ = rects[win]
  output = [row[left:left + w] for row in grid[top:top + h]]
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the canonical fixtures through explicit latent parameters."""
  train = [
      generate(width=11, height=12, rects=[
          (1, 1, 3, 4, [(0, 3, 4), (1, 1, 4)]),
          (6, 4, 4, 6, [(2, 2, 6)]),
      ]),
      generate(width=20, height=22, rects=[
          (2, 2, 5, 6, [(0, 5, 4), (1, 1, 4), (2, 4, 6), (3, 2, 6)]),
          (4, 11, 10, 5, [(2, 2, 6), (4, 3, 4), (5, 1, 6), (7, 3, 4)]),
          (11, 2, 8, 7, [(1, 5, 4), (2, 2, 4), (3, 3, 6), (6, 2, 4),
                         (6, 5, 6)]),
          (16, 12, 3, 5, [(0, 1, 4), (1, 3, 6), (2, 0, 6)]),
      ]),
      generate(width=21, height=22, rects=[
          (1, 1, 6, 8, [(1, 4, 6), (1, 6, 4), (2, 2, 4), (3, 4, 4),
                        (4, 7, 6)]),
          (2, 12, 10, 6, [(1, 2, 6), (3, 3, 4), (5, 1, 6), (6, 4, 4),
                          (7, 2, 6)]),
          (8, 5, 10, 6, [(1, 1, 6), (2, 4, 6), (4, 3, 4), (6, 1, 6),
                         (7, 4, 4)]),
          (11, 0, 4, 4, [(0, 3, 6), (1, 0, 6), (2, 1, 4), (2, 3, 6)]),
          (14, 14, 4, 5, [(0, 4, 4), (1, 1, 4), (2, 3, 6)]),
          (19, 10, 3, 10, [(1, 1, 4), (1, 6, 4), (1, 8, 4), (2, 3, 6)]),
      ]),
      generate(width=15, height=22, rects=[
          (2, 6, 5, 6, [(0, 1, 4), (2, 2, 6), (2, 4, 6), (4, 4, 4)]),
          (6, 0, 7, 5, [(2, 1, 4), (4, 2, 4)]),
          (11, 9, 5, 6, [(2, 1, 6), (2, 3, 6), (3, 2, 4)]),
          (14, 0, 3, 5, [(0, 4, 4), (1, 1, 4), (2, 2, 6)]),
          (19, 4, 3, 8, [(1, 0, 4), (1, 3, 6), (1, 5, 4), (2, 1, 4),
                         (2, 6, 6)]),
      ]),
      generate(width=18, height=21, rects=[
          (1, 1, 3, 3, [(0, 1, 6), (2, 0, 4), (2, 2, 6)]),
          (2, 6, 5, 6, [(1, 1, 6), (1, 4, 4), (2, 3, 6), (4, 1, 6)]),
          (5, 13, 5, 5, [(2, 1, 6), (3, 3, 4)]),
          (6, 1, 3, 3, [(0, 1, 4), (1, 0, 6), (2, 2, 6)]),
          (11, 2, 8, 10, [(0, 4, 6), (2, 8, 4), (3, 3, 6), (3, 7, 6),
                          (5, 5, 6), (6, 1, 4)]),
          (12, 14, 4, 4, [(1, 2, 6), (2, 0, 6), (3, 2, 4)]),
      ]),
  ]
  test = [
      generate(width=25, height=22, rects=[
          (0, 18, 4, 6, [(0, 1, 6), (0, 4, 4), (2, 2, 4), (2, 5, 6)]),
          (2, 4, 6, 4, [(2, 2, 4), (4, 1, 6)]),
          (3, 10, 5, 5, [(1, 1, 6), (2, 3, 4), (3, 1, 4)]),
          (6, 18, 5, 4, [(1, 1, 4), (1, 3, 6), (2, 1, 6), (4, 1, 6)]),
          (12, 1, 4, 4, [(0, 3, 6), (1, 1, 4), (3, 2, 6)]),
          (13, 8, 9, 8, [(2, 2, 6), (2, 4, 4), (3, 6, 6), (4, 4, 4),
                         (7, 2, 6), (7, 5, 4)]),
          (14, 19, 5, 6, [(1, 3, 6), (2, 0, 6), (3, 3, 4)]),
      ]),
  ]
  return {"train": train, "test": test}
