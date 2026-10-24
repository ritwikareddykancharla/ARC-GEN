# Confetti palette coverage: f0df5ff0

The generator already covered this task ID and varied the canvas and seed count.
A remaining palette restriction prevented it from sampling an original example:
the old sampler drew six colours with replacement, so it could use at most six
distinct confetti colours. An original fixture contains seven.

The sampler now draws 1–8 distinct confetti colours without replacement, bounded
by available cells, and requires every selected colour to appear in the returned
scene. `num_confetti_colors` permits explicit count requests. Background (0) and
seed (1) retain their roles. Layout retries remain bounded at 200.

The rule remains: expand each blue seed to its 3×3 window while preserving coloured
confetti. Explicit canonical grids, transformation programs, checker, seed-window
geometry and colour roles are unchanged. This is a palette-domain correction,
not a new family or an altered target rule.

Validation: 15 focused tests cover canonical replay, counts 1–8, infeasible
requests, default count coverage and all eight spatial orientations. Fresh
certification checks 1,000 unique pairs, 8,000 augmented pair checks and 16 fixture
variants, with no reported sampler rejection. The episode-context audit is
rerun separately on the integrated source before release.
