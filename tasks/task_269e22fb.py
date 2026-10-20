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

"""Complete a uniquely located fragment of an episode-shared binary drawing.

The public task uses one fixed 20x20 drawing. Its seven fixtures are rebuilt
from that drawing only in validate(). Random generation constructs fresh
structured pictures from paths, rectangle outlines, filled blocks and steps.
The sampled 12..30 canvas dimensions are a synthetic extension, not a claim
that the canonical task has varying output sizes.

IMPORTANT: generate() alone samples a new picture. Use generate_episode() to
share the SAME picture across demonstrations and queries. A pair-only dataset
builder must not mix independent generate() calls for this family.

Each input is a two-colour crop of a rotated/reflected picture; its output is
the entire picture in that orientation and palette. Only crops with exactly
one placement across D4 AND both colour interpretations are accepted.
Ordinary random generation never uses the canonical picture or saved solver.
"""

import random
import numpy as np


def _integer(value, lo, hi, name):
  if type(value) is not int or not lo <= value <= hi:
    raise ValueError(name + " must be an integer in the documented range")
  return value


def _binary(template):
  if not isinstance(template, (list, tuple)) or not 3 <= len(template) <= 30:
    raise ValueError("template must be a binary rectangle, sides 3..30")
  width = len(template[0])
  if not 3 <= width <= 30:
    raise ValueError("template must be a binary rectangle, sides 3..30")
  if any(len(row) != width or any(type(v) is not int or v not in (0, 1)
                                  for v in row) for row in template):
    raise ValueError("template must be a binary rectangle")
  if {v for row in template for v in row} != {0, 1}:
    raise ValueError("template must contain both binary values")
  return [list(row) for row in template]


def _orientations(template):
  a = np.asarray(template, dtype=np.int8)
  return [np.fliplr(np.rot90(a, k)) if f else np.rot90(a, k)
          for k in range(4) for f in (False, True)]


def _placements(mask, variants, limit=2):
  """Count placements, including the alternate foreground interpretation."""
  a = np.asarray(mask, dtype=np.int8)
  total = 0
  h, w = a.shape
  for image in variants:
    if image.shape[0] < h or image.shape[1] < w:
      continue
    windows = np.lib.stride_tricks.sliding_window_view(image, (h, w))
    for candidate in (a, 1 - a):
      total += int(np.all(windows == candidate, axis=(-2, -1)).sum())
      if total >= limit:
        return total
  return total


