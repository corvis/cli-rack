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

import time
from typing import Optional


class ExecutionTimer(object):
    def __init__(self, start=True) -> None:
        self.__start_time: Optional[float] = None
        self.__end_time: Optional[float] = None
        if start:
            self.start()

    def start(self):
        self.__start_time = time.perf_counter()
        self.__end_time = None

    def stop(self):
        self.__end_time = time.perf_counter()

    @property
    def is_running(self):
        return self.__start_time is not None and self.__end_time is None

    @property
    def is_finished(self):
        return self.__start_time is not None and self.__end_time is not None

    @property
    def elapsed(self) -> Optional[float]:
        if self.is_finished:
            return self.__end_time - self.__start_time  # type: ignore
        if self.is_running:
            return time.perf_counter() - self.__start_time  # type: ignore
        else:
            return None

    def format_elapsed(self):
        val = self.elapsed
        if val is None:
            return "n/a"
        else:
            return "{}s".format(round(val, 2))
