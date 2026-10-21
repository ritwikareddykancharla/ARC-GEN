# df8cc377: proposed extra demonstration

Status: **teaching-context proposal, pending root policy review**. This does not certify the original canonical context.

The three original demonstrations have six frame interiors whose widths are all odd. Their outputs identify the top-versus-bottom checkerboard anchor, but not left versus right. The original query has an even-width interior, so those two remaining interpretations give different outputs. The strict solver and independent gate correctly abstain on every one of the 16 canonical D4/palette variants.

The proposal appends exactly one native-generated 10×10 demonstration. It contains a 4×3 frame (2×1 interior, one matching pixel) and a 3×5 frame (1×3 interior, two matching pixels). The first frame supplies the missing horizontal phase equation. Parameters and full grids are stored in `proposed-context-enriched-fixture.json`.

For anchor bits a (bottom) and b (right), the visible top-left interior phase is:

    a*(interior_height-1) + b*(interior_width-1)  mod 2.

Existing demonstrations supply a=0. The added demonstration supplies b=0. These two independent equations identify the entire corner hypothesis; this conclusion uses demonstration inputs/outputs, not the query answer.

One extra demonstration is minimal in number: zero leaves two distinguishable hypotheses, while one suffices. No claim is made that its number of pixels is minimal.

Verification in `context-enrichment-audit.json`:

- Four original pairs remain unchanged.
- Across 8 D4 transforms and 2 palettes: all 64 original-pair predictions and all 16 added-demo predictions match their existing labels.
- Original-context queries abstain in all 16 variants.
- Changing the factory's D4 argument on fixed visible context leaves predictions unchanged in 128 comparisons.
- Unchanged native generator renders the new demonstration; all parameters satisfy its random-domain constraints.
- Query labels are used only after prediction for exact verification.

This adds information to the teaching context; it does not establish that the original ambiguous context is solvable. Synthetic episodes can instead obtain the same missing evidence through fresh native demonstrations, keeping each sampled query fixed while replacing insufficient demonstrations.
