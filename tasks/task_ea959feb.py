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

"""ARC-GEN style generator for task ea959feb.

Rule: the input is a periodic wallpaper over the colours 1..n.
  * Each row repeats horizontally with period px.
  * Each row equals the row above with every colour increased by one, wrapping
    cyclically within 1..n. The vertical period is therefore n.
  * Solid rectangles of colour 1 are pasted over the wallpaper.
Colour 1 is also a genuine wallpaper colour. A mask can cover genuine 1 cells
and merge visually with neighbouring genuine 1s. The output is the clean
wallpaper with the rectangles removed. Masked cells whose true colour is 1
stay 1.

Scope: all original pairs are 22x25 (height x width). The rule does not
depend on size, so other sizes are synthetic extensions. Default random
generation uses the native size about half the time. Otherwise it draws each
side from 15..30. Callers may request any side in 1..30. A random scene needs
height >= 4 (n >= 3 and n < height) and width >= 4 (px >= 2 and px < width).

The generator samples:
  * the colour count n in 3..9. The default prefers 5..min(9, height // 2),
    is never below max(base), and is always below the height. n = 2 is
    rejected: every non-1 cell would be colour 2, so no period could be
    identified.
  * the horizontal period px: 3..9 by default, at most width // 2.
  * a row-0 tile with minimal cyclic period px and at least min(3, px, n)
    distinct colours.
  * num_masks colour-1 rectangles, each from 2x2 to 6x6. Mask sides are
    capped at a third of the grid side.

The default mask count is 3..6 on the native grid. On small grids it is
scaled down to 1..max(1, min(6, area // 40)), so tiny grids remain feasible.
Masks never overlap. They may touch the border or each other. About a third
of later masks are placed flush against an earlier mask, giving the L-shaped
blobs seen in the original pairs.

Every scene must satisfy these conditions:
  1. every shorter shift (horizontal < px, vertical < n) shows a visible
     contradiction between two non-1 cells;
  2. the true shifts px and n each have at least one comparable non-1 pair;
  3. every residue class whose true colour is not 1 keeps an unmasked witness;
  4. at least one masked cell has a true colour other than 1.
Conditions 1-4 make the answer uniquely recoverable. Randomly sampled masks
must also satisfy a fifth condition:
  5. at least one masked cell has true colour 1, so a 1 stays 1 in the output.
"""

import random

import common


NATIVE_WIDTH = 25
NATIVE_HEIGHT = 22
MAX_MASKS = 8


def _req_int(name, v, lo, hi):
  """Accept Python ints and integer-like scalars (e.g. numpy ints).

  Rejects bool, float, strings and anything whose text form differs from
  its integer value.
  """
  if isinstance(v, (bool, float, str, bytes)):
    raise ValueError("%s must be an integer" % name)
  try:
    iv = int(v)
  except (TypeError, ValueError):
    raise ValueError("%s must be an integer" % name)
  if iv != v or str(v) != str(iv):
    raise ValueError("%s must be an integer" % name)
  if not lo <= iv <= hi:
    raise ValueError("%s must be in %d..%d" % (name, lo, hi))
  return iv


def _wallpaper(n, base, width, height):
  px = len(base)
  g = common.grid(width, height, 0)
  for y in range(height):
    for x in range(width):
      g[y][x] = (base[x % px] - 1 + y) % n + 1
  return g


def _minimal_cyclic(base):
  px = len(base)
  for p in range(1, px):
    if px % p == 0 and all(base[i] == base[(i + p) % px] for i in range(px)):
      return False
  return True


def _mask_cells(mask):
  r, c, mh, mw = mask
  return {(y, x) for y in range(r, r + mh) for x in range(c, c + mw)}


def _apply_masks(wall, masks):
  g = [row[:] for row in wall]
  for m in masks:
    for (y, x) in _mask_cells(m):
      g[y][x] = 1
  return g


