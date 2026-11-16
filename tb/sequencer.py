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

from pyuvm import uvm_component, uvm_sequence, uvm_sequence_item, uvm_sequencer


class BaseItem(uvm_sequence_item):
    pass

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
        raise(NotImplementedError)

class Sequencer(uvm_component):
    def build_phase(self):
        self.sequencer = uvm_sequencer(f"{self.get_name()}_sequencer", self)
        self.seq_item_export = self.sequencer.seq_item_export

    async def run_phase(self):
        self.sequence = Sequence.create(f"{self.get_name()}_sequence")
        await self.sequence.start(self.sequencer)
