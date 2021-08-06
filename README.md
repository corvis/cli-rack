![CLI Rack Cover Picture](https://raw.githubusercontent.com/corvis/cli-rack/master/docs/assets/cover-picture.png "PrCLI Rack Cover Picturee")

<h2 align="center">CLI Rack</h2>

<p align="center">
<a href="https://pypi.org/project/cli-rack/"><img src="https://img.shields.io/pypi/l/cli-rack?style=for-the-badge" title="License: MIT"/></a> 
<a href="https://pypi.org/project/cli-rack/"><img src="https://img.shields.io/pypi/pyversions/cli-rack?style=for-the-badge" title="Python Versions"/></a> 
<a href="https://github.com/psf/black/"><img src="https://img.shields.io/badge/Code%20Style-black-black?style=for-the-badge" title="Code style: black"/></a> 
<a href="https://pypi.org/project/cli-rack/"><img src="https://img.shields.io/pypi/v/cli-rack?style=for-the-badge" title="PyPy Version"/></a> 
<a href="https://pypi.org/project/cli-rack/"><img src="https://img.shields.io/pypi/dm/cli-rack?style=for-the-badge" title="PyPy Downloads"/></a> 
<br>
<a href="https://github.com/corvis/cli-rack/actions/workflows/sanity-check.yml"><img src="https://img.shields.io/github/workflow/status/corvis/cli-rack/Sanity%20Check?style=for-the-badge" title="Build Status"/></a> 
<a href="https://github.com/corvis/cli-rack/"><img src="https://img.shields.io/github/last-commit/corvis/cli-rack?style=for-the-badge" title="Last Commit"/></a> 
<a href="https://github.com/corvis/cli-rack/releases/"><img src="https://img.shields.io/github/release-date/corvis/cli-rack?style=for-the-badge" title="Last Release"/></a> 
</p>

Lightweight set of tools for creating pretty-looking CLI applications in Python. This library tends to simplify and
unify the approach to structuring CLI related code. At the moment it covers:

* Managing terminal output - verbosity levels, colored output, logger configuration
* Parsing arguments
* Modular application design - each module could extend argument parser with own command
* Modules discovery - scanning packages to find cli extension modules
* Module availability support - module might declare a method to verify if environment is suitable (e.g. all
  dependencies are present). If not, module will be automatically excluded from CLI interface
* Sync and Async execution manager
* Loading external components
* Installing optional dependencies

# Features

## CLI output

The module provides built-in methods to output information for the end user. It is configured to pint direct
informational messages, errors and warnings to the `stderr` and execution result to `stdout`.

The functionality is available via special object called `CLI`. Consider the following example:

```python
from cli_rack import CLI

CLI.setup()

CLI.print_info("This is just a message to user")
CLI.print_warn("This is a warning")
CLI.print_error("This is an error message")
CLI.print_error(ValueError("This is an exception"))
CLI.print_data("This text comes to STDOUT, not STDERR")
```

`CLI.setup()` must be invoked in the very beginning of the program as it determines terminal capabilities and configures
logger, filters and formatters. It is also possible to configure verbosity level on this stage. See
Section [Verbosity configuration](#verbosity-configuration) for details.

Methods `CLI.print_*` have very similar interface and are designed for printing information of specific type. It is
highly important to avoid simple built-in `print` function and use `CLI.print_*` methods instead as it allows to keep
output clean, consistent and well formatted. Also, verbosity control won't work for any data written directly into
output stream. It is also possible to override formatting options for individual message see
Section [Formatting capabilities](#formatting-capabilities) for more details.

#### CLI.print_info(msg: str, style: Optional[ansi.AnsiCodeType] = None)

### Verbosity configuration

TBD

### Debug mode

TBD

### Formatting capabilities

TBD

## Logging

### Preconfigured logger

TBD

### Streamlined interface for tuning configuration

TBD

## Loading external libraries

If you are building modular application you might want to allow your app with external components loaded from remote
repository/server/registry. `cli_rack.loader` package streamlines development of this feature.

The example below illustrates the main idea:

```python

from cli_rack import CLI, ansi
from cli_rack.loader import LoaderRegistry

CLI.setup()
CLI.verbose_mode()
CLI.print_info("Loading module using loader registry\n", ansi.Mod.BOLD)

LoaderRegistry.target_dir = "generated"

resource_meta = LoaderRegistry.load("github://logicify/healthcheckbot")
CLI.print_info(resource_meta.to_dict())
```

Here we configure loader to put downloaded modules into `generated` folder. Then ask to download module using the
following resource locator `github://logicify/healthcheckbot`. `LoaderRegistry` tries to find loader capable to handle
this type of locator (built-in `GithubLoader` in this case) and passes control to particular loader.

Loader will check if the local copy of the package is already present and it is up to date. If this is the case nothing
will be downloaded. Otherwise, it will download data and put it under `target_dir`.

The data in the remote location might have different directory layout and it is highly likely you don't need file from
the root, but rather interested in some subdirectory. For this purpose you could create a `path_resolver` function like
this:

```python
import os
from cli_rack.loader import LoadedDataMeta, InvalidPackageStructure, LoaderRegistry


def packages_dir_resolver(meta: LoadedDataMeta) -> str:
    if os.path.isdir(os.path.join(meta.path, "packages")):
        return "packages"
    raise InvalidPackageStructure(meta, "Folder \"packages\" must be present in directory root")


LoaderRegistry.target_dir = "generated"
resource_meta = LoaderRegistry.load("github://corvis/esphome-packages", packages_dir_resolver)
```

### cli_rack.loader.LocalLoader

TBD

### cli_rack.loader.GithubLoader

TBD

### Extending cli_rack.loader with custom loader

It is pretty trivial to implement custom loader to fetch data from other sources (e.g. your proprietary company NAS):

1. Implement `cli_rack.loader.BaseLocatorDef` and `cli_rack.loader.BaseLoader` (you might want to
   use [GithubLoader](https://github.com/corvis/cli-rack/blob/development/src/cli_rack/loader.py) as an example).
2. Register it in `LoaderRegistry`:

```python
from cli_rack.loader import LoaderRegistry
LoaderRegistry.register(MyLoader)
```

## Modular application architecture

    TBD
    * Global options
    * Commands
    * Params
    * Dynamic available commands discovery
    * Commands availability
    * Automatic dependencies installation

# Credits

* Dmitry Berezovsky, author

# Disclaimer

This module is licensed under MIT. This means you are free to use it in commercial projects.

The MIT license clearly explains that there is no warranty for this free software. Please see the included LICENSE file
for details.
