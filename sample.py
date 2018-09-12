from rbnf.easy import *
from astpretty import pprint
import dis
from reley.compiler import Ctx, Bytecode
from yapf.yapflib.yapf_api import FormatCode

ze_exp = ze.compile('import reley.grammar.[*]')

result = ze_exp.match("""
infix 0 `$`
def ($) a b -> a b
print $ (fn a b c -> c) 1 2 3
""").result

print(FormatCode(str(result))[0])

ctx = Ctx({}, {}, Bytecode(), {'+': 10}, False)
ctx.visit(result)

global_ctx = {'+': lambda a: lambda b: a + b}
code = ctx.bc.to_code()

dis.dis(code)

exec(code, global_ctx)
