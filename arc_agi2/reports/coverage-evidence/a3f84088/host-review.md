# a3f84088 — uniform ring construction, labelled teaching correction

The visible rule is a repeating ring sequence: grey, red, grey, background, continuing into the centre. It is independent of canvas size. The old generator skipped the final centre only when the canvas side was 13, and prevented a frame width of 13 during random generation. These were exceptions, not an input-visible rule.

The active constructor now removes those two clauses, as approved by the root agent. It preserves the original size range and expands back to frame width 13. An independent layer-peeling implementation matches every one of the 351 size/frame-width combinations in the original parameter bounds. Four size-13 cases previously omitted a non-background centre.

The teaching copy changes exactly one cell: zero-based train[3], row 5, column 5, from 0 to 5. The original canonical JSON stays unchanged. The same inconsistency is discussed in [open issue #132](https://github.com/fchollet/ARC-AGI/issues/132); this is a labelled local teaching interpretation, not an officially adopted benchmark correction.

The emitted program uses minimum distance to the square boundary; the independent gate paints nested perimeters. Both require demonstration agreement and read only query input. The source has no D4 branch or canvas-specific fallback. A poisoned query output cannot affect the gate.

The proposed-copy audit passed 1,000 unique fresh pairs, 8,000 augmented pair checks, and 16 fixture variants. Those counts refer to the labelled teaching copy, not canonical label reproduction. A separate live audit follows policy integration.
