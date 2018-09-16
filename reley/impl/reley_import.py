import os
from importlib.machinery import ModuleSpec
from rbnf.easy import *
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from Redy.Tools.PathLib import Path
from .grammar import RBNF
from .compiler import *
import sys, types

parse_fn = None
reley_module_specs = {}


@visit.case(Import)
def _(imp: Import, ctx: Ctx):
    reley_mod_ctx = None
    spec = find_reley_module_spec(imp.imp_name)
    if spec:
        reley_mod_ctx: Ctx = get_context_from_spec(spec)

    if imp.name:
        ctx.add_local(imp.name, Val())

    stuffs = imp.stuffs or (imp.stuffs is 0 and tuple(
        Alias(imp.loc, each, each) for each in reley_mod_ctx.exported))

    if stuffs:
        for each in stuffs:
            if reley_mod_ctx:
                if each.imp_name in reley_mod_ctx.precedences:
                    ctx.precedences[each.name] = reley_mod_ctx.precedences[
                        each.imp_name]

                ctx.add_local(each.name, reley_mod_ctx.symtb[each.imp_name])
            else:
                ctx.add_local(each.name, Val())

    yield from wait(DECLARED)
    yield from wait(EVALUATED)
    yield from wait(RESOLVED)
    ctx.bc.append(Instr("LOAD_CONST", arg=0, lineno=imp.lineno + 1))
    ctx.bc.append(
        Instr(
            "LOAD_CONST",
            tuple(each.name for each in imp.stuffs) if imp.stuffs else
            ('*', ) if imp.stuffs is 0 else 0,
            lineno=imp.lineno + 1))
    ctx.bc.append(
        Instr("IMPORT_NAME", arg=imp.imp_name, lineno=imp.lineno + 1))
    if stuffs:
        for each in stuffs:
            ctx.bc.append(
                Instr(
                    "IMPORT_FROM", arg=each.imp_name, lineno=each.lineno + 1))
            name = each.name
            if name in ctx.bc.cellvars:
                ctx.bc.append(
                    Instr(
                        "STORE_DEREF", CellVar(name), lineno=each.lineno + 1))
            else:
                ctx.bc.append(
                    Instr('STORE_FAST', name, lineno=each.lineno + 1))

    elif imp.stuffs is 0:
        ctx.bc.append(Instr("IMPORT_STAR", lineno=imp.lineno + 1))

    if stuffs:

        if not imp.name:
            ctx.bc.append(Instr("POP_TOP", lineno=imp.lineno + 1))
            return
    if imp.name and imp.name in ctx.bc.cellvars:
        ctx.bc.append(
            Instr("STORE_DEREF", CellVar(imp.name), lineno=imp.lineno + 1))
    else:
        ctx.bc.append(Instr('STORE_FAST', imp.name, lineno=imp.lineno + 1))


def get_parse_fn():
    global parse_fn

    if not parse_fn:
        language = Language('reley')
        file_path = Path(__file__).parent().into('grammar.rbnf')
        build_language(RBNF, language, str(file_path))
        lexer, impl, namespace = language.lexer, language.implementation, language.namespace
        top_parser = language.named_parsers['module']

        def match(text, filename) -> ze.ResultDescription:
            state = State(impl, filename=filename)
            tokens = tuple(
                setattr(each, 'filename', filename) or each
                for each in lexer(text))
            result: Result = top_parser.match(tokens, state)

            return ze.ResultDescription(state, result.value, tokens)

        parse_fn = match

    return parse_fn


def print_ret(f):
    def call(*args, **kwargs):
        ret = f(*args, **kwargs)
        print(ret)
        return ret

    return call


def get_reley_module_spec_from_path(names, module_path):
    with Path(module_path).open('r') as fr:
        spec = ModuleSpec(names, ReleyLoader(names, module_path))
        reley_module_specs[names] = spec
        code = fr.read()
        parse = get_parse_fn()

        result = parse(code, module_path)
        check_parsing_complete(code, result.tokens, result.state)
        ast = result.result
        ctx = Ctx({}, {}, Bytecode(), {}, False)
        ctx.visit(ast)
        ctx.bc.filename = module_path
        spec.source_code = code
        spec.context = ctx
        return spec


def find_reley_module_spec(names, reload=False):

    reley_paths = sys.path

    for reley_path in reley_paths:

        if not reload:
            spec = reley_module_specs.get(names)
            if spec:
                return spec

        path_secs = (reley_path, *names.split('.'))
        *init, end = path_secs
        directory = Path(*init)
        if not directory.is_dir():
            continue
        end = end + '.hs'
        for each in os.listdir(str(directory)):
            if each.lower() == end:
                module_path = directory.into(each)
                return get_reley_module_spec_from_path(names, str(module_path))


class ReleyLoader:
    def __init__(self, mod_name, mod_path):
        self.mod_name = mod_name
        self.mod_path = mod_path

    def create_module(self, spec):
        doc = spec.context.bc.docstring
        mod = types.ModuleType(self.mod_name, doc)
        return mod

    def exec_module(self, module):
        f = self.mod_path
        setattr(module, '__path__', f)
        setattr(module, '__package__', self.mod_name)
        setattr(module, '__loader__', self)
        code: Bytecode = module.__spec__.context.bc
        code.filename = str(self.mod_path)

        exec(code.to_code(), module.__dict__)


def get_context_from_spec(spec: ModuleSpec) -> Ctx:
    return getattr(spec, 'context')
