# e74e1818: rectangular, asymmetric colour bands

The rule reverses rows within each contiguous single-colour band, preserving
all cell counts and canvas dimensions. The constructor previously sampled only
odd square grids from 7 to 15, horizontally symmetric patterns, and a restricted
band-count/height relation. None of these three restrictions is required by
that rule.

The replacement samples height and width independently in 3..30, 1..9 bands
(limited by the number of interior rows), arbitrary positive band heights,
and symmetric or asymmetric row patterns. Each occupied row remains nonempty
and monochromatic, bands use distinct nonblack colours, and the canvas keeps a
black border. It samples partitions and occupied positions directly, without
unbounded rejection loops. Explicit canonical scenes retain their labels.

RE-ARC style precedents were read in `diversity/rearc/generators.py`, particularly
`generate_8be77c9e` and `generate_6d0aefbc`: independent height/width ranges,
content counts and placements, with dimensions constrained by the output rule.
Those generators are references for sampling breadth, not substitutes for this
family's semantics. Native background zero is retained; episode-wide palette
permutations provide other visible background colours.

## Checks

- Standard certification: 1,000 fresh queries, 8,000 D4/palette checks and 16
  canonical fixture variants, all passed. Factory code is unchanged.
- Independent probe: 2,000 pairs, 733 input shapes. The unchanged exported
  program and the fixed-background coordinate checker pass all 2,000.
- The archived checker fails six valid dense scenes because its modal-colour
  heuristic mistakes foreground for background. All six inputs, labels,
  predictions and colour counts are retained. The archived reference is not
  edited. No density restriction is introduced to hide the failures.
- The demonstration gate compares eight natural alternatives: identity,
  per-band vertical/horizontal/180-degree reflection, whole-grid reflections,
  and per-band sparse/dense row sorting. This is a finite ambiguity check,
  not a claim of unique identification among every imaginable rule.
- Symmetric demonstrations can make vertical and 180-degree band reflection
  indistinguishable. A test retains the same asymmetric query, rejects that
  context, and accepts an informative asymmetric demonstration under all D4
  transforms and a nontrivial palette. Query answers are never consumed by
  the gate.
- The context audit keeps 500 queries fixed, uses mixed demonstration shapes
  with a novel query shape (the canonical profile), four distinct input orbits
  and a common global split. It resamples demonstrations only, then verifies
  the accepted records in all eight D4 variants. Source hashes accompany it.

This isolated expansion is not yet part of the frozen six-family export.
