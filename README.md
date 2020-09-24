# dso tools
A set of tools for analyzing and modifying Torque3d VM bytecode.

## Installation
```bash
$ git clone git@github.com:florczakraf/dso-tools.git
$ cd dso-tools
$ pip install .
```
or in case of development:
```bash
$ pip install -e .[dev]
```

## Usage Examples
For examples browse [tests](tests) and [examples](examples) directories.

This package provides an entry-point called `dso`. You can call it with `--help` to get started.

## Development
```
$ pytest
$ black .
```
