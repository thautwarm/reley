from typing import Generic, Iterable, TypeVar, Optional, Iterator
from functools import reduce
from .expr_based_ast import Operator, Call, Symbol

T = TypeVar('T')


class TwoSideLink(Iterable, Generic[T]):
    def __init__(self,
                 content: T,
                 prev: 'Optional[TwoSideLink[T]]' = None,
                 next: 'Optional[TwoSideLink]' = None):
        self.content: T = content
        self.next = next
        self.prev = prev

    def __iter__(self) -> 'Iterator[TwoSideLink[T]]':
        yield self
        if self.next:
            yield from self.next

    def __str__(self):
        return 'L<{}>'.format(self.content)

    __repr__ = __str__

    @classmethod
    def from_iter(cls, iterable: 'Iterable') -> 'Optional[TwoSideLink]':
        if not iterable:
            return None
        s_iterable = iter(iterable)
        try:
            fst = cls(next(s_iterable))
        except StopIteration:
            return None

        reduce(lambda a, b: setattr(a, "next", cls(b)) or setattr(a.next, "prev", a) or a.next, s_iterable, fst)
        return fst


def bin_reduce(op_priorities):
    def bin_reduce(seq: Iterable):
        seq = TwoSideLink.from_iter(seq)

        def sort_by_func(e: 'TwoSideLink'):
            return op_priorities[e.content.name]

        op_nodes = (each for each in seq if isinstance(each.content, Operator))
        op_nodes = sorted(op_nodes, key=sort_by_func, reverse=True)

        bin_expr = None

        for each in op_nodes:
            sym = Symbol(loc=each.content.loc, name=each.content.name)
            bin_expr = Call(sym.loc, Call(sym.loc, sym, each.prev.content),
                            each.next.content)
            each.content = bin_expr
            try:
                each.prev.prev.next = each
                each.prev = each.prev.prev
            except AttributeError:
                pass

            try:
                each.next.next.prev = each
                each.next = each.next.next
            except AttributeError:
                pass

        return bin_expr

    return bin_reduce
