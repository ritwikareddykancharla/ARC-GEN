# d931c21c — closed outlines and observable seam semantics

The teaching copy removes the isolated red corner at zero-based train[2], row 13, column 3 (2 to 0). GitHub's exact patch in [open PR #75](https://github.com/arcprize/ARC-AGI-2/pull/75) was downloaded and checked: its before and after task objects exactly match the stored canonical and proposed teaching fixtures. [Issue #58](https://github.com/arcprize/ARC-AGI-2/issues/58) explains why that corner has no supporting nearby blue wall. The PR remains unmerged. Original benchmark labels are unchanged.

The archived solver's green lining is not sufficient for all generated scenes. The constructor paints a green perimeter on each constituent rectangle, including internal seams. Touching the blue wall and touching a constituent rectangle's perimeter agree on the fixtures, but disagree on long internal seams. The archived touch-wall rule failed 10 of the first 100 fresh scenes. The native piece-boundary rule matched 1,000 of 1,000 fresh draws.

A visible interior is one rectangle or two adjacent rectangles. For a stepped union the split is unique. For an aligned L-shape the constructor accepts the decomposition with strictly smaller minimum piece area; equal-area alternatives are rejected. This is D4-invariant. The emitted program searches horizontal and vertical cuts. The independent gate searches corner-anchored rectangles with rectangular complements. It does not read latent constructor parameters.

Both plausible lining rules are retained as hypotheses. Demonstrations must distinguish them, or their query outputs must agree. An episode with only ordinary rectangle demonstrations and a seam-sensitive query is rejected for insufficient evidence, and receives new demonstrations instead of removing the harder query. All-open demonstrations also cannot invent the two output colours. There is no minimum-mismatch fallback, default hypothesis, hidden D4 choice, or constructor narrowing.

The native constructor is unchanged. Canonical third-demo labels deliberately fail the uniform rule. Audit counts refer specifically to the labelled teaching copy. The full gate and all-D4 audit is saved separately when complete.
