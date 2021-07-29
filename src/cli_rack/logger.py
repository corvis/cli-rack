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
from typing import Dict, Optional

from .ansi import Seq, Fg, Mod, AnsiCodeType


class CommonCliLogFormatter(logging.Formatter):
    DEFAULT_STACK_COLOR = Mod.NORMAL & Fg.YELLOW
    DEFAULT_COLORS = {
        logging.DEBUG: Fg.LIGHT_BLACK,
        logging.INFO: Mod.NORMAL & Fg.BLUE,
        logging.WARN: Mod.BOLD & Fg.YELLOW,
        logging.ERROR: Mod.BOLD & Fg.RED,
        logging.CRITICAL: Mod.BOLD & Fg.RED,
    }
    DEFAULT_LOGGER_NAME_LEN = 12
    DEFAULT_LEVEL_MAP = {
        logging.DEBUG: "D",
        logging.INFO: "I",
        logging.WARN: "W",
        logging.ERROR: "E",
        logging.CRITICAL: "C",
    }

    def __init__(
        self,
        use_colors=True,
        level2color: Dict[int, str] = None,
        stack_color: str = None,
        level2name: Dict[int, str] = None,
        max_logger_name_len=None,
        show_stack_traces=False,
    ):
        super().__init__()
        self.use_colors = use_colors
        self.logger2color: Dict[str, str] = {}
        self.level2color: Dict[int, str] = level2color or dict(self.DEFAULT_COLORS)
        self.level2name: Dict[int, str] = level2name or dict(self.DEFAULT_LEVEL_MAP)
        self.stack_color: str = stack_color or self.DEFAULT_STACK_COLOR
        self.max_logger_name_len: Optional[int] = max_logger_name_len or self.DEFAULT_LOGGER_NAME_LEN
        self.show_stack_traces = show_stack_traces

    def get_color_for_record(self, record: logging.LogRecord):
        color = self.logger2color.get(record.name)
        if color is None:
            color = self.level2color.get(record.levelno, repr(Fg.DEFAULT))
        return color

    def _color_seq(self, color: Optional[AnsiCodeType]):
        if color is None:
            color = Fg.DEFAULT
        return Seq.style(color) if self.use_colors else ""

    def _color_reset(self):
        return Seq.reset() if self.use_colors else ""

    def format_logger_name(self, name: str) -> str:
        if self.max_logger_name_len is None:
            return name
        logger_name_formatted: str = name
        if len(logger_name_formatted) > self.max_logger_name_len:
            logger_name_formatted = logger_name_formatted[: self.max_logger_name_len]
        return logger_name_formatted.ljust(self.max_logger_name_len, " ")

    def formatMessage(self, record: logging.LogRecord):
        logger_name_formatted = self.format_logger_name(record.name)
        color = self.get_color_for_record(record)
        components = [
            "[" + self.level2name.get(record.levelno, " ") + "]",
            "[" + logger_name_formatted + "] ",
            record.message,
        ]
        result = "".join(components)
        return Seq.wrap(color, result) if self.use_colors else result

    def formatException(self, ei):
        components = [self._color_seq(self.level2color.get(logging.ERROR))]
        if self.show_stack_traces:
            full_ex_text = super().formatException(ei)
            components.append(self._color_seq(self.stack_color) + full_ex_text)
        components.append(self._color_reset())
        return "".join(components)


class UILogFormatter(CommonCliLogFormatter):
    DEFAULT_COLORS = {
        logging.DEBUG: Fg.LIGHT_BLACK,
        logging.INFO: Fg.DEFAULT,
        logging.WARN: Mod.BOLD & Fg.YELLOW,
        logging.ERROR: Mod.BOLD & Fg.RED,
        logging.CRITICAL: Mod.BOLD & Fg.RED,
    }

    def formatMessage(self, record: logging.LogRecord):
        color = self.get_color_for_record(record)
        prefix = ""
        if record.levelno == logging.ERROR:
            prefix = "ERROR: "
        elif record.levelno == logging.FATAL:
            prefix = "FATAL ERROR: "
        result = prefix + record.message
        return Seq.wrap(color, result) if self.use_colors else result
