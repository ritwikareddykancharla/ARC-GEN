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

"""ARC-GEN style generator for task 53fb4810.

Rule: the background is 8 and blobs are made of colour 1. A blob may have a
striped strip of other colours attached to one of its four sides. The strip
is as wide as the blob's outermost line of cells on that side. If the strip
already reaches the grid border, it has been fired and stays unchanged. If it
stops short of the border, it is a stub of h lines. The stub is repeated
with period h outward to the border, and the repeat overwrites whatever lies
in its path, such as another blob's fired strip.

Scope: the background is fixed at 8 and the blob colour is fixed at 1. Grids
have 6..30 cells per side when the size is requested, and default random
sizes are 10..30. Sizes other than the fixture sizes are synthetic
extensions. A scene holds 1..4 blobs, limited by grid size. Blobs are rounded
rectangles with corner cells removed and 3..5 cells per side (a 3x3 one is a
plus), or small full rectangles with 2..3 cells per side. Every scene has at
least one unfired stub of 1..3 lines, and each stub's minimal period equals
its length. Scenes may also contain fired strips (periodic, sometimes with an
irregular tail) and blobs without strips. Extensions may cross fired strips.
Each blob has at most one strip.
"""

import random

import common

BG = 8
PALETTE = [2, 3, 4, 5, 6, 7, 9]
DIRECTIONS = ["up", "down", "left", "right"]
MIN_SIDE = 6
MAX_SIDE = 30


def _blob_cells(top, left, bh, bw, rounded):
  cells = set()
  for r in range(bh):
    for c in range(bw):
      if rounded and r in (0, bh - 1) and c in (0, bw - 1):
        continue
      cells.add((top + r, left + c))
  return cells


def _edge(cells, direction):
  """Returns (edge index, sorted perpendicular coordinates) of a side."""
  if direction == "up":
    e = min(y for y, _ in cells)
    return e, sorted(x for y, x in cells if y == e)
  if direction == "down":
    e = max(y for y, _ in cells)
    return e, sorted(x for y, x in cells if y == e)
  if direction == "left":
    e = min(x for _, x in cells)
    return e, sorted(y for y, x in cells if x == e)
  e = max(x for _, x in cells)
  return e, sorted(y for y, x in cells if x == e)


def _distance(direction, edge, height, width):
  if direction == "up":
    return edge
  if direction == "down":
    return height - 1 - edge
  if direction == "left":
    return edge
  return width - 1 - edge


def _line(direction, edge, perp, k):
  if direction == "up":
    return [(edge - k, p) for p in perp]
  if direction == "down":
    return [(edge + k, p) for p in perp]
  if direction == "left":
    return [(p, edge - k) for p in perp]
  return [(p, edge + k) for p in perp]


def _geometry(obj, height, width):
  """Computes blob, strip (input) and extension (output) cells."""
  blob = _blob_cells(obj["top"], obj["left"], obj["bh"], obj["bw"],
                     obj["rounded"])
  geo = {"blob": blob, "stub": {}, "ext": {}, "first": set(),
         "fired": bool(obj.get("fired"))}
  direction = obj.get("direction")
  if direction is None:
    return geo
  edge, perp = _edge(blob, direction)
  dist = _distance(direction, edge, height, width)
  lines = obj["lines"]
  for k, vals in enumerate(lines, 1):
    for cell, v in zip(_line(direction, edge, perp, k), vals):
      geo["stub"][cell] = v
  if not geo["fired"]:
    h = len(lines)
    for k in range(h + 1, dist + 1):
      cells = _line(direction, edge, perp, k)
      if k == h + 1:
        geo["first"] = set(cells)
      for cell, v in zip(cells, lines[(k - 1) % h]):
        geo["ext"][cell] = v
  return geo


def _checked_geometry(obj, height, width):
  """Validate explicit latents before indexing a canvas."""
  for name in ("top", "left", "bh", "bw"):
    if not isinstance(obj.get(name), int):
      raise ValueError("object geometry must use integer coordinates")
  if obj["top"] < 0 or obj["left"] < 0 or obj["bh"] < 1 or obj["bw"] < 1:
    raise ValueError("object must have positive size and nonnegative position")
  if obj["top"] + obj["bh"] > height or obj["left"] + obj["bw"] > width:
    raise ValueError("blob outside canvas")
  if obj.get("rounded") and min(obj["bh"], obj["bw"]) < 3:
    raise ValueError("rounded blobs need at least three cells per side")
  direction = obj.get("direction")
  lines = obj.get("lines", [])
  if direction is None:
    if lines or obj.get("fired"):
      raise ValueError("stripless blob cannot have lines or be fired")
  else:
    if direction not in DIRECTIONS:
      raise ValueError("unknown strip direction")
    blob = _blob_cells(obj["top"], obj["left"], obj["bh"], obj["bw"], obj["rounded"])
    edge, perp = _edge(blob, direction)
    dist = _distance(direction, edge, height, width)
    if not lines or any(len(line) != len(perp) for line in lines):
      raise ValueError("strip lines must match the outermost blob edge")
    if any(not isinstance(c, int) or c not in range(10) or c in (1, BG)
           for line in lines for c in line):
      raise ValueError("strip colours must differ from blob and background")
    if obj.get("fired"):
      if len(lines) != dist:
        raise ValueError("fired strip must reach the border exactly")
    elif not len(lines) < dist:
      raise ValueError("unfired stub must stop short of the border")
  return _geometry(obj, height, width)


