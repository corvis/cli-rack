#    CLI Rack - Lightweight set of tools for building pretty-looking CLI applications in Python
#    Copyright (C) 2021 Dmitry Berezovsky
#    The MIT License (MIT)
#    
#    Permission is hereby granted, free of charge, to any person obtaining
#    a copy of this software and associated documentation files
#    (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#    
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#    
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from typing import Dict, Tuple, Type

_TYPE_OVERLOADS = {
    int: type("EInt", (int,), dict()),
    float: type("EFloat", (float,), dict()),
    str: type("EStr", (str,), dict()),
    dict: type("EDict", (dict,), dict()),
    list: type("EList", (list,), dict()),
}

# cache created classes here
_CLASS_LOOKUP: Dict[Tuple[Type, Type], Type] = {}


def add_class_to_obj(value, cls):
    """Add a class to a python type.
    This function modifies value so that it has cls as a basetype.
    The value itself may be modified by this action! You must use the return
    value of this function however, since some types need to be copied first (heaptypes).
    """
    if isinstance(value, cls):
        # If already is instance, do not add
        return value

    try:
        orig_cls = value.__class__
        key = (orig_cls, cls)
        new_cls = _CLASS_LOOKUP.get(key)
        if new_cls is None:
            new_cls = orig_cls.__class__(orig_cls.__name__, (orig_cls, cls), {})
            _CLASS_LOOKUP[key] = new_cls
        value.__class__ = new_cls
        return value
    except TypeError:
        # Non heap type, look in overloads dict
        for type_, func in _TYPE_OVERLOADS.items():
            # Use type() here, we only need to trigger if it's the exact type,
            # as otherwise we don't need to overload the class
            if type(value) is type_:  # pylint: disable=unidiomatic-typecheck
                return add_class_to_obj(func(value), cls)
        raise


def list_starts_with(list_, sub):
    return len(sub) <= len(list_) and all(list_[i] == x for i, x in enumerate(sub))


def is_approximately_integer(value):
    if isinstance(value, int):
        return True
    return abs(value - round(value)) < 0.001
