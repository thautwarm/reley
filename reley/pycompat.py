import sys, os
from .grammar import RBNF
from .compiler import Ctx
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from bytecode import Bytecode, dump_bytecode
from types import ModuleType
from rbnf.easy import *
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from Redy.Tools.PathLib import Path

parse_fn = None


def get_parse_fn():
    global parse_fn
    if not parse_fn:
        language = Language('reley')
        file_path = Path(__file__).parent().into('grammar.rbnf')
        build_language(RBNF, language, str(file_path))
        parse_fn = build_parser(language)
    return parse_fn


class ReleyLoader:
    def __init__(self, mod_name, mod_path):
        self.mod_name = mod_name
        self.mod_path = mod_path

    def create_module(self, spec: ModuleSpec):
        return ModuleType(spec.name, spec)

    def exec_module(self, module):
        f = self.mod_path
        setattr(module, '__path__', f)
        setattr(module, '__package__', self.mod_name)
        with Path(f).open('r') as fr:
            source_code = fr.read()

            parse = get_parse_fn()
            result = parse(source_code)
        f = str(Path(f))
        result.state.filename = f
        check_parsing_complete(source_code, result.tokens, result.state)
        ast = result.result
        ctx = Ctx({}, {}, Bytecode(), {'+': 10}, False)
        ctx.visit(ast)
        ctx.bc.filename = f
        dump_bytecode(ctx.bc)
        code = ctx.bc.to_code()

        exec(code, module.__dict__)


class ReleyFinder:

    virtual_name = 'my_virtual_module'

    def find_spec(self, fullname: str, paths, target=None):
        for path in paths:

            path = path or './'
            *packages, end = fullname.split('.')
            if packages:
                packages = packages[1:]

            path = os.path.join(path, *packages)
            for each in os.listdir(path):

                name, ext = os.path.splitext(each)
                if ext.lower() == '.hs' and name == end:
                    return ModuleSpec(
                        fullname,
                        ReleyLoader(fullname,
                                    os.path.abspath(os.path.join(path, each))))


sys.meta_path.append(ReleyFinder())
