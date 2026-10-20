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

"""ARC-GEN style generator for task db615bd4.

Rule: the grid is a lattice of dots on a background colour, with one dot at
every (odd row, odd column) cell. Some lattice dots use a second colour and
trace the outline of a rectangle (the frame). Loose pieces sit on (even, even)
cells outside the frame. Each piece is a full rectangular grid of points in
its own colour. In the output:
  * the frame is drawn as solid lines;
  * everything strictly inside the frame is cleared to background;
  * every piece is removed from its old position;
  * each piece's filled bounding box (a block) is packed inside the frame.
Blocks are packed in a row if the frame interior is wider than it is tall,
and in a column if it is taller. They keep the input order of the pieces along
that axis. There is one background cell between neighbouring blocks. The
group is centred on the packing axis, and each block is centred on the cross
axis.

Scope:
  * Grid sides are odd. Random mode samples 13..29 and accepts fixed sides in
    11..29. The fixtures are 25x25, so other sizes are synthetic extensions
    that the lattice rule permits.
  * Random mode uses 2..4 pieces by default, or 1..7 if requested. A piece
    has 1..3 points along the packing axis (attested: 1, 2 and 3).
  * Cross-axis points per piece: the fixtures show 2 and 3 (block thickness
    3 or 5), and all blocks in a scene share them. By default one value is
    used per scene. Thickness 1 (one point) is a labelled synthetic extension,
    sampled with low weight. Mixed thicknesses in one scene are opt-in only
    (mixed_cross=True). They are synthetic because the fixtures never show how
    unequal blocks align on the cross axis.
  * Packing-axis margin defaults to 1, as in every fixture. 2..4 is opt-in
    (pack_margin) and synthetic: it relies on centring the group.
  * Cross-axis margin is 1..3 (all attested). 4 is opt-in.
  * Layout. Attested: every piece lies in a band on the HIGH cross side of the
    frame (below a wide frame, right of a tall frame). Synthetic extensions:
    a band on the LOW cross side, bands where pieces clear of the frame along
    the packing axis sit at other cross positions, and 'beyond' layouts where
    every piece lies past the frame along the packing axis. The layout control
    restricts this ('attested', 'band_high', 'band_low', 'beyond').
  * Order distractor: in most multi-piece scenes the pieces' cross-axis order
    is made to disagree with their packing-axis order, so reading order
    (row-major or column-major) differs from the correct packing order.
  * Pieces never touch the frame, even diagonally, and never touch the grid
    border in random mode. Their intervals along the packing axis are pairwise
    disjoint, so the order is unambiguous. The interior is never square.
    Background is strictly the most common colour, and the dot colour is
    strictly the most common of the rest. All colours are pairwise distinct.
  * Feasibility is checked analytically. If cheap rejection sampling finds
    no configuration, a bounded enumeration of feasible configurations is
    used. Incompatible fixed controls raise ValueError. An internal invariant
    violation raises RuntimeError (a sampler bug, not a control rejection).
"""

import random

import common


SIDES = tuple(range(13, 30, 2))
MIN_SIDE, MAX_SIDE = 11, 29
CONFIG_TRIES = 300
LAYOUT_TRIES = 200
ORDER_TRIES = 8
LAYOUTS = ("attested", "band_high", "band_low", "beyond")


def _check_int(name, value, lo, hi):
  """Require a genuine int (not bool) within [lo, hi]."""
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError("%s must be an integer" % name)
  if not lo <= value <= hi:
    raise ValueError("%s must be in %d..%d" % (name, lo, hi))


def _block_dims(pieces):
  """Return (colour, y0, x0, block_h, block_w) for each piece."""
  return [(c, y0, x0, 2 * nr - 1, 2 * nc - 1) for c, y0, x0, nr, nc in pieces]


