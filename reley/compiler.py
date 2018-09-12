from Redy.Magic.Pattern import Pattern
from typing import Dict
from bytecode import Instr, Bytecode, FreeVar, CellVar, Label
from toolz import curry
from functools import reduce
from .precedence import bin_reduce
from reley.expr_based_ast import *

map = curry(map)
reduce = curry(reduce)
getattr = curry(getattr)

OPTIMIZED = 1
NEWLOCALS = 2
NESTED = 16
NOFREE = 64
GENERATOR = 32
COROUTINE = 128
ITERABLE_COROUTINE = 256


@curry
def flip(f, a, b):
    return f(b, a)


def fst(it):
    return it[0]


class Val:
    pass


def lens(**kwargs):
    def apply(it):
        return {**it, **kwargs}

    return apply


def identity(it):
    return it


def fix_bytecode(bc: Bytecode):
    for each in bc:
        if isinstance(each, Instr):
            if isinstance(each.arg, CellVar):
                bc.cellvars.append(each.arg.name)
            elif isinstance(each.arg, FreeVar):
                bc.freevars.append(each.arg.name)


class Ctx:
    # precedences: dict
    symtb: Dict[str, Val]
    local: Dict[str, Val]
    bc: Bytecode
    precedences: Dict[str, int]
    is_nested: bool

    def __init__(self, symtb, local, bc, precedences, is_nested):
        self.symtb = symtb
        self.local = local
        self.bc = bc
        self.precedences = precedences
        self.is_nested = is_nested

    def new(self) -> 'Ctx':
        return Ctx(self.symtb, {}, Bytecode(), self.precedences, True)

    def add_infix(self, name, priority):
        self.precedences = {**self.precedences, **{name: priority}}

    def add_local(self, name, val):
        if name not in self.local:
            self.local[name] = val
            symtb = self.symtb = {**self.symtb}
            symtb[name] = val

    def visit(self, tast):
        return visit(tast, self)


@Pattern
def visit(tast, _):
    return type(tast)


@visit.case(DefFun)
def _(tast: DefFun, ctx: Ctx):
    new_ctx = ctx.new()
    args = [arg.name for arg in tast.args]

    for each in tast.args:
        new_ctx.visit(each)

    bc = new_ctx.bc
    bc.kwonlyargcount = 0
    bc.filename = tast.loc.filename

    if any(args):
        bc.argcount = 1
        if len(args) is 1:
            bc.argnames = args
        else:
            arg_name = '.'.join(args)
            bc.argnames = [arg_name]
            bc.append(Instr('LOAD_FAST', arg_name, lineno=tast.args[0].lineno))
            bc.append(Instr('UNPACK_SEQUENCE', arg=len(args)))
            for arg in args:
                bc.append(Instr('STORE_FAST', arg=arg))
    else:
        bc.argcount = 0

    new_ctx.visit(tast.body)

    bc.name = tast.name or '<lambda>'
    bc.append(Instr("RETURN_VALUE"))
    fix_bytecode(bc)
    # for each in (bc):
    #     print(each)
    # print('++++++++++')
    if any(bc.freevars):
        for each in bc.freevars:
            if each not in ctx.local:
                ctx.bc.flags |= NEWLOCALS
                ctx.bc.freevars.append(each)
            ctx.bc.append(
                Instr('LOAD_CLOSURE', CellVar(each), lineno=tast.lineno))
        ctx.bc.append(
            Instr("BUILD_TUPLE", arg=len(bc.freevars), lineno=tast.lineno))
    else:
        bc.flags |= NOFREE
    if ctx.is_nested:
        bc.flags |= NESTED
    bc.flags |= OPTIMIZED

    ctx.bc.append(Instr('LOAD_CONST', arg=bc.to_code(), lineno=tast.lineno))
    ctx.bc.append(Instr('LOAD_CONST', arg=bc.name, lineno=tast.lineno))
    ctx.bc.append(
        Instr(
            'MAKE_FUNCTION',
            arg=8 if any(bc.freevars) else 0,
            lineno=tast.lineno))

    if tast.name:
        name = tast.name
        if name not in ctx.local:
            ctx.add_local(name, Val())

        ctx.bc.append(Instr('STORE_FAST', name, lineno=tast.lineno))
        ctx.bc.append(Instr("LOAD_FAST", name, lineno=tast.lineno))


@visit.case(Number)
def _(tast: Number, ctx: Ctx):
    ctx.bc.append(Instr("LOAD_CONST", tast.value, lineno=tast.lineno))


