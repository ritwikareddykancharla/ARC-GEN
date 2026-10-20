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

"""ARC task 4c7dc4dd: visual analogy between four framed squares.

The input shows a noisy diagonally periodic background.  Two long single
colour rectangles each enclose two equally sized square frames (single-colour
border, interior mostly 0).  One rectangle holds a complete example pair
(source frame and target frame); the other holds a question frame and a frame
whose interior is entirely 0.  The output is the missing interior, obtained by
applying the example's relation to the question.  Three relations exist:

* parity complement: nonzero cells become 0 and 0 cells take the colour the
  pattern uses on that checkerboard parity;
* mirror completion: a corner motif is mirrored into all four corners and the
  rest of the interior is filled with the frame's border colour;
* gap lines: gaps between consecutive nonzero cells in a row or column are
  filled with the marker colour that is not shared with the example (the
  example fills with its own non-shared marker colour).

Random scenes sample the relation, interior size (4..6), grid size,
orientation (rectangles stacked vertically or side by side), placements,
background tiling/noise, colours, and which frames play which roles.  Every
non-empty interior is required to have a nonzero cell on the odd
checkerboard parity, so the parity colours are always well defined.
Fixture replay (validate) passes the original input grid together with the
latent question location, size and relation, because the hand-made noisy
backgrounds are impractical to re-derive from a small parameter set.
"""

import random

import common


_TRAIN1 = (
    "1234113412 3412341234 1234123412",
    "4123412341 2341234123 4123412341",
    "3411111111 1111111111 1111111111",
    "2314444444 4123412341 2341134113",
    "1214100004 3412341234 4444443412",
    "4114611164 2341234124 1000042311",
    "3414000014 1234123414 6000641214",
    "1314000014 4123112314 0000044113",
    "1214000014 3412341234 0000043412",
    "4114444444 2141234124 0000142311",
    "3412341234 1134123414 4444441214",
    "1311234123 4113412341 2341234113",
    "1211111111 1111111111 1111111112",
    "4123412341 2341234123 4123412341",
    "3412341234 1234121412 3411141234",
    "2341234123 4123412341 2141214113",
    "1234122222 2222222222 2222123412",
    "4123422341 2341234444 4442412341",
    "3412324444 4444124000 0042341234",
    "2341224000 0043414000 0042214123",
    "1234124600 0242344000 0042123412",
    "4123424000 0041234000 0042412341",
    "3412324000 0041124000 0042341234",
    "2341224200 0043414444 4442234123",
    "1231124444 4442341234 1232123412",
    "4123422222 2222222222 2222112341",
    "3412341234 1234113412 3412341234",
    "2341234123 4123412341 2141234123",
    "1234123112 3412341234 1234123412",
    "4123412341 2341234123 4123412341",
)

_TRAIN2 = (
    "4123044444 4444430124 4123412401",
    "1240143012 3412401230 1230123012",
    "2301240888 8883412304 2301430123",
    "3012341804 0080423012 3012341230",
    "0123042844 0081430123 4423012301",
    "1230444804 4482401234 1230123012",
    "2301240804 0083412342 2222222223",
    "3012341888 8884423012 2222222220",
    "0123042301 2301430122 0123012321",
    "1230444012 3012404232 1888888022",
    "2401440423 0124412302 2800008123",
    "3012341230 4230443012 4800008220",
    "4123042301 2341440122 0800008321",
    "1230143012 3012441232 1800008022",
    "2301244123 0423412302 2888888123",
    "3012344234 1230423042 3012301220",
    "0423042301 2301430122 0123012321",
    "1230143412 3012401232 4230123022",
    "2301240123 0123414342 2401230123",
    "3012341230 4230443012 3012304220",
    "0123042301 2301430122 0123012321",
    "1230444012 3012401232 1888888022",
    "2301240888 8883412302 2800208123",
    "3012441840 4480443012 3822208220",
    "0123044800 4481430122 0800008321",
    "1230144840 0082401232 1802208022",
    "2301440840 4484412342 2888888123",
    "3012341888 8880423012 3000000420",
    "0123042301 2301430122 2222222221",
    "1230144444 4444401230 4230423012",
)

