from cli_rack import CLI, ansi


def print_messages():
    CLI.print_info("This is just a message to user")
    CLI.print_warn("This is a warning")
    CLI.print_error("This is an error message")
    CLI.print_error(ValueError("This is an exception"))
    CLI.print_data("This text comes to STDOUT, not STDERR")


def simulate_exception():
    try:
        a = 1 / 0  # noqa: F841
    except Exception as e:
        CLI.print_error(e)


def main():
    CLI.setup()
    CLI.print_info("Simple user messages example\n", ansi.Mod.BOLD)

    CLI.print_info("Testing basic output capabilities", ansi.Mod.BOLD & ansi.Fg.BLUE)
    print_messages()

    CLI.print_info("Enable stack traces", ansi.Mod.BOLD & ansi.Fg.BLUE)
    CLI.set_stack_traces(True)
    simulate_exception()
    CLI.set_stack_traces(False)

    CLI.print_info("\nSame test with disabled colored output", ansi.Mod.BOLD & ansi.Fg.BLUE)
    CLI.use_colors = False
    CLI.set_stack_traces(False)
    print_messages()

    CLI.print_info("Enable stack traces", ansi.Mod.BOLD & ansi.Fg.BLUE)
    CLI.set_stack_traces(True)
    simulate_exception()
    CLI.set_stack_traces(False)


if __name__ == "__main__":
    main()