def _build(width, height, background, dot, frame_color, frame, pieces):
  """Render the input and output grids from the latent scene description."""
  fy0, fx0, fy1, fx1 = frame
  grid = common.grid(width, height, background)
  for y in range(1, height, 2):
    for x in range(1, width, 2):
      grid[y][x] = dot
  for y in range(fy0, fy1 + 1, 2):
    for x in range(fx0, fx1 + 1, 2):
      if y in (fy0, fy1) or x in (fx0, fx1):
        grid[y][x] = frame_color
  output = [row[:] for row in grid]
  for color, y0, x0, nr, nc in pieces:
    for i in range(nr):
      for j in range(nc):
        grid[y0 + 2 * i][x0 + 2 * j] = color
  for y in range(fy0, fy1 + 1):
    for x in range(fx0, fx1 + 1):
      if y in (fy0, fy1) or x in (fx0, fx1):
        output[y][x] = frame_color
      else:
        output[y][x] = background
  iy0, ix0 = fy0 + 1, fx0 + 1
  ih, iw = fy1 - fy0 - 1, fx1 - fx0 - 1
  blocks = _block_dims(pieces)
  if iw > ih:
    blocks.sort(key=lambda b: b[2])
    total = sum(b[4] for b in blocks) + len(blocks) - 1
    pos = ix0 + (iw - total) // 2
    for color, _, _, h, w in blocks:
      ty = iy0 + (ih - h) // 2
      for y in range(ty, ty + h):
        for x in range(pos, pos + w):
          output[y][x] = color
      pos += w + 1
  else:
    blocks.sort(key=lambda b: b[1])
    total = sum(b[3] for b in blocks) + len(blocks) - 1
    pos = iy0 + (ih - total) // 2
    for color, _, _, h, w in blocks:
      tx = ix0 + (iw - w) // 2
      for y in range(pos, pos + h):
        for x in range(tx, tx + w):
          output[y][x] = color
      pos += h + 1
  return {"input": grid, "output": output}


def _color_counts_ok(grid, background, dot):
  """Background strictly most common; dot strictly most common of the rest."""
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bg_count = counts.get(background, 0)
  dot_count = counts.get(dot, 0)
  for color, count in counts.items():
    if color != background and count >= bg_count:
      return False
    if color not in (background, dot) and count >= dot_count:
      return False
  return True


def _check_scene(width, height, background, dot, frame_color, frame, pieces):
  """Raise ValueError if a scene violates the task invariants."""
  _check_int("width", width, 1, 30)
  _check_int("height", height, 1, 30)
  if width % 2 == 0 or height % 2 == 0:
    raise ValueError("grid sides must be odd")
  if not pieces:
    raise ValueError("need at least one piece")
  if len(frame) != 4:
    raise ValueError("frame must be (fy0, fx0, fy1, fx1)")
  for v in frame:
    _check_int("frame coordinate", v, 0, 29)
  for p in pieces:
    if len(p) != 5:
      raise ValueError("pieces must be (colour, y0, x0, n_rows, n_cols)")
    for v in p:
      _check_int("piece field", v, 0, 29)
  colors = [background, dot, frame_color] + [p[0] for p in pieces]
  for c in colors:
    _check_int("colour", c, 0, 9)
  if len(set(colors)) != len(colors):
    raise ValueError("colours must be distinct values in 0..9")
  fy0, fx0, fy1, fx1 = frame
  if any(v % 2 == 0 for v in frame):
    raise ValueError("frame corners must lie on odd coordinates")
  if not (1 <= fy0 and fy1 <= height - 2 and 1 <= fx0 and fx1 <= width - 2):
    raise ValueError("frame out of bounds")
  ih, iw = fy1 - fy0 - 1, fx1 - fx0 - 1
  if ih < 1 or iw < 1 or ih == iw:
    raise ValueError("frame interior must be non-empty and non-square")
  horizontal = iw > ih
  for _, _, _, nr, nc in pieces:
    if nr < 1 or nc < 1:
      raise ValueError("pieces need at least one point per side")
  blocks = _block_dims(pieces)
  for _, y0, x0, bh, bw in blocks:
    if y0 % 2 or x0 % 2:
      raise ValueError("pieces must lie on even coordinates")
    if y0 < 0 or x0 < 0 or y0 + bh > height or x0 + bw > width:
      raise ValueError("piece out of bounds")
    if (y0 <= fy1 + 1 and y0 + bh - 1 >= fy0 - 1 and
        x0 <= fx1 + 1 and x0 + bw - 1 >= fx0 - 1):
      raise ValueError("piece overlaps or touches the frame")
  key = 2 if horizontal else 1
  size = 4 if horizontal else 3
  ordered = sorted(blocks, key=lambda b: b[key])
  for a, b in zip(ordered, ordered[1:]):
    if a[key] + a[size] - 1 >= b[key]:
      raise ValueError("pieces must be disjoint along the packing axis")
  total = sum(b[size] for b in blocks) + len(blocks) - 1
  cross = max(b[3] if horizontal else b[4] for b in blocks)
  along_space, cross_space = (iw, ih) if horizontal else (ih, iw)
  if total > along_space - 2 or cross > cross_space - 2:
    raise ValueError("blocks need a margin of at least one cell")


