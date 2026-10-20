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

"""ARC task ac2e8ecf: hollow frames rise, crosses fall.

Rule. A black canvas holds single-colour objects of two kinds.
- Hollow frames are one cell thick, at least 3x3, and enclose background.
- Crosses have no hole. Each one has a full-width horizontal bar and a
  full-height vertical bar that cross strictly inside its bounding box.
Every object keeps its shape, colour and columns.
- Frames move up to the top edge and crosses move down to the bottom edge.
- Stacking uses bounding boxes.
- Frames are processed by top row, starting with the highest.
- Crosses are processed by bottom row, starting with the lowest.
- Each object moves until it meets the grid edge or the box of an
  already-placed object of the same kind that shares any of its columns.
- Objects of different kinds pass through each other, as the 1-cross and
  the 2-frame do in train pair 1.

Canonical-compatible cross contact. In every fixture, a cross that rests on
another cross touches it through aligned vertical bars. There, box-level and
cell-level gravity agree. Frames always agree because their top and bottom
rows are full.
- The default cross_contact="cell" requires this agreement, in both random
  scenes and explicit scenes.
- "box_gap" (at least one cross rests on a box without bar contact) and
  "any" are labelled opt-in extensions. They rely on box-level semantics
  that the fixtures cannot confirm.

Random construction (constructive, no blind packing):
- The width is cut into vertical lanes 3..9 wide, separated by optional
  blank columns.
- Each lane holds at most height//3 objects, and their heights sum to at
  most the grid height. As a result:
  - every input arrangement fits;
  - output frames stay inside the top F rows of the lane and output crosses
    inside the bottom C rows, with F + C <= height, so the two kinds never
    collide.
- Objects in different lanes never share columns.
- Inside a lane, widths and offsets vary, so partial column overlaps and
  chains occur.
- A spine lane forces every object to contain one common column.
- Requirements are built into a focus lane, which is a spine lane:
  - stacking puts two objects of one kind there;
  - cross-on-cross stacking puts two crosses there, with bars aligned in
    cell mode;
  - pass-through puts a cross above a frame there in the input.
- Box sizes grow from 3x3 under an ink budget.
- Vertical slack is scattered randomly.
- Colours are assigned so that same-colour objects never touch, even
  diagonally, in either the input or the output.

Scope:
- Grid size: sides 10..30. Random grids default to 10..22.
- Counts: 1..6 frames and 1..6 crosses on request, 1..4 each by default.
- Infeasible requests raise ValueError immediately. A request is infeasible
  if it breaks the ink majority, (w//3)*(h//3) >= objects, or the count
  needs of the requested requirements.
- Defaults: stacking is required with p=0.85, cross-on-cross stacking with
  p=0.45 when there are at least 2 crosses, and pass-through with p=0.75.
- Explicit scenes are validated for the following, all as ValueError:
  - malformed or nested arguments;
  - out-of-bounds or overlapping boxes;
  - same-colour contact;
  - missing kinds;
  - heavy ink;
  - output collisions or overflow;
  - identity pairs;
  - cross_contact disagreement.
- Ties: input boxes are disjoint, so same-kind objects that share columns
  always have distinct sort rows. Processing order is therefore never tied.
"""

import random

import common


_KINDS = ("frame", "cross")
_CONTACT_MODES = ("cell", "box_gap", "any")
_MIN_SIDE, _MAX_SIDE = 10, 30
_RAND_LO, _RAND_HI = 10, 22
_MAX_COUNT = 6
_DEFAULT_MAX_COUNT = 4
_MAX_BOX = 6
_MAX_LANE = 9
_ATTEMPTS = 300
_SAFE_AFTER = 150


def _is_int(v):
  return isinstance(v, int) and not isinstance(v, bool)


def _cells(kind, h, w, cr, cc):
  """Relative cells of an object of the given kind and box size."""
  cells = set()
  if kind == "frame":
    for r in range(h):
      for c in range(w):
        if r in (0, h - 1) or c in (0, w - 1):
          cells.add((r, c))
  else:
    for c in range(w):
      cells.add((cr, c))
    for r in range(h):
      cells.add((r, cc))
  return cells


def _abs_cells(o, top=None):
  t = o[2] if top is None else top
  return {(t + r, o[3] + c) for (r, c) in _cells(o[0], o[4], o[5], o[6], o[7])}


