# 973e499e: rectangular colour-matched self-tiling

The original generator sampled square inputs of side3–5, two or three nonzero colours, and line strokes. The archived verifier and existing standalone program already implement the same rule for rectangular inputs: output dimensions H²×W², with each H×W block retaining exactly the cells matching its corresponding input cell.

The constructor now samples independent H,W2–5 (16shapes), two to five used colours by default, and line/block/pixel patterns. Explicit requests can use up to nine nonzero colours when they fit. All requested colours must occur. Inputs larger than5 on either axis are excluded because the squared output axis would exceed30. Existing explicit size/colours calls and canonical fixture labels are unchanged. Rejection loops are bounded and never substitute a fixed example.

Validation:68tests cover all16shapes×3styles, palette counts2–9, deterministic replay, invalid requests, independent closed-form labels, unchanged canonical fixtures, archived verifier agreement, and all8D4/palette program variants. Standard recertification passes1000fresh pairs,8000augmented pair checks and16fixture variants, with1000distinct inputs and no rejected proposals. See native-certificates/973e499e.json for exact source hashes.

## Episode evidence and production registration

The new `self_match_evidence.py` compares equality, inequality and all-cell
masks; outer-cell versus inner-cell paint colours; and independent orientations
of the block map and its tiles. Fill colours are inferred from demonstrations.
All rules fitting every demonstration must agree on each query input. It never
reads a query answer. This finite competitor family is not a general proof of
identifiability.

The tests include three horizontally symmetric demonstrations and an asymmetric
query with four distinct input orbits. Correct colour matching and reflected
tile matching agree on all demonstrations but disagree on the query. Replacing
one demonstration with an asymmetric scene resolves the conflict while leaving
the query unchanged. The checks hold under all eight D4 transforms and two
palettes; adding a bogus query answer does not affect the result.

A seeded fixed-query audit accepted all 1,000 queries without replacing any
query. Demonstrations were resampled under the original task's strict shape
profile and four-distinct-orbit requirement. Every accepted episode passed all
eight augmented program/target checks (8,000 total). The query answer was read
only after context admission. See `context-audit.json` for exact source hashes,
shape counts and rejection counts. This family is now registered for episode
production. Focused gate tests:25 passed, in addition to68 constructor tests.
