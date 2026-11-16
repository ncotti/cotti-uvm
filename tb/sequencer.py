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


import random
from abc import abstractmethod
from enum import IntEnum

from pyuvm import *


class AluMode(IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


class AluSeqItem(uvm_sequence_item):
    """TinyAlu sequence item"""

    def __init__(self, a:int=0, b:int=0, mode:AluMode=AluMode.ADD):
        super().__init__("alu_sequence_item")
        self.a = a
        self.b = b
        self.mode = mode

    def __eq__(self, other):
        return (
            (self.a == other.a) and
            (self.b == other.b) and
            (self.mode == other.mode)
        )

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.a:02x} \
        OP: {self.mode.name} ({self.mode.value}) B: 0x{self.b:02x}"


class Sequence(uvm_sequence):

    async def body(self):
        for mode in list(AluMode):
            item = AluSeqItem()

            # Waits until the Driver asks for a new sequence item,
            # i.e., awaits the `seq_item_port`.
            await self.start_item(item)

            # Prepare the input value
            self.new_item(item)
            item.mode = mode

            # Send the sequence item through the `seq_item_export`
            await self.finish_item(item)

    @abstractmethod
    def new_item(self, item) -> None:
        """This method must """
        raise(NotImplementedError)


class Sequencer(uvm_component):
    def build_phase(self):
        self.sequencer = uvm_sequencer(f"{self.get_name()}_sequencer", self)
        self.seq_item_export = self.sequencer.seq_item_export


    async def run_phase(self):
        self.sequence = Sequence.create(f"{self.get_name()}_sequence")
        await self.sequence.start(self.sequencer)
