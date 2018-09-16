from reley.impl.pycompat import *
import os
import haskell_test.comment
import haskell_test.import_hs
import haskell_test.operator
import haskell_test.sum_n
import haskell_test.test_prelude

from haskell_test.sum_n import m_sum
lst = (5, (2, (1, ())))
print(m_sum(lst))
