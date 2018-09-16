from .compiler import Ctx
from .pycompat import find_reley_module_spec
from wisepy.talking import Talking
from bytecode import Bytecode
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from Redy.Tools.PathLib import Path
from importlib._bootstrap_external import MAGIC_NUMBER
import marshal
import struct, time

talking = Talking()


@talking
def cc(f: 'input filename', o: 'output filename'):
    """
    compile reley source code into pyc files
    """
    code = find_reley_module_spec(f)
    timestamp = struct.pack('i', int(time.time()))
    marshalled_code_object = marshal.dumps(code)
    with Path(o).open('wb') as f:
        f.write(MAGIC_NUMBER)
        f.write(timestamp)
        f.write(b'A\x00\x00\x00')
        f.write(marshalled_code_object)


@talking
def run(f: 'input filename', o: 'output filename'):
    """
    compile reley source code into pyc files
    """
    code = filename_to_bc(f)
    exec(code)


def main():
    talking.on()