def _new_template(height, width):
  """Draw fresh latent strokes and shapes; no reference-program filtering."""
  for attempt in range(80):
    a = [[0] * width for _ in range(height)]
    # Long bent strokes create spatial structure rather than independent noise.
    for stroke in range(random.randint(3, 6)):
      r, c = random.randrange(height), random.randrange(width)
      for segment in range(random.randint(3, 7)):
        dr, dc = random.choice(((0, 1), (0, -1), (1, 0), (-1, 0)))
        for step in range(random.randint(2, max(height, width) // 2)):
          a[r][c] = 1
          nr, nc = r + dr, c + dc
          if not (0 <= nr < height and 0 <= nc < width):
            break
          r, c = nr, nc
    for box in range(random.randint(2, 5)):
      h, w = random.randint(2, max(2, height // 2)), random.randint(2, max(2, width // 2))
      y, x = random.randrange(height - h + 1), random.randrange(width - w + 1)
      filled = random.random() < .3
      for r in range(h):
        for c in range(w):
          if filled or r in (0, h - 1) or c in (0, w - 1):
            a[y + r][x + c] = 1
    # Diagonal staircases introduce boundaries distinct from rectilinear paths.
    r, c = random.randrange(height), random.randrange(width)
    dr, dc = random.choice((-1, 1)), random.choice((-1, 1))
    for step in range(random.randint(3, min(height, width))):
      a[r][c] = 1
      if not (0 <= r + dr < height and 0 <= c + dc < width):
        break
      a[r][c + dc] = 1
      r, c = r + dr, c + dc
    density = sum(map(sum, a)) / (height * width)
    if not .15 <= density <= .8:
      continue
    variants = _orientations(a)
    fingerprints = {(v.shape, v.tobytes()) for v in variants}
    if len(fingerprints) == 8:
      return a
  raise RuntimeError("could not construct an asymmetric structured picture")


def generate(template=None, template_height=None, template_width=None,
             orientation=None, flip=None, fg=None, bg=None, height=None,
             width=None, row=None, col=None):
  """Construct one pair; pass template explicitly to share episode context.

  template: binary picture; sides 3..30. None creates a fresh random picture.
  template_height/width: new-picture sides 12..30, incompatible with template.
  orientation: counter-clockwise quarter turns, 0..3; flip: horizontal reflection.
  fg/bg: distinct colours 0..9, independent of majority colour in the crop.
  height/width, row/col: crop dimensions and top-left after orientation.
  Partial crop controls are honoured by sampling only compatible orientations.
  Degenerate, out-of-bounds or ambiguous fixed controls raise ValueError.
  """
  for value, name in ((template_height, "template_height"),
                      (template_width, "template_width")):
    if value is not None:
      _integer(value, 12, 30, name)
  if template is not None:
    if template_height is not None or template_width is not None:
      raise ValueError("template and new-picture dimensions are incompatible")
    picture = _binary(template)
  else:
    picture = _new_template(template_height if template_height is not None else random.randint(12, 30),
                            template_width if template_width is not None else random.randint(12, 30))
  if orientation is not None:
    _integer(orientation, 0, 3, "orientation")
  if flip is not None and type(flip) is not bool:
    raise ValueError("flip must be a boolean")
  for value, name in ((fg, "fg"), (bg, "bg")):
    if value is not None:
      _integer(value, 0, 9, name)
  if fg is not None and fg == bg:
    raise ValueError("foreground and background must differ")
  for value, name in ((height, "height"), (width, "width")):
    if value is not None:
      _integer(value, 1, 30, name)
  for value, name in ((row, "row"), (col, "col")):
    if value is not None:
      _integer(value, 0, 29, name)
  variants = _orientations(picture)
  choices = []
  for k in range(4) if orientation is None else [orientation]:
    for f in (False, True) if flip is None else [flip]:
      a = variants[2 * k + int(f)]
      hmax = a.shape[0] - (row if row is not None else 0)
      wmax = a.shape[1] - (col if col is not None else 0)
      if hmax < (height if height is not None else 3) or wmax < (width if width is not None else 3):
        continue
      choices.append((k, f))
  if not choices:
    raise ValueError("crop controls do not fit any requested orientation")
  for attempt in range(200):
    k, f = random.choice(choices)
    a = variants[2 * k + int(f)]
    H, W = a.shape
    hmax, wmax = H - (row or 0), W - (col or 0)
    h = height if height is not None else random.randint(3, hmax)
    w = width if width is not None else random.randint(3, wmax)
    if h * w == H * W:
      continue
    y = row if row is not None else random.randrange(H - h + 1)
    x = col if col is not None else random.randrange(W - w + 1)
    mask = a[y:y+h, x:x+w]
    if not (np.any(mask == 0) and np.any(mask == 1)):
      continue
    if _placements(mask, variants) != 1:
      continue
    if fg is None and bg is None:
      foreground, background = random.sample(range(10), 2)
    elif fg is None:
      background = bg
      foreground = random.choice([c for c in range(10) if c != bg])
    elif bg is None:
      foreground = fg
      background = random.choice([c for c in range(10) if c != fg])
    else:
      foreground, background = fg, bg
    paint = lambda m: np.where(m == 1, foreground, background).astype(int).tolist()
    return {"input": paint(mask), "output": paint(a)}
  raise ValueError("no unique nontrivial crop found under these controls")


def _equivalence(grid):
  """Palette/D4 input identity, to avoid repetitions inside one episode."""
  colours = sorted({v for row in grid for v in row})
  mask = [[int(v == colours[0]) for v in row] for row in grid]
  return min((v.shape, v.tobytes()) for oriented in _orientations(mask)
             for v in (oriented, 1-oriented))


def generate_episode(template=None, template_height=None, template_width=None,
                     num_demos=3, num_queries=1):
  """Three demos and one query by default, all using one fresh picture."""
  _integer(num_demos, 1, 7, "num_demos")
  _integer(num_queries, 1, 3, "num_queries")
  if template is not None:
    if template_height is not None or template_width is not None:
      raise ValueError("template and new-picture dimensions are incompatible")
    picture = _binary(template)
  else:
    h = random.randint(12, 30) if template_height is None else _integer(template_height, 12, 30, "template_height")
    w = random.randint(12, 30) if template_width is None else _integer(template_width, 12, 30, "template_width")
    picture = _new_template(h, w)
  pairs, seen = [], set()
  for attempt in range(100):
    pair = generate(template=picture)
    key = _equivalence(pair["input"])
    if key in seen:
      continue
    seen.add(key)
    pairs.append(pair)
    if len(pairs) == num_demos + num_queries:
      return {"train": pairs[:num_demos], "test": pairs[num_demos:]}
  raise ValueError("not enough distinct unique crops for the requested episode")


# Canonical fixture reconstruction only; never used by random generation.
_ROWS = (
    "11000000000000011000",
    "11111100000000011000",
    "11111110000000011100",
    "11000111000000011100",
    "00000011100000111110",
    "00000001110000100110",
    "00000000110011100110",
    "00000000010010100110",
    "00000000011110100110",
    "01111111110110100110",
    "01000000011110100110",
    "01111111110010100110",
    "01010000010011100110",
    "11101111110000100110",
    "01011000010000111110",
    "11101000010001101100",
    "01011000010001000110",
    "11101000010001100011",
    "01011000101000101110",
    "11100001000100111000",
)


def _base():
  return [[int(ch) for ch in row] for row in _ROWS]


def validate():
  """Reconstruct the canonical examples from explicit latent parameters."""
  train = [
      generate(template=_base(), orientation=0, flip=False, fg=7, bg=8, height=8, width=10,
               row=0, col=0),
      generate(template=_base(), orientation=2, flip=False, fg=7, bg=8, height=16, width=8,
               row=0, col=6),
      generate(template=_base(), orientation=1, flip=False, fg=3, bg=0, height=10, width=10,
               row=0, col=0),
      generate(template=_base(), orientation=0, flip=True, fg=7, bg=8, height=13, width=12,
               row=2, col=0),
      generate(template=_base(), orientation=1, flip=False, fg=7, bg=8, height=8, width=10,
               row=12, col=10),
  ]
  test = [
      generate(template=_base(), orientation=3, flip=False, fg=8, bg=7, height=10, width=10,
               row=0, col=0),
      generate(template=_base(), orientation=1, flip=True, fg=5, bg=6, height=11, width=10,
               row=4, col=10),
  ]
  return {"train": train, "test": test}
