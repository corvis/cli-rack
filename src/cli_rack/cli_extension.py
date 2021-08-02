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
import logging

from cli_rack import CLI
from cli_rack.modular import GlobalArgsExtension


class VerboseModeCliExtension(GlobalArgsExtension):
    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            required=False,
            help="If set, output will be more verbose",
            default=False,
        )
        parser.add_argument(
            "-l",
            "--log-level",
            dest="log_level",
            action="store",
            choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
            required=False,
            help="If set more verbose output will used",
            default=logging.getLevelName(logging.INFO),
        )

    def handle(self, args: argparse.Namespace):
        if args.verbose and args.log_level is None:
            CLI.set_log_level(logging.getLevelName("INFO"))
        elif args.log_level is not None:
            CLI.set_log_level(logging.getLevelName(args.log_level))


class DebugModeCliExtension(GlobalArgsExtension):
    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "-d",
            "--debug",
            dest="debug",
            action="store_true",
            required=False,
            help="If set, debug output will be enabled. This includes stack traces for exceptions.",
            default=False,
        )

    def handle(self, args: argparse.Namespace):
        if args.debug:
            CLI.set_log_level(logging.DEBUG)
            CLI.set_stack_traces(True)
        else:
            CLI.set_stack_traces(False)
