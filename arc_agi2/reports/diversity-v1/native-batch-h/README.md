# Native H:6d1d5c90 marker-controlled picture roll

Source review found two incidental restrictions in the old constructor: fixed
6x7 input/6x6 output, and exactly7 used colours despite8 in every canonical
pair. The rule is to remove the left control strip and cyclically roll the
picture down by the marker row. No object shape or density is necessary for
that rule. The independent archived checker and standalone factory already
implement the general relation; neither was changed.

Changes: input heights2–30, picture widths1–29 (input adds one control column),
1–8 actual picture colours, bars/blocks/pixels, and every valid marker row.
A quarter of default dimensions stay6x6 picture; remaining dimensions sample
independently. The image is constructed before labels are computed. Explicit
legacy colours retain6x7 defaults and exact labels, including all canonical
fixtures. Default scenes use strip colours2/6 only in the control column;
explicit legacy inputs remain accepted with old labels. No canonical labels
or benchmark files changed.

New demo-only gate considers both picture axes and affine marker-to-shift
maps (a*r+b,0<=a,b<30), including copying, constant shifts, reversed/end-relative
and off-by-one interpretations. All surviving hypotheses must agree on the
query input. This is a bounded ambiguity check, not universal identifiability.
The query answer is used only afterward for final program verification.

Validation:52 focused tests, unchanged canonical replay;1000 fresh pairs,
8000 augmented pair checks,16 fixture variants,991 unique native inputs,
zero sampler rejections. One thousand domain draws cover509 input shapes and
3–10 used input colours (118 have8). All500 fixed queries find verified contexts
within100 attempts;128 ambiguous-context and9 repeated-identity attempts are
resampled with the query fixed. See audit.json for source hashes and every
query outcome. No source registration or production export is claimed here.

Small dimensions can have finite identity capacity. No count of repeated
examples is presented as unique diversity. The original seven-colour domain
remains reachable; the expanded distribution is deliberately different.
