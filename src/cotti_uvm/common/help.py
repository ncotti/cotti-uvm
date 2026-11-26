"""Helper functions."""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
from pathlib import Path

from pyuvm import ConfigDB


def config_db_get(key: str) -> object:
    """Get a value from the global ConfigDB."""
    return ConfigDB().get(None, "", key)


def config_db_set(key: str, value: object) -> None:
    """Set a "key,value" pair into the global ConfigDB.

    A value in the ConfigDB is usually stored relative to the current
    path in the environment like this:

    ```
    # "self" object is an uvm_component with name "my_component"
    ConfigDB().set(self, "env.logs", "key", "value")
    ```

    This would place the value in the database in the location:
    `uvm_test_top.my_component.env.logs`.

    A value can be retrieved by using solely "key,value" pair. Usage of paths
    for the DB is only required if there were two values with the same KEY,
    which is unlikely. Therefore, this function treats the ConfigDB as a big
    global dictionary.
    """
    ConfigDB().set(None, "*", key, value)


def read_hex(filename: str) -> list:
    """Read a memory HEX file, and returns a list with its contents.

    Memory files are expected to be formatted as one hex value per row, like this:

    ```
    0x12345678
    0x11111111
    0x22222222
    0x33333333
    0x44444444
    ```
    """
    with Path.open(filename) as file:
        return [int(line.strip(), 16) for line in file if line.strip()]


def signed(value: int, width: int) -> int:
    """Return a signed representation of the number, expressed with `width` bits.

    By default, cocotb values are returned as unsigned integers. This function
    allows you to work with a signed representation.

    E.g.:
    ```
    signed(127, 8) == 127
    signed(128, 8) == -127
    signed(255, 8) == -1
    ```
    """
    max_unsigned_value = (2**width) - 1
    max_signed_value = (2 ** (width - 1)) - 1
    if value >= 0 and value <= max_signed_value:
        signed_value = value
    elif value > max_signed_value and value <= max_unsigned_value:
        signed_value = value - (max_unsigned_value + 1)
    else:
        signed_value = max_unsigned_value

    return signed_value