def _dilate(cells):
  out = set()
  for (y, x) in cells:
    for dy in (-1, 0, 1):
      for dx in (-1, 0, 1):
        out.add((y + dy, x + dx))
  return out


def _compatible(a, b):
  """Inputs are separated, and extensions avoid blobs, live stubs and each
  other. Extensions may still cross fired strips."""
  inp_a = a["blob"] | set(a["stub"])
  inp_b = b["blob"] | set(b["stub"])
  if _dilate(inp_a) & inp_b:
    return False
  hard_a = a["blob"] | (set() if a["fired"] else set(a["stub"]))
  hard_b = b["blob"] | (set() if b["fired"] else set(b["stub"]))
  ext_a, ext_b = set(a["ext"]), set(b["ext"])
  if ext_a & _dilate(hard_b) or ext_b & _dilate(hard_a):
    return False
  if _dilate(ext_a) & ext_b:
    return False
  if a["first"] & inp_b or b["first"] & inp_a:
    return False
  return True


def _rand_line(n):
  return [random.choice(PALETTE) for _ in range(n)]


def _periodic_lines(n, h):
  """h (1..3) lines of width n whose minimal period is exactly h.

  For h <= 3 this only requires that the last line differs from the first.
  """
  lines = [_rand_line(n) for _ in range(h)]
  if h >= 2 and lines[-1] == lines[0]:
    i = random.randrange(n)
    lines[-1][i] = random.choice([c for c in PALETTE if c != lines[0][i]])
  return lines


def _random_object(kind, height, width):
  rounded = random.random() < 0.75
  if rounded:
    bh, bw = random.randint(3, 5), random.randint(3, 5)
  else:
    bh, bw = random.randint(2, 3), random.randint(2, 3)
  if bh > height or bw > width:
    return None
  obj = {"top": random.randint(0, height - bh),
         "left": random.randint(0, width - bw),
         "bh": bh, "bw": bw, "rounded": rounded,
         "direction": None, "fired": False, "lines": []}
  if kind == "none":
    return obj
  direction = random.choice(DIRECTIONS)
  blob = _blob_cells(obj["top"], obj["left"], bh, bw, rounded)
  edge, perp = _edge(blob, direction)
  dist = _distance(direction, edge, height, width)
  n = len(perp)
  obj["direction"] = direction
  if kind == "fired":
    if dist < 3:
      return None
    period = random.randint(1, 3)
    base = _periodic_lines(n, period)
    lines = [list(base[i % period]) for i in range(dist)]
    if dist >= 5 and random.random() < 0.3:
      for t in range(1, random.randint(1, 2) + 1):
        lines[-t] = _rand_line(n)
    obj["fired"] = True
    obj["lines"] = lines
    return obj
  h = random.randint(1, 3)
  if dist < h + 1:
    return None
  obj["lines"] = _periodic_lines(n, h)
  return obj


def _render(height, width, geos):
  grid = common.grid(width, height, BG)
  for g in geos:
    for (y, x) in g["blob"]:
      grid[y][x] = 1
    for (y, x), v in g["stub"].items():
      grid[y][x] = v
  output = [row[:] for row in grid]
  for g in geos:
    for (y, x), v in g["ext"].items():
      output[y][x] = v
  return grid, output


def _bg_dominant(grid):
  counts = {}
  for row in grid:
    for v in row:
      counts[v] = counts.get(v, 0) + 1
  bgc = counts.get(BG, 0)
  return all(c * 2 < bgc for k, c in counts.items() if k != BG)


