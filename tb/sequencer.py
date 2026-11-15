from pyuvm import *
from enum import IntEnum
import random

class AluMode(IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4

class AluSeqItem(uvm_sequence_item):

    def __init__(self, a:int, b:int, mode:AluMode):
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


class BaseSeq(uvm_sequence):

    async def body(self):
        for mode in list(AluMode):
            cmd_tr = AluSeqItem(0, 0, mode)

            # TODO, why does it need the command in the "start_item"?
            # Waits until the Driver asks for a new sequence item,
            # i.e., awaits the `seq_item_port`.
            await self.start_item(cmd_tr)

            # Prepare the input value
            self.set_operands(cmd_tr)

            # Send the sequence item through the `seq_item_export`
            await self.finish_item(cmd_tr)

    def set_operands(self, tr):
        pass


class RandomSeq(BaseSeq):
    def set_operands(self, tr: AluSeqItem):
        tr.a = random.randint(0, 255)
        tr.bb = random.randint(0, 255)


class MaxSeq(BaseSeq):
    def set_operands(self, tr: AluSeqItem):
        tr.a = 0xff
        tr.b = 0xff