_TEST1 = (
    "3466346634 5636566456 6456365636",
    "4563333333 3333636666 6666666645",
    "5633563666 3653366664 6634563666",
    "6343655555 5563456365 5555554663",
    "3453350000 0563666455 0000055634",
    "6563450010 0543636565 0000056645",
    "5633650181 0563646635 0000053656",
    "6343650010 0563456345 0000054666",
    "3453350000 0533666455 0000055634",
    "4663455555 5543636565 5555556645",
    "5633663456 3453346634 6634666656",
    "6343634563 4563656345 6346634663",
    "3453666634 5633666456 3466345634",
    "4563456345 6343636563 4563456645",
    "5633663656 3463346634 5634563666",
    "6663666563 4663456365 6645634663",
    "6463365634 5633566456 3656345634",
    "4563456665 6343666566 4666456645",
    "5633566466 3453346634 6664563656",
    "6343634563 4563456645 6365634663",
    "3453355555 5533566455 5555555664",
    "4563658181 8563636565 0000056646",
    "6633551808 1553646635 0040053656",
    "6343658000 8563456365 0424054663",
    "6453351808 1533666655 0040055634",
    "4563458181 8543636565 0000056645",
    "5633555555 5553346635 5555553656",
    "6363634663 4563456666 6666666663",
    "3453333333 3333663456 3456365636",
    "4663456365 6345634563 6563456345",
)

_TEST2 = (
    "2345623456 2388623456 2345623456",
    "6834562345 6234568345 6234582385",
    "5621111111 1111111111 1111111184",
    "8581385623 4562885623 4562345183",
    "3481233333 3336234563 3333333162",
    "2341630833 8035623453 0800003186",
    "8231838333 3834562343 8300003145",
    "8621433333 3333486883 0000003184",
    "4581833333 3332348623 0000003123",
    "3451238333 3836234563 0000003162",
    "8341830833 8035623453 0000003156",
    "8831833333 3334562343 3333333148",
    "5621456234 5623458234 5623456134",
    "4561111111 1111111111 1111111128",
    "8486234562 3456234562 3456234568",
    "2348688856 2345623456 2388628488",
    "6444444444 4444444444 4444442385",
    "5423456234 5623486666 6666846834",
    "4466666666 6582346000 0806345623",
    "3486000000 6456236000 0686244582",
    "2446000000 6345626000 0006643456",
    "6436000000 6234866000 0006542845",
    "5486000000 6623486000 0006446234",
    "4466000000 6562386000 0006345623",
    "8456000000 6456286666 6666244882",
    "8446666666 6348623486 2345643456",
    "6444444444 4444444444 4444442348",
    "5628456234 5623456288 8623456234",
    "4862385623 8562345823 4568345623",
    "3456834568 3858234862 8456234568",
)


def _decode(rows):
  return [[int(ch) for ch in row.replace(" ", "")] for row in rows]


def _zeros(h, w):
  return [[0] * w for _ in range(h)]


def _parity(x):
  """Parity complement of an interior (None if the interior is empty)."""
  h, w = len(x), len(x[0])
  cols = {}
  for r in range(h):
    for c in range(w):
      if x[r][c]:
        cols.setdefault((r + c) % 2, x[r][c])
  if not cols:
    return None
  if 0 not in cols:
    cols[0] = cols[1]
  if 1 not in cols:
    cols[1] = cols[0]
  return [[0 if x[r][c] else cols[(r + c) % 2] for c in range(w)]
          for r in range(h)]


