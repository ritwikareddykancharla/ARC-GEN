"""Generator for ARC task 981571dc: repair of an off-centre D4-symmetric mosaic.

Rule
----
Each input is a 30x30 crop (rows 0..29, columns 0..29) of a latent 32x32 mosaic
that is fully symmetric under the dihedral group D4 with both axes at 15.5: the
colour of cell (y, x) depends only on the unordered pair
{min(y, 31-y), min(x, 31-x)}.  Because the crop drops the last two rows and
columns of the 32x32 canvas, the mirror is off-centre inside the 30x30 grid
(y <-> 31-y, x <-> 31-x) and rows/columns 0-1 have no mirror partner inside the
grid; the transpose symmetry supplies their partners.  Some rectangular patches
are painted 0, a colour the mosaic never uses.  The output rewrites every 0 cell
with the colour carried by its symmetric partners; all non-zero cells are kept.

Scope
-----
The generator constructs the latent orbit colouring (a transpose-symmetric 16x16
quadrant of the 32x32 canvas), crops it to 30x30 and erases 1..6 random
rectangles, which may adjoin or overlap to form irregular holes (including
holes that touch the un-mirrored rows/columns 0-1).  An erasure set is rejected
unless every masked cell keeps at least one unmasked D4 image inside the crop,
so the repair is uniquely determined and never relies on an invisible partner.
The grid size is intrinsically fixed at 30x30 and colours are 1..9; 0 is
reserved for the mask.
"""

# Copyright 2026 Ritwika Kancharla
# Licensed under the Apache License, Version 2.0.

import random

import common

SIZE = 30      # side of the visible crop
AXIS = 31      # mirror partner of index a is AXIS - a (axes at 15.5)
QUAD = 16      # orbit indices range over 0..15


def _rows(spec):
  """Converts a quadrant given as digit strings or int lists to int lists."""
  out = []
  for row in spec:
    out.append([int(c) for c in row])
  return out


def _orbit(y, x):
  """Canonical orbit index of cell (y, x) under the off-centre D4 group."""
  a = min(y, AXIS - y)
  b = min(x, AXIS - x)
  return (a, b) if a <= b else (b, a)


def _mates(y, x):
  """All other D4 images of (y, x) that fall inside the 30x30 crop."""
  cands = [(y, AXIS - x), (AXIS - y, x), (AXIS - y, AXIS - x),
           (x, y), (x, AXIS - y), (AXIS - x, y), (AXIS - x, AXIS - y)]
  out = set()
  for py, px in cands:
    if (py, px) != (y, x) and 0 <= py < SIZE and 0 <= px < SIZE:
      out.add((py, px))
  return out


def _mask_cells(masks):
  """Set of (y, x) cells covered by the given rectangles, clipped to the grid."""
  cells = set()
  for top, left, height, width in masks:
    for y in range(top, top + height):
      for x in range(left, left + width):
        if 0 <= y < SIZE and 0 <= x < SIZE:
          cells.add((y, x))
  return cells


def _solvable(cells):
  """True when every masked cell has an unmasked D4 image inside the crop."""
  if not cells:
    return False
  for (y, x) in cells:
    if not any(m not in cells for m in _mates(y, x)):
      return False
  return True


def _sample_quadrant(num_colors):
  """Samples a transpose-symmetric 16x16 quadrant over a random palette."""
  palette = random.sample(range(1, 10), num_colors)
  quad = [[0] * QUAD for _ in range(QUAD)]
  for i in range(QUAD):
    for j in range(i, QUAD):
      c = random.choice(palette)
      quad[i][j] = c
      quad[j][i] = c
  return quad


def _sample_masks(num_masks):
  """Samples num_masks random rectangles (top, left, height, width)."""
  masks = []
  for _ in range(num_masks):
    height = random.randint(1, 10)
    width = random.randint(1, 10)
    top = random.randint(0, SIZE - height)
    left = random.randint(0, SIZE - width)
    masks.append((top, left, height, width))
  return masks


