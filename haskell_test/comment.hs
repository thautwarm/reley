module
    test1
where

import unittest (TestCase)
import toolz (curry)

infix 10 (.)
infix 0  ($)
(.) = curry getattr
($) a b = a b

|||<comment1>
test1 () = ()

main() =
    (curry (test . "assertEqual")) (test1. "__doc__") "<comment1>"
    help test1
    where
    test = TestCase()

