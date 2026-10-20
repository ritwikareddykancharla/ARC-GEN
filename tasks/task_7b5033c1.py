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

"""ARC-GEN style generator for task 7b5033c1.

Rule: the input is one winding path of coloured cells on a plain
background. The path never touches itself sideways, so it is an induced
4-connected path. The path is split into runs of colour. The output is a
single column that unrolls the path cell by cell. The walk starts at the
path end that comes first in reading order (top-most, then left-most).

Scope: the original examples are 16x16. By default each grid side is
sampled from 10..22, which is a synthetic extension. Explicit sizes from
1..30 are accepted when the path still fits. The background is any colour
0..9 and always stays the strict plurality colour of the input.

The path is built from straight runs that turn at right angles. It mostly
goes down, but it can also go left, right and sometimes up. Each new cell
is checked so the path stays induced. If growing fails, a randomised
down/right staircase is used instead; it is always induced.

The default path length is 12..30, and it is sampled once per attempt.
The output column has at most 30 rows, so the path is capped at 30 cells.
By default there are 2..6 colour runs, each at least 2 cells long.
Neighbouring runs always differ in colour. A colour may come back in a
later run that is not next to it. Colour changes are placed independently
of the turns.

End disambiguation: by default, randomly grown paths are kept only when
the chosen end (first in reading order) is the reading-order-first cell
of the whole path and is not to the right of the other end. This keeps
the competing hypotheses "top-most end", "left-most end", "end nearest
the top-left corner" and "top-most path cell" in agreement, as they are
in every demonstration. Set consistent_ends=False to also sample scenes
where only the reading-order rule decides.
"""

import collections
import random

import common


_DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
_WEIGHTS = {"D": 5, "U": 1, "L": 3, "R": 3}
_MAX_LEN = 30


def _path_from_moves(start, moves):
  path = [tuple(start)]
  for m in moves:
    if m not in _DIRS:
      raise ValueError("moves must use only U/D/L/R")
    dr, dc = _DIRS[m]
    r, c = path[-1]
    path.append((r + dr, c + dc))
  return path


def _can_extend(path, cells, nxt, width, height):
  r, c = nxt
  if not (0 <= r < height and 0 <= c < width) or nxt in cells:
    return False
  for dr, dc in _DIRS.values():
    n = (r + dr, c + dc)
    if n in cells and n != path[-1]:
      return False
  return True


def _is_induced_path(path, width, height):
  cells = set(path)
  if len(cells) != len(path) or len(path) < 2:
    return False
  index = {p: i for i, p in enumerate(path)}
  for i, (r, c) in enumerate(path):
    if not (0 <= r < height and 0 <= c < width):
      return False
    for dr, dc in _DIRS.values():
      n = (r + dr, c + dc)
      if n in index and abs(index[n] - i) != 1:
        return False
    if i > 0 and abs(path[i - 1][0] - r) + abs(path[i - 1][1] - c) != 1:
      return False
  return True


def _ends_consistent(path):
  """True when every plausible end-choice hypothesis picks the same end."""
  a, b = path[0], path[-1]
  first, other = (a, b) if a < b else (b, a)
  return first == min(path) and first[1] <= other[1]


