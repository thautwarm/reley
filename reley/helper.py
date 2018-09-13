from rbnf.std.common import recover_codes

from .expr_based_ast import *


def is_indented(trailer, state):
    leader = state.ctx['leader']
    return leader.loc.colno < trailer.loc.colno


is_indented.name = 'is_indented'


def is_aligned(trailer, state):
    leader = state.ctx['leader']
    return leader.loc.colno == trailer.loc.colno


is_aligned.name = 'is_aligned'


def atom_rewrite(get):
    suite_, num_, strs_, symbol_, if_, let_, ret_, yield_, lit_ = map(
        get, ('SUITE', 'NUM', 'STRS', 'SYMBOL', 'IF', 'LET', 'RET', 'YIELD',
              'LITERAL'))
    if suite_: return suite_
    if num_: return Number(loc @ num_, eval(num_.value))
    if strs_: return Str(loc @ strs_[0], ''.join(eval(_.value) for _ in strs_))
    if symbol_: return Symbol(loc @ symbol_, symbol_.name)
    if if_: return If(loc @ if_, get('cond'), get('iftrue'), get('iffalse'))
    if let_: return Where(loc @ let_, get('out'), get('stmts'))
    if ret_: return Return(loc @ ret_, get('expr'))
    if yield_: return Yield(loc @ yield_, get('expr'))
    if lit_: return lit_
    raise TypeError


def bin_op_rewrite(get):
    basic, names, seq = map(get, ('basic', 'names', 'seq'))
    if basic:
        return Operator(loc @ basic, basic.value)
    if names:
        return Operator(loc @ names[0], recover_codes(names))
    if seq:
        return Operator(loc @ seq[0], ''.join(map(lambda _: _.value, seq)))
    raise TypeError
