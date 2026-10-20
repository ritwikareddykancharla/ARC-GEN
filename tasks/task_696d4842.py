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

"""ARC task 696d4842: snake paths slide forward to their markers.

Rule: the background is black (0). Each scene has one or more bent paths. A
path is one cell wide and has a single colour. Each path has a single-cell
marker of another colour. The marker lies straight ahead of one end of the
path (the head), in the direction of the path's last step, with n >= 1 empty
cells in between. In the output the path grows those n cells in its own
colour, so it touches the marker. The n cells at the other end of the path
(the tail) are repainted in the marker colour. The tail is counted along the
path, so it can go around corners.

Scope: the canonical fixtures use 20x20 and 30x30 grids. Random generation
samples height and width independently from 12..30 (rectangular sizes are a
synthetic extension). A random scene has 1-3 paths by default, or exactly
num_paths (1..4) when it is requested. A path has 2-4 perpendicular,
self-avoiding, non-self-touching segments, and n ranges from 1 to
min(len-1, 8). All path and marker colours are distinct and nonzero. Each
path's footprint (its cells, its extension corridor and its marker) is at
least one empty cell away from every other footprint, including diagonally.
The ray from each tail end must not reach any marker, so exactly one end of
each path is active.
"""

import collections
import random

import common


_DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
_KEYS = ("start", "segments", "n", "colour", "marker_colour")


def _trace(start, segments):
  """Return the path cells, ordered from the tail end to the head end."""
  r, c = start
  cells = [(r, c)]
  for d, length in segments:
    dr, dc = _DIRS[d]
    for _ in range(length):
      r += dr
      c += dc
      cells.append((r, c))
  return cells


def _layout(spec):
  """Return (path cells tail->head, extension cells, marker cell)."""
  cells = _trace(spec["start"], spec["segments"])
  (hr, hc), (pr, pc) = cells[-1], cells[-2]
  dr, dc = hr - pr, hc - pc
  n = spec["n"]
  ext = [(hr + dr * i, hc + dc * i) for i in range(1, n + 1)]
  marker = (hr + dr * (n + 1), hc + dc * (n + 1))
  return cells, ext, marker


def _inside(cell, height, width):
  return 0 <= cell[0] < height and 0 <= cell[1] < width


def _shape_ok(cells, ext, marker, height, width):
  """Check bounds, self-avoidance, and a clear extension corridor."""
  for cell in cells + ext + [marker]:
    if not _inside(cell, height, width):
      return False
  if len(set(cells)) != len(cells):
    return False
  index = {cell: i for i, cell in enumerate(cells)}
  for i, (r, c) in enumerate(cells):
    for dr, dc in _DIRS.values():
      j = index.get((r + dr, c + dc))
      if j is not None and abs(i - j) != 1:
        return False
  body = cells[:-1]
  for (r, c) in ext + [marker]:
    for (pr, pc) in body:
      if max(abs(r - pr), abs(c - pc)) < 2:
        return False
  return True


