"""
Commonly useful comparators.
"""

from __future__ import absolute_import, division, print_function

import functools
import linecache

from ._make import __ne__, _generate_unique_filename, attrib, attrs


# def _make_operator(name, operation, key):
#     """
#     Creates a operator function.
#     """
#     name = "__%s__" % (name,)
#
#     unique_filename = _generate_unique_filename(_make_operator, name)
#     lines = [
#         "def %s(self, other):" % (name,),
#         "    if other.value.__class__ is not self.value.__class__:",
#         "        return NotImplemented",
#         ]
#
#     if key:
#         lines.append("    other_value = self._key(other.value)")
#         lines.append("    self_value = self._key(self.value)")
#     else:
#         lines.append("    other_value = other.value")
#         lines.append("    self_value = self.value")
#
#     lines.append("    return (other_value %s self_value)" % (operation,))
#
#     script = "\n".join(lines)
#     global_vars = {}
#     local_vars = {}
#     bytecode = compile(script, unique_filename, "exec")
#     eval(bytecode, global_vars, local_vars)
#
#     # In order of debuggers like PDB being able to step through the code,
#     # we add a fake linecache entry.
#     linecache.cache[unique_filename] = (
#         len(script),
#         None,
#         script.splitlines(True),
#         unique_filename,
#     )
#     return local_vars[name]


def _make_operator(name, operation, key):
    """
    Creates a operator function.
    """
    name = "__%s__" % (name,)

    unique_filename = _generate_unique_filename(_make_operator, name)
    lines = [
        "def %s(self, other):" % (name,),
        "    if other.value.__class__ is not self.value.__class__:",
        "        return NotImplemented",
        "    if self._key:",
        "        other_value = self._key(other.value)",
        "        self_value = self._key(self.value)",
        "    else:",
        "        other_value = other.value",
        "        self_value = self.value",
        "    result = (self_value %s other_value)" % (operation,),
        "    if self._nonzero:",
        "        result = self._nonzero(result)",
        "    return result",
    ]

    script = "\n".join(lines)
    global_vars = {}
    local_vars = {}
    bytecode = compile(script, unique_filename, "exec")
    eval(bytecode, global_vars, local_vars)

    # In order of debuggers like PDB being able to step through the code,
    # we add a fake linecache entry.
    linecache.cache[unique_filename] = (
        len(script),
        None,
        script.splitlines(True),
        unique_filename,
    )
    return local_vars[name]


# def _add_nonzero(nonzero):
#     """
#     Decorates an operation with a nonzero function.
#     """
#     def _nonzero_decorator(fcn):
#         if nonzero:
#             def __fcn__(self, other):
#                 return nonzero(fcn(self, other))
#             return __fcn__
#         return fcn
#
#     return _nonzero_decorator


def compare(key=None, nonzero=None, order=True, capture_exceptions=True):
    """
    Creates a comparator class that applies *key* function to values *before*
    comparing them, and applies *nonzero* to the result.

    :param callable key: A callable that applied to values before
        comparing them.

        For example, use ``lambda value: value.casefold()`` to create a
        comparator that compares values in a case insensitive way.

    :param callable nonzero: A callable that applied to the result
        of the comparison operation.

        For example, use ``lambda value: value.all()`` to create a
        comparator that is able to compare ``numpy arrays``.

    :param bool order: If ``True`` (default), generate methods ``__lt__``,
       ``__le__``, ``__gt__`` and ``__ge__``.

    :param bool capture_exceptions: If ``True`` (default), exceptions raised
       within comparison methods will be captured and treated as False.

    .. versionadded:: attrs-20.1.0.dev0-botant.
    """

    @attrs(slots=True, eq=False)
    class Comparator(object):
        value = attrib()

    cls = Comparator
    cls._key = staticmethod(key)
    cls._nonzero = staticmethod(nonzero)
    cls.__eq__ = _make_operator("eq", "==", key)
    cls.__ne__ = __ne__

    if order:
        cls.__lt__ = _make_operator("lt", "<", key)
        cls = functools.total_ordering(cls)

    return cls
