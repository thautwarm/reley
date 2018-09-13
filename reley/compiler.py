import dis

from Redy.Magic.Pattern import Pattern
from typing import Dict
from bytecode import Instr, Bytecode, FreeVar, CellVar, Label, dump_bytecode
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
        if not isinstance(each, Instr):
            continue
        arg = each.arg
        if not isinstance(arg, FreeVar):
            continue
        name = arg.name
        if name not in bc.freevars:
            bc.freevars.append(name)


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

    def add_non_local(self, name, val):
        if name not in self.symtb:
            self.symtb = symtb = {**self.symtb}
            symtb[name] = val

    def add_local(self, name, val):
        if name not in self.local:
            self.local[name] = val
            symtb = self.symtb = {**self.symtb}
            symtb[name] = val
            self.bc.flags |= NEWLOCALS

    def add_locals(self, name_vals):
        if any(name_vals):
            self.bc.flags |= NEWLOCALS
        for name, val in name_vals:
            if name not in self.local:
                self.local[name] = val
                symtb = self.symtb = {**self.symtb}
                symtb[name] = val

    def visit(self, tast):
        return visit(tast, self)


@Pattern
def visit(tast, _):
    return type(tast)


@visit.case(DefVar)
def _(tast: DefVar, ctx: Ctx):
    name = tast.name
    ctx.add_local(name, Val())
    yield from ctx.visit(tast.value)
    yield
    if name in ctx.bc.cellvars:
        ctx.bc.append(Instr("STORE_DEREF", arg=CellVar(name)))
    else:
        ctx.bc.append(Instr('STORE_FAST', arg=tast.name))
    yield


@visit.case(DefFun)
def visit_def_fun(def_fun: DefFun, ctx: Ctx):
    name = def_fun.name
    if name:
        ctx.add_local(name, Val())

    new_ctx = ctx.new()
    args = [arg.name for arg in def_fun.args]
    for each in def_fun.args:
        new_ctx.visit(each)

    bc = new_ctx.bc
    bc.kwonlyargcount = 0
    bc.filename = def_fun.loc.filename

    if any(args):
        bc.argcount = 1
        if len(args) is 1:
            bc.argnames = args
        else:
            arg_name = '.'.join(args)
            bc.argnames = [arg_name]
            bc.append(
                Instr('LOAD_FAST', arg_name, lineno=def_fun.args[0].lineno))
            bc.append(Instr('UNPACK_SEQUENCE', arg=len(args)))
            for arg in args:
                bc.append(Instr('STORE_FAST', arg=arg))
    else:
        bc.argcount = 0

    yield

    async_app(new_ctx.visit(def_fun.body))
    bc.name = name or '<lambda>'
    bc.append(Instr("RETURN_VALUE"))
    fix_bytecode(bc)
    # for each in (bc):
    #     print(each)
    # print('++++++++++')

    if any(bc.freevars):
        for each in bc.freevars:
            if each not in ctx.local:
                if each not in ctx.bc.freevars:
                    ctx.bc.freevars.append(each)
                ctx.bc.append(
                    Instr(
                        'LOAD_CLOSURE', FreeVar(each), lineno=def_fun.lineno))
            else:
                if each not in ctx.bc.cellvars:
                    ctx.bc.cellvars.append(each)
                ctx.bc.append(
                    Instr(
                        'LOAD_CLOSURE', CellVar(each), lineno=def_fun.lineno))
        ctx.bc.append(
            Instr("BUILD_TUPLE", arg=len(bc.freevars), lineno=def_fun.lineno))

    if ctx.is_nested:
        bc.flags |= NESTED
    bc.flags |= OPTIMIZED
    # dump_bytecode(bc)
    yield
    code = bc.to_code()
    # dis.show_code(code)
    ctx.bc.append(Instr('LOAD_CONST', arg=code, lineno=def_fun.lineno))
    ctx.bc.append(Instr('LOAD_CONST', arg=bc.name, lineno=def_fun.lineno))
    ctx.bc.append(
        Instr(
            'MAKE_FUNCTION',
            arg=8 if any(bc.freevars) else 0,
            lineno=def_fun.lineno))

    if name:
        if name in ctx.bc.cellvars:
            ctx.bc.append(
                Instr("STORE_DEREF", CellVar(name), lineno=def_fun.lineno))
        else:
            ctx.bc.append(Instr('STORE_FAST', name, lineno=def_fun.lineno))


@visit.case(Number)
def _(tast: Number, ctx: Ctx):
    ctx.bc.append(Instr("LOAD_CONST", tast.value, lineno=tast.lineno))
    yield


@visit.case(Str)
def _(tast: Str, ctx: Ctx):
    ctx.bc.append(Instr("LOAD_CONST", tast.value, lineno=tast.lineno))
    yield


