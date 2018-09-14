import operator (add, sub)
import toolz (curry)

infix 0 ($)
infix 5 (+)
infix 5 (-)

($) f a = f a
(+) = curry add
(-) = curry sub

main () =
    print $ 1 + 2 - 3