def _mirror(x, fc):
  """Mirror a corner motif into all four corners, fill the rest with fc."""
  h, w = len(x), len(x[0])
  nz = [(r, c) for r in range(h) for c in range(w) if x[r][c]]
  if not nz:
    return None
  out = [row[:] for row in x]
  flips = ((lambda r, c: (r, w - 1 - c)), (lambda r, c: (h - 1 - r, c)),
           (lambda r, c: (h - 1 - r, w - 1 - c)))
  for f in flips:
    for r in range(h):
      for c in range(w):
        if out[r][c] == 0:
          rr, cc = f(r, c)
          out[r][c] = x[rr][cc]
  y0 = min(r for r, _ in nz)
  y1 = max(r for r, _ in nz)
  x0 = min(c for _, c in nz)
  x1 = max(c for _, c in nz)
  boxes = ((y0, x0, y1, x1), (y0, w - 1 - x1, y1, w - 1 - x0),
           (h - 1 - y1, x0, h - 1 - y0, x1),
           (h - 1 - y1, w - 1 - x1, h - 1 - y0, w - 1 - x0))
  cov = [[False] * w for _ in range(h)]
  for a, b, c, d in boxes:
    for r in range(a, c + 1):
      for k in range(b, d + 1):
        cov[r][k] = True
  for r in range(h):
    for c in range(w):
      if not cov[r][c] and out[r][c] == 0:
        out[r][c] = fc
  return out


def _lines(x, col):
  """Fill gaps between consecutive nonzero cells of rows/columns with col."""
  h, w = len(x), len(x[0])
  out = [row[:] for row in x]
  for r in range(h):
    xs = [c for c in range(w) if x[r][c]]
    for a, b in zip(xs, xs[1:]):
      for c in range(a + 1, b):
        out[r][c] = col
  for c in range(w):
    ys = [r for r in range(h) if x[r][c]]
    for a, b in zip(ys, ys[1:]):
      for r in range(a + 1, b):
        out[r][c] = col
  return out


def _has_odd(x):
  """True if some nonzero cell lies on the odd checkerboard parity."""
  return any(x[r][c] for r in range(len(x)) for c in range(len(x[0]))
             if (r + c) % 2 == 1)


def _split(total, k):
  cuts = sorted(random.randint(0, total) for _ in range(k - 1))
  parts, prev = [], 0
  for c in cuts:
    parts.append(c - prev)
    prev = c
  parts.append(total - prev)
  return parts


def _background(h, w):
  p = random.randint(3, 5)
  pool = list(range(10)) if random.random() < 0.3 else list(range(1, 10))
  cyc = random.sample(pool, p)
  sign = random.choice((1, -1))
  off = random.randrange(p)
  g = common.grid(w, h, 0)
  for r in range(h):
    for c in range(w):
      g[r][c] = cyc[(c + sign * r + off) % p]
  noise = random.randint(1, 9)
  dens = random.uniform(0.02, 0.08)
  for r in range(h):
    for c in range(w):
      if random.random() < dens:
        g[r][c] = noise
  return g


def _parity_pattern(m, ce, co):
  for _ in range(200):
    dens = random.uniform(0.25, 0.55)
    if random.random() < 0.5:
      hq = (m + 1) // 2
      base = [[random.random() < dens for _ in range(hq)] for _ in range(hq)]
      mask = [[base[min(r, m - 1 - r)][min(c, m - 1 - c)] for c in range(m)]
              for r in range(m)]
    else:
      mask = [[random.random() < dens for _ in range(m)] for _ in range(m)]
    cells = [(r, c) for r in range(m) for c in range(m) if mask[r][c]]
    if len(cells) < 2 or len(cells) > m * m - 3:
      continue
    if len({(r + c) % 2 for r, c in cells}) < 2:
      continue
    return [[(ce if (r + c) % 2 == 0 else co) if mask[r][c] else 0
             for c in range(m)] for r in range(m)]
  return None


def _mirror_pattern(m, fc, cm):
  half = m // 2
  for _ in range(200):
    a = random.randint(2, half)
    b = random.randint(2, half)
    mot = [[random.choice((0, cm, cm, fc)) for _ in range(b)] for _ in range(a)]
    cells = [(r, c) for r in range(a) for c in range(b) if mot[r][c]]
    if not any(mot[r][c] == cm for r, c in cells):
      continue
    rs = {r for r, _ in cells}
    cs = {c for _, c in cells}
    if 0 not in rs or a - 1 not in rs or 0 not in cs or b - 1 not in cs:
      continue
    corner = random.randrange(4)
    r0 = 0 if corner in (0, 1) else m - a
    c0 = 0 if corner in (0, 2) else m - b
    x = _zeros(m, m)
    for r in range(a):
      for c in range(b):
        x[r0 + r][c0 + c] = mot[r][c]
    if not _has_odd(x):
      continue
    return x
  return None


