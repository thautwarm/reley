module ($), (+), (-), (*), (/), (//), (`in`), attr, contains where
import operator (add, sub, eq, mul, truediv, floordiv, contains, mod)
import toolz (curry)

infix 0 ($)
infix 10 (+)
infix 10 (-)
infix 20 (*)
infix 20 (/)
infix 20 (//)
infix 40 (`contains`)
infix 40 (`in`)
infix 50 (`attr`)

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






