from pyuvm import *
from common.tinyalu_ref import *
import random

class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, value):
        super().__init__(name)
        self.value = value

    def __eq__(self, other):
        return (
            (self.value.aa == other.value.aa) and
            (self.value.bb == other.value.bb) and
            (self.value.mode == other.value.op)
        )

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.value.aa:02x} \
        OP: {self.value.mode.name} ({self.value.mode.value}) B: 0x{self.value.bb:02x}"


class BaseSeq(uvm_sequence):

    async def body(self):
        for mode in list(AluMode):
            cmd_tr = AluSeqItem("cmd_tr", AluInput(0, 0, mode))
            await self.start_item(cmd_tr)
            self.set_operands(cmd_tr.value)
            await self.finish_item(cmd_tr)

    def set_operands(self, tr):
        pass


class RandomSeq(BaseSeq):
    def set_operands(self, tr: AluInput):
        tr.aa = random.randint(0, 255)
        tr.bb = random.randint(0, 255)


class MaxSeq(BaseSeq):
    def set_operands(self, tr: AluInput):
        tr.aa = 0xff
        tr.bb = 0xff