def _sample_spec(height, width, extension=None, num_segments=None):
  """Sample one path's geometry. Returns None if the sample is invalid."""
  nseg = num_segments if num_segments is not None else random.randint(2, 4)
  maxlen = max(2, min(height, width) // 3)
  dirs = [random.choice("UDLR")]
  for _ in range(nseg - 1):
    dirs.append(random.choice("LR" if dirs[-1] in "UD" else "UD"))
  segments = [(d, random.randint(1, maxlen)) for d in dirs]
  start = (random.randrange(height), random.randrange(width))
  total = 1 + sum(length for _, length in segments)
  if total < 4:
    return None
  n = extension if extension is not None else random.randint(1, min(total - 1, 8))
  if n >= total:
    return None
  spec = {"start": start, "segments": segments, "n": n}
  cells, ext, marker = _layout(spec)
  if not _shape_ok(cells, ext, marker, height, width):
    return None
  return spec


def _ray(grid, start, d, height, width):
  """Walk from start in direction d over background.

  Returns the first non-background cell hit (or None) and the number of
  background cells crossed.
  """
  r, c = start[0] + d[0], start[1] + d[1]
  count = 0
  while _inside((r, c), height, width) and grid[r][c] == 0:
    count += 1
    r += d[0]
    c += d[1]
  if _inside((r, c), height, width):
    return (r, c), count
  return None, count


def _render(height, width, paths):
  inp = common.grid(width, height, 0)
  layouts = [_layout(p) for p in paths]
  for p, (cells, _, marker) in zip(paths, layouts):
    for r, c in cells:
      inp[r][c] = p["colour"]
    inp[marker[0]][marker[1]] = p["marker_colour"]
  out = [row[:] for row in inp]
  for p, (cells, ext, _) in zip(paths, layouts):
    for r, c in ext:
      out[r][c] = p["colour"]
    for r, c in cells[:p["n"]]:
      out[r][c] = p["marker_colour"]
  return inp, out, layouts


def _scene_ok(inp, paths, layouts, height, width):
  """Check that each path has exactly one active end and 0 is background."""
  counts = collections.Counter(v for row in inp for v in row)
  for colour, cnt in counts.items():
    if colour != 0 and cnt >= counts[0]:
      return False
  markers = set(lay[2] for lay in layouts)
  for p, (cells, _, marker) in zip(paths, layouts):
    tail_dir = (cells[0][0] - cells[1][0], cells[0][1] - cells[1][1])
    hit, cnt = _ray(inp, cells[0], tail_dir, height, width)
    if hit in markers and cnt >= 1:
      return False
    head_dir = (cells[-1][0] - cells[-2][0], cells[-1][1] - cells[-2][1])
    hit, cnt = _ray(inp, cells[-1], head_dir, height, width)
    if hit != marker or cnt != p["n"]:
      return False
  return True


def _random_scene(height, width, num_paths, extension=None, num_segments=None):
  """Place exactly num_paths separated paths, or return None."""
  for _ in range(60):
    blocked = set()
    specs = []
    for _ in range(num_paths):
      placed = None
      for _ in range(120):
        spec = _sample_spec(height, width, extension, num_segments)
        if spec is None:
          continue
        cells, ext, marker = _layout(spec)
        fp = cells + ext + [marker]
        if any(cell in blocked for cell in fp):
          continue
        placed = (spec, fp)
        break
      if placed is None:
        break
      spec, fp = placed
      specs.append(spec)
      for r, c in fp:
        for dr in (-1, 0, 1):
          for dc in (-1, 0, 1):
            blocked.add((r + dr, c + dc))
    if len(specs) != num_paths:
      continue
    colours = random.sample(range(1, 10), 2 * num_paths)
    for i, spec in enumerate(specs):
      spec["colour"] = colours[2 * i]
      spec["marker_colour"] = colours[2 * i + 1]
    inp, _, layouts = _render(height, width, specs)
    if _scene_ok(inp, specs, layouts, height, width):
      return specs
  return None


def _check_explicit(height, width, paths):
  """Reject explicit path lists that do not form a valid scene."""
  if not paths:
    raise ValueError("paths must be a non-empty list")
  used = set()
  colours = set()
  for p in paths:
    for key in _KEYS:
      if key not in p:
        raise ValueError("path is missing key %r" % key)
    if type(p["n"]) is not int or p["n"] < 1:
      raise ValueError("n must be at least 1")
    colour, mcol = p["colour"], p["marker_colour"]
    if not (type(colour) is int and type(mcol) is int and
            1 <= colour <= 9 and 1 <= mcol <= 9 and colour != mcol):
      raise ValueError("path and marker colours must be distinct, 1..9")
    if colour in colours or mcol in colours:
      raise ValueError("path and marker colours must be unique across paths")
    colours.update((colour,mcol))
    if not p["segments"] or any(type(v) is not int for v in p["start"]):
      raise ValueError("path needs segments and an integer origin")
    for d, length in p["segments"]:
      if d not in _DIRS or type(length) is not int or length < 1:
        raise ValueError("bad segment %r" % ((d, length),))
    cells, ext, marker = _layout(p)
    if p["n"] >= len(cells):
      raise ValueError("n must be smaller than the path length")
    if not _shape_ok(cells, ext, marker, height, width):
      raise ValueError("path is out of bounds, self-touching or blocked")
    fp = cells + ext + [marker]
    if any(cell in used for cell in fp):
      raise ValueError("path footprints overlap")
    used.update(fp)
  inp, _, layouts = _render(height, width, paths)
  if not _scene_ok(inp, paths, layouts, height, width):
    raise ValueError("scene has an ambiguous or broken marker alignment")


def generate(height=None, width=None, num_paths=None, paths=None,
             extension=None, num_segments=None):
  """Generate one input/output pair.

  Args:
    height: grid height, 1..30 (12..30 when sampled).
    width: grid width, 1..30 (12..30 when sampled).
    num_paths: number of path/marker pairs, 1..4 (1..3 when sampled). When
      given it is honoured exactly; ValueError if it cannot be placed.
    extension: exact number of head-extension/tail-repainting cells per
      random path, in 1..15. Default is sampled in 1..8.
    num_segments: exact random segment count in 2..6 (default 2..4).
    paths: optional explicit list of dicts with keys "start" (tail cell
      (row, col)), "segments" (list of (dir in 'UDLR', length)), "n"
      (extension length), "colour" and "marker_colour". The head is the
      last traced cell, and the marker sits n+1 cells beyond it. Requires
      explicit height and width.
  """
  for name, value in (("height", height), ("width", width)):
    if value is not None and (type(value) is not int or not 1 <= value <= 30):
      raise ValueError("%s must be in 1..30" % name)
  if num_paths is not None and (type(num_paths) is not int or not 1 <= num_paths <= 4):
    raise ValueError("num_paths must be in 1..4")
  if paths is not None:
    if extension is not None or num_segments is not None:
      raise ValueError("random extension/segment controls conflict with paths")
    if height is None or width is None:
      raise ValueError("explicit paths require explicit height and width")
    if num_paths is not None and num_paths != len(paths):
      raise ValueError("num_paths does not match len(paths)")
    _check_explicit(height, width, paths)
  else:
    for name,value,lo,hi in (("extension",extension,1,15),
                             ("num_segments",num_segments,2,6)):
      if value is not None and (type(value) is not int or not lo<=value<=hi):
        raise ValueError(name + " outside supported integer range")
    specs = None
    for _ in range(20):
      h = height if height is not None else random.randint(12, 30)
      w = width if width is not None else random.randint(12, 30)
      if num_paths is not None:
        k = num_paths
      else:
        k = random.choice([1, 2, 2, 2, 3, 3])
      specs = _random_scene(h, w, k, extension, num_segments)
      if specs is not None:
        height, width, paths = h, w, specs
        break
    if specs is None:
      raise ValueError("could not place the requested paths in the grid")
  inp, out, _ = _render(height, width, paths)
  return {"input": inp, "output": out}


def _p(start, segments, n, colour, marker_colour):
  return {"start": start, "segments": segments, "n": n,
          "colour": colour, "marker_colour": marker_colour}


def validate():
  """Reconstruct the canonical fixtures from explicit latent parameters."""
  train = [
      generate(height=20, width=20, paths=[
          _p((4, 2), [("R", 4), ("D", 2)], 3, 3, 8),
          _p((15, 4), [("R", 6), ("U", 5)], 4, 6, 4),
      ]),
      generate(height=30, width=30, paths=[
          _p((4, 6), [("D", 10), ("R", 5)], 6, 4, 2),
          _p((25, 13), [("L", 2), ("U", 3), ("L", 2)], 5, 1, 6),
      ]),
      generate(height=20, width=20, paths=[
          _p((3, 2), [("R", 2), ("D", 3), ("R", 4), ("U", 2)], 3, 4, 6),
          _p((12, 3), [("R", 6), ("D", 4), ("R", 2)], 6, 3, 8),
      ]),
  ]
  test = [
      generate(height=20, width=20, paths=[
          _p((2, 2), [("R", 1), ("D", 3), ("R", 3)], 3, 2, 6),
          _p((11, 5), [("D", 3), ("R", 7), ("U", 1)], 4, 3, 4),
      ]),
  ]
  return {"train": train, "test": test}