def _lines_pattern(m, mark, own):
  for _ in range(300):
    x = _zeros(m, m)
    for _ in range(random.randint(1, 2)):
      line = random.randrange(m)
      a = random.randint(0, m - 3)
      b = random.randint(a + 2, m - 1)
      ca = random.choice((mark, own))
      cb = random.choice((mark, own))
      if random.random() < 0.5:
        x[line][a], x[line][b] = ca, cb
      else:
        x[a][line], x[b][line] = ca, cb
    if random.random() < 0.5:
      x[random.randrange(m)][random.randrange(m)] = random.choice((mark, own))
    vals = {v for row in x for v in row} - {0}
    if vals != {mark, own}:
      continue
    if sum(1 for row in x for v in row if v) > 6:
      continue
    if not _has_odd(x):
      continue
    probe = _lines(x, -1)
    if sum(1 for row in probe for v in row if v == -1) < 2:
      continue
    return x
  return None


def _example_rule(s, t, fc):
  """Return the sole relation compatible with an example, or None if ambiguous."""
  matches = set()
  for name in ("parity", "mirror"):
    for a, b in ((s, t), (t, s)):
      r = _parity(a) if name == "parity" else _mirror(a, fc)
      if r is not None and r == b:
        matches.add(name)
  for a, b in ((s, t), (t, s)):
    for c in sorted({v for row in b for v in row} - {0}):
      if _lines(a, c) == b:
        matches.add("lines")
  return next(iter(matches)) if len(matches) == 1 else None


def _relation_case(rel, m, fcx, fcq, encl_ex, encl_q):
  """Returns (source, target, question, answer) interiors or None."""
  colours = list(range(1, 10))
  if rel == "parity":
    pool = [c for c in colours if c != fcx]
    ce = random.choice(pool)
    co = ce if random.random() < 0.4 else random.choice(
        [c for c in pool if c != ce])
    qpool = [c for c in colours if c != fcq]
    qe = qo = None
    for _ in range(50):
      qe = random.choice(qpool)
      qo = qe if random.random() < 0.4 else random.choice(
          [c for c in qpool if c != qe])
      if {qe, qo} != {ce, co}:
        break
    if {qe, qo} == {ce, co}:
      return None
    s = _parity_pattern(m, ce, co)
    q = _parity_pattern(m, qe, qo)
    if s is None or q is None:
      return None
    t, a = _parity(s), _parity(q)
  elif rel == "mirror":
    cm = random.choice([c for c in colours if c != fcx])
    cmq = random.choice([c for c in colours if c != fcq])
    s = _mirror_pattern(m, fcx, cm)
    q = _mirror_pattern(m, fcq, cmq)
    if s is None or q is None or s == q:
      return None
    t, a = _mirror(s, fcx), _mirror(q, fcq)
  else:
    pool = [c for c in colours if c not in (fcx, fcq)]
    if random.random() < 0.5:
      f1, f2 = encl_ex, encl_q
    else:
      f1, f2 = random.sample(pool, 2)
    mark = random.choice([c for c in pool if c not in (f1, f2)])
    s = _lines_pattern(m, mark, f1)
    q = _lines_pattern(m, mark, f2)
    if s is None or q is None:
      return None
    t, a = _lines(s, f1), _lines(q, f2)
    qcols = {v for row in q for v in row} - {0}
    scols = {v for row in s for v in row} - {0}
    if qcols - scols != {f2}:
      return None
  for x in (s, t, q):
    if not _has_odd(x):
      return None
  if _example_rule(s, t, fcx) != rel:
    return None
  return s, t, q, a


def _runs(g):
  h, w = len(g), len(g[0])
  rr = [[0] * w for _ in range(h)]
  dd = [[0] * w for _ in range(h)]
  for y in range(h):
    for x in range(w - 1, -1, -1):
      same = x + 1 < w and g[y][x + 1] == g[y][x]
      rr[y][x] = 1 + (rr[y][x + 1] if same else 0)
  for x in range(w):
    for y in range(h - 1, -1, -1):
      same = y + 1 < h and g[y + 1][x] == g[y][x]
      dd[y][x] = 1 + (dd[y + 1][x] if same else 0)
  return rr, dd


