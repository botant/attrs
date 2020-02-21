"""
Tests for equality and ordering methods from `attrib._make`
when a comparator object is specified.
"""

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


# ObjWithoutTruthValue is a simple object that has no truth value,
# e.g. __eq__ returns something other than a boolean, and Python
# tries to convert that non-boolean to a boolean by calling __bool__
# (or __nonzero__ in Python 2) on it.
#
# We could simulate this behaviour by simply throwing an exception from __eq__,
# but this complicated chain of events is more realistic because
# it mimics what happens when we compare numpy arrays and pandas dataframes.
@attr.s(eq=False)
class ObjWithoutTruthValue(object):

    value = attr.ib()

    def __eq__(self, other):
        return ObjWithoutTruthValue(self.value == other.value)

    def __lt__(self, other):
        return ObjWithoutTruthValue(self.value < other.value)

    def __bool__(self):
        raise ValueError("ObjWithoutTruthValue has no truth value.")

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
            cls(ObjWithoutTruthValue(1), 2) == cls(ObjWithoutTruthValue(1), 2)
        with pytest.raises(ValueError):
            cls(ObjWithoutTruthValue(1), 2) != cls(ObjWithoutTruthValue(1), 2)

    @pytest.mark.parametrize("cls", [OrderC, OrderCSlots])
    def test_order_exception(self, cls):
        """
        Test for ordering methods when attribute has not truth value.
        """
        with pytest.raises(ValueError):
            cls(ObjWithoutTruthValue(1), 2) < cls(ObjWithoutTruthValue(2), 2)
        with pytest.raises(ValueError):
            cls(ObjWithoutTruthValue(1), 2) > cls(ObjWithoutTruthValue(2), 2)

        with pytest.raises(ValueError):
            cls(ObjWithoutTruthValue(1), 2) <= cls(ObjWithoutTruthValue(2), 2)
        with pytest.raises(ValueError):
            cls(ObjWithoutTruthValue(1), 2) >= cls(ObjWithoutTruthValue(2), 2)

    @given(booleans())
    def test_comparator(self, slots):
        """
        Test for equality and ordering methods when attribute has comparator.
        """
        _DCmp = attr.comparators.using_functions(
            eq=ObjWithoutTruthValue.is_equal, lt=ObjWithoutTruthValue.less_than
        )

        _D = make_class(
            "_D", {"a": attr.ib(comparator=_DCmp), "b": attr.ib()}, slots=slots
        )

        assert _D(ObjWithoutTruthValue(1), 2) == _D(ObjWithoutTruthValue(1), 2)
        assert _D(ObjWithoutTruthValue(1), 1) != _D(ObjWithoutTruthValue(1), 2)
        assert _D(ObjWithoutTruthValue(2), 2) != _D(ObjWithoutTruthValue(1), 2)

        assert _D(ObjWithoutTruthValue(1), 2) >= _D(ObjWithoutTruthValue(1), 2)
        assert _D(ObjWithoutTruthValue(1), 2) <= _D(ObjWithoutTruthValue(1), 2)

        assert _D(ObjWithoutTruthValue(0), 1) < _D(ObjWithoutTruthValue(1), 2)
        assert _D(ObjWithoutTruthValue(2), 3) > _D(ObjWithoutTruthValue(1), 2)


class TestComparatorUsingKey(object):
    """
    Tests for `attr.comparators.using_key`.
    """

    def test_lower(self):
        """
        Test using `string.lower`.
        """
        # Create comparator without ordering
        _DCmp = attr.comparators.using_key(
            key=lambda value: value.lower(), order=False
        )
        assert _DCmp("abc") == _DCmp("abc")
        assert _DCmp("abc") == _DCmp("ABC")

        if PY2:
            # Python2 seems to interprets NotImplemented as False
            assert not _DCmp("abc") > _DCmp("abc")
            assert not _DCmp("abc") < _DCmp("abc")
            assert not _DCmp("abc") >= _DCmp("abc")
            assert not _DCmp("abc") <= _DCmp("abc")
        else:
            # Ordering methods should not work since we specified order=False
            with pytest.raises(TypeError):
                assert _DCmp("abc") > _DCmp("abc")
            with pytest.raises(TypeError):
                assert _DCmp("abc") < _DCmp("abc")
            with pytest.raises(TypeError):
                assert _DCmp("abc") >= _DCmp("abc")
            with pytest.raises(TypeError):
                assert _DCmp("abc") <= _DCmp("abc")

    def test_abs(self):
        """
        Test using `abs`.
        """
        _DCmp = attr.comparators.using_key(key=abs)
        assert _DCmp(1) == _DCmp(1)
        assert _DCmp(1) == _DCmp(-1)
        assert _DCmp(1) <= _DCmp(-3)
        assert _DCmp(1) < _DCmp(-3)
        assert not (_DCmp(1) != _DCmp(-1))
        assert not (_DCmp(1) > _DCmp(-1))


class TestComparatorUsingFunctions(object):
    """
    Tests for `attr.comparators.using_functions`.
    """

    def test_lower(self):
        """
        Test using `string.lower`.
        """
        # Create comparator without ordering
        _DCmp = attr.comparators.using_functions(
            eq=lambda obj, other: obj.lower() == other.lower()
        )
        assert _DCmp("abc") == _DCmp("abc")
        assert _DCmp("abc") == _DCmp("ABC")

        if PY2:
            # Python2 seems to interprets NotImplemented as False
            assert not _DCmp("abc") > _DCmp("abc")
            assert not _DCmp("abc") < _DCmp("abc")
            assert not _DCmp("abc") >= _DCmp("abc")
            assert not _DCmp("abc") <= _DCmp("abc")
        else:
            # Ordering methods should not work since we specified order=False
            with pytest.raises(TypeError):
                assert _DCmp("abc") > _DCmp("abc")
            with pytest.raises(TypeError):
                assert _DCmp("abc") < _DCmp("abc")
            with pytest.raises(TypeError):
                assert _DCmp("abc") >= _DCmp("abc")
            with pytest.raises(TypeError):
                assert _DCmp("abc") <= _DCmp("abc")

    def test_abs(self):
        """
        Test using `abs`.
        """
        _DCmp = attr.comparators.using_functions(
            eq=lambda obj, other: abs(obj) == abs(other),
            lt=lambda obj, other: abs(obj) < abs(other),
        )
        assert _DCmp(1) == _DCmp(1)
        assert _DCmp(1) == _DCmp(-1)
        assert _DCmp(1) <= _DCmp(-3)
        assert _DCmp(1) < _DCmp(-3)
        assert not (_DCmp(1) != _DCmp(-1))
        assert not (_DCmp(1) > _DCmp(-1))
