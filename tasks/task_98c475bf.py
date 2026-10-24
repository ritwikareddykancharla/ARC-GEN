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

"""ARC task 98c475bf: redraw the colour-specific motif line on the marker rows.

Rule: the grid has two solid border columns (x=0 and x=W-1) of one colour.
Between them there is one decorated horizontal motif line spanning x=1..W-2,
plus one or more marker pairs. A marker pair is a single cell of some colour
at x=1 and at x=W-2, on a row whose interior is otherwise empty. In the
output the interior is cleared and the border columns stay. On every marker
row a motif line of the marker colour is drawn. Each colour has its own
fixed decoration, taken from a lookup table rather than derived geometrically:
  6: box around x=2..4 from dy=-2 to dy=+3, with a line gap at x=3
  7: vertical bars at x=13 and x=15 for dy=+-1 and +-2
  2: X shape, dy=+-2 at x=6 and x=8, dy=+-1 at x=7
  1: bars at x=14 and x=16 for dy=+-1
  3: diamond, dy=+-2 at x=5, dy=+-1 at x=4 and x=6, line gap at x=4..6

Scope:
  - The width is sampled per scene from 18..30. All fixtures are 20 wide.
    Decorations keep their absolute x positions from the left border (the
    rightmost is x=16, so 18 is the narrowest canvas that holds the table).
    This is supported only for episodes whose demonstrations share the
    query's width: the demonstrated line span then fixes the anchoring. A
    novel query width would leave it unclear whether decorations anchor
    left, right or scale, and the evidence gate and factory refuse it.
  - An explicit height without a width keeps the legacy 20-wide canvas, so
    legacy explicit calls replay unchanged. Unconstrained calls draw the
    width once, before any retry, and never change it to recover.
  - The motif table is fixed to the five colours shown in the fixtures.
  - The height is sampled from 12..30. All fixtures are 20 tall, so other
    heights are a synthetic extension. They stay unambiguous because the rule
    only moves lines vertically.
  - Sampled values: the border colour (any of 1..9 not otherwise used), the
    colour and row of the input line, the number of marker pairs (1..3 by
    default, up to 4 on request, with distinct colours that are never the
    line or border colour), and a random vertical packing of the marker
    motifs.
  - Output motifs may overlap the rows of the erased input motif, as in the
    canonical test. Marker rows never fall inside the input motif footprint.
  - marker_colours restricts the marker colours. A host should use it to
    keep test marker colours to colours whose motif appears in the train
    pairs. A single-pair generator cannot enforce that coverage itself. The episode
    builder must verify this with arc_agi2.motif_context before augmentation.
"""

import random

import common

WIDTH = 20  # canonical and legacy canvas width
CANONICAL_HEIGHT = 20
MIN_HEIGHT = 12
MAX_HEIGHT = 30
MAX_MARKERS = 4
SAMPLED_COUNTS = (1, 1, 1, 2, 2, 3)
MAX_TRIES = 500

# colour -> (decoration cells as (dy, x), set of gap xs in the line row)
MOTIFS = {
    6: ([(-2, 2), (-2, 3), (-2, 4), (-1, 2), (-1, 4), (1, 2), (1, 4),
         (2, 2), (2, 4), (3, 2), (3, 3), (3, 4)], {3}),
    7: ([(d, x) for d in (-2, -1, 1, 2) for x in (13, 15)], set()),
    2: ([(-2, 6), (-2, 8), (-1, 7), (1, 7), (2, 6), (2, 8)], set()),
    1: ([(d, x) for d in (-1, 1) for x in (14, 16)], set()),
    3: ([(-2, 5), (-1, 4), (-1, 6), (1, 4), (1, 6), (2, 5)], {4, 5, 6}),
}
# The interior spans x=1..W-2, so every absolute decoration x must be <= W-2.
MIN_WIDTH = max(x for deco, _ in MOTIFS.values() for _, x in deco) + 2
MAX_WIDTH = 30


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _span(colour):
  dys = [d for d, _ in MOTIFS[colour][0]] + [0]
  return min(dys), max(dys)


def _rows_needed(colour):
  lo, hi = _span(colour)
  return hi - lo + 1


def _min_stack(colours):
  """Minimum height for separated motifs of the given colours."""
  if not colours:
    return 0
  return sum(_rows_needed(c) for c in colours) + len(colours) - 1


def _footprint(row, colour):
  lo, hi = _span(colour)
  return row + lo, row + hi


def _fits(row, colour, height):
  a, b = _footprint(row, colour)
  return a >= 0 and b <= height - 1


def _separated(a, b, intervals):
  return all(a > pb + 1 or b < pa - 1 for pa, pb in intervals)


def _covers_marker(row, colour, markers):
  a, b = _footprint(row, colour)
  return any(a <= r <= b for r, _ in markers)