def _scene_ok(g, boxes, n, ei, qi):
  """Frames must be the unique 4-member largest bordered-square group, and
  the smallest bordered rectangle around the empty frame must pair it with
  the question frame."""
  h, w = len(g), len(g[0])
  rr, dd = _runs(g)

  def bordered(y0, x0, y1, x1):
    c = g[y0][x0]
    ww, hh = x1 - x0 + 1, y1 - y0 + 1
    return (rr[y0][x0] >= ww and dd[y0][x0] >= hh and g[y1][x0] == c and
            rr[y1][x0] >= ww and g[y0][x1] == c and dd[y0][x1] >= hh)

  groups = {}
  for y0 in range(h):
    for x0 in range(w):
      if rr[y0][x0] < 4 or dd[y0][x0] < 4:
        continue
      for hh in range(4, min(15, dd[y0][x0]) + 1):
        for ww in range(4, min(15, rr[y0][x0]) + 1):
          y1, x1 = y0 + hh - 1, x0 + ww - 1
          if bordered(y0, x0, y1, x1):
            groups.setdefault((hh, ww), []).append((y0, x0, y1, x1))
  if sorted(groups.get((n, n), [])) != sorted(boxes):
    return False
  for key, val in groups.items():
    if key != (n, n) and len(val) == 4 and key[0] * key[1] >= n * n:
      return False
  fy0, fx0, fy1, fx1 = boxes[ei]
  best, partners = None, set()
  for y0 in range(fy0):
    for x0 in range(fx0):
      r, d = rr[y0][x0], dd[y0][x0]
      if x0 + r - 1 <= fx1 or y0 + d - 1 <= fy1:
        continue
      for y1 in range(fy1 + 1, y0 + d):
        for x1 in range(fx1 + 1, x0 + r):
          if not bordered(y0, x0, y1, x1):
            continue
          inside = [i for i, (a, b, c, e) in enumerate(boxes)
                    if a > y0 and b > x0 and c < y1 and e < x1]
          if len(inside) == 2 and ei in inside:
            other = inside[0] if inside[1] == ei else inside[1]
            area = (y1 - y0) * (x1 - x0)
            if best is None or area < best:
              best, partners = area, {other}
            elif area == best:
              partners.add(other)
  return best is not None and partners == {qi}