def _box(o, top=None):
  t = o[2] if top is None else top
  return (t, o[3], t + o[4] - 1, o[3] + o[5] - 1)


def _boxes_overlap(a, b):
  return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _cols_overlap(a, b):
  return a[3] <= b[3] + b[5] - 1 and b[3] <= a[3] + a[5] - 1


def _touch(ca, cb):
  """True if any cell of ca equals or is 8-adjacent to a cell of cb."""
  for (y, x) in ca:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        if (y + dy, x + dx) in cb:
          return True
  return False


def _ink(o):
  if o[0] == "frame":
    return 2 * (o[4] + o[5]) - 4
  return o[4] + o[5] - 1


def _frame_order(objs):
  return sorted((i for i, o in enumerate(objs) if o[0] == "frame"),
                key=lambda i: (objs[i][2], objs[i][3]))


def _cross_order(objs):
  return sorted((i for i, o in enumerate(objs) if o[0] == "cross"),
                key=lambda i: (-(objs[i][2] + objs[i][4]), objs[i][3]))


def _stack(objs, height):
  """Returns the output top row of every object (box-level gravity)."""
  tops = [None] * len(objs)
  placed = []
  for i in _frame_order(objs):
    ny = 0
    for (j, t) in placed:
      if _cols_overlap(objs[i], objs[j]):
        ny = max(ny, t + objs[j][4])
    tops[i] = ny
    placed.append((i, ny))
  placed = []
  for i in _cross_order(objs):
    limit = height
    for (j, t) in placed:
      if _cols_overlap(objs[i], objs[j]):
        limit = min(limit, t)
    tops[i] = limit - objs[i][4]
    placed.append((i, tops[i]))
  return tops


def _support_bars(objs, tops, i):
  """Bar columns of crosses whose output box directly supports cross i."""
  below = tops[i] + objs[i][4]
  return {objs[j][3] + objs[j][7] for j in range(len(objs))
          if j != i and objs[j][0] == "cross" and tops[j] == below and
          _cols_overlap(objs[i], objs[j])}


def _aligned_rests(objs, tops, height):
  """For each cross resting on a cross: True if the vertical bars touch."""
  res = []
  for i in _cross_order(objs):
    if tops[i] + objs[i][4] == height:
      continue
    res.append(objs[i][3] + objs[i][7] in _support_bars(objs, tops, i))
  return res


def _object_error(o, width, height):
  if not isinstance(o, (list, tuple)) or len(o) != 8:
    return "each object must be a sequence (kind, colour, top, left, h, w, cr, cc)"
  kind, colour, top, left, h, w, cr, cc = o
  if not isinstance(kind, str) or kind not in _KINDS:
    return "kind must be 'frame' or 'cross'"
  if not all(_is_int(v) for v in (colour, top, left, h, w, cr, cc)):
    return "object fields other than kind must be integers"
  if not 1 <= colour <= 9:
    return "colour must be 1..9"
  if h < 3 or w < 3:
    return "object boxes must be at least 3x3"
  if top < 0 or left < 0 or top + h > height or left + w > width:
    return "object outside the grid"
  if kind == "cross" and not (1 <= cr <= h - 2 and 1 <= cc <= w - 2):
    return "cross bars must be strictly interior"
  return None


def _scene_error(objs, width, height):
  """Input-scene problems, or None. Disjoint boxes imply no order ties."""
  if not objs:
    return "explicit scene needs objects"
  for o in objs:
    err = _object_error(o, width, height)
    if err:
      return err
  if {o[0] for o in objs} != set(_KINDS):
    return "scene needs at least one frame and one cross"
  boxes = [_box(o) for o in objs]
  cells = [_abs_cells(o) for o in objs]
  for i in range(len(objs)):
    for j in range(i + 1, len(objs)):
      if _boxes_overlap(boxes[i], boxes[j]):
        return "object bounding boxes overlap or nest"
      if objs[i][1] == objs[j][1] and _touch(cells[i], cells[j]):
        return "same-colour objects touch and would merge"
  if 2 * sum(_ink(o) for o in objs) >= width * height:
    return "too much ink: background must stay the majority"
  return None


