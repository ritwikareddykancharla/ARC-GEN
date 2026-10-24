# 973e499e: rectangular colour-matched self-tiling

The original generator sampled square inputs of side3–5, two or three nonzero colours, and line strokes. The archived verifier and existing standalone program already implement the same rule for rectangular inputs: output dimensions H²×W², with each H×W block retaining exactly the cells matching its corresponding input cell.

The constructor now samples independent H,W2–5 (16shapes), two to five used colours by default, and line/block/pixel patterns. Explicit requests can use up to nine nonzero colours when they fit. All requested colours must occur. Inputs larger than5 on either axis are excluded because the squared output axis would exceed30. Existing explicit size/colours calls and canonical fixture labels are unchanged. Rejection loops are bounded and never substitute a fixed example.

Validation:68tests cover all16shapes×3styles, palette counts2–9, deterministic replay, invalid requests, independent closed-form labels, unchanged canonical fixtures, archived verifier agreement, and all8D4/palette program variants. Standard recertification passes1000fresh pairs,8000augmented pair checks and16fixture variants, with1000distinct inputs and no rejected proposals. See native-certificates/973e499e.json for exact source hashes.

This commit expands the generator. It does not yet register this family for the hybrid episode export: demonstration sufficiency and strict pool support must be checked separately. No benchmark labels, verifier or standalone program were edited.
