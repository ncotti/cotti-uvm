import cocotb
import pyuvm
from cotti_uvm.bfm import Bfm
from cocotb.clock import Clock
from cocotb.queue import QueueEmpty
from cocotb.triggers import ClockCycles, FallingEdge
from cotti_uvm.coverage import Coverage
from pyuvm import *
from cotti_uvm.sequencer import *
import random
from enum import IntEnum
from cotti_uvm.env import Env

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

def golden_ref(op: AluSeqItem):
    """DUT's golden reference model"""
    if op.mode == AluMode.ADD:
        result = op.a + op.b
    elif op.mode == AluMode.AND:
        result = op.a & op.b
    elif op.mode == AluMode.XOR:
        result = op.a ^ op.b
    elif op.mode == AluMode.MUL:
        result = op.a * op.b
    return result


class TinyAluBfm(Bfm):
    """TinyAlu BFM"""
    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 1

    async def input_driver(self):
        self.dut.start.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            st = int(self.dut.start.value)
            dn = int(self.dut.done.value)
            if st == 0 and dn == 0:
                try:
                    op = self.input_driver_queue.get_nowait()
                    self.dut.A.value = op.a
                    self.dut.B.value = op.b
                    self.dut.op.value = op.mode
                    self.dut.start.value = 1
                except QueueEmpty:
                    continue
            elif st == 1 and dn == 1:
                self.dut.start.value = 0

    async def input_monitor(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            start = int(self.dut.start.value)
            if start == 1 and prev_start == 0:
                cmd_tuple = AluSeqItem(
                    int(self.dut.A.value),
                    int(self.dut.B.value),
                    AluMode(self.dut.op.value))
                self.input_monitor_queue.put_nowait(cmd_tuple)
            prev_start = start

    async def output_monitor(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            done = int(self.dut.done.value)
            if prev_done == 0 and done == 1:
                result = int(self.dut.result.value)
                self.output_monitor_queue.put_nowait(result)
            prev_done = done


class TinyAluCoverage(Coverage):
    """Coverage for the TinyAlu"""
    def write(self, cmd):
        self.coverage_checklist.add(cmd.mode)



class BaseTest(uvm_test):
    def build_phase(self):
        self.env = Env(self,
            TinyAluBfm(),
            golden_ref=golden_ref,
            coverage_type=TinyAluCoverage,
            coverage_set=list(AluMode)
            )

    async def run_phase(self):
        self.raise_objection()
        await ClockCycles(cocotb.top.clk, 50)  # to do last transaction
        self.drop_objection()


class RandomSeq(Sequence):
    def items(self) -> list[AluSeqItem]:
        out = []
        for mode in list(AluMode):
            item = AluSeqItem(
                a=random.randint(0, 255),
                b=random.randint(0, 255),
                mode=mode
            )
            out.append(item)
        return out


class MaxSeq(Sequence):
    def items(self) -> list[AluSeqItem]:
        out = []
        for mode in list(AluMode):
            item = AluSeqItem(
                a=0xFF,
                b=0xFF,
                mode=mode
            )
            out.append(item)
        return out


@pyuvm.test()
class RandomTest(BaseTest):
    def start_of_simulation_phase(self):
        uvm_factory().set_type_override_by_type(Sequence, RandomSeq)


@pyuvm.test()
class MaxTest(BaseTest):
    def start_of_simulation_phase(self):
        uvm_factory().set_type_override_by_type(Sequence, MaxSeq)
