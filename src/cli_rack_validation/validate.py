import copy
import logging
import re
import uuid as uuid_
from contextlib import contextmanager
from datetime import datetime

import voluptuous as vol

from .const import CONST_HOUR, CONST_MINUTE, CONST_SECOND
from .domain import HexInt, TimePeriod, TimePeriodMilliseconds, TimePeriodMicroseconds, TimePeriodSeconds, \
    TimePeriodMinutes, EnumValue, ValidationResult
from .utils import add_class_to_obj, list_starts_with

_LOGGER = logging.getLogger(__name__)

TIME_PERIOD_REGEX = re.compile(r"^([-+]?[0-9]*\.?[0-9]*)\s*(\w*)$")

# The code below is heavily inspired by config validation functionality of ESPHome (https://esphome.io/)
# Specifically it is based on the following module published under MIT license:
# https://github.com/esphome/esphome/blob/b955527f6ce3e6a7d8066112beb03b4b2e1b1e87/esphome/config_validation.py

Schema = vol.Schema
All = vol.All
Coerce = vol.Coerce
Range = vol.Range
Invalid = vol.Invalid
MultipleInvalid = vol.MultipleInvalid
Any = vol.Any
Lower = vol.Lower
Upper = vol.Upper
Length = vol.Length
Exclusive = vol.Exclusive
Inclusive = vol.Inclusive
ALLOW_EXTRA = vol.ALLOW_EXTRA
UNDEFINED = vol.UNDEFINED
Optional = vol.Optional
Required = vol.Required
RequiredFieldInvalid = vol.RequiredFieldInvalid


def alphanumeric(value):
    if value is None:
        raise Invalid("string value is None")
    value = str(value)
    if not value.isalnum():
        raise Invalid(f"{value} is not alphanumeric")
    return value

def anything(value):
    return value

def string(value):
    """Validate that a configuration value is a string. If not, automatically converts to a string.
    Note that this can be lossy, for example the input value 60.00 (float) will be turned into
    "60.0" (string). For values where this could be a problem `string_string` has to be used.
    """
    if isinstance(value, (dict, list)):
        raise Invalid("string value cannot be dictionary or list.")
    if isinstance(value, bool):
        raise Invalid(
            "Auto-converted this value to boolean, please wrap the value in quotes."
        )
    if isinstance(value, str):
        return value
    if value is not None:
        return str(value)
    raise Invalid("string value is None")


def string_strict(value):
    """Like string, but only allows strings, and does not automatically convert other types to
    strings."""
    if isinstance(value, str):
        return value
    raise Invalid(
        "Must be string, got {}. did you forget putting quotes "
        "around the value?".format(type(value))
    )


def boolean(value):
    """Validate the given config option to be a boolean.
    This option allows a bunch of different ways of expressing boolean values:
     - instance of boolean
     - 'true'/'false'
     - 'yes'/'no'
     - 'enable'/disable
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower()
        if value in ("true", "yes", "on", "enable"):
            return True
        if value in ("false", "no", "off", "disable"):
            return False
    raise Invalid(
        "Expected boolean value, but cannot convert {} to a boolean. "
        "Please use 'true' or 'false'".format(value)
    )


def ensure_list(*validators):
    """Validate this configuration option to be a list.
    If the config value is not a list, it is automatically converted to a
    single-item list.
    None and empty dictionaries are converted to empty lists.
    """
    user = All(*validators)
    list_schema = Schema([user])

    def validator(value):
        if value is None or (isinstance(value, dict) and not value):
            return []
        if not isinstance(value, list):
            return [user(value)]
        return list_schema(value)

    return validator


def hex_int(value):
    """Validate the given value to be a hex integer. This is mostly for cosmetic
    purposes of the generated code.
    """
    return HexInt(int_(value))


def int_(value):
    """Validate that the config option is an integer.
    Automatically also converts strings to ints.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if int(value) == value:
            return int(value)
        raise Invalid(
            "This option only accepts integers with no fractional part. Please remove "
            "the fractional part from {}".format(value)
        )
    value = string_strict(value).lower()
    base = 10
    if value.startswith("0x"):
        base = 16
    try:
        return int(value, base)
    except ValueError:
        # pylint: disable=raise-missing-from
        raise Invalid(f"Expected integer, but cannot parse {value} as an integer")


def int_range(min=None, max=None, min_included=True, max_included=True):
    """Validate that the config option is an integer in the given range."""
    if min is not None:
        assert isinstance(min, int)
    if max is not None:
        assert isinstance(max, int)
    return All(
        int_,
        Range(min=min, max=max, min_included=min_included, max_included=max_included),
    )


