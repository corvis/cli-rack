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

import argparse
import os
import subprocess
import sys
from typing import Sequence, Union, Dict, AbstractSet, TypeVar, Iterable, Optional, Type, Any


def any_of_keys_exists(keys: Sequence[str], _dict: Union[Dict, Sequence, AbstractSet]) -> bool:
    for k in keys:
        if k in _dict:
            return True
    return False


def parse_bool_val(v: str) -> bool:
    if isinstance(v, bool):
        return v
    if v.lower() in ("on", "yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("off", "no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


AnyScalarType = TypeVar("AnyScalarType", str, int, float, dict)


def scalar_to_list(obj: Union[Iterable[AnyScalarType], AnyScalarType]) -> Iterable[AnyScalarType]:
    """
    Expects either a sequence of objects or just object.
    In case of scalar value returns this value wrapped into list
    If iterable is given - just returns it as it is.
    :param obj:
    :return:
    """
    if isinstance(obj, Iterable) and not isinstance(obj, str):
        return obj
    return [obj]  # type: ignore


def ensure_dir(dir_name: str):
    os.makedirs(dir_name, exist_ok=True)


def run_executable(*args, hide_output=False, mute_output=False) -> subprocess.CompletedProcess:
    stdout = sys.stdout
    stderr = sys.stderr
    if mute_output:
        stdout = stderr = subprocess.DEVNULL  # type: ignore
    elif hide_output:
        stdout = stderr = subprocess.PIPE  # type: ignore
    return subprocess.run(args, bufsize=1024, universal_newlines=True, stdout=stdout, stderr=stderr, shell=False)


def is_successful_exit_code(self, *args, expected_code=0) -> bool:
    return self.run_executable(*args, mute_output=True).returncode == expected_code


_T = TypeVar("_T")


def none_throws(optional: Optional[_T], message: str = "Unexpected `None`") -> _T:
    """Convert an optional to its value. Raises an `AssertionError` if the
    value is `None`"""
    if optional is None:
        raise AssertionError(message)
    return optional


def safe_cast(new_type: Type[_T], value: Any) -> _T:
    """safe_cast will change the type checker's inference of x if it was
    already a subtype of what we are casting to, and error otherwise."""
    return value  # type: ignore[no-any-return]
