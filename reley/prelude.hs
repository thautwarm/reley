module ($), (+), (-), (*), (/), (//), (`in`), attr, contains where
import operator (add, sub, eq, mul, truediv, floordiv, contains, mod)
import toolz (curry)


||| use `f $ arg` to avoid nested parentheses.

($) a b = a b
(+) = curry add
(-) = curry sub
(*) = curry mul
(/) = curry truediv
(%) = curry mod
(//) = curry floordiv

flip f a b = f b a

attr = curry getattr
contains = curry contains
(`in`) = flip contains