def hex_int_range(min=None, max=None, min_included=True, max_included=True):
    """Validate that the config option is an integer in the given range."""
    return All(
        hex_int,
        Range(min=min, max=max, min_included=min_included, max_included=max_included),
    )


uint16_t = int_range(min=0, max=65535)
uint32_t = int_range(min=0, max=4294967295)
uint64_t = int_range(min=0, max=18446744073709551615)
hex_uint8_t = hex_int_range(min=0, max=255)
hex_uint16_t = hex_int_range(min=0, max=65535)
hex_uint32_t = hex_int_range(min=0, max=4294967295)
hex_uint64_t = hex_int_range(min=0, max=18446744073709551615)


def float_range(min=None, max=None, min_included=True, max_included=True):
    """Validate that the config option is a floating point number in the given range."""
    if min is not None:
        assert isinstance(min, (int, float))
    if max is not None:
        assert isinstance(max, (int, float))
    return All(
        float_,
        Range(min=min, max=max, min_included=min_included, max_included=max_included),
    )


port = int_range(min=1, max=65535)
float_ = Coerce(float)
positive_float = float_range(min=0)
zero_to_one_float = float_range(min=0, max=1)
negative_one_to_one_float = float_range(min=-1, max=1)
positive_int = int_range(min=0)
positive_not_null_int = int_range(min=0, min_included=False)


# Adapted from:
# https://github.com/alecthomas/voluptuous/issues/115#issuecomment-144464666
def has_at_least_one_key(*keys):
    """Validate that at least one of the given keys exist in the config."""

    def validate(obj):
        """Test keys exist in dict."""
        if not isinstance(obj, dict):
            raise Invalid("expected dictionary")

        if not any(k in keys for k in obj):
            raise Invalid("Must contain at least one of {}.".format(", ".join(keys)))
        return obj

    return validate


def has_exactly_one_key(*keys):
    """Validate that exactly one of the given keys exist in the config."""

    def validate(obj):
        if not isinstance(obj, dict):
            raise Invalid("expected dictionary")

        number = sum(k in keys for k in obj)
        if number > 1:
            raise Invalid("Cannot specify more than one of {}.".format(", ".join(keys)))
        if number < 1:
            raise Invalid("Must contain exactly one of {}.".format(", ".join(keys)))
        return obj

    return validate


def has_at_most_one_key(*keys):
    """Validate that at most one of the given keys exist in the config."""

    def validate(obj):
        if not isinstance(obj, dict):
            raise Invalid("expected dictionary")

        number = sum(k in keys for k in obj)
        if number > 1:
            raise Invalid("Cannot specify more than one of {}.".format(", ".join(keys)))
        return obj

    return validate


def has_none_or_all_keys(*keys):
    """Validate that none or all of the given keys exist in the config."""

    def validate(obj):
        if not isinstance(obj, dict):
            raise Invalid("expected dictionary")

        number = sum(k in keys for k in obj)
        if number != 0 and number != len(keys):
            raise Invalid(
                "Must specify either none or all of {}.".format(", ".join(keys))
            )
        return obj

    return validate


TIME_PERIOD_ERROR = (
    "Time period {} should be format number + unit, for example 5ms, 5s, 5min, 5h"
)

time_period_dict = All(
    Schema(
        {
            Optional("days"): float_,
            Optional("hours"): float_,
            Optional("minutes"): float_,
            Optional("seconds"): float_,
            Optional("milliseconds"): float_,
            Optional("microseconds"): float_,
        }
    ),
    has_at_least_one_key(
        "days", "hours", "minutes", "seconds", "milliseconds", "microseconds"
    ),
    lambda value: TimePeriod(**value),
)


def time_period_str_colon(value):
    """Validate and transform time offset with format HH:MM[:SS]."""
    if isinstance(value, int):
        raise Invalid("Make sure you wrap time values in quotes")
    if not isinstance(value, str):
        raise Invalid(TIME_PERIOD_ERROR.format(value))

    try:
        parsed = [int(x) for x in value.split(":")]
    except ValueError:
        # pylint: disable=raise-missing-from
        raise Invalid(TIME_PERIOD_ERROR.format(value))

    if len(parsed) == 2:
        hour, minute = parsed
        second = 0
    elif len(parsed) == 3:
        hour, minute, second = parsed
    else:
        raise Invalid(TIME_PERIOD_ERROR.format(value))

    return TimePeriod(hours=hour, minutes=minute, seconds=second)


