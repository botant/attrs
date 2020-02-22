"""
Tests for equality and ordering methods from `attrib._make`
when a comparator object is specified.
"""

import functools

import pytest

from hypothesis import given
from hypothesis.strategies import booleans

import attr

from attr._compat import PY2

from .utils import make_class, simple_class


EqC = simple_class(eq=True)
EqCSlots = simple_class(eq=True, slots=True)
OrderC = simple_class(order=True)
OrderCSlots = simple_class(order=True, slots=True)


@attr.s(eq=False)
class ClassNoTruthValue(object):

    """
    ClassNoTruthValue mimics what happens when we compare `numpy arrays` and
    `pandas dataframes`: we get back an object of the same type as the inputs
    instead of a `boolean`. When this happens, Python tries to convert that
    `non-boolean` to a `boolean` by calling `__bool__`
    (or `__nonzero__` in Python 2) on it.
    """

    value = attr.ib()

    def __eq__(self, other):
        return ClassNoTruthValue(self.value == other.value)

    def __lt__(self, other):
        return ClassNoTruthValue(self.value < other.value)

    def __bool__(self):
        raise ValueError("ClassNoTruthValue has no truth value.")

    __nonzero__ = __bool__  # Python 2

    @staticmethod
    def is_equal(obj, other):
        return (obj == other).value

    @staticmethod
    def less_than(obj, other):
        return (obj < other).value


class TestComparator(object):
    """
    Tests for equality and ordering when a comparator object is specified.
    """

    @pytest.mark.parametrize("cls", [EqC, EqCSlots])
    def test_equality_exception(self, cls):
        """
        Test for equality methods when attribute has not truth value.
        """
        with pytest.raises(ValueError):
            cls(ClassNoTruthValue(1), 2) == cls(ClassNoTruthValue(1), 2)
        with pytest.raises(ValueError):
            cls(ClassNoTruthValue(1), 2) != cls(ClassNoTruthValue(1), 2)

    @pytest.mark.parametrize("cls", [OrderC, OrderCSlots])
    def test_order_exception(self, cls):
        """
        Test for ordering methods when attribute has not truth value.
        """
        with pytest.raises(ValueError):
            cls(ClassNoTruthValue(1), 2) < cls(ClassNoTruthValue(2), 2)
        with pytest.raises(ValueError):
            cls(ClassNoTruthValue(1), 2) > cls(ClassNoTruthValue(2), 2)

        with pytest.raises(ValueError):
            cls(ClassNoTruthValue(1), 2) <= cls(ClassNoTruthValue(2), 2)
        with pytest.raises(ValueError):
            cls(ClassNoTruthValue(1), 2) >= cls(ClassNoTruthValue(2), 2)

    @given(booleans())
    def test_comparator(self, slots):
        """
        Test for equality and ordering methods when attribute has comparator.
        """

        @functools.total_ordering
        class Cmp(object):
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return ClassNoTruthValue.is_equal(self.value, other.value)

            def __lt__(self, other):
                return ClassNoTruthValue.less_than(self.value, other.value)

            def __ne__(self, other):
                return not self.__eq__(other)

        C = make_class("C", {"a": attr.ib(comparator=Cmp)}, slots=slots)

        assert C(ClassNoTruthValue(1)) == C(ClassNoTruthValue(1))
        assert C(ClassNoTruthValue(2)) != C(ClassNoTruthValue(1))

        assert C(ClassNoTruthValue(1)) >= C(ClassNoTruthValue(1))
        assert C(ClassNoTruthValue(1)) <= C(ClassNoTruthValue(1))

        assert C(ClassNoTruthValue(0)) < C(ClassNoTruthValue(1))
        assert C(ClassNoTruthValue(2)) > C(ClassNoTruthValue(1))


class TestUsingKey(object):
    """
    Tests for `attr.comparators.using_key`.
    """

    def test_equality(self):
        """
        Test equality.
        """
        Cmp = attr.comparators.using_key(key=lambda value: value.lower())
        assert Cmp("abc") == Cmp("abc")
        assert Cmp("abc") == Cmp("ABC")

    def test_ordering(self):
        """
        Test ordering.
        """
        Cmp = attr.comparators.using_key(key=abs)
        assert Cmp(1) < Cmp(-3)
        assert Cmp(1) > Cmp(0)

        assert Cmp(1) >= Cmp(0)
        assert Cmp(1) >= Cmp(1)
        assert Cmp(1) <= Cmp(-1)
        assert Cmp(1) <= Cmp(-2)

    def test_no_ordering(self):
        """
        Test no ordering.
        """
        Cmp = attr.comparators.using_key(key=lambda x: x, order=False)

        if PY2:
            assert not Cmp(2) > Cmp(1)
            assert not Cmp(0) < Cmp(1)

            assert not Cmp(1) >= Cmp(1)
            assert not Cmp(1) <= Cmp(1)
        else:
            with pytest.raises(TypeError):
                assert Cmp(2) > Cmp(1)
            with pytest.raises(TypeError):
                assert Cmp(0) < Cmp(1)
            with pytest.raises(TypeError):
                assert Cmp(1) >= Cmp(1)
            with pytest.raises(TypeError):
                assert Cmp(1) <= Cmp(1)


class TestUsingFunctions(object):
    """
    Tests for `attr.comparators.using_functions`.
    """

    def test_equality(self):
        """
        Test equality.
        """
        # Usual equality
        Cmp = attr.comparators.using_functions(eq=lambda x, y: x == y)
        assert Cmp(1) == Cmp(1)
        assert Cmp(1) != Cmp(-1)

        # Weird equality, just for fun
        Cmp = attr.comparators.using_functions(eq=lambda x, y: x == -y)
        assert Cmp(1) != Cmp(1)
        assert Cmp(1) == Cmp(-1)

    @pytest.mark.parametrize(
        "functions",
        [
            {"lt": lambda x, y: x < y},
            {"le": lambda x, y: x <= y},
            {"gt": lambda x, y: x > y},
            {"ge": lambda x, y: x >= y},
        ],
    )
    def test_ordering(self, functions):
        """
        Test ordering functions created as combinations of the input
        functions.
        """
        Cmp = attr.comparators.using_functions(
            eq=lambda x, y: x == y, **functions
        )
        assert Cmp(1) == Cmp(1)
        assert Cmp(1) != Cmp(-1)

        assert Cmp(1) < Cmp(3)
        assert Cmp(1) > Cmp(0)

        assert Cmp(1) >= Cmp(1)
        assert Cmp(1) >= Cmp(0)
        assert Cmp(1) <= Cmp(1)
        assert Cmp(1) <= Cmp(3)

    def test_no_ordering(self):
        """
        Test no ordering.
        """
        Cmp = attr.comparators.using_functions(eq=lambda x, y: x == y)

        if PY2:
            assert not Cmp(2) > Cmp(1)
            assert not Cmp(0) < Cmp(1)

            assert not Cmp(1) >= Cmp(1)
            assert not Cmp(1) <= Cmp(1)
        else:
            with pytest.raises(TypeError):
                assert Cmp(2) > Cmp(1)
            with pytest.raises(TypeError):
                assert Cmp(0) < Cmp(1)
            with pytest.raises(TypeError):
                assert Cmp(1) >= Cmp(1)
            with pytest.raises(TypeError):
                assert Cmp(1) <= Cmp(1)
