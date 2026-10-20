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

"""ARC task 20a9e565: extend a growing sequence of figures, read it in a window.

Rule
  The input shows a sequence of groups. A group is a run of consecutive
  occupied lines (rows or columns), and groups are separated by one empty
  line. Each group is derived from the previous one:
    - its colour advances along a colour cycle, or stays the same;
    - every line grows by its own size recurrence (constant, linear, or two
      alternating increments);
    - each line is continued with its periodic pattern, where a period may
      carry a colour permutation;
    - when the group gets longer, its extra lines are built from earlier
      lines of the same group.
  Two grey (5) L-shaped corner pieces mark a window. The window lies on a
  group that is not drawn yet: the next one, or the one after it. The output
  is the content of the continued sequence inside that window.

Scope
  Scenes are built in a canonical frame: groups are row runs and the sequence
  grows downwards. The scene is then optionally flipped vertically and/or
  transposed. Four latent families are supported:
    comb   - a solid bar growing on one side, plus tooth lines. Each step the
             group gets one line longer by copying its last tooth line
             (train 1).
    ladder - a fixed number of one-sided periodic lines growing linearly from
             a common anchor (train 3; the window can lie two groups ahead).
    mirror - lines that are mirror-symmetric about a centre and periodic
             outwards, optionally with a colour permutation per period. Their
             half widths grow by two alternating increments (train 2, test 1).
    stair  - a cap followed by staircase pieces. Each group cycles its colours
             and adds one more piece pushed outwards (test 2).
  Group colours follow a 2- or 3-colour cycle that is fully visible. The
  exception is multi-coloured mirror patterns, whose colours stay constant.
  The window always lies inside a single undrawn group.
"""

import copy
import random

import common

_BG = 0
_MARK = 5
_COLOURS = [1, 2, 3, 4, 6, 7, 8, 9]


def _step(phi, v, k=1):
  for _ in range(k):
    v = phi.get(v, v)
  return v


def _cycle(colours):
  n = len(colours)
  if n < 2:
    return {}
  return {colours[i]: colours[(i + 1) % n] for i in range(n)}


