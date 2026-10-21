"""Label-free evidence gate for e5062a87 (template stamping into open cells).

Dispatch signature (colour_evidence.require_colour_evidence style):
    require_stamp_fit_evidence(demonstrations, queries, palette)
demonstrations: [{'input': g, 'output': g}, ...]   (visible, augmented coords)
queries:        [{'input': g}, ...]                (NO labels are read)
palette:        the episode colour permutation; open colour = palette[0],
                template colour = palette[2].

Raises MissingColourEvidence when the demonstrations fit no hypothesis of the
D4-closed stamping family, or when surviving hypotheses disagree on any query
(context shortfall). Delegates to the independent gate e5062a87_gate.gate.
"""
try:  # integrated inside the arc_agi2 package
    from .colour_evidence import MissingColourEvidence
    from . import e5062a87_gate as _G
except ImportError:  # portable use from ROOT/e5062a87
    import e5062a87_gate as _G

    class MissingColourEvidence(ValueError):
        pass


def require_stamp_fit_evidence(demonstrations, queries, palette=None):
    pal = list(range(10)) if palette is None else list(palette)
    zero, tcol = int(pal[0]), int(pal[2])
    demos = [(d['input'], d['output']) for d in demonstrations]
    if not demos:
        raise MissingColourEvidence('e5062a87: no demonstrations')
    if not queries:
        raise MissingColourEvidence('e5062a87: no queries')
    for q in queries:
        status, _, _ = _G.gate(demos, q['input'], zero, tcol)
        if status == 'unexplained':
            raise MissingColourEvidence('e5062a87: demonstrations fit no stamping hypothesis')
        if status != 'identified':
            raise MissingColourEvidence('e5062a87: surviving stamping hypotheses disagree on a query')
    return True