def _odd_range(lo, hi):
  """Odd integers in [lo, hi]."""
  return [v for v in range(lo, hi + 1) if v % 2 == 1]


def _even_range(lo, hi):
  """Even integers in [lo, hi]."""
  return [v for v in range(lo, hi + 1) if v % 2 == 0]


def _config_modes(along, cross_side, pm, k, sum_p, maxbc):
  """Return (band_feasible, beyond_feasible) for a latent configuration.

  along/cross_side are the grid sides on the packing/cross axes. sum_p is
  the total number of along-axis points over all pieces, and maxbc is the
  largest block thickness on the cross axis.
  """
  ia = 2 * sum_p - 1 + 2 * pm
  ic = maxbc + 2 * k
  if ic >= ia or ia > along - 4 or ic > cross_side - 4:
    return False, False
  band = cross_side >= ic + maxbc + 7
  beyond = 2 * sum_p <= along - ia - 6
  return band, beyond


def _mode_ok(band, beyond, layout):
  """Whether the requested layout family is feasible."""
  if layout is None:
    return band or beyond
  if layout == "beyond":
    return beyond
  return band


def _composition(n, total):
  """Random list of n values in 1..3 summing to total (n <= total <= 3n)."""
  pts = [1] * n
  for _ in range(total - n):
    k = random.choice([i for i in range(n) if pts[i] < 3])
    pts[k] += 1
  return pts


def _cross_list(n, ctl, top=None):
  """Cross-axis point counts for each piece."""
  if ctl["mixed_cross"]:
    top = top if top is not None else random.choice((2, 3))
    vals = [random.randint(1, top) for _ in range(n)]
    i, j = random.sample(range(n), 2)
    vals[i] = top
    vals[j] = random.randint(1, top - 1)
    return vals
  if top is not None:
    return [top] * n
  c = ctl["cross_points"]
  if c is None:
    c = random.choices((1, 2, 3), weights=(1, 4, 3))[0]
  return [c] * n


def _axis_sides(hz, ctl):
  """Fixed (along, cross) sides for this orientation, or None."""
  if hz:
    return ctl["width"], ctl["height"]
  return ctl["height"], ctl["width"]


def _sample_config(ctl):
  """One cheap random configuration draw; None if infeasible."""
  hz = ctl["horizontal"]
  if hz is None:
    hz = random.random() < 0.5
  along_f, cross_f = _axis_sides(hz, ctl)
  along = along_f if along_f is not None else random.choice(SIDES)
  cross_side = cross_f if cross_f is not None else random.choice(SIDES)
  n = ctl["num_pieces"]
  if n is None:
    n = random.randint(2, 4)
  pm = ctl["pack_margin"] if ctl["pack_margin"] is not None else 1
  k = ctl["cross_margin"]
  if k is None:
    k = random.choice((1, 2, 3))
  p_list = [random.choice((1, 2, 2, 3)) for _ in range(n)]
  c_list = _cross_list(n, ctl)
  band, beyond = _config_modes(along, cross_side, pm, k, sum(p_list),
                               2 * max(c_list) - 1)
  if _mode_ok(band, beyond, ctl["layout"]):
    return (hz, along, cross_side, pm, k, p_list, c_list)
  return None


def _enumerate_configs(ctl):
  """All feasible coarse configurations under the fixed controls."""
  hz_opts = ([ctl["horizontal"]] if ctl["horizontal"] is not None
             else [True, False])
  n_opts = ([ctl["num_pieces"]] if ctl["num_pieces"] is not None
            else [2, 3, 4])
  pm = ctl["pack_margin"] if ctl["pack_margin"] is not None else 1
  k_opts = ([ctl["cross_margin"]] if ctl["cross_margin"] is not None
            else [1, 2, 3])
  if ctl["mixed_cross"]:
    c_opts = [2, 3]
  elif ctl["cross_points"] is not None:
    c_opts = [ctl["cross_points"]]
  else:
    c_opts = [1, 2, 3]
  found = []
  for hz in hz_opts:
    along_f, cross_f = _axis_sides(hz, ctl)
    for along in ([along_f] if along_f is not None else SIDES):
      for cross_side in ([cross_f] if cross_f is not None else SIDES):
        for n in n_opts:
          for k in k_opts:
            for c in c_opts:
              for s in range(n, 3 * n + 1):
                band, beyond = _config_modes(along, cross_side, pm, k, s,
                                             2 * c - 1)
                if _mode_ok(band, beyond, ctl["layout"]):
                  found.append((hz, along, cross_side, n, pm, k, s, c))
  return found


