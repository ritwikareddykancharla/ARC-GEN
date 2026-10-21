# 9356391f: generator label repair, original fixtures preserved

The rule is: draw successive square rings from the legend; if a ring exceeds the canvas, turn its corresponding legend swatch gray. The independent [atlas explanation](https://github.com/yhay81/arc-agi-2-solution-atlas/blob/main/notes/9356391f.json) and [solver](https://github.com/yhay81/arc-agi-2-solution-atlas/blob/main/solutions/9356391f.py) both state this rule. Source snapshots and hashes are recorded here.

Canonical train[0] has seed (11,5), outer radius 5, so its bottom edge would reach row16 of a16-row grid. Its last swatch therefore changes8→5. No canonical cell needs correction. Original Opus instead proposed a seed-column legend modification; that is indistinguishable on these fixtures but not generally supported. `counterfactual-hypotheses.json` separates the hypotheses using native-supported parameter values.

The native constructor used hidden `last=5` only in validate(), while random generation omitted clipping marks. The proposed constructor preserves all random sampling parameters and input grids, removes that latent label override, and applies the clipping rule to every case. The parent reviewed and authorized applying this constructor fix. Canonical labels, teaching policy, shared admission and certificates remain untouched by this worker.

`audit.json` records the separately designated proposed-constructor audit:1,000 unique fresh pairs,8,000 D4/palette pair checks,16 canonical fixture variants. All pass an independent coordinate-perimeter oracle.320 of the1,000 native outputs differ; no input differs. Twelve failures of the former native labels are retained in `native-label-counterexamples.json`.

`native_constructor_before.py` preserves the old source. `proposed_constructor.py` preserves the audited proposal; live source differs only in explanatory comments/docstring. `../host-audit.json` records the subsequent standard audit against the live constructor hash. Seven focused tests are in `arc_agi2/test_clipped_ring_swatches.py`.

No matching official GitHub issue or PR was found. The supporting atlas is independent third-party evidence, not an official correction notice.
