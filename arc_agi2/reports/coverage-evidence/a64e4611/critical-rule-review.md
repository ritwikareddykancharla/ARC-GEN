# Critical review of the visible-clearance candidate

**The constants are family parameters, not uniquely identified by the original demonstrations.** A search over minimum run length1–30 and pruning width0–10 leaves20 demo-compatible variants (run12–16, prune3–6). They all solve the canonical query, yet disagree on10 of the12 retained random inputs. Thus the successful fixture audit is compatible with multiple extensions to synthetic scenes.

The existing atlas selects12/3, but this provenance is supporting implementation evidence, not authoritative evidence of intended semantics. It is defensible only as a named synthetic convention; it is not defensible as an ambiguity-only correction of the old family.

| Seed | Why synthetic labels changed |
|---|---|
| 646110001 | painted native outline: 3 cells |
| 646110003 | painted native outline: 22 cells |
| 646110005 | painted native outline: 6 cells |
| 646110006 | painted native outline: 7 cells |
| 646110007 | painted native outline: 8 cells; painted accidentally clear noise space: 6 cells |
| 646110011 | painted native outline: 9 cells |
| 646110012 | painted native outline: 5 cells |
| 646110013 | painted native outline: 2 cells |
| 646110015 | painted native outline: 6 cells |
| 646110016 | painted native outline: 27 cells |
| 646110023 | painted native outline: 8 cells; removed native green no 12 cell safe run: 33 cells |
| 646110024 | removed native green no 12 cell safe run: 42 cells; painted native outline: 2 cells |

Added cells occupy either a hidden rectangle outline or chance-clear noise space. They qualify as long safe runs under the visible rule, but were not part of a native rectangle interior. Removed cells either lack the12-cell run requirement or are trimmed as short exposed dead ends. These differences are mechanistic, not merely formatting or tie corrections. In particular, the minimum-run criterion can remove genuine native short branches.

Recommended treatment: do not count this as proof that the original sampler is solved. If adopted, version it as a separate visible-clearance synthetic variant and record parameters in provenance. A stronger alternative is to fit the threshold family on the episode demonstrations and require surviving hypotheses to agree on the query; disagreement should trigger additional informative demonstrations or explicit abstention, never query-label selection.

No native constructor, canonical labels, shared policy or admission certificate was changed.