def _pack(colours, height):
  """Stacks marker motifs in random order with random slack.

  Consecutive motifs are always separated by at least one empty row.
  Returns a list of (row, colour), or None if the motifs cannot fit.
  """
  order = random.sample(list(colours), len(colours))
  slack = height - _min_stack(order)
  if slack < 0:
    return None
  cuts = sorted(random.randint(0, slack) for _ in range(len(order)))
  gaps = [cuts[0]] + [cuts[i] - cuts[i - 1] for i in range(1, len(cuts))]
  result = []
  top = 0
  for i, c in enumerate(order):
    top += gaps[i]
    lo, _ = _span(c)
    result.append((top - lo, c))
    top += _rows_needed(c) + 1
  return result


def _stamp(g, row, colour):
  deco, gaps = MOTIFS[colour]
  for x in range(1, len(g[0]) - 1):
    if x not in gaps:
      g[row][x] = colour
  for dy, x in deco:
    g[row + dy][x] = colour


def _canvas(border, height, width):
  g = common.grid(width, height, 0)
  for y in range(height):
    g[y][0] = border
    g[y][width - 1] = border
  return g


def generate(border=None, line_color=None, line_row=None, markers=None,
             num_markers=None, height=None, marker_colours=None, width=None):
  """Build one input/output pair.

  Args:
    border: int colour (1..9) of the two border columns. It must differ from
      the line colour and from every marker colour. It may be a MOTIFS colour.
    line_color: colour of the input motif line. It must be a MOTIFS key.
    line_row: int row of the input motif line. The whole motif must fit, and
      its footprint must not contain any marker row.
    markers: list of (row, colour) marker pairs (1..4 entries) with distinct
      MOTIFS colours other than the line and border colours. The output
      motifs must fit and be separated by at least one empty row.
    num_markers: number of marker pairs (1..4) when markers are sampled. The
      default samples 1..3. If markers is also given, it must equal
      len(markers).
    height: int grid height (12..30).
    marker_colours: optional iterable of allowed marker colours (a non-empty
      subset of the MOTIFS keys). This also applies to explicit markers.
    width: int grid width (18..30). If None, an explicit height keeps the
      legacy width 20; otherwise the width is sampled uniformly.

  Raises:
    ValueError: if the explicit parameters are invalid or incompatible, or
      no scene is found within MAX_TRIES tries. The width never changes.
  """
  colours = sorted(MOTIFS)
  for name, v in (("border", border), ("line_color", line_color),
                  ("line_row", line_row), ("num_markers", num_markers),
                  ("height", height), ("width", width)):
    if v is not None and not _is_int(v):
      raise ValueError("%s must be an int" % name)
  if height is not None and not MIN_HEIGHT <= height <= MAX_HEIGHT:
    raise ValueError("height must be in %d..%d" % (MIN_HEIGHT, MAX_HEIGHT))
  if width is not None and not MIN_WIDTH <= width <= MAX_WIDTH:
    raise ValueError("width must be in %d..%d" % (MIN_WIDTH, MAX_WIDTH))
  limit = height if height is not None else MAX_HEIGHT
  if border is not None and not 1 <= border <= 9:
    raise ValueError("border must be a colour in 1..9")
  if line_color is not None and line_color not in MOTIFS:
    raise ValueError("line_color must be one of %s" % colours)
  if line_color is not None and line_color == border:
    raise ValueError("line_color must differ from border")
  if num_markers is not None and not 1 <= num_markers <= MAX_MARKERS:
    raise ValueError("num_markers must be in 1..%d" % MAX_MARKERS)
  if line_row is not None and not 0 <= line_row < limit:
    raise ValueError("line_row must be in 0..%d" % (limit - 1))
  if line_row is not None and line_color is not None:
    if not _fits(line_row, line_color, limit):
      raise ValueError("line motif does not fit at line_row")
  if marker_colours is not None:
    if not isinstance(marker_colours, (list, tuple, set, frozenset)):
      raise ValueError("marker_colours must be a collection of colours")
    mc = list(marker_colours)
    if not mc or any(not _is_int(c) or c not in MOTIFS for c in mc):
      raise ValueError("marker_colours must be a non-empty subset of %s"
                       % colours)
    allowed = sorted(set(mc))
  else:
    allowed = list(colours)

  mk_in = None
  if markers is not None:
    if not isinstance(markers, (list, tuple)):
      raise ValueError("markers must be a list or tuple")
    mk_in = []
    for m in markers:
      if (not isinstance(m, (list, tuple)) or len(m) != 2
          or not _is_int(m[0]) or not _is_int(m[1])):
        raise ValueError("each marker must be an (int row, int colour) pair")
      mk_in.append((m[0], m[1]))
    if not 1 <= len(mk_in) <= MAX_MARKERS:
      raise ValueError("markers must have 1..%d entries" % MAX_MARKERS)
    if num_markers is not None and num_markers != len(mk_in):
      raise ValueError("num_markers disagrees with len(markers)")
    mcs = [c for _, c in mk_in]
    if len(set(mcs)) != len(mcs):
      raise ValueError("marker colours must be distinct")
    if any(c not in MOTIFS for c in mcs):
      raise ValueError("marker colours must be MOTIFS keys")
    if any(c not in allowed for c in mcs):
      raise ValueError("marker colours must lie in marker_colours")
    if border is not None and border in mcs:
      raise ValueError("border must differ from every marker colour")
    if line_color is not None and line_color in mcs:
      raise ValueError("line_color must differ from every marker colour")
    intervals = []
    for r, c in mk_in:
      if not _fits(r, c, limit):
        raise ValueError("marker motif at row %d does not fit" % r)
      a, b = _footprint(r, c)
      if not _separated(a, b, intervals):
        raise ValueError("marker motifs must be separated by an empty row")
      intervals.append((a, b))
    if line_color is not None and line_row is not None:
      if _covers_marker(line_row, line_color, mk_in):
        raise ValueError("a marker row lies inside the input motif")

  # The smallest four-motif stack needs21 rows and excludes colour6.
  # Its mandatory input6-box needs six marker-free rows, which do not exist
  # at that exact packing. Other four-motif stacks already need at least22.
  if (num_markers == 4 or (mk_in is not None and len(mk_in) == 4)) and limit < 22:
    raise ValueError("four markers plus an input motif require height >=22")

  explicit_cols = [c for _, c in mk_in] if mk_in is not None else []

  def pool_for(c):
    return [m for m in allowed if m != c and m != border]

  if line_color is not None:
    lc_all = [line_color]
  else:
    lc_all = [c for c in colours
              if c != border and c not in explicit_cols
              and (line_row is None or _fits(line_row, c, limit))]
  if not lc_all:
    raise ValueError("no line colour is compatible with the parameters")
  count_choices = None
  if mk_in is None:
    max_pool = max(len(pool_for(c)) for c in lc_all)
    if max_pool == 0:
      raise ValueError("no marker colour is available")
    if num_markers is not None:
      if num_markers > max_pool:
        raise ValueError("not enough marker colours for num_markers")
      count_choices = [num_markers]
    else:
      count_choices = [n for n in SAMPLED_COUNTS if n <= max_pool]
    n_min = min(count_choices)
    need = min(_min_stack(sorted(pool_for(c), key=_rows_needed)[:n_min])
               for c in lc_all if len(pool_for(c)) >= n_min)
    if need > limit:
      raise ValueError("%d marker motifs need height >= %d" % (n_min, need))

  if width is not None:
    w = width
  elif height is not None:
    w = WIDTH
  else:
    w = random.randint(MIN_WIDTH, MAX_WIDTH)

  for _ in range(MAX_TRIES):
    count = len(mk_in) if mk_in is not None else random.choice(count_choices)
    # Colour of the input motif line.
    if mk_in is None:
      choices = [c for c in lc_all if len(pool_for(c)) >= count]
      if not choices:
        continue
    else:
      choices = lc_all
    lc = random.choice(choices) if line_color is None else line_color
    # Marker colours and the minimum height.
    if mk_in is None:
      mcols = random.sample(pool_for(lc), count)
      need = max(MIN_HEIGHT, _min_stack(mcols))
    else:
      mcols = explicit_cols
      need = max([MIN_HEIGHT] + [_footprint(r, c)[1] + 1 for r, c in mk_in])
    if line_row is not None:
      if _footprint(line_row, lc)[0] < 0:
        continue
      need = max(need, _footprint(line_row, lc)[1] + 1)
    if height is not None:
      if need > height:
        continue
      h = height
    else:
      if need > MAX_HEIGHT:
        continue
      h = random.randint(need, MAX_HEIGHT)
    # Marker rows: a random separated packing of the marker motifs.
    if mk_in is None:
      mk = _pack(mcols, h)
      if mk is None:
        continue
    else:
      mk = list(mk_in)
    # Row of the input line: its footprint must avoid every marker row.
    if line_row is not None:
      if not _fits(line_row, lc, h) or _covers_marker(line_row, lc, mk):
        continue
      lr = line_row
    else:
      cands = [r for r in range(h)
               if _fits(r, lc, h) and not _covers_marker(r, lc, mk)]
      if not cands:
        continue
      lr = random.choice(cands)
    # Border colour.
    used = {lc} | set(mcols)
    if border is not None:
      bc = border
    else:
      bc = random.choice([c for c in range(1, 10) if c not in used])
    gin = _canvas(bc, h, w)
    _stamp(gin, lr, lc)
    for r, c in mk:
      gin[r][1] = c
      gin[r][w - 2] = c
    gout = _canvas(bc, h, w)
    for r, c in mk:
      _stamp(gout, r, c)
    return {"input": gin, "output": gout}
  raise ValueError("could not construct a %d-wide scene compatible with the "
                   "given parameters (likely no free rows for the input "
                   "motif)" % w)


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  h, w = CANONICAL_HEIGHT, WIDTH
  train = [
      generate(border=9, line_color=6, line_row=2, markers=[(9, 7)],
               height=h, width=w),
      generate(border=7, line_color=1, line_row=17, markers=[(13, 6)],
               height=h, width=w),
      generate(border=5, line_color=7, line_row=7, markers=[(15, 2)],
               height=h, width=w),
      generate(border=2, line_color=3, line_row=15, markers=[(3, 1)],
               height=h, width=w),
  ]
  test = [
      generate(border=1, line_color=2, line_row=7,
               markers=[(3, 3), (15, 6)], height=h, width=w),
  ]
  return {"train": train, "test": test}
