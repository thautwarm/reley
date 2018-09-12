def is_indented(trailer, state):
    leader = state.ctx['leader']
    return leader.loc.colno < trailer.loc.colno


is_indented.name = 'is_indented'


def is_aligned(trailer, state):
    leader = state.ctx['leader']
    return leader.loc.colno == trailer.loc.colno


is_aligned.name = 'is_aligned'
