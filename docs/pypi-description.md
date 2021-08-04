# CLI Rack

![CLI Rack Cover Picture](https://raw.githubusercontent.com/corvis/cli-rack/master/docs/assets/cover-picture.png "PrCLI Rack Cover Picturee")

Lightweight set of tools for creating pretty-looking CLI applications in Python. This library tends to simplify and
unify the approach to structuring CLI related code. At the moment it covers:

* Managing terminal output - verbosity levels, colored output, logger configuration
* Parsing arguments
* Modular application design - each module could extend argument parser with own command
* Modules discovery - scanning packages to find cli extension modules
* Module availability support - module might declare a method to verify if environment is suitable (e.g. all
  dependencies are present). If not, module will be automatically excluded from CLI interface
* Sync and Async execution manager

More details and documentation is here: https://github.com/corvis/cli-rack

## Quick examples

Using unified CLI output:

```python
from cli_rack import CLI

CLI.setup()

CLI.print_info("This is just a message to user")
CLI.print_warn("This is a warning")
CLI.print_error("This is an error message")
CLI.print_error(ValueError("This is an exception"))
CLI.print_data("This text comes to STDOUT, not STDERR")
```

# Credits

* Dmitry Berezovsky, author

# Disclaimer

This module is licensed under MIT. This means you are free to use it in commercial projects.

The MIT license clearly explains that there is no warranty for this free software. Please see the included LICENSE file
for details.