def _shift_status(g, p, axis):
  """Return (has_pairs, has_mismatch) for shift p, ignoring colour-1 cells."""
  h, w = len(g), len(g[0])
  pairs = False
  for y in range(h - (p if axis == 0 else 0)):
    for x in range(w - (p if axis == 1 else 0)):
      a = g[y][x]
      b = g[y + p][x] if axis == 0 else g[y][x + p]
      if a != 1 and b != 1:
        if a != b:
          return pairs, True
        pairs = True
  return pairs, False


def _periods_recoverable(g, n, px):
  if px >= len(g[0]) or n >= len(g):
    return False
  for p in range(1, px):
    if not _shift_status(g, p, 1)[1]:
      return False
  for p in range(1, n):
    if not _shift_status(g, p, 0)[1]:
      return False
  pairs, bad = _shift_status(g, px, 1)
  if bad or not pairs:
    return False
  pairs, bad = _shift_status(g, n, 0)
  if bad or not pairs:
    return False
  return True


def _witnesses_ok(wall, g, n, px):
  h, w = len(g), len(g[0])
  seen, need = set(), set()
  for y in range(h):
    for x in range(w):
      key = (y % n, x % px)
      if wall[y][x] != 1:
        need.add(key)
        if g[y][x] != 1:
          seen.add(key)
  return need <= seen


def _scene_ok(wall, g, n, px):
  return (g != wall and _periods_recoverable(g, n, px)
          and _witnesses_ok(wall, g, n, px))


def _masks_hit_genuine_one(wall, masks):
  for m in masks:
    for (y, x) in _mask_cells(m):
      if wall[y][x] == 1:
        return True
  return False


def _try_place(mh, mw, width, height, masks, occupied, touch):
  """Propose one rectangle, flush against an earlier mask when touch is set."""
  if touch and masks:
    r0, c0, h0, w0 = random.choice(masks)
    side = random.randint(0, 3)
    if side == 0:
      r, c = r0 + h0, random.randint(c0 - mw + 1, c0 + w0 - 1)
    elif side == 1:
      r, c = r0 - mh, random.randint(c0 - mw + 1, c0 + w0 - 1)
    elif side == 2:
      r, c = random.randint(r0 - mh + 1, r0 + h0 - 1), c0 + w0
    else:
      r, c = random.randint(r0 - mh + 1, r0 + h0 - 1), c0 - mw
  else:
    r = random.randint(0, height - mh)
    c = random.randint(0, width - mw)
  if r < 0 or c < 0 or r + mh > height or c + mw > width:
    return None
  mask = (r, c, mh, mw)
  cells = _mask_cells(mask)
  if cells & occupied:
    return None
  return mask, cells