def generate(relation=None, size=None, orientation=None, width=None,
             height=None, input_grid=None, question=None, fill=None,
             qcolor=None):
  """Generates one input/output pair.

  Args:
    relation: "parity", "mirror" or "lines" (random if None).
    size: interior side length of the frames, 4..6 (random if None).
    orientation: "stacked" (rectangles one above the other, frames side by
      side) or "side" (rectangles side by side, frames stacked).
    width, height: optional final grid dimensions (must fit the layout).
    input_grid: fixture replay only; an existing input grid.
    question: fixture replay only; (row, col) of the question frame corner.
    fill: fixture replay only; fill colour for the "lines" relation.
    qcolor: fixture replay only; frame colour override for "mirror".
  """
  if input_grid is not None:
    g = [list(row) for row in input_grid]
    r0, c0 = question
    m = size
    q = [g[r0 + 1 + i][c0 + 1:c0 + 1 + m] for i in range(m)]
    if relation == "parity":
      out = _parity(q)
    elif relation == "mirror":
      out = _mirror(q, qcolor if qcolor else g[r0][c0])
    else:
      out = _lines(q, fill)
    return {"input": g, "output": out}

  if relation is not None and relation not in ("parity", "mirror", "lines"):
    raise ValueError("unknown relation")
  if size is not None and size not in (4, 5, 6):
    raise ValueError("interior size must be 4..6")
  if orientation is not None and orientation not in ("stacked", "side"):
    raise ValueError("unknown layout orientation")
  rel = relation or random.choice(("parity", "mirror", "lines"))
  m = size or random.choice((4, 5, 6))
  n = m + 2
  orient = orientation or random.choice(("stacked", "side"))
  min_h = 2 * (n + 4) + 1
  min_w = 2 * n + 6
  requested = (height, width) if orient == "stacked" else (width, height)
  if any(v is not None and not low <= v <= 30 for v, low in zip(requested, (min_h, min_w))):
    raise ValueError("requested dimensions cannot fit the chosen frame layout")
  for _ in range(300):
    encl = random.sample(range(1, 10), 2)
    fpool = [c for c in range(1, 10) if c not in encl]
    fa = random.choice(fpool)
    fb = fa if random.random() < 0.5 else random.choice(
        [c for c in fpool if c != fa])
    frame_col = [fa, fb]
    ex_rect = random.randrange(2)
    q_rect = 1 - ex_rect
    case = _relation_case(rel, m, frame_col[ex_rect], frame_col[q_rect],
                          encl[ex_rect], encl[q_rect])
    if case is None:
      continue
    s_in, t_in, q_in, ans = case
    if orient == "stacked":
      hs_arg, ws_arg = height, width
    else:
      hs_arg, ws_arg = width, height
    hs = hs_arg or random.randint(min_h, 30)
    ws = ws_arg or random.randint(min_w, 30)
    v = _split(hs - min_h, 5)
    hr = [n + 4 + v[1], n + 4 + v[3]]
    tops = [v[0], v[0] + hr[0] + 1 + v[2]]
    rects, frames, frect = [], [], []
    for i in range(2):
      e = _split(ws - min_w, 5)
      left, g1, g2, g3 = e[0], 1 + e[1], 2 + e[2], 1 + e[3]
      wr = 2 + g1 + n + g2 + n + g3
      top = tops[i]
      rects.append((top, left, top + hr[i] - 1, left + wr - 1))
      inner = hr[i] - 2
      for k in range(2):
        off = random.randint(1, inner - n - 1)
        col = left + 1 + g1 if k == 0 else left + 1 + g1 + n + g2
        frames.append((top + 1 + off, col))
        frect.append(i)
    hh, ww = hs, ws
    if orient == "side":
      rects = [(b, a, d, c) for a, b, c, d in rects]
      frames = [(c, r) for r, c in frames]
      hh, ww = ws, hs
    ex_pair = [2 * ex_rect, 2 * ex_rect + 1]
    random.shuffle(ex_pair)
    q_pair = [2 * q_rect, 2 * q_rect + 1]
    random.shuffle(q_pair)
    qi, ei = q_pair
    interiors = {ex_pair[0]: s_in, ex_pair[1]: t_in, qi: q_in,
                 ei: _zeros(m, m)}
    g = _background(hh, ww)
    for i, (a, b, c, d) in enumerate(rects):
      for x in range(b, d + 1):
        g[a][x] = encl[i]
        g[c][x] = encl[i]
      for y in range(a, c + 1):
        g[y][b] = encl[i]
        g[y][d] = encl[i]
    boxes = []
    for idx, (r0, c0) in enumerate(frames):
      fc = frame_col[frect[idx]]
      for y in range(n):
        for x in range(n):
          if y in (0, n - 1) or x in (0, n - 1):
            g[r0 + y][c0 + x] = fc
          else:
            g[r0 + y][c0 + x] = interiors[idx][y - 1][x - 1]
      boxes.append((r0, c0, r0 + n - 1, c0 + n - 1))
    if not _scene_ok(g, boxes, n, ei, qi):
      continue
    return {"input": g, "output": ans}
  raise RuntimeError("could not build a valid scene")


def validate():
  """Reconstructs the canonical fixtures through explicit generate calls."""
  train = [
      generate(input_grid=_decode(_TRAIN1), question=(18, 6), size=5,
               relation="lines", fill=2),
      generate(input_grid=_decode(_TRAIN2), question=(21, 21), size=4,
               relation="parity"),
  ]
  test = [
      generate(input_grid=_decode(_TEST1), question=(20, 19), size=5,
               relation="parity"),
      generate(input_grid=_decode(_TEST2), question=(17, 16), size=6,
               relation="mirror"),
  ]
  return {"train": train, "test": test}
