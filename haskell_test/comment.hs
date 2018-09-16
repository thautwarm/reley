module
    test1
where

import unittest (TestCase)
import toolz (curry)
import reley.prelude (*)

infix 10 (.)
(.) = curry getattr

|||<comment1>
test1 () = ()

main() =
    (curry (test . "assertEqual")) (test1. "__doc__") "<comment1>"
    help test1
    print $ (\a b c -> a) 1 2 3
    where
    test = TestCase()

