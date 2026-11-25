# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""Sequencer (Sequence + Sequencer).

This class is a superset of the confusing "sequence" and "sequencer"
UVM classes.

The UVM standard defines an `uvm_sequence` as the one responsible for
generating `uvm_sequence_item`, and the `uvm_sequencer` as just a "FIFO"
that communicates the `uvm_sequence` with the `uvm_driver`.

The `uvm_sequence` must call its `start()` method, with the sequencer as the
argument.

                                       (seq_item_export/port)
################              #################  |   ##############
# uvm_sequence # start() ---> # uvm_sequencer # ---> # uvm_driver #
################              #################      ##############

Instead of doing this, the "Sequencer" is defined as the combination of
the sequence and sequencer, exposing the `seq_item_export` for the driver to
use.

Note: This is the only case in which the one sending the data is called
"export", and the one receiving the "port". This is because the "port" is
actually the one who initiates the transaction, and the driver is the one who
is requesting the data.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

import cocotb
from cocotb.triggers import gather
from pyuvm import (
    uvm_component,
    uvm_put_port,
    uvm_sequence,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_tlm_fifo,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


class Item(uvm_sequence_item):
    """Re-export of the `uvm_sequence_item`.

    An "Item" has the following added constraints:

    1. The user must define the __eq__() method.
    2. The user must define the __str__() method.
    3. The user must define its constructor in such a way that it can be
    called without arguments, i.e., with all default values.
    """

    def __init__(self, name: str = "sequence_item") -> None:
        """Override constructor.

        If you override it, you must call it with super().__init__(),
        and the new constructor must not have mandatory values.
        """
        super().__init__(name)
        self.name = name
        self.dut = cocotb.top

    @abstractmethod
    async def delay(self) -> None:
        """Delay between sequence items.

        The sequence does the following:
        1. Generate a new item from `self.items()`.
        2. Waits until the driver is ready to receive a new item.
        3. Sends the item immediately.
        4. The driver changes the DUT's input signals.
        5. Optionally, waits `item.delay()`.
        6. The drivers acknowledges that the item finished, and repeats from 1.

        This guarantees that at least `self.delay()` time will pass in
        between inputs, regardless of the driver's input delay.
        """

    @abstractmethod
    def __eq__(self, other: Self) -> bool:
        """Equality == operator."""
        error_str = "Sequence items must define the __eq__() method."
        raise (NotImplementedError(error_str))

    def __hash__(self) -> int:
        """Hash."""
        return hash(self.name)

    @abstractmethod
    def __str__(self) -> str:
        """Convert object to string."""
        error_str = "Sequence items must define the __str__() method."
        raise (NotImplementedError(error_str))


class Sequence(uvm_sequence):
    """A Sequence defines different input values fed to the DUT.

    By defining the `items()` method, each iterator will be fed to the
    DUT through the Driver.
    """

    async def body(self) -> None:
        """Mandatory function from `uvm_sequence`.

        Gets launched when you call `self.start()`.
        """
        for item in self.items():
            # Waits until the Driver asks for a new sequence item,
            # i.e., awaits the `seq_item_port`.
            await self.start_item(item)

            # Send the sequence item through the `seq_item_export`
            await self.finish_item(item)

    @abstractmethod
    def items(self) -> Iterable[Item]:
        """Return an iterable list of `uvm_sequence_item`.

        All items will be sent to the Driver and feed into the DUT.
        """
        error_str = "Sequence must implement the items() method."
        raise (NotImplementedError(error_str))


class Sequencer(uvm_component):
    """UVM sequencer.

    This class combines the concepts of "Sequence" and "Sequencer" into one.
    """

    def __init__(self, name: str, parent: object | None, sequence_type: Sequence) -> None:
        """Just add the sequence type as an argument."""
        super().__init__(name, parent)
        self.sequence_type = sequence_type

    def build_phase(self) -> None:
        """Sequencer's UVM build phase."""
        self.sequencer = uvm_sequencer(f"{self.get_name()}_sequencer", self)
        self.seq_item_export = self.sequencer.seq_item_export
        self.fifo = uvm_tlm_fifo("sequencer_tlm_fifo", self)
        self.sequencer_end_put_port = uvm_put_port("sequencer_end_put_port", self)

    def connect_phase(self) -> None:
        """Sequencer's UVM connect phase."""
        self.sequencer_end_put_port.connect(self.fifo.put_export)

    async def run_phase(self) -> None:
        """Sequencer's UVM run phase."""
        if not isinstance(self.sequence_type, list):
            sequence_type_list = [self.sequence_type]
        else:
            sequence_type_list = self.sequence_type

        sequence_awaitable_list = []
        for sequence_type in sequence_type_list:
            sequence = sequence_type(sequence_type.__name__)
            sequence_awaitable_list.append(sequence.start(self.sequencer))

        await gather(*sequence_awaitable_list)

        await self.sequencer_end_put_port.put(datum=True)
