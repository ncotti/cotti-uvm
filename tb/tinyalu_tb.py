import cocotb
import pyuvm
from bfm import Bfm
from cocotb.clock import Clock
from cocotb.queue import QueueEmpty
from cocotb.triggers import ClockCycles, FallingEdge
from common.help import *
from coverage import Coverage
from driver import Driver
from monitor import InputMonitor, OutputMonitor
from pyuvm import *
from scoreboard import Scoreboard
from sequencer import *

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

class AluEnv(uvm_env):

    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        config_db_set("SEQR", self.seqr)
        config_db_set("coverage_set", set(AluMode))
        config_db_set("bfm", TinyAluBfm())
        config_db_set("coverage_percentage", 100)
        config_db_set("golden_ref", golden_ref)

        self.driver = Driver("driver", self)
        self.input_monitor = InputMonitor("input_monitor", self)
        self.output_monitor = OutputMonitor("output_monitor", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = TinyAluCoverage("coverage", self)
        c = Clock(cocotb.top.clk, 4, "ns")
        c.start()

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)

        self.input_monitor.ap.connect(self.scoreboard.input_monitor_fifo.analysis_export)
        self.input_monitor.ap.connect(self.coverage.analysis_export)

        self.output_monitor.ap.connect(self.scoreboard.output_monitor_fifo.analysis_export)

@pyuvm.test()
class BaseTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.seqr = config_db_get("SEQR")

    async def run_phase(self):
        self.raise_objection()
        seq = BaseSeq.create("seq")
        await seq.start(self.seqr)
        await ClockCycles(cocotb.top.clk, 50)  # to do last transaction
        self.drop_objection()


@pyuvm.test()
class RandomTest(BaseTest):
    def start_of_simulation_phase(self):
        uvm_factory().set_type_override_by_type(BaseSeq, RandomSeq)


@pyuvm.test()
class MaxTest(BaseTest):
    def start_of_simulation_phase(self):
        uvm_factory().set_type_override_by_type(BaseSeq, MaxSeq)



