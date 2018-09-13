from typing import NamedTuple, List, Tuple
from Redy.Magic.Classic import record
from numpy import number
from rbnf.easy import Tokenizer
globals()['NamedTuple'] = object


class Loc:
    __slots__ = ['lineno', 'colno', 'filename']

    lineno: int
    colno: int
    filename: str

    def __init__(self, lineno, colno, filename):
        self.lineno = lineno
        self.colno = colno
        self.filename = filename

    def __matmul__(self, other):
        if isinstance(other, Tokenizer):
            return Loc(other.lineno, other.colno, self.filename)
        return Loc(*other.loc)

    def __iter__(self):
        yield self.lineno
        yield self.colno
        yield self.filename

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'Loc(lineno={!r}, colno={!r}, filename={!r})'.format(
            self.lineno, self.colno, self.filename)

    def update(self, lineno=None, colno=None, filename=None):
        if lineno:
            self.lineno = lineno
        if colno:
            self.colno = colno
        if filename:
            self.filename = filename


class TAST:
    loc: Loc

    @property
    def iter_fields(self):
        for it in self.__annotations__:
            if not it.startswith('_') and it not in ('iter_fields', 'lineno'):
                yield it, getattr(self, it)

    @property
    def lineno(self):
        return self.loc.lineno


loc = Loc(0, 0, "")


@record
class DefTy(TAST, NamedTuple):
    loc: Loc
    name: str
    structure: TAST


@record
class DefFun(TAST, NamedTuple):
    loc: Loc
    name: str
    args: 'List[Arg]'
    body: TAST


@record
class Arg(TAST, NamedTuple):
    loc: Loc
    name: str
    ty: TAST


@record
class Suite(TAST, NamedTuple):
    loc: Loc
    statements: List[TAST]


@record
class Definition(TAST, NamedTuple):
    loc: Loc
    statements: List[TAST]


@record
class Where(TAST, NamedTuple):
    loc: Loc
    out: Suite
    pre_def: Definition


@record
class DefVar(TAST, NamedTuple):
    loc: Loc
    name: str
    value: TAST


@record
class If(TAST, NamedTuple):
    loc: Loc
    cond: TAST
    iftrue: TAST
    iffalse: TAST


@record
class Call(TAST, NamedTuple):
    loc: Loc
    callee: TAST
    arg: TAST


@record
class Symbol(TAST, NamedTuple):
    loc: Loc
    name: str


@record
class Number(TAST, NamedTuple):
    loc: Loc
    value: number


@record
class Str(TAST, NamedTuple):
    loc: Loc
    value: str


@record
class HList(TAST, NamedTuple):
    loc: Loc
    seq: List[TAST]


@record
class HDict(TAST, NamedTuple):
    loc: Loc
    seq: List[Tuple[TAST, TAST]]


def make_set(seq: List[TAST]):
    return tuple((each, Void(each.loc)) for each in seq)


@record
class Tuple(TAST, NamedTuple):
    loc: Loc
    seq: Tuple[TAST, ...]


@record
class Return(TAST, NamedTuple):
    loc: Loc
    expr: TAST


@record
class Yield(TAST, NamedTuple):
    loc: Loc
    expr: TAST


@record
class BinSeq(TAST, NamedTuple):
    loc: Loc
    seq: List[TAST]


@record
class Infix(TAST, NamedTuple):
    loc: Loc
    precedence: int
    op: str


@record
class Operator(TAST, NamedTuple):
    loc: Loc
    name: str


@record
class Void(TAST, NamedTuple):
    loc: Loc
    pass


@record
class Module(NamedTuple):
    stmts: Definition


def transform(f):
    def ff(it):
        return generic_visit(f(it))

    def generic_visit(ast: TAST):
        def stream():
            ast_new = f(ast)
            for key, value in ast_new.iter_fields:

                if isinstance(value, Loc):
                    yield key, value
                elif type(value) in (tuple, list):
                    yield key, list(ff(e) for e in value)
                else:
                    yield key, ff(value)

        if hasattr(ast, 'iter_fields'):

            return type(ast)(**dict(stream()))

        return ast

    return generic_visit
