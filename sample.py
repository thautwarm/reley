from rbnf.easy import *
from astpretty import pprint
import dis
from reley.compiler import Ctx, Bytecode
from bytecode import dump_bytecode
from yapf.yapflib.yapf_api import FormatCode

ze_exp = ze.compile('import reley.grammar.[*]')

result = ze_exp.match(r"""

infix 0 ($)    

($) a = a 1

main () =
    print $ (\x -> x + 1) 1

""").result
# print(FormatCode(str(result))[0])

ctx = Ctx({}, {}, Bytecode(), {'+': 10}, False)
ctx.visit(result)
# #
global_ctx = {'+': lambda a: lambda b: a + b}
# print(dump_bytecode(ctx.bc))
code = ctx.bc.to_code()

# dis.dis(code)
#
# exec(code, global_ctx)
