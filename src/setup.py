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

import codecs
import os
from os import path

from setuptools import setup, find_packages

src_dir = path.abspath(path.dirname(__file__))
root_dir = path.join(src_dir, '..')

# == Read version ==
version_override = os.environ.get('VERSION_OVERRIDE', None) or None


def read_file(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read_file(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


if not version_override:
    version = get_version("cli_rack/__version__.py")
else:
    print("Using overridden version: " + version_override)
    version = version_override


# == END: Read version ==

def read_requirements(file_name: str):
    with open(file_name, 'r') as f:
        result = f.readlines()
    return list(filter(lambda l: not (l.startswith('#') or l.strip() == ''), result))


# Get the long description from the README file
readme_file = path.join(root_dir, 'docs/pypi-description.md')
try:
    from m2r import parse_from_file

    long_description = parse_from_file(readme_file)
except ImportError:
    # m2r may not be installed in user environment
    with open(readme_file) as f:
        long_description = f.read()

# Requirements
requirements_file = path.join(root_dir, 'requirements.txt')
requirements = read_requirements(requirements_file)

setup(
    name='cli-rack',
    # Semantic versioning should be used:
    # https://packaging.python.org/distributing/?highlight=entry_points#semantic-versioning-preferred
    version=version,
    description='CLI Rack - Lightweight set of tools for building pretty-looking CLI applications in Python',
    long_description=long_description,
    url='https://github.com/corvis/cli-rack',
    keywords='python cli terminal modular oop',

    # Author
    author='Dmitry Berezovsky',

    # License
    license='MIT',

    # Technical meta
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Home Automation',

        # License (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        # Python versions support
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>3.6',

    # Structure
    packages=find_packages(include=['cli_rack', 'cli_rack.*']),
    # py_modules=["app", 'cli', 'daemonize'],

    install_requires=requirements,

    # Extra dependencies might be installed with:
    # pip install -e .[dev,test]
    extras_require={},

    package_data={
        # 'examples': [path.join(root_dir, 'examples')],
    },

    # test_suite='nose2.collector.collector',
    # tests_require=[
    #     'nose2==0.8.0',
    # ],
    entry_points={}
)