def _qval(block, sigma, t):
  v = block[t % len(block)]
  if v == _BG:
    return _BG
  return _step(sigma, v, t // len(block))


def _line(cells):
  return (cells, min(cells), max(cells))


def _total(p):
  return p["n"] + p["m"] + 1


def _halfwidths(h0, a, b, count):
  hs = [h0]
  for j in range(1, count):
    hs.append(hs[-1] + (a if j % 2 == 1 else b))
  return hs


def _build_comb(p):
  cyc, a, d = p["colours"], p["anchor"], p["dir"]
  groups = []
  for k in range(_total(p)):
    col = cyc[k % len(cyc)]
    length = p["h0"] + p["g"] * k
    lines = [_line({a + d * t: col for t in range(length)})]
    for j in range(p["L0"] - 1 + k):
      mask = p["masks"][min(j, len(p["masks"]) - 1)]
      lines.append(_line({a + d * o: col for o in mask}))
    groups.append(lines)
  return groups, _cycle(cyc)


def _build_ladder(p):
  cyc, a, d = p["colours"], p["anchor"], p["dir"]
  groups = []
  for k in range(_total(p)):
    col = cyc[k % len(cyc)]
    lines = []
    for block, base in p["lines"]:
      e = base + p["g"] * k
      cells = {a + d * t: col for t in range(e + 1) if block[t % len(block)]}
      lo, hi = (a, a + e) if d > 0 else (a - e, a)
      lines.append((cells, lo, hi))
    groups.append(lines)
  return groups, _cycle(cyc)


def _build_mirror(p):
  phi = _cycle(p["colours"])
  c, half, total = p["centre"], p["half"], _total(p)
  groups = [[] for _ in range(total)]
  for spec in p["lines"]:
    hs = _halfwidths(spec["h0"], spec["a"], spec["b"], total)
    for k in range(total):
      cells = {}
      for t in range(hs[k] + 1):
        v = _qval(spec["block"], spec["sigma"], t)
        if v != _BG:
          v = _step(phi, v, k)
          cells[c - t] = v
          cells[c + half + t] = v
      groups[k].append((cells, c - hs[k], c + half + hs[k]))
  return groups, phi


def _build_stair(p):
  cyc, left, right, s = p["colours"], p["left"], p["right"], p["step"]
  groups = []
  for k in range(_total(p)):
    ck = cyc[k % len(cyc)]
    lines = [_line({x: ck for x in range(left, right + 1)})]
    if p["cap_h"] == 2:
      lines.append(_line({left: ck, right: ck}))
    for j in range(1, k + 1):
      cj = cyc[(k + j) % len(cyc)]
      cp = cyc[(k + j - 1) % len(cyc)]
      piece = {}
      for x in range(left - s * j, left - s * (j - 1) + 1):
        piece[x] = cj
      for x in range(right + s * (j - 1), right + s * j + 1):
        piece[x] = cj
      lines.append(_line(piece))
      lines.append(_line({left - s * j: cj, left - s * (j - 1): cp,
                          right + s * (j - 1): cp, right + s * j: cj}))
    groups.append(lines)
  return groups, _cycle(cyc)


_BUILDERS = {"comb": _build_comb, "ladder": _build_ladder,
             "mirror": _build_mirror, "stair": _build_stair}


def _orient(rows, flip, transpose):
  rows = [list(r) for r in rows]
  if flip:
    rows = rows[::-1]
  if transpose:
    rows = [list(c) for c in zip(*rows)]
  return rows


def _render(groups, p):
  hc, wc = p["hc"], p["wc"]
  inp = [list(r) for r in common.grid(wc, hc, _BG)]
  full = [list(r) for r in common.grid(wc, hc, _BG)]
  row = p["start"]
  for gi, lines in enumerate(groups):
    for li, (cells, _, _) in enumerate(lines):
      r = row + li
      if 0 <= r < hc:
        for x, v in cells.items():
          if 0 <= x < wc:
            full[r][x] = v
            if gi < p["n"]:
              inp[r][x] = v
    row += len(lines) + 1
  r0, r1, c0, c1 = p["window"]
  crop = [full[r][c0:c1 + 1] for r in range(r0, r1 + 1)]
  inp = _orient(inp, p["flip"], p["transpose"])
  if p["flip"]:
    r0, r1 = hc - 1 - r1, hc - 1 - r0
  if p["transpose"]:
    r0, r1, c0, c1 = c0, c1, r0, r1
  for r, c in ((r0, c0), (r0, c0 + 1), (r0 + 1, c0),
               (r1 - 1, c1), (r1, c1 - 1), (r1, c1)):
    inp[r][c] = _MARK
  return inp, _orient(crop, p["flip"], p["transpose"])


def _best_period(seq):
  # Shortest-scoring period (possibly with a colour permutation) at the end.
  best = None
  n = len(seq)
  for per in range(1, n):
    f, inv, run = {}, {}, 0
    for i in range(n - 1, per - 1, -1):
      a, b = seq[i - per], seq[i]
      if (a == _BG) != (b == _BG):
        break
      if f.get(a, b) != b or inv.get(b, a) != a:
        break
      f[a] = b
      inv[b] = a
      run += 1
    if run >= per and (best is None or run - per > best[0]):
      best = (run - per, per, f)
  return best


def _grow(seq, k):
  seq = list(seq)
  if k <= 0:
    return seq
  found = _best_period(seq)
  per, f = (1, {}) if found is None else (found[1], found[2])
  for _ in range(k):
    v = seq[-per]
    seq.append(f.get(v, v))
  return seq


def _continues(prev, cur, phi):
  # The visible previous line must determine the new line's continuation.
  pcells, plo, phi_ = prev
  cells, lo, hi = cur
  if lo > plo or hi < phi_:
    return False
  seq = [_step(phi, pcells.get(x, _BG)) for x in range(plo, phi_ + 1)]
  seq = _grow(seq, hi - phi_)
  seq = _grow(seq[::-1], plo - lo)[::-1]
  return seq == [cells.get(x, _BG) for x in range(lo, hi + 1)]


def _consistent(groups, phi, p, inp, out):
  n, wc = p["n"], p["wc"]
  for lines in groups[:-1]:
    for cells, lo, hi in lines:
      if not cells or min(cells) != lo or max(cells) != hi:
        return False
      if lo < 0 or hi >= wc:
        return False
  for k in range(n, len(groups)):
    prev = groups[k - 1]
    for li, cur in enumerate(groups[k]):
      if li < len(prev) and not _continues(prev[li], cur, phi):
        return False
  cols = sorted({x for lines in groups[:n] for cells, _, _ in lines
                 for x in cells})
  runs = 1 + sum(1 for a, b in zip(cols, cols[1:]) if b != a + 1)
  if runs >= n:
    return False
  counts = {}
  for row in inp:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  if any(c >= counts.get(_BG, 0) for v, c in counts.items() if v != _BG):
    return False
  if all(v == _BG for row in out for v in row):
    return False
  return True


def _sample_comb():
  colours = random.sample(_COLOURS, random.choice([2, 3]))
  n = random.randint(len(colours) + 1, 5)
  m = random.choice([0, 0, 1])
  l0 = random.choice([2, 2, 3])
  h0 = random.randint(2, 5)
  g = random.choice([1, 1, 2])
  w = random.randint(1, min(3, h0 - 1))
  masks = []
  for _ in range(l0 - 1):
    masks.append(sorted(random.sample(range(w + 1),
                                      random.randint(1, w + 1))))
  total = n + m + 1
  start = random.randint(0, 2)
  need = start + sum(l0 + k for k in range(total)) + total - 1
  length = h0 + g * (total - 1)
  ml, mr = random.randint(0, 3), random.randint(0, 3)
  wc = ml + length + mr
  if need > 30 or wc > 30:
    return None
  d = random.choice([1, -1])
  return {"family": "comb", "hc": min(30, need + random.randint(0, 2)),
          "wc": wc, "start": start, "n": n, "m": m, "colours": colours,
          "L0": l0, "anchor": ml if d > 0 else wc - 1 - mr, "dir": d,
          "h0": h0, "g": g, "masks": masks}


def _sample_ladder():
  colours = random.sample(_COLOURS, random.choice([2, 3]))
  n = random.randint(len(colours) + 1, 6)
  m = random.choice([0, 0, 1])
  total = n + m + 1
  count = random.randint(2, 4)
  start = random.randint(0, 2)
  need = start + count * total + total - 1
  if need > 30:
    return None
  g = random.randint(1, 3)
  lines = []
  for _ in range(count):
    for _ in range(20):
      per = random.choice([1, 2, 2, 3])
      block = [1] + [random.randint(0, 1) for _ in range(per - 1)]
      base = random.randint(1, 4)
      if all(block[(base + g * k) % per] for k in range(total - 1)):
        lines.append([block, base])
        break
    else:
      return None
  if all(all(block) for block, _ in lines):
    return None
  ml, mr = random.randint(0, 3), random.randint(0, 3)
  e = max(base for _, base in lines) + g * (total - 1)
  wc = ml + e + 1 + mr
  if wc > 30:
    return None
  d = random.choice([1, -1])
  return {"family": "ladder", "hc": min(30, need + random.randint(0, 2)),
          "wc": wc, "start": start, "n": n, "m": m, "colours": colours,
          "anchor": ml if d > 0 else wc - 1 - mr, "dir": d, "g": g,
          "lines": lines}


def _sample_mirror():
  multi = random.random() < 0.4
  if multi:
    pal = random.sample(_COLOURS, random.choice([2, 3]))
    sigma = _cycle(pal)
    colours = []
    n = random.randint(3, 6)
  else:
    colours = random.sample(_COLOURS, random.choice([2, 3]))
    sigma = {}
    n = random.randint(len(colours) + 1, 6)
  m = random.choice([0, 0, 1])
  total = n + m + 1
  count = random.choice([2, 2, 3])
  start = random.randint(0, 2)
  need = start + count * total + total - 1
  if need > 30:
    return None
  half = random.choice([0, 1])
  specs = []
  for _ in range(count):
    for _ in range(40):
      per = random.randint(2, 5)
      if multi:
        block = [random.choice(pal) if random.random() < 0.85 else _BG
                 for _ in range(per)]
      else:
        block = [colours[0] if random.random() < 0.65 else _BG
                 for _ in range(per)]
      if all(v == _BG for v in block):
        continue
      h0 = random.randint(0, 3)
      a = random.choice([0, 1, 1, 2, 2, 3])
      b = random.choice([0, 1, 1, 2, 2, 3])
      if a + b == 0:
        continue
      hs = _halfwidths(h0, a, b, total)
      if any(_qval(block, sigma, hs[k]) == _BG for k in range(total - 1)):
        continue
      specs.append({"block": block, "sigma": dict(sigma), "h0": h0,
                    "a": a, "b": b})
      break
    else:
      return None
  hmax = max(_halfwidths(s["h0"], s["a"], s["b"], total)[-1] for s in specs)
  ml, mr = random.randint(0, 2), random.randint(0, 2)
  centre = ml + hmax
  wc = centre + hmax + half + 1 + mr
  if wc > 30:
    return None
  return {"family": "mirror", "hc": min(30, need + random.randint(0, 2)),
          "wc": wc, "start": start, "n": n, "m": m, "colours": colours,
          "centre": centre, "half": half, "lines": specs}


def _sample_stair():
  colours = random.sample(_COLOURS, random.choice([2, 2, 3]))
  cap_h = random.choice([1, 2])
  s = random.randint(1, 3)
  w = random.randint(2, 6)
  n = random.choice([3, 3, 4])
  if n < len(colours) + 1:
    return None
  m = random.choice([0, 0, 1])
  t = n + m
  start = random.randint(0, 2)
  need = start + sum(cap_h + 2 * k for k in range(t + 1)) + t
  ml, mr = random.randint(0, 3), random.randint(0, 3)
  left = ml + s * t
  wc = left + w + s * t + 1 + mr
  if need > 30 or wc > 30:
    return None
  return {"family": "stair", "hc": min(30, need + random.randint(0, 2)),
          "wc": wc, "start": start, "n": n, "m": m, "colours": colours,
          "left": left, "right": left + w, "step": s, "cap_h": cap_h}


_SAMPLERS = {"comb": _sample_comb, "ladder": _sample_ladder,
             "mirror": _sample_mirror, "stair": _sample_stair}


def _sample(family, width=None, height=None):
  for _ in range(200):
    p = _SAMPLERS[family]()
    if p is None:
      continue
    if width is not None:
      if p["wc"] > width:
        continue
      p["wc"] = width
    if height is not None:
      if p["hc"] > height:
        continue
      p["hc"] = height
    groups, phi = _BUILDERS[family](p)
    ts = p["start"] + sum(len(g) + 1 for g in groups[:-1])
    tl = len(groups[-1])
    if ts + tl > p["hc"] or tl < 2:
      continue
    xs = [x for cells, _, _ in groups[-1] for x in cells]
    lo, hi = max(0, min(xs)), min(p["wc"] - 1, max(xs))
    if hi - lo < 1:
      continue
    if random.random() < 0.5:
      r0, r1 = ts, ts + tl - 1
    else:
      r0 = random.randint(ts, ts + tl - 2)
      r1 = random.randint(r0 + 1, ts + tl - 1)
    if random.random() < 0.4:
      c0, c1 = lo, hi
    else:
      c0 = random.randint(lo, hi - 1)
      c1 = random.randint(c0 + 1, hi)
    p["window"] = [r0, r1, c0, c1]
    p["flip"] = random.random() < 0.5
    p["transpose"] = random.random() < 0.5
    inp, out = _render(groups, p)
    if _consistent(groups, phi, p, inp, out):
      return p
  return None


def generate(family=None, params=None, width=None, height=None):
  """Build one input/output pair.

  Args:
    family: optional family name ("comb", "ladder", "mirror", "stair").
      If None, a family is sampled at random.
    width: optional canonical width, before transpose (up to 30).
    height: optional canonical height, before transpose (up to 30).
      Requested sizes must fit the sequence; padding does not enlarge objects.
    params: optional complete latent scene description, used for fixture
      replay. It is a dict with these keys:
        family;
        hc, wc: canonical height and width;
        start: first group row;
        n: number of shown groups;
        m: number of hidden groups skipped before the target;
        colours: colour cycle;
        window: canonical [r0, r1, c0, c1];
        flip, transpose;
        plus the family-specific keys (see the builders).
      If None, a fresh random scene is sampled.
  """
  if family is not None and family not in _BUILDERS:
    raise ValueError("Unknown sequence family")
  for dimension in (width, height):
    if dimension is not None and (not isinstance(dimension, int) or not 2 <= dimension <= 30):
      raise ValueError("Canonical dimensions must be integers in 2..30")
  if params is not None:
    p = copy.deepcopy(params)
    if family is not None and p["family"] != family:
      raise ValueError("Explicit parameters do not match family")
    if (width is not None and p["wc"] != width) or (height is not None and p["hc"] != height):
      raise ValueError("Explicit parameters do not match dimensions")
  else:
    p = None
    for _ in range(40):
      fam = family or random.choice(["comb", "ladder", "mirror", "mirror",
                                     "stair"])
      p = _sample(fam, width, height)
      if p is not None:
        break
    if p is None:
      raise RuntimeError("could not construct a valid scene")
  if not (2 <= p["hc"] <= 30 and 2 <= p["wc"] <= 30):
    raise ValueError("Canonical dimensions must be in 2..30")
  r0, r1, c0, c1 = p["window"]
  if not (0 <= r0 < r1 < p["hc"] and 0 <= c0 < c1 < p["wc"]):
    raise ValueError("Window must be at least 2x2 and inside the canvas")
  groups, _ = _BUILDERS[p["family"]](p)
  inp, out = _render(groups, p)
  return {"input": inp, "output": out}


_SIG2 = {9: 4, 8: 9, 4: 8}

_FIXTURES = {
    "train": [
        {"family": "comb", "hc": 30, "wc": 30, "start": 1, "n": 4, "m": 0,
         "colours": [1, 2, 4], "L0": 2, "anchor": 28, "dir": -1, "h0": 4,
         "g": 1, "masks": [[0, 2]], "window": [19, 24, 26, 28],
         "flip": False, "transpose": True},
        {"family": "mirror", "hc": 29, "wc": 29, "start": 1, "n": 6,
         "m": 0, "colours": [], "centre": 14, "half": 0,
         "lines": [{"block": [9, 8, 8, 8], "sigma": _SIG2, "h0": 0,
                    "a": 3, "b": 1},
                   {"block": [9, 9, 8, 4], "sigma": _SIG2, "h0": 1,
                    "a": 1, "b": 3}],
         "window": [19, 20, 14, 27], "flip": False, "transpose": True},
        {"family": "ladder", "hc": 30, "wc": 30, "start": 1, "n": 5,
         "m": 1, "colours": [7, 2, 3], "anchor": 1, "dir": 1, "g": 2,
         "lines": [[[1], 4], [[1, 0], 4], [[1], 4]],
         "window": [25, 27, 1, 17], "flip": False, "transpose": True},
    ],
    "test": [
        {"family": "mirror", "hc": 30, "wc": 30, "start": 1, "n": 4,
         "m": 0, "colours": [6, 4], "centre": 14, "half": 1,
         "lines": [{"block": [0, 6, 6, 6, 0], "sigma": {}, "h0": 2,
                    "a": 1, "b": 4},
                   {"block": [6, 6, 0, 6, 6], "sigma": {}, "h0": 1,
                    "a": 3, "b": 2},
                   {"block": [6, 0, 0, 0, 6], "sigma": {}, "h0": 0,
                    "a": 4, "b": 1}],
         "window": [17, 18, 7, 27], "flip": True, "transpose": False},
        {"family": "stair", "hc": 29, "wc": 29, "start": 0, "n": 3,
         "m": 0, "colours": [3, 2], "left": 12, "right": 16, "step": 2,
         "cap_h": 2, "window": [15, 22, 6, 22], "flip": False,
         "transpose": False},
    ],
}


def validate():
  """Rebuild the canonical pairs from their explicit latent parameters."""
  return {"train": [generate(params=p) for p in _FIXTURES["train"]],
          "test": [generate(params=p) for p in _FIXTURES["test"]]}
