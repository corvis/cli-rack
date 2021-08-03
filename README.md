![CLI Rack Cover Picture](https://raw.githubusercontent.com/corvis/cli-rack/master/docs/assets/cover-picture.png "PrCLI Rack Cover Picturee")

<h2 align="center">CLI Rack</h2>

<p align="center">
<a href="https://github.com/psf/black/"><img src="https://img.shields.io/badge/Code%20Style-black-black?style=for-the-badge" title="Code style: black"/></a> 
<br>
<a href="https://github.com/corvis/cli-rack/"><img src="https://img.shields.io/github/last-commit/corvis/cli-rack?style=for-the-badge" title="Last Commit"/></a> 
  <a href="https://github.com/corvis/cli-rack/releases/"><img src="https://img.shields.io/github/release-date/corvis/cli-rack?style=for-the-badge" title="Last Release"/></a> 
</p>

Lightweight set of tools for creating pretty-looking CLI applications in Python. This library tends to simplify and
unify the approach to structuring CLI related code. At the moment it covers:

1. Managing terminal output - verbosity levels, colored output, logger configuration
2. Parsing arguments
3. Modular application design - each module could extend argument parser with own command
4. Modules discovery - scanning packages to find cli extension modules
5. Module availability support - module might declare a method to verify if environment is suitable (e.g. all
   dependencies are present). If not, module will be automatically excluded from CLI interface
6. Sync and Async execution manager

# Credits

* Dmitry Berezovsky, author

# Disclaimer

This module is licensed under MIT. This means you are free to use it in commercial projects.

The MIT license clearly explains that there is no warranty for this free software. Please see the included LICENSE file
for details.
