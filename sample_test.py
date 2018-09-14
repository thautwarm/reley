from reley.impl.pycompat import *

from haskell_test.comment import test1
import haskell_test.comment as mod
print(mod.__dict__.keys())
test1()

import haskell_test.test_prelude