def generate(quadrant=None, masks=None, num_colors=None, num_masks=None):
  """Returns {"input": grid, "output": grid} for one symmetry-repair scene.

  Args:
    quadrant: optional 16 rows (lists of ints or 16-character digit strings)
      giving the top-left 16x16 quadrant of the latent 32x32 mosaic.  Entry
      [i][j] with i <= j is the colour of orbit (i, j); the lower triangle is
      ignored, so the quadrant is effectively transpose-symmetric.
    masks: optional list of (top, left, height, width) rectangles whose cells
      are erased to colour 0 in the input.  Rectangles may overlap or adjoin.
    num_colors: palette size (3..9) used when sampling the quadrant.
    num_masks: number of erased rectangles (1..6) used when sampling masks.
  """
  if quadrant is None:
    if num_colors is None:
      num_colors = random.randint(3, 9)
    quadrant = _sample_quadrant(num_colors)
  else:
    quadrant = _rows(quadrant)

  if masks is None:
    if num_masks is None:
      num_masks = random.choice([1, 1, 2, 2, 3, 3, 4, 5, 6])
    chosen = None
    for _ in range(500):
      cand = _sample_masks(num_masks)
      if _solvable(_mask_cells(cand)):
        chosen = cand
        break
    if chosen is None:
      # Interior patch whose vertical mirror (rows 27..29) is always visible.
      chosen = [(2, 2, 3, 3)]
    masks = chosen

  output = common.grid(SIZE, SIZE, 0)
  for y in range(SIZE):
    for x in range(SIZE):
      a, b = _orbit(y, x)
      output[y][x] = quadrant[a][b]

  input_grid = [row[:] for row in output]
  for (y, x) in _mask_cells(masks):
    input_grid[y][x] = 0

  return {"input": input_grid, "output": output}


def validate():
  """Reconstructs the canonical train/test pairs from explicit latents."""
  train = [
      generate(
          quadrant=["2828681146662428", "8555821264444442",
                    "2544118864162448", "8542128164618282",
                    "6811376324289633", "8212783644426313",
                    "1188633624483113", "1281366382823331",
                    "4666242844331412", "6444444244224288",
                    "6416244832241818", "6461828232472888",
                    "2428963314129933", "4442631342889383",
                    "2448311318183828", "8282333128883388"],
          masks=[(0, 19, 7, 6), (7, 19, 6, 3), (25, 20, 2, 3),
                 (26, 26, 2, 2), (27, 13, 2, 10), (29, 20, 1, 3)]),
      generate(
          quadrant=["9296241687715673", "2966441178556676",
                    "9666114675877736", "6662616215753665",
                    "2416212156731861", "4411122266768898",
                    "1146229977366969", "6162129236651898",
                    "8771567385589633", "7855667658436936",
                    "7587773654853333", "1575366583543631",
                    "5673186196338868", "6676889869368178",
                    "7736696933336777", "3665189836318878"],
          masks=[(0, 21, 6, 8), (2, 7, 4, 4), (5, 0, 2, 4), (10, 5, 6, 7)]),
      generate(
          quadrant=["8884888655635925", "8384888858589995",
                    "8848889865552959", "4488688538555598",
                    "8886849159255989", "8888418199959229",
                    "8898988929598285", "6885119855989952",
                    "5563592549446646", "5858999596646575",
                    "6555295946944767", "3855559844416574",
                    "5925598966462544", "9995922965755224",
                    "2959828547674244", "5598995265744444"],
          masks=[(0, 9, 2, 4), (6, 13, 8, 3), (8, 2, 6, 6), (18, 28, 8, 2)]),
      generate(
          quadrant=["6737172217655757", "7699775576517777",
                    "3997252765765799", "7979257751667794",
                    "1722999657573399", "7755969577773696",
                    "2527999957999936", "2577659777949663",
                    "1765575726257737", "7651777766247377",
                    "6576579922623767", "5166779454257776",
                    "5757339977372521", "7777369673775511",
                    "5799993637672125", "7794966377761152"],
          masks=[(5, 1, 7, 6), (12, 23, 4, 4), (22, 14, 2, 6), (24, 18, 6, 2)]),
  ]
  test = [
      generate(
          quadrant=["1935993944263336", "9355973546223334",
                    "3559339922263336", "5595959562626461",
                    "9939188933364214", "9735858133342224",
                    "3399885933361224", "9595919964614449",
                    "4426333675583666", "4622333455516943",
                    "2226333655756449", "6262646181586394",
                    "3336421436661828", "3334222469438622",
                    "3336122464492228", "6461444963948286"],
          masks=[(12, 9, 5, 2), (26, 25, 4, 5)]),
  ]
  return {"train": train, "test": test}
