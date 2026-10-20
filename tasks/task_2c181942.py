"""ARC-GEN style generator for ARC task 2c181942 (hub docking).

Rule: the grid has a background (8) and one "hub": a 2x2 background hole
with a two-cell bar on each side. Each bar has its own colour. The other
shapes are loose. A loose shape whose colour matches a bar is rotated (no
reflection) so that its narrow tip faces the hub. The tip is an edge holding
exactly two adjacent cells, centred on that edge. The shape is then placed
just outside that bar, with its tip aligned to the bar. Loose shapes whose
colour matches no bar are erased. The hub itself is unchanged.

Scope: the grid size, hub position, the four distinct bar colours, the set
of hub sides that receive a shape, and the shapes themselves are all sampled.
Each shape has an even width (2, 4 or 6), a centred two-cell tip, and is
optionally left/right symmetric. Each shape is shown in the input under a
random rotation. Distractor shapes use colours that match no bar. Each hub
colour is used by at most one loose shape. The background is fixed at 8, as
in every original example.
"""

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

import random

import common

BACKGROUND = 8
SIDES = ("top", "bottom", "left", "right")
# Counter-clockwise quarter turns that bring a tip-down canonical shape to
# the orientation it has when docked on each hub side.
DOCK_TURNS = {"top": 0, "left": 1, "bottom": 2, "right": 3}


def _parse(mask):
  """Converts a list of '1'/'.' strings (or 0/1 lists) into 0/1 lists."""
  out = []
  for row in mask:
    if isinstance(row, str):
      out.append([1 if ch == "1" else 0 for ch in row])
    else:
      out.append([1 if v else 0 for v in row])
  return out


def _rot(mask, k):
  """Rotates a mask counter-clockwise k times (same convention as rot90)."""
  for _ in range(k % 4):
    h, w = len(mask), len(mask[0])
    mask = [[mask[j][w - 1 - i] for j in range(h)] for i in range(w)]
  return mask


def _tip_ok(row):
  """True if the edge has exactly two adjacent cells centred on it."""
  idx = [i for i, v in enumerate(row) if v]
  return (len(idx) == 2 and idx[1] == idx[0] + 1
          and 2 * idx[0] + 2 == len(row))


def _unique_dock(canon):
  """True if only the canonical orientation has a valid tip at the bottom."""
  for k in (1, 2, 3):
    t = _rot(canon, k)
    if _tip_ok(t[-1]) and t != canon:
      return False
  return True


def _connected8(cells):
  cells = set(cells)
  start = next(iter(cells))
  seen, stack = {start}, [start]
  while stack:
    r, c = stack.pop()
    for dr in (-1, 0, 1):
      for dc in (-1, 0, 1):
        n = (r + dr, c + dc)
        if n in cells and n not in seen:
          seen.add(n)
          stack.append(n)
  return len(seen) == len(cells)


