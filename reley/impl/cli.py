from .pycompat import sys
from .reley_import import get_reley_module_spec_from_path, get_context_from_spec
from wisepy.talking import Talking
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
    spec = get_reley_module_spec_from_path('main', f)
    code = get_context_from_spec(spec).bc.to_code()
    timestamp = struct.pack('i', int(time.time()))
    marshalled_code_object = marshal.dumps(code)
    with Path(o).open('wb') as f:
        f.write(MAGIC_NUMBER)
        f.write(timestamp)
        f.write(b'A\x00\x00\x00')
        f.write(marshalled_code_object)


@talking
def run(f: 'input filename'):
    """
    compile reley source code into pyc files
    """
    spec = get_reley_module_spec_from_path('main', f)
    code = get_context_from_spec(spec).bc.to_code()
    exec(code)


def main():
    talking.on()