@visit.case(Str)
def _(tast: Str, ctx: Ctx):
    ctx.bc.append(Instr("LOAD_CONST", tast.value, lineno=tast.lineno))


@visit.case(Symbol)
def _(tast: Symbol, ctx: Ctx):
    name = tast.name

    if name in ctx.local:
        return ctx.bc.append(Instr('LOAD_FAST', name, lineno=tast.lineno))

    if name in ctx.symtb:
        return ctx.bc.append(
            Instr('LOAD_DEREF', FreeVar(name), lineno=tast.lineno))
    else:
        return ctx.bc.append(Instr('LOAD_GLOBAL', name, lineno=tast.lineno))


@visit.case(Call)
def visit_call(ast: Call, ctx: Ctx):
    ctx.visit(ast.callee)

    if isinstance(ast.arg, Void):
        return ctx.bc.append(Instr("CALL_FUNCTION", arg=0, lineno=ast.lineno))
    else:
        ctx.visit(ast.arg)
        return ctx.bc.append(Instr("CALL_FUNCTION", arg=1, lineno=ast.lineno))


@visit.case(If)
def _(ast: If, ctx: Ctx):
    label1 = Label()
    label2 = Label()
    ctx.visit(ast.cond)
    ctx.bc.append(
        Instr("POP_JUMP_IF_FALSE", arg=label1, lineno=ast.cond.lineno))
    ctx.visit(ast.iftrue)
    ctx.bc.append(Instr('JUMP_FORWARD', arg=label2, lineno=ast.iftrue.lineno))
    ctx.bc.append(label1)
    ctx.visit(ast.iffalse)
    ctx.bc.append(label2)


@visit.case(Arg)
def _(ast: Arg, ctx: Ctx):
    ctx.bc.argnames.append(ast.name)
    # TODO:
    ctx.add_local(ast.name, ast.ty)


@visit.case(Suite)
def _(ast: Suite, ctx: Ctx):
    not_start = True
    pop = lambda lineno: not_start or ctx.bc.append(Instr('POP_TOP', lineno=lineno))
    if ast.statements:
        for each in ast.statements:
            pop(each.lineno)
            ctx.visit(each)
            not_start = False
    else:
        ctx.bc.append(Instr('LOAD_CONST', None))


def _last_lineno(bc):
    for each in bc[::-1]:
        if hasattr(each, 'lineno'):
            return each.lineno
    return 1


@visit.case(Module)
def _(ast: Module, ctx: Ctx):
    not_start = True
    pop = lambda lineno: not_start or ctx.bc.append(Instr('POP_TOP', lineno=lineno))
    for each in ast.statements:
        pop(each.lineno)
        ctx.visit(each)
        not_start = False

    lineno = _last_lineno(ctx.bc)

    ctx.bc.append(Instr("RETURN_VALUE", lineno=lineno))


@visit.case(BinSeq)
def _(ast: BinSeq, ctx: Ctx):
    reduce = bin_reduce(ctx.precedences)
    ctx.visit(reduce(ast.seq))


@visit.case(Infix)
def _(ast: Infix, ctx: Ctx):
    ctx.add_infix(ast.op, ast.precedence)
    ctx.bc.append(Instr("LOAD_CONST", arg=ast.precedence, lineno=ast.lineno))


@visit.case(Void)
def _(_, ctx: Ctx):
    ctx.bc.append(Instr("LOAD_CONST", None))


@visit.case(Tuple)
def _(tp: Tuple, ctx: Ctx):
    for each in tp.seq:
        ctx.visit(each)
    ctx.bc.append(Instr("BUILD_TUPLE", arg=len(tp.seq), lineno=tp.lineno))


@visit.case(Return)
def _(ret: Return, ctx: Ctx):
    ctx.visit(ret.expr)
    ctx.bc.append(Instr('RETURN_VALUE', lineno=ret.lineno))


@visit.case(Return)
def _(yd: Yield, ctx: Ctx):
    ctx.visit(yd.expr)
    ctx.bc.append(Instr("YIELD_VALUE", lineno=yd.lineno))


@visit.case(Let)
def _(let: Let, ctx: Ctx):
    ctx.visit(let.value)
    origin = let.name
    count = len(ctx.bc)
    target = f'{origin}.{count}'

    def substitue(it: TAST):
        if hasattr(it, 'name') and it.name == origin:
            return type(it)(**dict(it.iter_fields, name=target))
        return it

    ctx.add_local(target, Val())
    ctx.bc.append(Instr('STORE_FAST', arg=target, lineno=let.value.lineno))
    out = transform(substitue)(let.out)
    ctx.visit(out)