@visit.case(Symbol)
def _(tast: Symbol, ctx: Ctx):
    name = tast.name

    if name in ctx.local and name not in ctx.bc.cellvars:
        ctx.bc.append(Instr('LOAD_FAST', name, lineno=tast.lineno))
        return (yield)
    if name in ctx.symtb:
        ctx.bc.append(Instr('LOAD_DEREF', FreeVar(name), lineno=tast.lineno))
        return (yield)
    else:
        ctx.bc.append(Instr('LOAD_GLOBAL', name, lineno=tast.lineno))
        return (yield)


@visit.case(Call)
def visit_call(ast: Call, ctx: Ctx):
    yield from ctx.visit(ast.callee)

    if isinstance(ast.arg, Void):
        ctx.bc.append(Instr("CALL_FUNCTION", arg=0, lineno=ast.lineno))
    else:
        yield from ctx.visit(ast.arg)
        ctx.bc.append(Instr("CALL_FUNCTION", arg=1, lineno=ast.lineno))


@visit.case(If)
def _(ast: If, ctx: Ctx):
    label1 = Label()
    label2 = Label()
    yield from ctx.visit(ast.cond)
    ctx.bc.append(
        Instr("POP_JUMP_IF_FALSE", arg=label1, lineno=ast.cond.lineno))
    yield from ctx.visit(ast.iftrue)
    ctx.bc.append(Instr('JUMP_FORWARD', arg=label2, lineno=ast.iftrue.lineno))
    ctx.bc.append(label1)
    yield from ctx.visit(ast.iffalse)
    ctx.bc.append(label2)


@visit.case(Arg)
def _(ast: Arg, ctx: Ctx):
    ctx.bc.argnames.append(ast.name)
    # TODO:
    ctx.add_local(ast.name, ast.ty)


@visit.case(Suite)
def _(ast: Suite, ctx: Ctx):
    if ast.statements:

        def pop(lineno):
            return lambda: ctx.bc.append(Instr('POP_TOP', lineno=lineno))

        def now():
            return ()

        for each in ast.statements:
            now()
            pop(each.lineno)
            async_app(ctx.visit(each))
            now = pop(each.lineno)
    else:
        ctx.bc.append(Instr('LOAD_CONST', None))
    yield


@visit.case(Definition)
def _(ast: Suite, ctx: Ctx):
    if ast.statements:
        cos = []

        for each in ast.statements:
            cos.append(ctx.visit(each))

        run_event_loop(cos)
    yield


@visit.case(Module)
def _(ast: Module, ctx: Ctx):
    async_app(ctx.visit(ast.stmts))
    if ctx.local.get('main'):

        ctx.bc.append(Instr('LOAD_FAST', arg='main'))
        ctx.bc.append(Instr('CALL_FUNCTION', arg=0))
        ctx.bc.append(Instr("RETURN_VALUE"))
    else:
        ctx.bc.append(Instr("LOAD_CONST", 0))
        ctx.bc.append(Instr("RETURN_VALUE"))


@visit.case(BinSeq)
def _(ast: BinSeq, ctx: Ctx):
    reduce = bin_reduce(ctx.precedences)
    yield from ctx.visit(reduce(ast.seq))


@visit.case(Infix)
def _(ast: Infix, ctx: Ctx):
    ctx.add_infix(ast.op, ast.precedence)
    yield


@visit.case(Void)
def _(_, ctx: Ctx):
    ctx.bc.append(Instr("LOAD_CONST", None))
    yield


@visit.case(Tuple)
def _(tp: Tuple, ctx: Ctx):
    for each in tp.seq:
        yield from ctx.visit(each)
    ctx.bc.append(Instr("BUILD_TUPLE", arg=len(tp.seq), lineno=tp.lineno))


@visit.case(Return)
def _(ret: Return, ctx: Ctx):
    yield from ctx.visit(ret.expr)
    ctx.bc.append(Instr('RETURN_VALUE', lineno=ret.lineno))


@visit.case(Yield)
def _(yd: Yield, ctx: Ctx):
    yield from ctx.visit(yd.expr)
    ctx.bc.append(Instr("YIELD_VALUE", lineno=yd.lineno))


@visit.case(Where)
def _(where: Where, ctx: Ctx):
    names = new_entered_names(where.pre_def)
    count = len(ctx.bc)
    targets = {origin: f'{origin}.{count}' for origin in names}

    def substitute(it: TAST):
        if hasattr(it, 'name'):
            value = targets.get(it.name)
            if value:
                return type(it)(**dict(it.iter_fields, name=value))
            return it
        elif hasattr(it, 'names'):
            return type(it)(**dict(
                it.iter_fields,
                names=tuple(targets.get(each) or each for each in it.names)))
        return it

    pre_def = transform(substitute)(where.pre_def)
    out = transform(substitute)(where.out)
    yield from ctx.visit(pre_def)
    yield from ctx.visit(out)


def new_entered_names(it: Definition):
    for each in it.statements:
        if isinstance(each, (DefFun, DefTy, DefVar)):
            yield each.name


def async_app(co):
    for _ in co:
        pass


def run_event_loop(cos):
    tasks = list(range(len(cos)))
    while tasks:
        for each in tuple(tasks):
            try:
                next(cos[each])
            except StopIteration:
                tasks.remove(each)
