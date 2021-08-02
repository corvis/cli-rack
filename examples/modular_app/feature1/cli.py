import argparse

from cli_rack import CLI
from cli_rack.modular import CliExtension


class MyFeatureCliExtension(CliExtension):
    COMMAND_NAME = "my-ext"
    COMMAND_DESCRIPTION = "This is my cool feature"

    def handle(self, args):
        CLI.print_info("My Cool extension works!")


class MyFeatureCliExtension2(CliExtension):
    COMMAND_NAME = "my-ext2"
    COMMAND_DESCRIPTION = "Another cool feature"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument("--foo", type=str)

    def handle(self, args):
        CLI.print_info("My Another extension works!")
