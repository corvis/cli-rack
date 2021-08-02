import sys

from cli_rack import CLI
from cli_rack.modular import DiscoveryManager, CliAppManager

discovery_manager = DiscoveryManager()


def main(argv):
    CLI.setup()
    CLI.debug_mode()
    app_manager = CliAppManager("myprog")
    app_manager.parse_and_handle_global()
    modules = discovery_manager.discover_cli_extensions("modular_app")
    CLI.print_info(modules)

    app_manager.register_extension(*[x.cli_extension for x in modules])
    app_manager.setup()
    app_manager.args_parser.print_help()
    parsed = app_manager.parse(argv)
    print(parsed)


if __name__ == "__main__":
    main(sys.argv[1:])