def _output_error(objs, tops, height, contact):
  """Output-side problems, or None."""
  for o, t in zip(objs, tops):
    if t < 0 or t + o[4] > height:
      return "stacked objects do not fit in the grid"
  boxes = [_box(o, t) for o, t in zip(objs, tops)]
  cells = [_abs_cells(o, t) for o, t in zip(objs, tops)]
  for i in range(len(objs)):
    for j in range(i + 1, len(objs)):
      if objs[i][0] != objs[j][0] and _boxes_overlap(boxes[i], boxes[j]):
        return "a frame and a cross collide in the output"
      if objs[i][1] == objs[j][1] and _touch(cells[i], cells[j]):
        return "same-colour objects touch in the output"
  if all(t == o[2] for o, t in zip(objs, tops)):
    return "scene is already settled (identity pair)"
  rests = _aligned_rests(objs, tops, height)
  if contact == "cell" and not all(rests):
    return ("a cross rests on another cross's box without bar contact; "
            "pass cross_contact='box_gap' or 'any' to allow this extension")
  if contact == "box_gap" and all(rests):
    return "cross_contact='box_gap' needs a cross resting without bar contact"
  return None


def _render(objs, width, height, tops=None):
  g = common.grid(width, height, 0)
  for i, o in enumerate(objs):
    t = o[2] if tops is None else tops[i]
    for (y, x) in _abs_cells(o, t):
      if g[y][x] != 0:
        raise ValueError("objects overlap")
      g[y][x] = o[1]
  return g


def _has_frame_stack(objs, tops):
  return any(o[0] == "frame" and t > 0 for o, t in zip(objs, tops))


def _has_cross_stack(objs, tops, height):
  return any(o[0] == "cross" and t + o[4] < height for o, t in zip(objs, tops))


def _has_pass_through(objs):
  """True if a cross starts above a frame that shares its columns."""
  for f in objs:
    if f[0] != "frame":
      continue
    for c in objs:
      if c[0] == "cross" and _cols_overlap(f, c) and c[2] + c[4] <= f[2]:
        return True
  return False