def _random_walk(width, height, target, start=None, accept=None, tries=60):
  """Grows an induced path of exactly `target` cells, or returns None."""
  for _ in range(tries):
    if start is None:
      s = (random.randint(0, max(0, height // 3)),
           random.randint(0, width - 1))
    else:
      s = tuple(start)
    path = [s]
    cells = {s}
    prev = None
    stalls = 0
    while len(path) < target and stalls < 20:
      if prev is None:
        options = ["D", "L", "R"]
      elif prev in ("U", "D"):
        options = ["L", "R"]
      else:
        options = ["D", "U"]
      d = random.choices(options, weights=[_WEIGHTS[o] for o in options])[0]
      run = random.randint(1, 5)
      moved = 0
      for _ in range(run):
        if len(path) >= target:
          break
        dr, dc = _DIRS[d]
        nxt = (path[-1][0] + dr, path[-1][1] + dc)
        if not _can_extend(path, cells, nxt, width, height):
          break
        path.append(nxt)
        cells.add(nxt)
        moved += 1
      if moved:
        prev = d
        stalls = 0
      else:
        stalls += 1
    if len(path) == target and (accept is None or accept(path)):
      return path
  return None


def _staircase(width, height, target, start=None, right_only=False):
  """Monotone down/left or down/right path, which is always induced."""
  for _ in range(20):
    hdir = "R" if right_only else random.choice("LR")
    if start is None:
      if target - 1 > (height - 1) + (width - 1):
        return None
      nd = random.randint(max(0, target - 1 - (width - 1)),
                          min(height - 1, target - 1))
      nh = target - 1 - nd
      r0 = random.randint(0, height - 1 - nd)
      if hdir == "R":
        c0 = random.randint(0, width - 1 - nh)
      else:
        c0 = random.randint(nh, width - 1)
    else:
      r0, c0 = start
      room_h = width - 1 - c0 if hdir == "R" else c0
      room_v = height - 1 - r0
      if target - 1 > room_h + room_v:
        continue
      nd = random.randint(max(0, target - 1 - room_h), min(room_v, target - 1))
      nh = target - 1 - nd
    moves = ["D"] * nd + [hdir] * nh
    random.shuffle(moves)
    return _path_from_moves((r0, c0), moves)
  return None


def _random_runs(length, background, k=None):
  if k is None:
    kmax = max(1, min(6, length // 2))
    k = random.randint(min(2, kmax), kmax)
  base = 2 if 2 * k <= length else 1
  sizes = [base] * k
  for _ in range(length - base * k):
    sizes[random.randrange(k)] += 1
  runs = []
  prev = None
  for s in sizes:
    palette = [c for c in range(10) if c != background and c != prev]
    col = random.choice(palette)
    runs.append((col, s))
    prev = col
  return runs


def generate(width=None, height=None, background=None, start=None,
             moves=None, runs=None, length=None, num_runs=None,
             consistent_ends=None):
  """Generates an input/output pair for task 7b5033c1.

  Args:
    width: grid width (number of columns), 1..30.
    height: grid height (number of rows), 1..30.
    background: background colour 0..9. It must differ from every run
      colour, and it must remain the strict plurality colour of the input.
    start: (row, col) of the first path cell in generation order. It is
      required when moves is given. Without moves, a random path is grown
      from this cell. It must lie inside the grid.
    moves: string of U/D/L/R steps that trace the path from start.
    runs: list of (colour, count) colour runs along the generation order.
      Neighbouring runs must differ in colour. The counts fix the path
      length.
    length: number of path cells, 2..30. It must agree with runs and moves
      when those are given.
    num_runs: number of colour runs. It must agree with runs when given.
    consistent_ends: if True, the chosen end must be the reading-order-first
      path cell and must not lie right of the other end. Default None means
      True for random paths and unchecked for explicit moves. If it is
      explicitly True with moves, an inconsistent path raises ValueError.
      If False, any induced path is allowed.
  """
  for name, value in (("width", width), ("height", height),
                      ("background", background), ("length", length),
                      ("num_runs", num_runs)):
    if value is not None and type(value) is not int:
      raise ValueError(name + " must be an integer")
  if consistent_ends is not None and type(consistent_ends) is not bool:
    raise ValueError("consistent_ends must be a boolean")
  if moves is not None and not isinstance(moves, str):
    raise ValueError("moves must be a string")
  if start is not None and (not isinstance(start, (list, tuple)) or
                            len(start) != 2 or
                            any(type(v) is not int for v in start)):
    raise ValueError("start must be an integer (row, col) pair")
  if runs is not None and (not isinstance(runs, (list, tuple)) or
      any(not isinstance(run, (list, tuple)) or len(run) != 2 or
          any(type(v) is not int for v in run) for run in runs)):
    raise ValueError("runs must be integer (colour, count) pairs")
  if moves is not None and start is None:
    raise ValueError("moves requires start")
  if start is not None:
    start = (int(start[0]), int(start[1]))
  if runs is not None:
    runs = [(int(c), int(n)) for c, n in runs]
    if not runs or any(n < 1 for _, n in runs):
      raise ValueError("runs must be non-empty with positive counts")
    if any(not 0 <= c <= 9 for c, _ in runs):
      raise ValueError("run colours must be 0..9")
    for i in range(1, len(runs)):
      if runs[i][0] == runs[i - 1][0]:
        raise ValueError("adjacent runs must differ in colour")
    total = sum(n for _, n in runs)
    if length is not None and length != total:
      raise ValueError("length disagrees with runs")
    if num_runs is not None and num_runs != len(runs):
      raise ValueError("num_runs disagrees with runs")
    length = total
  if num_runs is not None and not 1 <= num_runs <= _MAX_LEN:
    raise ValueError("num_runs must be 1..30")
  if length is not None:
    if not 2 <= length <= _MAX_LEN:
      raise ValueError("path length must be 2..30")
    if num_runs is not None and num_runs > length:
      raise ValueError("num_runs exceeds length")

  rel = None
  need_w, need_h = 1, 1
  if moves is not None:
    rel = _path_from_moves(start, moves)
    if length is not None and len(rel) != length:
      raise ValueError("moves length disagrees with length/runs")
    if min(r for r, _ in rel) < 0 or min(c for _, c in rel) < 0:
      raise ValueError("path leaves the grid")
    need_h = max(r for r, _ in rel) + 1
    need_w = max(c for _, c in rel) + 1
  elif start is not None:
    if start[0] < 0 or start[1] < 0:
      raise ValueError("start out of grid")
    need_h, need_w = start[0] + 1, start[1] + 1

  if width is None:
    lo = max(10, need_w)
    width = random.randint(lo, max(lo, 22))
  if height is None:
    lo = max(10, need_h)
    height = random.randint(lo, max(lo, 22))
  if not (1 <= width <= 30 and 1 <= height <= 30):
    raise ValueError("grid sides must be 1..30")
  if start is not None and not (0 <= start[0] < height and
                                0 <= start[1] < width):
    raise ValueError("start out of grid")

  if background is None:
    used = {c for c, _ in runs} if runs is not None else set()
    free = [c for c in range(10) if c not in used]
    if not free:
      raise ValueError("no colour left for background")
    background = random.choice(free)
  if not 0 <= background <= 9:
    raise ValueError("background must be 0..9")
  if runs is not None and any(c == background for c, _ in runs):
    raise ValueError("run colour equals background")

  if rel is not None:
    path = rel
    if not _is_induced_path(path, width, height):
      raise ValueError("moves do not trace an induced path inside the grid")
    if consistent_ends and not _ends_consistent(path):
      raise ValueError("explicit path has ambiguous end choice")
  else:
    consistent = True if consistent_ends is None else bool(consistent_ends)
    accept = _ends_consistent if consistent else None
    # Keep the path strictly smaller than the background area so the
    # background is always the plurality colour.
    maxfit = min(_MAX_LEN, (width * height - 1) // 2)
    if maxfit < 2:
      raise ValueError("grid too small for a path plus a plurality background")
    if length is not None and length > maxfit:
      raise ValueError("path too long for the background to stay plurality")
    hi = min(maxfit, 2 * (width + height))
    if num_runs is not None and num_runs > hi:
      raise ValueError("num_runs too large for this grid")
    lo = min(12, width + height - 1, hi)
    if num_runs is not None:
      lo = max(lo, min(hi, 2 * num_runs))
    lo = max(2, lo)
    if lo > hi:
      raise ValueError("cannot fit a path in this grid")
    path = None
    for _ in range(30):
      t = length if length is not None else random.randint(lo, hi)
      cand = _random_walk(width, height, t, start, accept)
      if cand is None:
        cand = _staircase(width, height, t, start, right_only=consistent)
      if cand is not None and (accept is None or accept(cand)):
        path = cand
        break
    if path is None:
      raise ValueError("cannot fit a path of the requested length")
    if not _is_induced_path(path, width, height):
      raise RuntimeError("internal error: constructed path is not induced")
  if len(path) > _MAX_LEN:
    raise ValueError("path longer than 30 cells")

  if runs is None:
    if num_runs is not None and num_runs > len(path):
      raise ValueError("num_runs exceeds path length")
    runs = _random_runs(len(path), background, num_runs)
  colours = []
  for col, cnt in runs:
    colours.extend([col] * cnt)
  if len(colours) != len(path):
    raise ValueError("runs do not cover the path exactly")

  counts = collections.Counter(colours)
  if width * height - len(path) <= max(counts.values()):
    raise ValueError("background would not be the plurality colour")

  grid = common.grid(width, height, background)
  for (r, c), col in zip(path, colours):
    grid[r][c] = col
  # Output reads from the end that comes first in reading order.
  if path[-1] < path[0]:
    colours = colours[::-1]
  output = [[c] for c in colours]
  return {"input": grid, "output": output}


def validate():
  """Reconstructs the original task pairs from explicit latent parameters."""
  train = [
      generate(width=16, height=16, background=8, start=(1, 6),
               moves="DLDDDRRDDRRDDDLLLDDRR",
               runs=[(1, 5), (3, 4), (2, 5), (4, 5), (6, 3)]),
      generate(width=16, height=16, background=1, start=(1, 1),
               moves="DDRRRDDDDRRRDDDDDRRRDDR",
               runs=[(8, 7), (2, 8), (3, 9)]),
  ]
  test = [
      generate(width=16, height=16, background=2, start=(2, 1),
               moves="RRRDDRDDDLDDDRRRDDRRRUUR",
               runs=[(1, 5), (3, 3), (8, 6), (4, 6), (1, 3), (3, 2)]),
  ]
  return {"train": train, "test": test}
