import sys

from cli_rack import CLI
from cli_rack.modular import CliAppManager


def main(argv):
    CLI.setup()
    app_manager = CliAppManager("myprog")
    app_manager.allow_multiple_commands = True
    app_manager.parse_and_handle_global()
    app_manager.discover_and_register_extensions("modular_app")
    app_manager.setup()

    parsed_commands = app_manager.parse(argv)
    for cmd in parsed_commands:
        CLI.print_data(cmd)

    exec_manager = app_manager.create_execution_manager()
    exec_manager.run(parsed_commands)


if __name__ == "__main__":
    main(sys.argv[1:])
