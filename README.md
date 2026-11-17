# Cotti UVM

Modular classes to create UVM-based testbenches for cocoTB.

## Running examples

```bash
pip install -e .
make clean vrun
```

## Install

```bash
pip install cotti-uvm
```

## Update package version in PyPI

```bash
python3 -m pip install --upgrade build twine
python3 -m build
```

Update version number at `pyproject.toml`.

```bash
twine upload dist/*
```
