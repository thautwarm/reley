import operator (add, eq)
import functools (reduce)
import toolz (curry)

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
    print $ m_sum [1, 2, 3]

