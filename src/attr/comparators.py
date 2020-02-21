"""
Useful comparators.
"""

from __future__ import absolute_import, division, print_function

import functools

from ._compat import iteritems
from ._make import _add_method_dunders, attrib, make_class


def _make_ne():
    """
    Create *not equal* method.
    """

    def __ne__(self, other):
        """
        Check equality and either forward a NotImplemented or
        return the result negated.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    return __ne__


def using_key(key=None, order=True):
    """
    Creates a comparator class that applies *key* function to values *before*
    comparing them.

    :param callable key: A callable that applied to values before
        comparing them.

        For example, use `lambda value: value.casefold()` to create a
        comparator that compares values in a case insensitive way.

    :param bool order: If `True` (default), generate methods `__lt__`,
       `__le__`, `__gt__` and `__ge__` using `functools.total_ordering`.

    .. versionadded:: attrs-20.1.0.dev0-botant.
    """

    def __eq__(self, other):
        """
        Automatically created by attrs.
        """
        if other.__class__ is self.__class__:
            return self._key(self.value) == self._key(other.value)
        return NotImplemented

    cls = make_class("Comparator", {"value": attrib()}, slots=True, eq=False)
    cls._key = staticmethod(key)
    cls.__eq__ = _add_method_dunders(cls, __eq__)
    cls.__ne__ = _add_method_dunders(cls, _make_ne())

    if order:

        def __lt__(self, other):
            """
            Automatically created by attrs.
            """
            if other.__class__ is self.__class__:
                return self._key(self.value) < self._key(other.value)
            return NotImplemented

        cls.__lt__ = _add_method_dunders(cls, __lt__)
        cls = functools.total_ordering(cls)

    else:
        cls = _add_not_implemented_ordering_dunders(cls)

    return cls


def using_functions(eq, lt=None, le=None, gt=None, ge=None):
    """
    Creates a comparator class that uses function *eq* for equality operators,
    and *lt*, *le*, *gt*, *ge* for ordering operators.

    If at least one of *lt*, *le*, *gt*, *ge* is provided, the other functions
    are added with the help of `functools.total_ordering`.

    All functions should take 2 arguments and return a `boolean`.

    :param callable eq: Function called in `__eq__`.
    :param callable lt: Function called in `__lt__`.
    :param callable le: Function called in `__le__`.
    :param callable gt: Function called in `__gt__`.
    :param callable ge: Function called in `__ge__`.

    .. versionadded:: attrs-20.1.0.dev0-botant.
    """

    def _create_method(func):
        def __func__(self, other):
            """
            Automatically created by attrs.
            """
            if other.__class__ is self.__class__:
                return func(self.value, other.value)
            return NotImplemented

        return __func__

    cls = make_class("Comparator", {"value": attrib()}, slots=True, eq=False)
    cls.__eq__ = _add_method_dunders(cls, _create_method(eq))
    cls.__ne__ = _add_method_dunders(cls, _make_ne())

    meth_count = 0
    for name, meth in iteritems({"lt": lt, "le": le, "gt": gt, "ge": ge}):
        if meth is not None:
            meth_count += 1
            setattr(
                cls,
                "__%s__" % (name,),
                _add_method_dunders(cls, _create_method(meth)),
            )

    if meth_count == 0:
        cls = _add_not_implemented_ordering_dunders(cls)
    elif meth_count < 4:
        cls = functools.total_ordering(cls)

    return cls


def _add_not_implemented_ordering_dunders(cls):
    """
    Add ordering dunders that return NotImplemented.
    """

    def __func__(self, other):
        """
        Automatically created by attrs.
        """
        return NotImplemented

    cls.__lt__ = cls.__le__ = cls.__gt__ = cls.__ge__ = _add_method_dunders(
        cls, __func__
    )

    return cls
