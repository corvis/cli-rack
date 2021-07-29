from random import random
from time import sleep

from cli_rack import CLI, ansi
from cli_rack.stats import ExecutionTimer


def main():
    CLI.setup()
    CLI.print_info('Measuring execution time\n', ansi.Mod.BOLD)

    CLI.print_info('Starting long running fuction')
    timer = ExecutionTimer()
    for x in range(5):
        sleep(random())
    timer.stop()
    CLI.print_info('Execution finished in ' + timer.format_elapsed())


if __name__ == '__main__':
    main()
