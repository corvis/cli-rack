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

import logging
import sys
from typing import Optional

from . import ansi
from .logger import CommonCliLogFormatter, UILogFormatter


class __CLI:
    CLI_LOGGER = "cli-ui"

    def __init__(self) -> None:
        super().__init__()
        self.show_stack_traces = False
        self.ui_logger = logging.getLogger(self.CLI_LOGGER)
        self.log_formatter: Optional[logging.Formatter] = None
        self.ui_formatter: Optional[logging.Formatter] = None
        self.__support_colors = False

    def setup(self, ui_log_level=logging.INFO, log_level=logging.INFO, show_stack_traces=False):
        self.__support_colors = ansi.stream_supports_colors(sys.stderr) or ansi.stream_supports_colors(sys.stdin)
        self.log_formatter = CommonCliLogFormatter(
            use_colors=self.__support_colors, show_stack_traces=show_stack_traces
        )
        self.ui_formatter = UILogFormatter(use_colors=self.__support_colors, show_stack_traces=show_stack_traces)
        default_log_handler = logging.StreamHandler(sys.stderr)
        default_log_handler.formatter = self.log_formatter
        logging.basicConfig(level=log_level, handlers=[default_log_handler])
        ui_handler = logging.StreamHandler(sys.stderr)
        ui_handler.formatter = self.ui_formatter
        self.ui_logger.level = ui_log_level
        self.ui_logger.handlers = [ui_handler]
        self.ui_logger.propagate = False

    @property
    def support_colors(self) -> bool:
        return self.__support_colors

    @property
    def use_colors(self) -> Optional[bool]:
        if isinstance(self.log_formatter, CommonCliLogFormatter) and isinstance(
            self.ui_formatter, CommonCliLogFormatter
        ):
            return self.log_formatter.use_colors and self.ui_formatter.use_colors
        return None

    @use_colors.setter
    def use_colors(self, val: bool):
        if isinstance(self.log_formatter, CommonCliLogFormatter) and isinstance(
            self.ui_formatter, CommonCliLogFormatter
        ):
            self.log_formatter.use_colors = self.ui_formatter.use_colors = val

    def verbose_mode(self):
        self.set_ui_log_level(logging.DEBUG)
        self.set_log_level(logging.DEBUG)
        self.set_stack_traces(False)

    def normal_mode(self):
        self.set_ui_log_level(logging.INFO)
        self.set_log_level(logging.INFO)
        self.set_stack_traces(False)

    def debug_mode(self):
        self.set_ui_log_level(logging.DEBUG)
        self.set_log_level(logging.DEBUG)
        self.set_stack_traces(True)

    def set_ui_log_level(self, value):
        self.ui_logger.level = value

    def set_log_level(self, value):
        logging.root.level = value

    def set_stack_traces(self, value: bool):
        _attr_name = "show_stack_traces"
        if hasattr(self.ui_formatter, _attr_name):
            setattr(self.ui_formatter, _attr_name, value)
        if hasattr(self.log_formatter, _attr_name):
            setattr(self.log_formatter, _attr_name, value)

    def print_data(self, msg: str):
        if not isinstance(msg, str):
            msg = str(msg)
        print(msg)

    def print_info(self, msg: str, style: Optional[ansi.AnsiCodeType] = None):
        if not isinstance(msg, str):
            msg = str(msg)
        self.ui_logger.info(ansi.Seq.wrap(style, msg) if self.use_colors else msg)

    def print_warn(self, msg: str):
        if not isinstance(msg, str):
            msg = str(msg)
        self.ui_logger.warning(msg)

    def print_error(self, exception_or_msg):
        self.ui_logger.error(exception_or_msg, exc_info=isinstance(exception_or_msg, Exception))

    def print_fatal(self, exception_or_msg):
        self.ui_logger.critical(exception_or_msg, exc_info=isinstance(exception_or_msg, Exception))

    def print_debug(self, msg: str):
        if not isinstance(msg, str):
            msg = str(msg)
        self.ui_logger.debug(msg)

    def clear_screen(self):
        self.ui_logger.info(ansi.Seq.clear_screen())

    def fail(self, exception_or_msg: str, exit_code: int = 99):
        self.print_fatal(exception_or_msg)
        exit(exit_code)


CLI = __CLI()
