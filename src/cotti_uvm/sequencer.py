# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""
Sequencer (Sequence + Sequencer)

This class is a superset of the confusing "sequence" and "sequencer" UVM classes.

The UVM standard defines an `uvm_sequence` as the one responsible for generating
`uvm_sequence_item`, and the `uvm_sequencer` as just a "FIFO" that communicates
the `uvm_sequence` with the `uvm_driver`.

The `uvm_sequence` must call its `start()` method, with the sequencer as the
argument.

                                       (seq_item_export/port)
################              #################  |   ##############
# uvm_sequence # start() ---> # uvm_sequencer # ---> # uvm_driver #
################              #################      ##############

Instead of doing this, the "Sequencer" is defined as the combination of
the sequence and sequencer, exposing the `seq_item_export` for the driver to
use.

Note: This is the only case in which the one sending the data is called "export",
and the one receiving the "port". This is because the "port" is actually the
one who initiates the transaction, and the driver is the one who is requesting
the data.
"""

from abc import abstractmethod
from collections.abc import Iterable

from pyuvm import (
    uvm_component,
    uvm_put_port,
    uvm_sequence,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_tlm_fifo,
)


class Item(uvm_sequence_item):
    """This class is just a re-export of the `uvm_sequence_item`, but
    with added constraints:

    1. The user must define the __eq__() method.
    2. The user must define the __str__() method.
    3. The user must define its constructor in such a way that it can be
    called without arguments, i.e., with all default values.
    """

    def __init__(self, name: str = "sequence_item"):
        """This constructor might be overriden, but you must call it with
        super().__init__(), and the new constructor must not have
        mandatory values.
        """
        super().__init__(name)

    @abstractmethod
    def __eq__(self, other) -> bool:
        raise (
            NotImplementedError(
                "Sequence items must define the __eq__() method."
            )
        )

    @abstractmethod
    def __str__(self) -> str:
        raise (
            NotImplementedError(
                "Sequence items must define the __str__() method."
            )
        )


class Sequence(uvm_sequence):
    async def body(self):
        for item in self.items():
            # Waits until the Driver asks for a new sequence item,
            # i.e., awaits the `seq_item_port`.
            await self.start_item(item)

            # Send the sequence item through the `seq_item_export`
            await self.finish_item(item)

    @abstractmethod
    def items(self) -> Iterable[uvm_sequence_item]:
        """
        This function should return an iterable list of `uvm_sequence_item`.

        All items will be sent to the Driver and feed into the DUT.
        """
        raise (
            NotImplementedError("Sequence must implement the items() method.")
        )


class Sequencer(uvm_component):
    def __init__(self, name, parent, sequence_type: Sequence):
        super().__init__(name, parent)
        self.sequence_type = sequence_type

    def build_phase(self):
        self.sequencer = uvm_sequencer(f"{self.get_name()}_sequencer", self)
        self.seq_item_export = self.sequencer.seq_item_export
        self.fifo = uvm_tlm_fifo("sequencer_tlm_fifo", self)
        self.sequencer_end_put_port = uvm_put_port(
            "sequencer_end_put_port", self
        )

    def connect_phase(self):
        self.sequencer_end_put_port.connect(self.fifo.put_export)

    async def run_phase(self):
        sequence = self.sequence_type(f"{self.get_name()}_sequence")
        await sequence.start(self.sequencer)
        await self.sequencer_end_put_port.put(True)
