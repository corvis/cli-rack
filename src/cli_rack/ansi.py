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

"""
The module streamlines handling ansi escape sequences.
The most popular use case for escape sequences is to apply formatting to terminal output
e.g. set font color, bg color, underline, italic.

See more details here: https://en.wikipedia.org/wiki/ANSI_escape_code
"""
import os
import platform
import re
from typing import Union, Tuple, Optional

from .utils import any_of_keys_exists

AnsiCodeType = Union[str, int, "AnsiCode", Tuple[int, ...], None]

__COLOR_TERMS_RE = re.compile("^screen|^xterm|^vt100|^vt220|^rxvt|color|ansi|cygwin|linux", re.IGNORECASE)


class AnsiCode(object):
    def __init__(self, code: AnsiCodeType) -> None:
        self.__codes: Tuple[int, ...] = (0,)  # 0 - is Reset command
        if code is None:
            return
        if isinstance(code, tuple):
            self.__codes = code
        elif isinstance(code, int):
            self.__codes = (code,)
        elif isinstance(code, str):
            self.__codes = (int(code),)
        elif isinstance(code, self.__class__):
            self.__codes = code.codes
        else:
            raise ValueError(
                "Invalid code passed to AnsiCode constructor. "
                "Expected value is a number or a string representing number"
            )

    @property
    def codes(self) -> Tuple[int, ...]:
        return self.__codes

    def __and__(self, other: AnsiCodeType):
        if other is None:
            raise ValueError("Operation is not supported for AnsiCode and None")
        if isinstance(other, self.__class__):
            return AnsiCode(self.codes + other.codes)
        else:
            return self.__and__(AnsiCode(other))

    def __add__(self, other):
        return self & other

    def __repr__(self):
        return ";".join([repr(x) for x in self.codes])

    def __str__(self):
        return "AnsiCode<{}>".format(repr(self))


class Fg:
    BLACK = AnsiCode(30)
    RED = AnsiCode(31)
    GREEN = AnsiCode(32)
    YELLOW = AnsiCode(33)
    BLUE = AnsiCode(34)
    MAGENTA = AnsiCode(35)
    CYAN = AnsiCode(36)
    WHITE = AnsiCode(37)
    COLOR = AnsiCode((38, 5))
    """
    Expects the next components to be a either 8-bit color code or 3 RGB components color components for 24-bit colors.
    Example (Fg.COLOR & 5) or Fg.COLOR & (127, 113, 124)
    """
    DEFAULT = AnsiCode(39)
    RESET = DEFAULT

    LIGHT_BLACK = AnsiCode(90)
    LIGHT_RED = AnsiCode(91)
    LIGHT_GREEN = AnsiCode(92)
    LIGHT_YELLOW = AnsiCode(93)
    LIGHT_BLUE = AnsiCode(94)
    LIGHT_MAGENTA = AnsiCode(95)
    LIGHT_CYAN = AnsiCode(96)
    LIGHT_WHITE = AnsiCode(97)


class Bg:
    BLACK = AnsiCode(40)
    RED = AnsiCode(41)
    GREEN = AnsiCode(42)
    YELLOW = AnsiCode(43)
    BLUE = AnsiCode(44)
    MAGENTA = AnsiCode(45)
    CYAN = AnsiCode(46)
    WHITE = AnsiCode(47)
    COLOR = AnsiCode((48, 5))
    """
    Expects the next components to be a either 8-bit color code or 3 RGB components color components for 24-bit colors.
    Example (Bg.COLOR & 5) or Bg.COLOR & (127, 113, 124)
    """
    DEFAULT = AnsiCode(49)
    RESET = DEFAULT

    LIGHT_BLACK = AnsiCode(100)
    LIGHT_RED = AnsiCode(101)
    LIGHT_GREEN = AnsiCode(102)
    LIGHT_YELLOW = AnsiCode(103)
    LIGHT_BLUE = AnsiCode(104)
    LIGHT_MAGENTA = AnsiCode(105)
    LIGHT_CYAN = AnsiCode(106)
    LIGHT_WHITE = AnsiCode(107)


class Mod:
    BRIGHT = AnsiCode(1)
    BOLD = BRIGHT
    DIM = AnsiCode(2)
    ITALIC = AnsiCode(3)
    """Not widely supported. Sometimes treated as inverse or blink"""
    UNDERLINE = AnsiCode(4)
    """Style extensions exist for Kitty, VTE, mintty and iTerm2."""
    SLOW_BLINK = AnsiCode(5)
    """Less than 150 per minute"""
    RAPID_BLINK = AnsiCode(5)
    """MS-DOS ANSI.SYS, 150+ per minute; not widely supported"""
    STRIKE_THROUGH = AnsiCode(9)
    """Characters legible but marked as if for deletion"""
    FONT_PRIMARY = AnsiCode(10)
    """Primary (default) font"""
    FONT_ALT1 = AnsiCode(11)
    FONT_ALT2 = AnsiCode(12)
    FONT_ALT3 = AnsiCode(13)
    NORMAL = AnsiCode(22)
    """Neither bold nor faint; color changes where intensity is implemented as such."""
    RESET_ALL = AnsiCode(0)
    """All attributes off"""


class EraseMode:
    CURSOR_TO_END = 0
    CURSOR_TO_BEGIN = 1
    ALL = 2
    ALL_WITH_BUFFER = 3