def time_period_str_unit(value):
    """Validate and transform time period with time unit and integer value."""
    if isinstance(value, int):
        raise Invalid(
            "Don't know what '{0}' means as it has no time *unit*! Did you mean "
            "'{0}s'?".format(value)
        )
    if isinstance(value, TimePeriod):
        value = str(value)
    if not isinstance(value, str):
        raise Invalid("Expected string for time period with unit.")

    unit_to_kwarg = {
        "us": "microseconds",
        "microseconds": "microseconds",
        "ms": "milliseconds",
        "milliseconds": "milliseconds",
        "s": "seconds",
        "sec": "seconds",
        "seconds": "seconds",
        "min": "minutes",
        "minutes": "minutes",
        "h": "hours",
        "hours": "hours",
        "d": "days",
        "days": "days",
    }

    match = TIME_PERIOD_REGEX.match(value)

    if match is None:
        raise Invalid("Expected time period with unit, " "got {}".format(value))
    kwarg = unit_to_kwarg[one_of(*unit_to_kwarg)(match.group(2))]

    return TimePeriod(**{kwarg: float(match.group(1))})


def time_period_in_milliseconds_(value):
    if value.microseconds is not None and value.microseconds != 0:
        raise Invalid("Maximum precision is milliseconds")
    return TimePeriodMilliseconds(**value.as_dict())


def time_period_in_microseconds_(value):
    return TimePeriodMicroseconds(**value.as_dict())


def time_period_in_seconds_(value):
    if value.microseconds is not None and value.microseconds != 0:
        raise Invalid("Maximum precision is seconds")
    if value.milliseconds is not None and value.milliseconds != 0:
        raise Invalid("Maximum precision is seconds")
    return TimePeriodSeconds(**value.as_dict())


def time_period_in_minutes_(value):
    if value.microseconds is not None and value.microseconds != 0:
        raise Invalid("Maximum precision is minutes")
    if value.milliseconds is not None and value.milliseconds != 0:
        raise Invalid("Maximum precision is minutes")
    if value.seconds is not None and value.seconds != 0:
        raise Invalid("Maximum precision is minutes")
    return TimePeriodMinutes(**value.as_dict())


def update_interval(value):
    if value == "never":
        return 4294967295  # uint32_t max
    return positive_time_period_milliseconds(value)


time_period = Any(time_period_str_unit, time_period_str_colon, time_period_dict)
positive_time_period = All(time_period, Range(min=TimePeriod()))
positive_time_period_milliseconds = All(
    positive_time_period, time_period_in_milliseconds_
)
positive_time_period_seconds = All(positive_time_period, time_period_in_seconds_)
positive_time_period_minutes = All(positive_time_period, time_period_in_minutes_)
time_period_microseconds = All(time_period, time_period_in_microseconds_)
positive_time_period_microseconds = All(
    positive_time_period, time_period_in_microseconds_
)
positive_not_null_time_period = All(
    time_period, Range(min=TimePeriod(), min_included=False)
)


def time_of_day(value):
    value = string(value)
    try:
        date = datetime.strptime(value, "%H:%M:%S")
    except ValueError as err:
        try:
            date = datetime.strptime(value, "%H:%M:%S %p")
        except ValueError:
            # pylint: disable=raise-missing-from
            raise Invalid(f"Invalid time of day: {err}")

    return {
        CONST_HOUR: date.hour,
        CONST_MINUTE: date.minute,
        CONST_SECOND: date.second,
    }


def uuid(value):
    return Coerce(uuid_.UUID)(value)


METRIC_SUFFIXES = {
    "E": 1e18,
    "P": 1e15,
    "T": 1e12,
    "G": 1e9,
    "M": 1e6,
    "k": 1e3,
    "da": 10,
    "d": 1e-1,
    "c": 1e-2,
    "m": 0.001,
    "µ": 1e-6,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
    "f": 1e-15,
    "a": 1e-18,
    "": 1,
}


def float_with_unit(quantity, regex_suffix, optional_unit=False):
    pattern = re.compile(
        r"^([-+]?[0-9]*\.?[0-9]*)\s*(\w*?)" + regex_suffix + r"$", re.UNICODE
    )

    def validator(value):
        if optional_unit:
            try:
                return float_(value)
            except Invalid:
                pass
        match = pattern.match(string(value))

        if match is None:
            raise Invalid(f"Expected {quantity} with unit, got {value}")

        mantissa = float(match.group(1))
        if match.group(2) not in METRIC_SUFFIXES:
            raise Invalid("Invalid {} suffix {}".format(quantity, match.group(2)))

        multiplier = METRIC_SUFFIXES[match.group(2)]
        return mantissa * multiplier

    return validator


def percentage(value):
    """Validate that the value is a percentage.
    The resulting value is an integer in the range 0.0 to 1.0.
    """
    value = possibly_negative_percentage(value)
    return zero_to_one_float(value)


