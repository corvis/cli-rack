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

from typing import Optional, Any


class FixHintMixin:
    def __init__(self) -> None:
        self.fix_hint: Optional[str] = None

    @staticmethod
    def supports_fix_hint(obj: Any) -> bool:
        if obj is None:
            return False
        return hasattr(obj, "fix_hint")

    def add_hint(self, msg: str):
        if self.fix_hint is not None:
            self.fix_hint += "\n" + msg
        else:
            self.fix_hint = msg

    def hint_install_python_package(self, *packages: str):
        self.add_hint('Try to install package with "pip install {}"'.format(" ".join(packages)))
        return self


class ExtensionUnavailableError(Exception, FixHintMixin):
    def __init__(
        self, extension_name: str, reason: Optional[str] = None, hint: Optional[str] = None, *args: object
    ) -> None:
        super().__init__(*args)
        self.extension_name = extension_name
        self.reason = reason
        self.fix_hint = hint

    def __str__(self) -> str:
        return "{}".format(self.reason)


class ExecutionManagerError(Exception):
    pass
