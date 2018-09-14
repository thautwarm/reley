from wisepy.talking import Talking
from .compiler import Ctx
from .grammar import RBNF
from bytecode import Bytecode
from rbnf.easy import *
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from Redy.Tools.PathLib import Path
from importlib._bootstrap_external import MAGIC_NUMBER
import marshal
import struct, time

import sys

parse_fn = None


def get_parse_fn():
    global parse_fn
    if not parse_fn:
        language = Language('reley')
        file_path = Path(__file__).parent().into('grammar.rbnf')
        build_language(RBNF, language, str(file_path))
        parse_fn = build_parser(language)
    return parse_fn


talking = Talking()


@talking
def cc(f: 'input filename', o: 'output filename'):
    """
    compile reley source code into pyc files
    """
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
    code = ctx.bc.to_code()
    timestamp = struct.pack('i', int(time.time()))
    marshalled_code_object = marshal.dumps(code)
    with Path(o).open('wb') as f:
        f.write(MAGIC_NUMBER)
        f.write(timestamp)
        f.write(b'A\x00\x00\x00')
        f.write(marshalled_code_object)


def main():
    talking.on()