def possibly_negative_percentage(value):
    has_percent_sign = False
    if isinstance(value, str):
        try:
            if value.endswith("%"):
                has_percent_sign = False
                value = float(value[:-1].rstrip()) / 100.0
            else:
                value = float(value)
        except ValueError:
            # pylint: disable=raise-missing-from
            raise Invalid("invalid number")
    if value > 1:
        msg = "Percentage must not be higher than 100%."
        if not has_percent_sign:
            msg += " Please put a percent sign after the number!"
        raise Invalid(msg)
    if value < -1:
        msg = "Percentage must not be smaller than -100%."
        if not has_percent_sign:
            msg += " Please put a percent sign after the number!"
        raise Invalid(msg)
    return negative_one_to_one_float(value)


def percentage_int(value):
    if isinstance(value, str) and value.endswith("%"):
        value = int(value[:-1].rstrip())
    return value


def invalid(message):
    """Mark this value as invalid. Each time *any* value is passed here it will result in a
    validation error with the given message.
    """

    def validator(value):
        raise Invalid(message)

    return validator


def valid(value):
    """A validator that is always valid and returns the value as-is."""
    return value


@contextmanager
def prepend_path(path):
    """A contextmanager helper to prepend a path to all voluptuous errors."""
    if not isinstance(path, (list, tuple)):
        path = [path]
    try:
        yield
    except vol.Invalid as e:
        e.prepend(path)
        raise e


@contextmanager
def remove_prepend_path(path):
    """A contextmanager helper to remove a path from a voluptuous error."""
    if not isinstance(path, (list, tuple)):
        path = [path]
    try:
        yield
    except vol.Invalid as e:
        if list_starts_with(e.path, path):
            # Can't set e.path (namedtuple
            for _ in range(len(path)):
                e.path.pop(0)
        raise e


def one_of(*values, **kwargs):
    """Validate that the config option is one of the given values.
    :param values: The valid values for this type
    :Keyword Arguments:
      - *lower* (``bool``, default=False): Whether to convert the incoming values to lowercase
        strings.
      - *upper* (``bool``, default=False): Whether to convert the incoming values to uppercase
        strings.
      - *int* (``bool``, default=False): Whether to convert the incoming values to integers.
      - *float* (``bool``, default=False): Whether to convert the incoming values to floats.
      - *space* (``str``, default=' '): What to convert spaces in the input string to.
    """
    options = ", ".join(f"'{x}'" for x in values)
    lower = kwargs.pop("lower", False)
    upper = kwargs.pop("upper", False)
    string_ = kwargs.pop("string", False) or lower or upper
    to_int = kwargs.pop("int", False)
    to_float = kwargs.pop("float", False)
    space = kwargs.pop("space", " ")
    if kwargs:
        raise ValueError

    def validator(value):
        # pylint: disable=comparison-with-callable

        if string_:
            value = string(value)
            value = value.replace(" ", space)
        if to_int:
            value = int_(value)
        if to_float:
            value = float_(value)
        if lower:
            value = Lower(value)
        if upper:
            value = Upper(value)
        if value not in values:
            import difflib

            options_ = [str(x) for x in values]
            option = str(value)
            matches = difflib.get_close_matches(option, options_)
            if matches:
                raise Invalid(
                    "Unknown value '{}', did you mean {}?"
                    "".format(value, ", ".join(f"'{x}'" for x in matches))
                )
            raise Invalid(f"Unknown value '{value}', valid options are {options}.")
        return value

    return validator


def enum(mapping, **kwargs):
    """Validate this config option against an enum mapping.
    The mapping should be a dictionary with the key representing the config value name and
    a value representing the expression to set during code generation.
    Accepts all kwargs of one_of.
    """
    assert isinstance(mapping, dict)
    one_of_validator = one_of(*mapping, **kwargs)

    def validator(value):
        # pylint: disable=comparison-with-callable

        value = one_of_validator(value)
        value = add_class_to_obj(value, EnumValue)
        value.enum_value = mapping[value]
        return value

    return validator


def url(value):
    import urllib.parse

    value = string_strict(value)
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError as e:
        raise Invalid("Not a valid URL") from e

    if not parsed.scheme or not parsed.netloc:
        raise Invalid("Expected a URL scheme and host")
    return parsed.geturl()


def ensure_schema(schema) -> vol.Schema:
    if not isinstance(schema, vol.Schema):
        return Schema(schema)
    return schema


def validate_and_normalize(obj, schema, raise_on_error=True) -> ValidationResult:
    schema = ensure_schema(schema)
    result = ValidationResult(copy.deepcopy(obj))
    try:
        result.normalized_data = schema(obj)
    except MultipleInvalid as e:
        if raise_on_error:
            raise e
        result.error = e
    return result