def _feasible(w, h, nf, nc):
  """Ink minority and lane capacity with minimal 3x3 boxes."""
  return 2 * (8 * nf + 5 * nc) < w * h and (w // 3) * (h // 3) >= nf + nc


def _fix_bars(objs, tops, height, contact):
  """Sets cross bar columns to satisfy the contact mode; None if impossible."""
  objs = [list(o) for o in objs]
  last = None
  for i in _cross_order(objs):
    o = objs[i]
    if tops[i] + o[4] == height:
      continue
    bars = _support_bars(objs, tops, i)
    interior = range(o[3] + 1, o[3] + o[5] - 1)
    if contact == "cell":
      if o[3] + o[7] not in bars:
        opts = sorted(b for b in bars if b in interior)
        if not opts:
          return None
        o[7] = random.choice(opts) - o[3]
    else:
      last = (i, bars, interior)
  if contact == "box_gap" and all(_aligned_rests(objs, tops, height)):
    if last is None:
      return None
    i, bars, interior = last
    opts = [c for c in interior if c not in bars]
    if not opts:
      return None
    objs[i][7] = random.choice(opts) - objs[i][3]
  return [tuple(o) for o in objs]


def _colour(objs, tops):
  """DSATUR colouring so same-colour objects never touch (in or out)."""
  n = len(objs)
  cin = [_abs_cells(o) for o in objs]
  cout = [_abs_cells(o, t) for o, t in zip(objs, tops)]
  adj = [set() for _ in range(n)]
  for i in range(n):
    for j in range(i + 1, n):
      if _touch(cin[i], cin[j]) or _touch(cout[i], cout[j]):
        adj[i].add(j)
        adj[j].add(i)
  colours = [0] * n
  for _ in range(n):
    best = None
    for i in range(n):
      if colours[i]:
        continue
      sat = len({colours[j] for j in adj[i] if colours[j]})
      key = (sat, len(adj[i]), random.random())
      if best is None or key > best[0]:
        best = (key, i)
    i = best[1]
    banned = {colours[j] for j in adj[i]}
    choices = [c for c in range(1, 10) if c not in banned]
    if not choices:
      return None
    colours[i] = random.choice(choices)
  return [(o[0], colours[i]) + tuple(o[2:]) for i, o in enumerate(objs)]


def _attempt(wid, hgt, nf, nc, need_stack, need_cstack, need_pass, contact,
             safe):
  """One constructive lane-based scene; None if a soft check fails."""
  n = nf + nc
  cap = hgt // 3
  focus = []
  if need_cstack:
    focus = ["cross", "cross"]
  elif need_stack:
    kinds = [k for k, c in (("frame", nf), ("cross", nc)) if c >= 2]
    focus = [random.choice(kinds)] * 2
  force_pass = need_pass or safe
  if force_pass:
    for k in _KINDS:
      if k not in focus:
        focus.append(k)
  f = len(focus)
  lmin = -(-n // cap)
  lmax = min(wid // 3, n - f + 1 if f else n)
  if lmax < lmin:
    return None
  nl = random.randint(lmin, lmax)
  if random.random() < 0.6:
    nl = min(nl, random.randint(lmin, lmax))
  rest = (["frame"] * (nf - focus.count("frame")) +
          ["cross"] * (nc - focus.count("cross")))
  random.shuffle(rest)
  lanes = [list(focus)] + [[] for _ in range(nl - 1)]
  for lane in lanes:
    if not lane:
      lane.append(rest.pop())
  for k in rest:
    random.choice([lane for lane in lanes if len(lane) < cap]).append(k)
  spec = list(zip(lanes, [bool(f)] + [False] * (nl - 1)))
  random.shuffle(spec)
  widths = [3] * nl
  gaps = [0] * (nl + 1)
  for _ in range(wid - 3 * nl):
    grow = [i for i in range(nl) if widths[i] < _MAX_LANE]
    if grow and random.random() < 0.55:
      widths[random.choice(grow)] += 1
    else:
      gaps[random.randrange(nl + 1)] += 1
  xs = []
  x = gaps[0]
  for i in range(nl):
    xs.append(x)
    x += widths[i] + gaps[i + 1]
  objs, lane_of = [], []
  for li, (kinds, is_focus) in enumerate(spec):
    order = list(kinds)
    random.shuffle(order)
    if is_focus and force_pass:
      ci = order.index("cross")
      fi = len(order) - 1 - order[::-1].index("frame")
      if ci > fi:
        order[ci], order[fi] = order[fi], order[ci]
    for k in order:
      objs.append([k, 0, 0, 0, 3, 3, 1, 1])
      lane_of.append(li)
  ink = sum(_ink(o) for o in objs)
  lane_h = [3 * len(k) for k, _ in spec]
  for _ in range(random.randint(0, 3 * n)):
    i = random.randrange(len(objs))
    o, li = objs[i], lane_of[i]
    d = 2 if o[0] == "frame" else 1
    if 2 * (ink + d) >= wid * hgt:
      continue
    if random.random() < 0.5:
      if o[4] < _MAX_BOX and lane_h[li] < hgt:
        o[4] += 1
        lane_h[li] += 1
        ink += d
    elif o[5] < min(_MAX_BOX, widths[li]):
      o[5] += 1
      ink += d
  for li, (_, is_focus) in enumerate(spec):
    x0, lw = xs[li], widths[li]
    members = [i for i in range(len(objs)) if lane_of[i] == li]
    spine = None
    if is_focus or safe or random.random() < 0.6:
      spine = random.randint(x0 + 1, x0 + lw - 2)
    for i in members:
      o = objs[i]
      w = o[5]
      on_spine = spine is not None and o[0] == "cross" and contact == "cell"
      if spine is None:
        lo, hi = x0, x0 + lw - w
      elif on_spine:
        lo, hi = max(x0, spine - w + 2), min(x0 + lw - w, spine - 1)
      else:
        lo, hi = max(x0, spine - w + 1), min(x0 + lw - w, spine)
      o[3] = random.randint(lo, hi)
      if o[0] == "cross":
        o[6] = random.randint(1, o[4] - 2)
        o[7] = spine - o[3] if on_spine else random.randint(1, w - 2)
      else:
        o[6] = o[7] = 0
    gaps_v = [0] * (len(members) + 1)
    for _ in range(hgt - lane_h[li]):
      gaps_v[random.randrange(len(gaps_v))] += 1
    y = gaps_v[0]
    for k, i in enumerate(members):
      objs[i][2] = y
      y += objs[i][4] + gaps_v[k + 1]
  objs = [tuple(o) for o in objs]
  tops = _stack(objs, hgt)
  if contact != "any":
    objs = _fix_bars(objs, tops, hgt, contact)
    if objs is None:
      return None
  if need_stack and not (_has_frame_stack(objs, tops) or
                         _has_cross_stack(objs, tops, hgt)):
    return None
  if need_cstack and not _has_cross_stack(objs, tops, hgt):
    return None
  if need_pass and not _has_pass_through(objs):
    return None
  objs = _colour(objs, tops)
  if objs is None:
    return None
  if (_scene_error(objs, wid, hgt) or
      _output_error(objs, tops, hgt, contact)):
    return None
  return objs


def _sample(width, height, nf_req, nc_req, req_stack, req_cstack, req_pass,
            contact):
  """Picks a feasible size/count combination, then builds a scene."""
  min_nc = 2 if (contact == "box_gap" or req_cstack) else 1
  ws = [width] if width is not None else range(_RAND_LO, _RAND_HI + 1)
  hs = [height] if height is not None else range(_RAND_LO, _RAND_HI + 1)
  nfs = [nf_req] if nf_req is not None else range(1, _DEFAULT_MAX_COUNT + 1)
  ncs = [nc_req] if nc_req is not None else range(1, _DEFAULT_MAX_COUNT + 1)
  combos = [(w, h, a, b) for w in ws for h in hs for a in nfs for b in ncs
            if b >= min_nc and not (req_stack and max(a, b) < 2) and
            _feasible(w, h, a, b)]
  if not combos:
    raise ValueError("requested sizes/counts cannot hold the objects: need "
                     "2*(8*frames+5*crosses) < w*h and "
                     "(w//3)*(h//3) >= frames+crosses")
  wid, hgt, nf, nc = random.choice(combos)
  stack = req_stack if req_stack is not None else (
      max(nf, nc) >= 2 and random.random() < 0.85)
  cstack = req_cstack if req_cstack is not None else (
      nc >= 2 and random.random() < 0.45)
  if contact == "box_gap":
    cstack = True
  pas = req_pass if req_pass is not None else random.random() < 0.75
  for attempt in range(_ATTEMPTS):
    objs = _attempt(wid, hgt, nf, nc, stack, cstack, pas, contact,
                    attempt >= _SAFE_AFTER)
    if objs is not None:
      return wid, hgt, objs
  raise RuntimeError("could not build a scene after bounded retries")


def generate(width=None, height=None, objects=None, num_frames=None,
             num_crosses=None, require_stack=None, require_cross_stack=None,
             require_pass_through=None, cross_contact=None):
  """Builds one input/output pair.

  Args:
    width: grid width, an int in 10..30. Random scenes default to 10..22.
      Required with objects.
    height: grid height, an int in 10..30. Same convention as width.
    objects: explicit list of (kind, colour, top, left, h, w, cr, cc)
      sequences. kind is "frame" or "cross". cr and cc are the cross's bar
      offsets; for frames they are ignored but must be ints. The scene must
      satisfy all of the following:
      - both kinds are present;
      - boxes are disjoint, though they may touch;
      - same-colour objects do not touch in the input or the output;
      - ink covers less than half the grid;
      - output frames and crosses do not collide;
      - the output differs from the input;
      - cross contact satisfies cross_contact.
      Only cross_contact may be combined with this argument.
    num_frames: number of frames in a random scene, 1..6 (default 1..4).
    num_crosses: number of crosses in a random scene, 1..6 (default 1..4).
    require_stack: True forces an object to rest on another object of the
      same kind. False imposes nothing. None picks True with p=0.85 when
      possible.
    require_cross_stack: True forces a cross to rest on another cross; in
      the default cell mode their vertical bars are aligned. None picks True
      with p=0.45 when there are at least 2 crosses.
    require_pass_through: True forces a cross to start above a frame that
      shares its columns, so the two pass through each other. None picks
      True with p=0.75.
    cross_contact: controls how one cross may rest on another.
      - "cell" (default, canonical): every such rest has bar-to-bar contact.
      - "box_gap" (opt-in extension): at least one rest leaves a visible
        gap. Requires at least 2 crosses.
      - "any" (opt-in extension): no constraint.
  """
  for name, v in (("width", width), ("height", height)):
    if v is not None and (not _is_int(v) or not _MIN_SIDE <= v <= _MAX_SIDE):
      raise ValueError(name + " must be an int in 10..30")
  for name, v in (("require_stack", require_stack),
                  ("require_cross_stack", require_cross_stack),
                  ("require_pass_through", require_pass_through)):
    if v is not None and not isinstance(v, bool):
      raise ValueError(name + " must be None, True or False")
  if cross_contact is not None and (not isinstance(cross_contact, str) or
                                    cross_contact not in _CONTACT_MODES):
    raise ValueError("cross_contact must be 'cell', 'box_gap' or 'any'")
  contact = cross_contact if cross_contact is not None else "cell"
  if objects is not None:
    if width is None or height is None:
      raise ValueError("explicit objects require width and height")
    if any(v is not None for v in (num_frames, num_crosses, require_stack,
                                   require_cross_stack,
                                   require_pass_through)):
      raise ValueError("random controls cannot be combined with objects")
    if not isinstance(objects, (list, tuple)):
      raise ValueError("objects must be a list of 8-field sequences")
    objs = []
    for o in objects:
      if not isinstance(o, (list, tuple)) or len(o) != 8:
        raise ValueError("each object must be an 8-field sequence")
      objs.append(tuple(o))
    err = _scene_error(objs, width, height)
    if err:
      raise ValueError(err)
    tops = _stack(objs, height)
    err = _output_error(objs, tops, height, contact)
    if err:
      raise ValueError(err)
  else:
    for name, v in (("num_frames", num_frames), ("num_crosses", num_crosses)):
      if v is not None and (not _is_int(v) or not 1 <= v <= _MAX_COUNT):
        raise ValueError(name + " must be an int in 1..6")
    if num_crosses is not None and num_crosses < 2:
      if contact == "box_gap":
        raise ValueError("cross_contact='box_gap' needs at least 2 crosses")
      if require_cross_stack:
        raise ValueError("require_cross_stack needs at least 2 crosses")
    if (require_stack and num_frames is not None and num_crosses is not None
        and max(num_frames, num_crosses) < 2):
      raise ValueError("require_stack needs 2 objects of one kind")
    width, height, objs = _sample(width, height, num_frames, num_crosses,
                                  require_stack, require_cross_stack,
                                  require_pass_through, contact)
    tops = _stack(objs, height)
  return {"input": _render(objs, width, height),
          "output": _render(objs, width, height, tops)}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(width=13, height=13, objects=[
          ("frame", 1, 2, 4, 3, 3, 0, 0),
          ("cross", 1, 2, 10, 3, 3, 1, 1),
          ("cross", 2, 4, 0, 3, 3, 1, 1),
          ("cross", 8, 5, 6, 3, 4, 1, 2),
          ("frame", 5, 8, 2, 3, 4, 0, 0),
          ("frame", 2, 9, 10, 3, 3, 0, 0)]),
      generate(width=16, height=13, objects=[
          ("cross", 2, 1, 9, 3, 3, 1, 1),
          ("frame", 1, 2, 1, 3, 3, 0, 0),
          ("cross", 1, 4, 12, 4, 4, 2, 1),
          ("frame", 8, 5, 5, 4, 3, 0, 0)]),
      generate(width=17, height=16, objects=[
          ("cross", 1, 0, 0, 3, 5, 1, 1),
          ("cross", 8, 2, 12, 3, 4, 1, 2),
          ("frame", 2, 3, 2, 4, 4, 0, 0),
          ("frame", 3, 4, 9, 3, 3, 0, 0),
          ("cross", 1, 8, 5, 4, 4, 1, 2),
          ("cross", 3, 9, 0, 3, 3, 1, 1),
          ("frame", 8, 10, 12, 3, 4, 0, 0)]),
  ]
  test = [
      generate(width=15, height=16, objects=[
          ("cross", 2, 1, 10, 4, 5, 1, 2),
          ("frame", 3, 2, 3, 3, 3, 0, 0),
          ("cross", 8, 3, 0, 4, 3, 1, 1),
          ("frame", 1, 6, 4, 3, 4, 0, 0),
          ("frame", 1, 6, 10, 5, 5, 0, 0),
          ("cross", 2, 10, 0, 3, 3, 1, 1)]),
  ]
  return {"train": train, "test": test}