class Seq:
    CSI = "\033[{params}{mod}"
    OSC = "\033]{params}{mod}"
    BEL = "\a"
    RESET = "\033[0m"
    STYLE = "\033[{params}m"

    @classmethod
    def __repr_ansii(cls, style: AnsiCodeType) -> str:
        return style if isinstance(style, str) else repr(style)

    @classmethod
    def style(cls, style: Optional[AnsiCodeType], msg: Optional[str] = None) -> str:
        if style is None:
            style = Fg.DEFAULT
        if msg is None:
            style_str = cls.STYLE.format(params=cls.__repr_ansii(style))
            return style_str
        else:
            return cls.wrap(style, msg)

    @classmethod
    def wrap(cls, style: Optional[AnsiCodeType], msg: str) -> str:
        style_str = cls.style(style)
        result = []
        for x in msg.split(cls.RESET):
            result.append(style_str)
            result.append(x)
            result.append(Seq.RESET)
        return "".join(result)

    @classmethod
    def reset(cls):
        return cls.RESET

    @classmethod
    def cursor_up(cls, num=1):
        """
        Moves the cursor "num" (default 1) cells in the given direction.
        If the cursor is already at the edge of the screen, this has no effect.
        """
        return cls.CSI.format(params=num, mod="A")

    @classmethod
    def cursor_down(cls, num=1):
        """
        Moves the cursor "num" (default 1) cells in the given direction.
        If the cursor is already at the edge of the screen, this has no effect.
        """
        return cls.CSI.format(params=num, mod="B")

    @classmethod
    def cursor_forward(cls, num=1):
        """
        Moves the cursor "num" (default 1) cells in the given direction.
        If the cursor is already at the edge of the screen, this has no effect.
        """
        return cls.CSI.format(params=num, mod="C")

    @classmethod
    def cursor_back(cls, num=1):
        """
        Moves the cursor "num" (default 1) cells in the given direction.
        If the cursor is already at the edge of the screen, this has no effect.
        """
        return cls.CSI.format(params=num, mod="D")

    @classmethod
    def cursor_next_line(cls, num=1):
        """
        Moves cursor to beginning of the line "num" (default 1) lines down.
        """
        return cls.CSI.format(params=num, mod="E")

    @classmethod
    def cursor_prev_line(cls, num=1):
        """
        Moves cursor to beginning of the line "num" (default 1) lines up.
        """
        return cls.CSI.format(params=num, mod="F")

    @classmethod
    def cursor_pos(cls, x=1, y=1):
        """
        Moves the cursor to row y, column x. The values are 1-based, and default to 1 (top left corner) if omitted.
        :param x:
        :param y:
        """
        return cls.CSI.format(params=";".join((str(y), str(x))), mod="H")

    @classmethod
    def title(cls, msg: str):
        """
        Sets window title to "msg"
        """
        return cls.OSC.format(params="2;" + msg, mod=cls.BEL)

    @classmethod
    def clear_screen(cls, mode: int = EraseMode.ALL_WITH_BUFFER):
        """
        Clears part of the screen.
        If "mode" is EraseMode.CURSOR_TO_END(0), clear from cursor to end of screen.
        If "mode" is EraseMode.CURSOR_TO_BEGIN(1), clear from cursor to beginning of the screen.
        If "mode" is EraseMode.ALL(2), clear entire screen (and moves cursor to upper left on DOS ANSI.SYS).
        If "mode" is EraseMode.ALL_WITH_BUFFER(3)(default), clear entire screen and delete all lines saved in the scrollback
        buffer (this feature was added for xterm and is supported by other terminal applications).
        """
        return cls.CSI.format(params=mode, mod="J")

    @classmethod
    def clear_line(cls, mode: int = EraseMode.ALL):
        """
        Erases part of the line.
        If "mode" is EraseMode.CURSOR_TO_END(0), clear from cursor to the end of the line.
        If "mode" is EraseMode.CURSOR_TO_BEGIN(1), clear from cursor to beginning of the line.
        If "mode" is EraseMode.ALL(2), clear entire line. Cursor position does not change.
        EraseMode.ALL_WITH_BUFFER(3) - is not applicable and behaves the same as EraseMode.ALL(2)
        """
        if mode > 2:
            mode = EraseMode.ALL
        return cls.CSI.format(params=mode, mod="K")


def stream_supports_colors(stream) -> bool:
    if os.environ.get("NOCOLOR"):
        return False
    supports = stream.isatty() if "isatty" in dir(stream) else False
    supports = supports or any_of_keys_exists(("COLORTERM", "PYCHARM_HOSTED"), os.environ.keys())
    if not supports and "CI" in os.environ:
        supports = any_of_keys_exists(
            ("TRAVIS", "CIRCLECI", "APPVEYOR", "GITLAB_CI", "GITHUB_ACTIONS", "BUILDKITE", "DRONE"), os.environ.keys()
        )
    if supports:
        return True
    term = os.environ.get("TERM")
    if term is not None:
        if term.lower() == "dumb":
            return False
        if __COLOR_TERMS_RE.match(term):
            return True
    try:
        if platform.system().lower() == "windows":
            version_tuple = platform.version().split(".")
            return int(version_tuple[0]) == 10 and int(version_tuple[2]) >= 10586
    except:  # noqa: E722
        return False
    return False