def _expand(base, ctl):
  """Turn a coarse enumerated configuration into a full one."""
  hz, along, cross_side, n, pm, k, s, c = base
  return (hz, along, cross_side, pm, k, _composition(n, s),
          _cross_list(n, ctl, top=c))


def _allocate(lengths, slots, base):
  """Place runs of lattice slots in order; return their start coordinates."""
  n = len(lengths)
  spare = slots - sum(lengths)
  bars = sorted(random.sample(range(spare + n), n))
  starts = []
  prev, slot = -1, 0
  for k in range(n):
    slot += bars[k] - prev - 1
    prev = bars[k]
    starts.append(base + 2 * slot)
    slot += lengths[k]
  return starts


def _order_disagrees(a_starts, c_starts):
  """True if cross-axis order contradicts packing-axis order somewhere."""
  n = len(a_starts)
  for i in range(n):
    for j in range(n):
      if a_starts[i] < a_starts[j] and c_starts[i] > c_starts[j]:
        return True
  return False


def _choose_layout(band, beyond, layout):
  """Pick (mode, side, same_side) among feasible layout families."""
  choices = []
  if layout is None:
    if band:
      choices += [("band", "high", None), ("band", "high", None),
                  ("band", "low", None)]
    if beyond:
      choices.append(("beyond", None, False))
  elif layout == "beyond":
    if beyond:
      choices.append(("beyond", None, False))
  elif layout == "attested":
    if band:
      choices.append(("band", "high", True))
  elif band:
    choices.append(("band", layout[5:], None))
  if not choices:
    return None
  mode, side, same_side = random.choice(choices)
  if mode == "band" and same_side is None:
    same_side = random.random() < 0.7
  return mode, side, same_side


