See examples at `test/*.hs`.
Currently you can install reley compiler with `python setup.py install`.

Usage
============

- Compile:

```
> reley cc <filename>.hs -o <out>.pyc
> python <out>.pyc
```

- Run Reley

```
> reley run <filename>.hs
```

- Import reley programs in Python

If you have a reley source file `haskell_test/sum_n.hs`:

```haskell
import operator (add, eq)
import functools (reduce)
import toolz (curry)
import reley.prelude ((+))

infix 5 (==)
infix 0 ($)
(==) = curry eq
($) a b = a b
(+) = curry add


m_sum lst = if lst == [] then 0
            else destruct lst
            where
                destruct (a, b) = a + m_sum(b)

main () =
    print $ m_sum [1, 2, 3, 4, 5, 6]
```

Then you can import it in Python

```python
import reley.impl.pycompat

from haskell_test.sum_n import m_sum
lst = (5, (2, (1, ())))
print(m_sum(lst))

```

About Reley
====================
It's in an early stage with many shortages.
Most of the crucial Haskell features are missing.