def _random_shape():
  """Samples a canonical (tip-down) shape whose docking is unambiguous."""
  for _ in range(400):
    w = random.choice([2, 4, 4, 4, 6])
    h = random.randint(2, 5 if w == 2 else 4)
    sym = random.random() < 0.65
    rows = []
    for _r in range(h - 1):
      if sym:
        half = [random.randint(0, 1) for _ in range(w // 2)]
        rows.append(half + half[::-1])
      else:
        rows.append([random.randint(0, 1) for _ in range(w)])
    tip = [0] * w
    tip[(w - 2) // 2] = 1
    tip[w // 2] = 1
    rows.append(tip)
    if not all(any(r) for r in rows):
      continue
    if not any(r[0] for r in rows) or not any(r[-1] for r in rows):
      continue
    cells = [(r, c) for r in range(h) for c in range(w) if rows[r][c]]
    if len(cells) < 4 or not _connected8(cells):
      continue
    if not _unique_dock(rows):
      continue
    return rows
  raise RuntimeError("Could not sample a uniquely oriented connected shape")


def _hub_cells(y, x):
  return {"top": [(y - 1, x), (y - 1, x + 1)],
          "bottom": [(y + 2, x), (y + 2, x + 1)],
          "left": [(y, x - 1), (y + 1, x - 1)],
          "right": [(y, x + 2), (y + 1, x + 2)]}


def _dock_origin(side, d, y, x):
  h, w = len(d), len(d[0])
  if side == "top":
    return y - 1 - h, x - (w - 2) // 2
  if side == "bottom":
    return y + 3, x - (w - 2) // 2
  if side == "left":
    return y - (h - 2) // 2, x - 1 - w
  return y - (h - 2) // 2, x + 3


def _mask_cells(m, oy, ox):
  return [(oy + r, ox + c) for r in range(len(m)) for c in range(len(m[0]))
          if m[r][c]]


def _hub_sites(g, bg):
  """All positions that look like a hub (used only as a validity check)."""
  hh, ww = len(g), len(g[0])
  sites = []
  for yy in range(1, hh - 2):
    for xx in range(1, ww - 2):
      if any(g[yy + a][xx + b] != bg for a in (0, 1) for b in (0, 1)):
        continue
      pairs = [(g[yy - 1][xx], g[yy - 1][xx + 1]),
               (g[yy + 2][xx], g[yy + 2][xx + 1]),
               (g[yy][xx - 1], g[yy + 1][xx - 1]),
               (g[yy][xx + 2], g[yy + 1][xx + 2])]
      if all(p[0] != bg and p[0] == p[1] for p in pairs):
        sites.append((yy, xx))
  return sites


def _build(width, height, y, x, colors, shapes, bg):
  """Paints the input and output grids from the latent scene."""
  grid_in = common.grid(width, height, bg)
  grid_out = common.grid(width, height, bg)
  hub = _hub_cells(y, x)
  for i, side in enumerate(SIDES):
    for (r, c) in hub[side]:
      grid_in[r][c] = colors[i]
      grid_out[r][c] = colors[i]
  side_of = {colors[i]: SIDES[i] for i in range(4)}
  for colour, canon, turns, oy, ox in shapes:
    canon = _parse(canon)
    for (r, c) in _mask_cells(_rot(canon, turns), oy, ox):
      grid_in[r][c] = colour
    if colour in side_of:
      side = side_of[colour]
      d = _rot(canon, DOCK_TURNS[side])
      dy, dx = _dock_origin(side, d, y, x)
      for (r, c) in _mask_cells(d, dy, dx):
        grid_out[r][c] = colour
  return {"input": grid_in, "output": grid_out}


def _sample_scene(width, height, colors, bg):
  palette = [c for c in range(10) if c != bg]
  for _ in range(600):
    hh = height if height is not None else random.randint(15, 30)
    ww = width if width is not None else random.randint(15, 30)
    cols = list(colors) if colors is not None else random.sample(palette, 4)
    n_match = random.choice([1, 2, 2, 3, 3, 4, 4])
    sides = random.sample(SIDES, n_match)
    others = [c for c in palette if c not in cols]
    n_dis = min(len(others), random.choice([0, 1, 1, 2]))
    latent = []
    for side in sides:
      latent.append([cols[SIDES.index(side)], _random_shape(),
                     random.randint(0, 3)])
    for c in random.sample(others, n_dis):
      latent.append([c, _random_shape(), random.randint(0, 3)])
    # Docked footprint relative to a hub at (0, 0).
    rel = []
    for side_cells in _hub_cells(0, 0).values():
      rel.extend(side_cells)
    for side in sides:
      canon = latent[sides.index(side)][1]
      d = _rot(canon, DOCK_TURNS[side])
      oy, ox = _dock_origin(side, d, 0, 0)
      rel.extend(_mask_cells(d, oy, ox))
    if len(set(rel)) != len(rel):
      continue
    min_r = min(r for r, _ in rel)
    max_r = max(r for r, _ in rel)
    min_c = min(c for _, c in rel)
    max_c = max(c for _, c in rel)
    lo_y, hi_y = max(1, -min_r), min(hh - 3, hh - 1 - max_r)
    lo_x, hi_x = max(1, -min_c), min(ww - 3, ww - 1 - max_c)
    if lo_y > hi_y or lo_x > hi_x:
      continue
    y = random.randint(lo_y, hi_y)
    x = random.randint(lo_x, hi_x)
    blocked = set()
    for r in range(y - 2, y + 4):
      for c in range(x - 2, x + 4):
        blocked.add((r, c))
    random.shuffle(latent)
    shapes, ok = [], True
    for colour, canon, turns in latent:
      m = _rot(canon, turns)
      h, w = len(m), len(m[0])
      if h > hh or w > ww:
        ok = False
        break
      placed = False
      for _t in range(120):
        oy = random.randint(0, hh - h)
        ox = random.randint(0, ww - w)
        cells = _mask_cells(m, oy, ox)
        if any(cell in blocked for cell in cells):
          continue
        for (r, c) in cells:
          for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
              blocked.add((r + dr, c + dc))
        shapes.append((colour, canon, turns, oy, ox))
        placed = True
        break
      if not placed:
        ok = False
        break
    if not ok:
      continue
    pair = _build(ww, hh, y, x, cols, shapes, bg)
    if _hub_sites(pair["input"], bg) != [(y, x)]:
      continue
    return pair
  raise RuntimeError("could not construct a valid hub scene")


def generate(width=None, height=None, hub_row=None, hub_col=None,
             colors=None, shapes=None, background=None):
  """Generates one input/output pair.

  Args:
    width: grid width (columns). Random in 15..30 if None.
    height: grid height (rows). Random in 15..30 if None.
    hub_row: row of the upper-left cell of the hub's 2x2 hole (explicit mode).
    hub_col: column of the upper-left cell of the hole (explicit mode).
    colors: bar colours (top, bottom, left, right), all distinct.
    shapes: explicit loose shapes, as a list of tuples
      (colour, canonical_mask, turns, row, col). canonical_mask is the shape
      with its centred two-cell tip on the bottom row, given as '1'/'.'
      strings. turns is the number of counter-clockwise quarter turns
      applied to get the input appearance. (row, col) is the input top-left.
      When shapes is None, a fresh random scene is built.
    background: background colour (default 8).
  """
  bg = BACKGROUND if background is None else background
  if bg not in range(10):
    raise ValueError("Background must be in 0..9")
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 1 <= dimension <= 30):
      raise ValueError("Grid dimensions must be integers in 1..30")
  if colors is not None and (len(colors) != 4 or len(set(colors)) != 4 or any(c not in range(10) or c == bg for c in colors)):
    raise ValueError("Four distinct hub colours required, excluding background")
  if shapes is None:
    if hub_row is not None or hub_col is not None:
      raise ValueError("Explicit hub position requires explicit shapes")
    if any(d is not None and d < 15 for d in (width, height)):
      raise ValueError("Random dimensions must be in 15..30")
    return _sample_scene(width, height, colors, bg)
  if any(v is None for v in (width, height, hub_row, hub_col, colors)):
    raise ValueError("Explicit shapes require complete hub geometry")
  if not (1 <= hub_row <= height - 3 and 1 <= hub_col <= width - 3):
    raise ValueError("Hub outside grid")
  occupied_in = {cell for cells in _hub_cells(hub_row, hub_col).values() for cell in cells}
  occupied_out = set(occupied_in)
  used_colours = set()
  for colour, mask, turns, oy, ox in shapes:
    if colour not in range(10) or colour == bg or colour in used_colours:
      raise ValueError("Loose shape colours must be distinct and not background")
    used_colours.add(colour)
    canon = _parse(mask)
    if not canon or not canon[0] or any(len(row) != len(canon[0]) for row in canon):
      raise ValueError("Mask must be nonempty and rectangular")
    cells = set(_mask_cells(_rot(canon, turns), oy, ox))
    if not cells or any(not (0 <= r < height and 0 <= c < width) for r, c in cells) or cells & occupied_in:
      raise ValueError("Input shape empty, outside grid or overlapping")
    occupied_in.update(cells)
    if colour in colors:
      if not _tip_ok(canon[-1]) or not _unique_dock(canon):
        raise ValueError("Matching shape must have an unambiguous centered tip")
      side = SIDES[list(colors).index(colour)]
      docked = _rot(canon, DOCK_TURNS[side])
      dy, dx = _dock_origin(side, docked, hub_row, hub_col)
      cells = set(_mask_cells(docked, dy, dx))
      if any(not (0 <= r < height and 0 <= c < width) for r, c in cells) or cells & occupied_out:
        raise ValueError("Docked shape outside grid or overlapping")
      occupied_out.update(cells)
  return _build(width, height, hub_row, hub_col, colors, shapes, bg)


def validate():
  """Reconstructs the canonical ARC pairs from explicit latent parameters."""
  train = [
      generate(width=20, height=23, hub_row=9, hub_col=6, colors=(6, 1, 3, 2),
               shapes=[(2, ["1111", ".11."], 0, 2, 13),
                       (4, [".11.", ".11.", "1111"], 0, 14, 12),
                       (3, ["1..1", "1111", ".11."], 2, 17, 3)]),
      generate(width=21, height=18, hub_row=7, hub_col=7, colors=(3, 4, 1, 2),
               shapes=[(3, ["1..1", ".11."], 2, 3, 15),
                       (1, ["1111", "1111", ".11."], 0, 12, 1),
                       (2, ["1111", ".11.", ".11."], 3, 13, 12)]),
      generate(width=25, height=20, hub_row=8, hub_col=12,
               colors=(1, 3, 2, 7),
               shapes=[(2, ["1..1", ".11.", ".11."], 2, 2, 2),
                       (3, ["11", "11"], 0, 2, 19),
                       (7, ["1..1", "1111", ".11."], 0, 14, 1),
                       (1, ["11", "11", "11", "11"], 1, 15, 18)]),
  ]
  test = [
      generate(width=26, height=24, hub_row=11, hub_col=14,
               colors=(1, 6, 4, 2),
               shapes=[(2, ["1..1", ".11.", ".11.", ".11."], 2, 3, 2),
                       (1, ["1111", ".11.", ".11."], 1, 1, 17),
                       (3, [".11", "111", "11."], 0, 13, 3),
                       (6, ["111111", "..11..", "..11..", "..11.."], 3,
                        17, 9),
                       (4, ["1..1", "1111", ".11."], 0, 14, 20)]),
  ]
  return {"train": train, "test": test}
