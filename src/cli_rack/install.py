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

import subprocess
import sys

try:
    import pip  # noqa: F401

    pip_available = True
except ImportError:
    pip_available = False


def verify_pip():
    if not pip_available:
        raise ValueError(
            "PIP is not available so automatic installation is not supported. "
            "In order to fix this either install PIP or avoid automatic dependencies installation"
        )


def _run_pip(*args, hide_output=True):
    stdout = sys.stdout
    stderr = sys.stderr
    if hide_output:
        stdout = stderr = subprocess.PIPE
    return subprocess.run(
        ["pip"] + args, bufsize=1024, universal_newlines=True, stdout=stdout, stderr=stderr, shell=False
    )


def is_package_installed(package_name: str):
    verify_pip()
    result = _run_pip("show", package_name)
    if result.returncode != 0:
        return False
    else:
        return True  # TODO: Verify version vere?


def install_package(package_name: str):
    verify_pip()
    result = _run_pip("install", package_name, hide_output=False)
    return result.returncode != 0
