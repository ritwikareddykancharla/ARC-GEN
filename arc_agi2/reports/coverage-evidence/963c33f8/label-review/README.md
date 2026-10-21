# 963c33f8: minimal native-compatible teaching hypothesis

**Status: ambiguous intended rule; original benchmark unchanged.** The proposed six-cell copy restores straight vertical movement in the third demonstration while preserving floor clearing in the second. It is a teaching hypothesis, not an officially confirmed correction.

## What the original examples show

The second demonstration has an unlit stick in column 7. Its floor cells at `(13,8)` and `(13,9)` change from gray (5) to background (7), while `(13,10)` and `(13,11)` remain gray. The native constructor applies a uniform radius-two floor clear around every unlit stick. This is positive evidence in the original example for preserving that behavior. It does not prove those two cells cannot themselves be labeling errors.

The third demonstration moves an unlit stick sideways from column 11 to column 12. The native constructor reproduces it using hidden `extras=[0,0,1]`, absent from random generation. No general visible mechanism for this sideways move was established. Undoing it changes six cells; `fixture-differences.json` records every old and new value. All coordinates are zero-based.

## Competing eight-cell interpretation

The existing curated copy also restores the two floor cells to gray, yielding eight changes. The independent [atlas correction metadata](https://github.com/yhay81/arc-agi-2-solution-atlas/blob/main/metadata/label_corrections.json) and [notes](https://github.com/yhay81/arc-agi-2-solution-atlas/blob/main/notes/963c33f8.json) favor this simpler straight-gravity interpretation. They link [Kaggle discussion 731040](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2/discussion/731040), whose body was unavailable to the browser. No matching official GitHub issue/PR was found. We cannot claim official endorsement of either interpretation.

The saved Opus solution was produced using the already corrected eight-cell task. Its agreement therefore cannot establish that the two original floor cells are erroneous.

## Audit results and retained artifacts

- `proposed-teaching-native-floor-clear.json`: the proposed six-cell copy.
- `canonical-snapshot.json`: unmodified original examples.
- `existing-eight-cell-snapshot.json`: prior curated candidate, retained.
- `fixture-differences.json`: exact comparisons of all three versions.
- `floor-clear-visible-evidence.json`: complete original demonstration and relevant floor cells.
- `audit.json`: 1,000 unique native pairs, 8,000 D4/palette checks, 16 proposed-six-cell fixture variants; all pass.
- `alternative_eight_cell_factory.py` and `audit-eight-cell-alternative.json`: separately labelled competing interpretation. It passes 1,000 pairs / 8,000 checks / 16 eight-cell fixture variants after relabeling synthetic outputs. This would change 172 of the same 1,000 native labels; inputs remain the same. Counterexamples are retained.
- `sources.json`: independent source snapshots, hashes and official-repository issue-search results.

The root agent selected the minimal six-cell teaching hypothesis for review and integration, explicitly retaining the uncertain-intent label. This worker has not changed fixture policy, canonical data, shared admission or live native constructor. The direct factory has no query-label access, no special case for fixture coordinates, and no inverse-augmentation wrapper. Five focused tests live in `arc_agi2/test_falling_stick_hypothesis.py`.