def _layout(cfg, ctl):
  """Place frame and pieces for a feasible configuration; None on failure."""
  hz, along, cross_side, pm, k, p_list, c_list = cfg
  n = len(p_list)
  sum_p = sum(p_list)
  ia = 2 * sum_p - 1 + 2 * pm
  bcs = [2 * c - 1 for c in c_list]
  maxbc = max(bcs)
  ic = maxbc + 2 * k
  band, beyond = _config_modes(along, cross_side, pm, k, sum_p, maxbc)
  picked = _choose_layout(band, beyond, ctl["layout"])
  if picked is None:
    return None
  mode, side, same_side = picked
  if mode == "band":
    if side == "high":
      fc0 = random.choice(_odd_range(1, cross_side - 6 - ic - maxbc))
    else:
      fc0 = random.choice(_odd_range(maxbc + 4, cross_side - 3 - ic))
    fa0 = random.choice(_odd_range(1, along - 3 - ia))
    a_starts = _allocate(p_list, (along - 3) // 2, 2)
  else:
    fc0 = random.choice(_odd_range(1, cross_side - 3 - ic))
    options = []
    for f0 in _odd_range(1, along - 3 - ia):
      f1 = f0 + ia + 1
      left = max(0, (f0 - 3) // 2)
      right = max(0, (along - f1 - 4) // 2)
      for j in range(n + 1):
        if sum(p_list[:j]) <= left and sum(p_list[j:]) <= right:
          options.append((f0, j, left, right))
    if not options:
      return None
    fa0, j, left, right = random.choice(options)
    a_starts = (_allocate(p_list[:j], left, 2) +
                _allocate(p_list[j:], right, fa0 + ia + 4))
  fa1 = fa0 + ia + 1
  fc1 = fc0 + ic + 1
  fixed = [c for c in (ctl["background"], ctl["dot"], ctl["frame_color"])
           if c is not None]
  free = [c for c in range(10) if c not in fixed]
  random.shuffle(free)
  bg = ctl["background"] if ctl["background"] is not None else free.pop()
  dt = ctl["dot"] if ctl["dot"] is not None else free.pop()
  fc = ctl["frame_color"] if ctl["frame_color"] is not None else free.pop()
  piece_colors = free[:n]
  starts_list = []
  for idx in range(n):
    a0 = a_starts[idx]
    a1 = a0 + 2 * p_list[idx] - 2
    bc = bcs[idx]
    starts = _even_range(2, cross_side - 2 - bc)
    if same_side and side == "high":
      starts = [s for s in starts if s >= fc1 + 2]
    elif same_side and side == "low":
      starts = [s for s in starts if s + bc - 1 <= fc0 - 2]
    elif a0 <= fa1 + 1 and a1 >= fa0 - 1:
      starts = [s for s in starts
                if s + bc - 1 <= fc0 - 2 or s >= fc1 + 2]
    if not starts:
      return None
    starts_list.append(starts)
  want_hard = n >= 2 and random.random() < 0.6
  c_starts = None
  for _ in range(ORDER_TRIES):
    c_starts = [random.choice(s) for s in starts_list]
    if not want_hard or _order_disagrees(a_starts, c_starts):
      break
  pieces = []
  for idx in range(n):
    a0, c0 = a_starts[idx], c_starts[idx]
    if hz:
      pieces.append((piece_colors[idx], c0, a0, c_list[idx], p_list[idx]))
    else:
      pieces.append((piece_colors[idx], a0, c0, p_list[idx], c_list[idx]))
  if hz:
    w, h, frame = along, cross_side, (fc0, fa0, fc1, fa1)
  else:
    w, h, frame = cross_side, along, (fa0, fc0, fa1, fc1)
  pair = _build(w, h, bg, dt, fc, frame, pieces)
  if not _color_counts_ok(pair["input"], bg, dt):
    return None
  try:
    _check_scene(w, h, bg, dt, fc, frame, pieces)
  except ValueError as err:
    raise RuntimeError("internal sampler invariant violated: %s" % err)
  return pair


def _random_controls(width, height, background, dot, frame_color, num_pieces,
                     horizontal, pack_margin, cross_margin, cross_points,
                     mixed_cross, layout):
  """Validate random-mode controls and pack them into a dict."""
  for name, v in (("width", width), ("height", height)):
    if v is not None:
      _check_int(name, v, MIN_SIDE, MAX_SIDE)
      if v % 2 == 0:
        raise ValueError("%s must be odd" % name)
  fixed = []
  for name, v in (("background", background), ("dot", dot),
                  ("frame_color", frame_color)):
    if v is not None:
      _check_int(name, v, 0, 9)
      fixed.append(v)
  if len(set(fixed)) != len(fixed):
    raise ValueError("fixed colours must be distinct")
  if num_pieces is not None:
    _check_int("num_pieces", num_pieces, 1, 7)
  if pack_margin is not None:
    _check_int("pack_margin", pack_margin, 1, 4)
  if cross_margin is not None:
    _check_int("cross_margin", cross_margin, 1, 4)
  if cross_points is not None:
    _check_int("cross_points", cross_points, 1, 3)
  for name, v in (("horizontal", horizontal), ("mixed_cross", mixed_cross)):
    if v is not None and not isinstance(v, bool):
      raise ValueError("%s must be None, True or False" % name)
  if layout is not None and layout not in LAYOUTS:
    raise ValueError("layout must be None or one of %s" % (LAYOUTS,))
  mixed = bool(mixed_cross)
  if mixed and cross_points is not None:
    raise ValueError("cross_points is incompatible with mixed_cross=True")
  if mixed and num_pieces == 1:
    raise ValueError("mixed_cross=True needs at least two pieces")
  return {"width": width, "height": height, "background": background,
          "dot": dot, "frame_color": frame_color, "num_pieces": num_pieces,
          "horizontal": horizontal, "pack_margin": pack_margin,
          "cross_margin": cross_margin, "cross_points": cross_points,
          "mixed_cross": mixed, "layout": layout}


def _random_scene(ctl):
  """Construct a valid latent scene honouring fixed controls (bounded)."""
  pool = None
  for _ in range(LAYOUT_TRIES):
    cfg = None
    if pool is None:
      for _ in range(CONFIG_TRIES):
        cfg = _sample_config(ctl)
        if cfg is not None:
          break
    if cfg is None:
      if pool is None:
        pool = _enumerate_configs(ctl)
      if not pool:
        raise ValueError("the fixed controls cannot fit together")
      cfg = _expand(random.choice(pool), ctl)
    pair = _layout(cfg, ctl)
    if pair is not None:
      return pair
  raise ValueError("could not sample a db615bd4 scene with these controls")


def generate(width=None, height=None, background=None, dot=None,
             frame_color=None, frame=None, pieces=None, num_pieces=None,
             horizontal=None, pack_margin=None, cross_margin=None,
             cross_points=None, mixed_cross=None, layout=None):
  """Generate one input/output pair.

  Args:
    width: grid width (odd). Required in explicit mode. In random mode it is
      honoured if given (11..29), else sampled from 13..29.
    height: grid height (odd). Treated like width.
    background: background colour. Honoured if given.
    dot: lattice dot colour. Honoured if given.
    frame_color: colour of the frame's lattice dots. Honoured if given.
    frame: (fy0, fx0, fy1, fx1), the frame corners on odd coordinates.
      Explicit mode only. It must be given together with pieces.
    pieces: list of (colour, y0, x0, n_rows, n_cols). Each piece is a full
      grid of points at (y0 + 2i, x0 + 2j) on even coordinates. Explicit mode
      only. It must be given together with frame.
    num_pieces: random mode only. Number of pieces (1..7). Default 2..4.
    horizontal: random mode only. True packs along a row, False along a
      column. Default random.
    pack_margin: random mode only. Packing-axis margin in cells (1..4).
      Default 1, as in all fixtures. Values above 1 are synthetic.
    cross_margin: random mode only. Cross-axis margin around the thickest
      block (1..4). Default 1..3, all attested.
    cross_points: random mode only. Cross-axis points per piece (1..3), shared
      by all pieces. Default weighted toward 2 and 3; 1 is synthetic.
    mixed_cross: random mode only. If True, pieces get different cross-axis
      thicknesses (synthetic, individually centred). Default False.
    layout: random mode only. None (default mixture), 'attested' (all pieces
      in a band on the high cross side, as in the fixtures), 'band_high',
      'band_low' (synthetic) or 'beyond' (synthetic: pieces past the frame
      along the packing axis).
  Explicit mode (frame and pieces given) requires width, height and all three
  colours, and rejects every random-only control. Random mode samples every
  control left as None. It raises ValueError if the fixed controls cannot fit
  together.
  """
  if (frame is None) != (pieces is None):
    raise ValueError("frame and pieces must be given together")
  if frame is not None:
    if None in (width, height, background, dot, frame_color):
      raise ValueError("explicit mode needs width, height and all colours")
    if any(v is not None for v in (num_pieces, horizontal, pack_margin,
                                   cross_margin, cross_points, mixed_cross,
                                   layout)):
      raise ValueError("random-only controls are not allowed in explicit mode")
    try:
      pieces = [tuple(p) for p in pieces]
      frame = tuple(frame)
    except TypeError:
      raise ValueError("frame and each piece must be sequences of integers")
    _check_scene(width, height, background, dot, frame_color, frame, pieces)
    pair = _build(width, height, background, dot, frame_color, frame, pieces)
    if not _color_counts_ok(pair["input"], background, dot):
      raise ValueError("background/dot must be the dominant colours")
    return pair
  ctl = _random_controls(width, height, background, dot, frame_color,
                         num_pieces, horizontal, pack_margin, cross_margin,
                         cross_points, mixed_cross, layout)
  return _random_scene(ctl)


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(25, 25, 8, 1, 4, (3, 3, 11, 13),
               [(2, 16, 6, 3, 2), (3, 18, 14, 3, 2)]),
      generate(25, 25, 4, 2, 1, (3, 5, 15, 13),
               [(8, 10, 16, 2, 2), (9, 14, 20, 1, 2), (3, 18, 16, 2, 2)]),
      generate(25, 25, 8, 2, 3, (5, 5, 15, 21),
               [(4, 18, 4, 2, 2), (9, 20, 10, 2, 3), (1, 18, 18, 2, 2)]),
  ]
  test = [
      generate(25, 25, 4, 1, 8, (3, 3, 15, 11),
               [(2, 4, 18, 2, 2), (3, 10, 20, 1, 2), (9, 12, 18, 2, 2)]),
  ]
  return {"train": train, "test": test}
