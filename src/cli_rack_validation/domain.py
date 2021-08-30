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

import math
from collections import OrderedDict
from typing import Any, Optional, List

from voluptuous import MultipleInvalid, Invalid

from .utils import is_approximately_integer


class EnumValue:
    """Special type used to mark enum values for validate.enum."""

    @property
    def enum_value(self):
        return getattr(self, "_enum_value", None)

    @enum_value.setter
    def enum_value(self, value):
        setattr(self, "_enum_value", value)


class HexInt(int):
    def __str__(self):
        value = self
        sign = "-" if value < 0 else ""
        value = abs(value)
        if 0 <= value <= 255:
            return f"{sign}0x{value:02X}"
        return f"{sign}0x{value:X}"


class IPAddress:
    def __init__(self, *args):
        if len(args) != 4:
            raise ValueError("IPAddress must consist of 4 items")
        self.args = args

    def __str__(self):
        return ".".join(str(x) for x in self.args)


class MACAddress:
    def __init__(self, *parts):
        if len(parts) != 6:
            raise ValueError("MAC Address must consist of 6 items")
        self.parts = parts

    def __str__(self):
        return ":".join(f"{part:02X}" for part in self.parts)

    @property
    def as_hex(self):
        num = "".join(f"{part:02X}" for part in self.parts)
        return f"0x{num}ULL"


class TimePeriod:
    def __init__(
            self,
            microseconds=None,
            milliseconds=None,
            seconds=None,
            minutes=None,
            hours=None,
            days=None,
    ):
        if days is not None:
            if not is_approximately_integer(days):
                frac_days, days = math.modf(days)
                hours = (hours or 0) + frac_days * 24
            self.days = int(round(days))
        else:
            self.days = None

        if hours is not None:
            if not is_approximately_integer(hours):
                frac_hours, hours = math.modf(hours)
                minutes = (minutes or 0) + frac_hours * 60
            self.hours = int(round(hours))
        else:
            self.hours = None

        if minutes is not None:
            if not is_approximately_integer(minutes):
                frac_minutes, minutes = math.modf(minutes)
                seconds = (seconds or 0) + frac_minutes * 60
            self.minutes = int(round(minutes))
        else:
            self.minutes = None

        if seconds is not None:
            if not is_approximately_integer(seconds):
                frac_seconds, seconds = math.modf(seconds)
                milliseconds = (milliseconds or 0) + frac_seconds * 1000
            self.seconds = int(round(seconds))
        else:
            self.seconds = None

        if milliseconds is not None:
            if not is_approximately_integer(milliseconds):
                frac_milliseconds, milliseconds = math.modf(milliseconds)
                microseconds = (microseconds or 0) + frac_milliseconds * 1000
            self.milliseconds = int(round(milliseconds))
        else:
            self.milliseconds = None

        if microseconds is not None:
            if not is_approximately_integer(microseconds):
                raise ValueError("Maximum precision is microseconds")
            self.microseconds = int(round(microseconds))
        else:
            self.microseconds = None

    def as_dict(self):
        out = OrderedDict()
        if self.microseconds is not None:
            out["microseconds"] = self.microseconds
        if self.milliseconds is not None:
            out["milliseconds"] = self.milliseconds
        if self.seconds is not None:
            out["seconds"] = self.seconds
        if self.minutes is not None:
            out["minutes"] = self.minutes
        if self.hours is not None:
            out["hours"] = self.hours
        if self.days is not None:
            out["days"] = self.days
        return out

    def __str__(self):
        if self.microseconds is not None:
            return f"{self.total_microseconds}us"
        if self.milliseconds is not None:
            return f"{self.total_milliseconds}ms"
        if self.seconds is not None:
            return f"{self.total_seconds}s"
        if self.minutes is not None:
            return f"{self.total_minutes}min"
        if self.hours is not None:
            return f"{self.total_hours}h"
        if self.days is not None:
            return f"{self.total_days}d"
        return "0s"

    def __repr__(self):
        return f"TimePeriod<{self.total_microseconds}>"

    @property
    def total_microseconds(self):
        return self.total_milliseconds * 1000 + (self.microseconds or 0)

    @property
    def total_milliseconds(self):
        return self.total_seconds * 1000 + (self.milliseconds or 0)

    @property
    def total_seconds(self):
        return self.total_minutes * 60 + (self.seconds or 0)

    @property
    def total_minutes(self):
        return self.total_hours * 60 + (self.minutes or 0)

    @property
    def total_hours(self):
        return self.total_days * 24 + (self.hours or 0)

    @property
    def total_days(self):
        return self.days or 0

    def __eq__(self, other):
        if isinstance(other, TimePeriod):
            return self.total_microseconds == other.total_microseconds
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, TimePeriod):
            return self.total_microseconds != other.total_microseconds
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, TimePeriod):
            return self.total_microseconds < other.total_microseconds
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, TimePeriod):
            return self.total_microseconds > other.total_microseconds
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, TimePeriod):
            return self.total_microseconds <= other.total_microseconds
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, TimePeriod):
            return self.total_microseconds >= other.total_microseconds
        return NotImplemented


class TimePeriodMicroseconds(TimePeriod):
    pass


class TimePeriodMilliseconds(TimePeriod):
    pass


class TimePeriodSeconds(TimePeriod):
    pass


class TimePeriodMinutes(TimePeriod):
    pass


class ValidationResult:
    def __init__(self, data: Any) -> None:
        self.error: Optional[MultipleInvalid] = None
        self.normalized_data: Any = data
        self.data: Any = data

    @property
    def has_errors(self) -> bool:
        return self.error is not None

    @property
    def errors(self) -> List[Invalid]:
        if self.has_errors:
            return self.error.errors    # type: ignore
        return []