def _sample_masks(count, width, height):
  """Place exactly `count` non-overlapping rectangles, or return None."""
  masks, occupied = [], set()
  max_h = min(6, max(2, height // 3))
  max_w = min(6, max(2, width // 3))
  for _ in range(count):
    placed = None
    touch = random.random() < 0.35
    for _ in range(100):
      mh = random.randint(min(2, height), max_h)
      mw = random.randint(min(2, width), max_w)
      placed = _try_place(mh, mw, width, height, masks, occupied, touch)
      if placed is not None:
        break
    if placed is None:
      return None
    masks.append(placed[0])
    occupied |= placed[1]
  return masks


def _default_mask_count(width, height):
  """Choose a mask count: 3..6 on native-sized grids, scaled down on small ones."""
  cap = max(1, min(6, (width * height) // 40))
  return random.randint(min(3, cap), cap)


def _normalise_masks(masks):
  if isinstance(masks, (str, bytes)) or not hasattr(masks, "__iter__"):
    raise ValueError("masks must be a list of (row, col, height, width)")
  out = []
  for m in masks:
    if isinstance(m, (str, bytes)) or not hasattr(m, "__iter__"):
      raise ValueError("mask must be (row, col, height, width)")
    m = list(m)
    if len(m) != 4:
      raise ValueError("mask must be (row, col, height, width)")
    r = _req_int("mask row", m[0], 0, 29)
    c = _req_int("mask col", m[1], 0, 29)
    mh = _req_int("mask height", m[2], 1, 30)
    mw = _req_int("mask width", m[3], 1, 30)
    if r + mh > 30 or c + mw > 30:
      raise ValueError("mask %r exceeds a 30x30 grid" % ((r, c, mh, mw),))
    out.append((r, c, mh, mw))
  if not 1 <= len(out) <= MAX_MASKS:
    raise ValueError("masks must contain 1..%d rectangles" % MAX_MASKS)
  occupied = set()
  for m in out:
    cells = _mask_cells(m)
    if cells & occupied:
      raise ValueError("explicit masks must not overlap")
    occupied |= cells
  return out


def _pick_side(given, native, use_native, need, explicit):
  if given is not None:
    return given
  if explicit:
    return native if need <= native else need
  if use_native and need <= native:
    return native
  return random.randint(max(15, min(need, 30)), 30)


def generate(num_colors=None, period=None, base=None, masks=None,
             num_masks=None, width=None, height=None):
  """Build one masked-wallpaper example.

  Args:
    num_colors: integer size n of the colour cycle 1..n, which is also the
      vertical period. Must be in 3..9 and smaller than the height.
      Random default: 5..min(9, height // 2), never below max(base) or 3.
    period: integer horizontal period px, in 2..15 and smaller than the width.
      If base is given, period must equal len(base).
      Random default: 3..min(9, width // 2).
    base: list of px integer colours, each in 1..num_colors, forming row 0 of
      the tile. Its length must be 2..15, and it must have minimal cyclic
      period len(base).
    masks: list of 1..8 non-overlapping integer (row, col, height, width)
      rectangles painted with colour 1. They must lie inside the grid.
    num_masks: number of randomly placed masks, in 1..8. If masks is also
      given, num_masks must equal len(masks). Random default: 3..6 on
      native-sized grids, scaled down to 1..max(1, min(6, area // 40)).
    width: integer grid width in 1..30. If omitted, it is chosen to fit the
      other controls. When base, masks and num_colors are all given, it
      defaults to 25, or to the smallest width that fits.
    height: integer grid height in 1..30. Defaults as for width. The native
      value is 22.

  Raises:
    ValueError: for inconsistent, ill-typed or unrecoverable caller-supplied
      parameters. This includes partial controls under which no valid scene
      is found within the bounded retries.
  """
  constrained = any(v is not None for v in (num_colors, period, base, masks,
                                            num_masks, width, height))
  if num_colors is not None:
    num_colors = _req_int("num_colors", num_colors, 3, 9)
  if period is not None:
    period = _req_int("period", period, 2, 15)
  if num_masks is not None:
    num_masks = _req_int("num_masks", num_masks, 1, MAX_MASKS)
  if width is not None:
    width = _req_int("width", width, 1, 30)
  if height is not None:
    height = _req_int("height", height, 1, 30)
  if base is not None:
    if isinstance(base, (str, bytes)) or not hasattr(base, "__iter__"):
      raise ValueError("base must be a list of colours")
    base = [_req_int("base colour", v, 1, 9) for v in base]
    if not 2 <= len(base) <= 15:
      raise ValueError("len(base) must be in 2..15")
    if period is not None and period != len(base):
      raise ValueError("period conflicts with len(base)")
    if num_colors is not None and max(base) > num_colors:
      raise ValueError("base uses colours outside 1..num_colors")
    if not _minimal_cyclic(base):
      raise ValueError("base is not minimally periodic")
  if masks is not None:
    masks = _normalise_masks(masks)
    if num_masks is not None and num_masks != len(masks):
      raise ValueError("num_masks conflicts with len(masks)")

  explicit = base is not None and masks is not None and num_colors is not None
  px_fixed = len(base) if base is not None else period
  base_max = max(base) if base is not None else 1

  # Work out the smallest sides compatible with the supplied controls.
  need_h, need_w = 1, 1
  if masks:
    need_h = max(r + mh for (r, _, mh, _) in masks)
    need_w = max(c + mw for (_, c, _, mw) in masks)
  n_lo = num_colors if num_colors is not None else max(5, base_max)
  if explicit:
    need_h = max(need_h, num_colors + 1)
    need_w = max(need_w, px_fixed + 1)
  else:
    need_h = max(need_h, 2 * n_lo)
    need_w = max(need_w, 2 * (px_fixed if px_fixed is not None else 3))
  use_native = explicit or random.random() < 0.5
  height = _pick_side(height, NATIVE_HEIGHT, use_native, need_h, explicit)
  width = _pick_side(width, NATIVE_WIDTH, use_native, need_w, explicit)

  if masks is not None:
    for (r, c, mh, mw) in masks:
      if r + mh > height or c + mw > width:
        raise ValueError("mask out of bounds for the requested grid")
  if px_fixed is not None and px_fixed >= width:
    raise ValueError("period must be smaller than width")
  if num_colors is not None and num_colors >= height:
    raise ValueError("num_colors must be smaller than height")

  if explicit:
    wall = _wallpaper(num_colors, base, width, height)
    g = _apply_masks(wall, masks)
    if not _scene_ok(wall, g, num_colors, len(base)):
      raise ValueError("explicit scene is not uniquely recoverable")
    return {"input": g, "output": wall}

  # Colour-count range. The preferred upper bound is height // 2, which gives
  # two vertical witnesses per class. The hard bound is n < height, the same
  # bound used on the explicit num_colors path.
  if num_colors is None:
    hard_hi = min(9, height - 1)
    pref_hi = min(9, height // 2)
    lo_n = max(3, base_max, min(5, pref_hi))
    hi_n = min(hard_hi, max(pref_hi, lo_n))
    if lo_n > hi_n:
      raise ValueError("grid too short for a recoverable colour cycle")
  if px_fixed is None:
    hi_p = min(9, width // 2)
    if hi_p < 2:
      raise ValueError("grid too narrow for any period")
    lo_p = min(3, hi_p)

  for _ in range(300):
    n = num_colors if num_colors is not None else random.randint(lo_n, hi_n)
    if base is not None:
      b = base
    else:
      px = px_fixed if px_fixed is not None else random.randint(lo_p, hi_p)
      b = None
      for _ in range(100):
        cand = [random.randint(1, n) for _ in range(px)]
        if _minimal_cyclic(cand) and len(set(cand)) >= min(3, px, n):
          b = cand
          break
      if b is None:
        continue
    if masks is not None:
      m = masks
    else:
      count = (num_masks if num_masks is not None
               else _default_mask_count(width, height))
      m = _sample_masks(count, width, height)
      if m is None:
        continue
    wall = _wallpaper(n, b, width, height)
    g = _apply_masks(wall, m)
    if not _scene_ok(wall, g, n, len(b)):
      continue
    if masks is None and not _masks_hit_genuine_one(wall, m):
      continue
    return {"input": g, "output": wall}
  if constrained:
    raise ValueError("no recoverable scene found under the given constraints")
  raise RuntimeError("could not build a valid scene")


def validate():
  """Reconstruct the original fixtures from explicit latent parameters."""
  train = [
      generate(num_colors=7, base=[7, 5, 5, 7, 4, 3, 4],
               masks=[(5, 20, 3, 3), (9, 4, 3, 5), (13, 3, 2, 3),
                      (17, 2, 4, 5), (17, 17, 4, 5)],
               width=25, height=22),
      generate(num_colors=6, base=[1, 6, 1, 4, 3, 4],
               masks=[(0, 2, 4, 5), (2, 13, 4, 5), (13, 2, 3, 2),
                      (16, 2, 4, 3), (14, 19, 4, 5)],
               width=25, height=22),
      generate(num_colors=8, base=[7, 4, 3, 4],
               masks=[(11, 11, 3, 4), (13, 4, 4, 3), (14, 9, 3, 2),
                      (17, 20, 4, 3), (18, 14, 2, 3)],
               width=25, height=22),
  ]
  test = [
      generate(num_colors=9, base=[7, 3, 1, 1, 3, 7, 4, 3, 4],
               masks=[(5, 8, 4, 5), (9, 4, 2, 3), (11, 3, 4, 5),
                      (10, 11, 3, 2)],
               width=25, height=22),
  ]
  return {"train": train, "test": test}