def _object_limit(height, width):
  """Maximum blob count supported for a grid (also guarantees a band fit)."""
  return max(1, min(4, max(height, width) // 5, 2 + (height * width) // 250))


def _check_side(name, value):
  if value is not None and not MIN_SIDE <= value <= MAX_SIDE:
    raise ValueError("%s must be in %d..%d" % (name, MIN_SIDE, MAX_SIDE))


def _pick_size(height, width, num_objects):
  for _ in range(100):
    h = height if height is not None else random.randint(10, MAX_SIDE)
    w = width if width is not None else random.randint(10, MAX_SIDE)
    if num_objects is None or _object_limit(h, w) >= num_objects:
      return h, w
  h = height if height is not None else MAX_SIDE
  w = width if width is not None else MAX_SIDE
  return h, w


def _place(kinds, height, width):
  """Places every requested object or returns None (no silent dropping)."""
  geos = []
  for kind in kinds:
    placed = False
    for _ in range(150):
      obj = _random_object(kind, height, width)
      if obj is None:
        continue
      g = _geometry(obj, height, width)
      if all(_compatible(g, o) for o in geos):
        geos.append(g)
        placed = True
        break
    if not placed:
      return None
  return geos


def _band_scene(height, width, n):
  """Randomised constructive fallback with exactly n unfired plus blobs.

  The longer side is split into n bands of at least 5 cells. Each band holds
  a plus whose stub points along the band, so the objects cannot interact.
  """
  vertical = width >= height
  span = width if vertical else height
  length = height if vertical else width
  band = span // n
  geos = []
  for i in range(n):
    off = i * band + 1 + random.randint(0, band - 5)
    forward = random.random() < 0.5
    if forward:
      s = random.randint(0, length - 5)
      dist = length - 1 - (s + 2)
    else:
      s = random.randint(2, length - 3)
      dist = s
    h = random.randint(1, min(3, dist - 1))
    if vertical:
      top, left = s, off
      direction = "down" if forward else "up"
    else:
      top, left = off, s
      direction = "right" if forward else "left"
    obj = {"top": top, "left": left, "bh": 3, "bw": 3, "rounded": True,
           "direction": direction, "fired": False,
           "lines": _periodic_lines(1, h)}
    geos.append(_geometry(obj, height, width))
  return _render(height, width, geos)


def _random_scene(height, width, num_objects):
  h = w = n = None
  for _ in range(60):
    h, w = _pick_size(height, width, num_objects)
    limit = _object_limit(h, w)
    n = num_objects if num_objects is not None else random.randint(1, limit)
    kinds = ["unfired"] + [random.choice(["fired", "fired", "unfired",
                                           "none"]) for _ in range(n - 1)]
    geos = _place(kinds, h, w)
    if geos is None:
      continue
    grid, output = _render(h, w, geos)
    if _bg_dominant(grid):
      return grid, output
  return _band_scene(h, w, n)


def generate(height=None, width=None, num_objects=None, objects=None):
  """Generates one input/output pair.

  Args:
    height: grid height, 6..30. It is required with objects. Otherwise it is
      honoured if given and sampled from 10..30 if not.
    width: grid width, 6..30. It is handled the same way as height.
    num_objects: number of blobs, 1..4, for random generation. It must fit
      the grid size (see _object_limit), and it cannot be combined with
      objects.
    objects: optional explicit latent scene. This is a list of dicts with keys
      top, left, bh, bw, rounded (corner cells removed), direction
      ("up"/"down"/"left"/"right" or None), fired (the strip already reaches
      the border), and lines. lines is a list of colour lines ordered outward
      from the blob. Each line is ordered by ascending perpendicular
      coordinate. For a fired strip it holds the full strip; otherwise it
      holds the stub.
  """
  _check_side("height", height)
  _check_side("width", width)
  if objects is not None:
    if height is None or width is None:
      raise ValueError("height and width are required with objects")
    if num_objects is not None:
      raise ValueError("num_objects cannot be combined with objects")
    if not objects:
      raise ValueError("need at least one blob")
    geos = [_checked_geometry(o, height, width) for o in objects]
    if any(not _compatible(a, b) for i, a in enumerate(geos) for b in geos[i + 1:]):
      raise ValueError("object inputs or live extensions conflict")
    grid, output = _render(height, width, geos)
    return {"input": grid, "output": output}
  if num_objects is not None:
    if not 1 <= num_objects <= 4:
      raise ValueError("num_objects must be in 1..4")
    hh = height if height is not None else MAX_SIDE
    ww = width if width is not None else MAX_SIDE
    if _object_limit(hh, ww) < num_objects:
      raise ValueError("grid too small for num_objects")
  grid, output = _random_scene(height, width, num_objects)
  return {"input": grid, "output": output}


def _obj(top, left, bh, bw, direction, fired, lines, rounded=True):
  return {"top": top, "left": left, "bh": bh, "bw": bw, "rounded": rounded,
          "direction": direction, "fired": fired, "lines": lines}


def validate():
  """Reconstructs the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=24, width=14, objects=[
          _obj(4, 3, 3, 3, "right", True, [[2], [3]] * 4),
          _obj(13, 9, 3, 3, "up", False, [[2], [4]]),
      ]),
      generate(height=23, width=13, objects=[
          _obj(1, 1, 5, 4, "down", True, [[2, 3]] * 17),
          _obj(12, 7, 5, 4, "up", False, [[4, 2]]),
      ]),
  ]
  test = [
      generate(height=25, width=18, objects=[
          _obj(4, 2, 3, 4, "down", True,
               [[4, 3], [6, 2]] * 8 + [[6, 3], [4, 2]]),
          _obj(15, 8, 3, 4, "up", False, [[7, 3], [2, 5]]),
          _obj(19, 13, 3, 4, "down", False, [[2, 4], [3, 5]]),
      ]),
  ]
  return {"train": train, "test": test}
