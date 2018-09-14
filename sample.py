from rbnf.easy import *
from Redy.Tools.PathLib import Path
from astpretty import pprint
import dis
from reley.compiler import Ctx, Bytecode
from bytecode import dump_bytecode
from yapf.yapflib.yapf_api import FormatCode

language = Language('reley')
file_path = Path(__file__).parent().into('reley').into('grammar.rbnf')
build_language(file_path.open('r').read(), language, str(file_path))
parse = build_parser(language)
# ze_exp = ze.compile('import reley.grammar.[*]')
result = parse(r"""

import operator (add, eq)
import functools (reduce)
import toolz (curry)

infix 5 (==)
(==) = curry eq


m_sum lst = if lst == [] then 0
            else destruct lst
            where
                destruct (a, b) = a + m_sum(b)

main () =
    print(m_sum [1, 2, 3])






""").result
# print(FormatCode(str(result))[0])

ctx = Ctx({}, {}, Bytecode(), {'+': 10}, False)
ctx.visit(result)

# #
global_ctx = {'+': lambda a: lambda b: a + b}
# print(dump_bytecode(ctx.bc))
# dump_bytecode(ctx.bc)
code = ctx.bc.to_code()
# dis.dis(code)
#
exec(code, global_ctx)
