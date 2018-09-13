from rbnf.easy import *
from astpretty import pprint
import dis
from reley.compiler import Ctx, Bytecode, async_app
from bytecode import dump_bytecode
from yapf.yapflib.yapf_api import FormatCode

ze_exp = ze.compile('import reley.grammar.[*]')

result = ze_exp.match(r"""

infix 1 (`app`)    
infix 0 ($)
($) a b = a b
app a = a 1
main () =
    print $ app (\a -> a + x)
    where
        x = 1

""").result
# print(FormatCode(str(result))[0])

ctx = Ctx({}, {}, Bytecode(), {'+': 10}, False)
ctx.visit(result)

# #
global_ctx = {'+': lambda a: lambda b: a + b}
# print(dump_bytecode(ctx.bc))
# dump_bytecode(ctx.bc)
code = ctx.bc.to_code()

#
# exec(code, global_ctx)
