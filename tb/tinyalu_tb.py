from pyuvm import *
import pyuvm
from cocotb.triggers import ClockCycles
import random
from common.tinyalu_utils import TinyAluBfm, Ops, alu_prediction, AluInput
from cocotb.clock import Clock
import cocotb

class Driver(uvm_driver):
    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()

    async def run_phase(self):
        await self.bfm.reset()
        self.bfm.start()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            input = AluInput(cmd.A, cmd.B, cmd.op)
            await self.bfm.send_op(input)
            self.seq_item_port.item_done()

class AluEnv(uvm_env):

    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver("driver", self)
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.result_mon = Monitor("result_mon", self, "get_result")
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        c = Clock(cocotb.top.clk, 4, "ns")
        c.start()

    def connect_phase(self):
        self.driver.seq_item_port.connect(
            self.seqr.seq_item_export)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage.analysis_export)
        self.result_mon.ap.connect(
            self.scoreboard.result_export)


class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} \
        OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"


class BaseSeq(uvm_sequence):

    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", 0, 0, op)
            await self.start_item(cmd_tr)
            self.set_operands(cmd_tr)
            await self.finish_item(cmd_tr)

    def set_operands(self, tr):
        pass


class RandomSeq(BaseSeq):
    def set_operands(self, tr):
        tr.A = random.randint(0, 255)
        tr.B = random.randint(0, 255)


class MaxSeq(BaseSeq):
    def set_operands(self, tr):
        tr.A = 0xff
        tr.B = 0xff

@pyuvm.test()
class BaseTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.seqr = ConfigDB().get(self, "", "SEQR")

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


class Coverage(uvm_subscriber):

    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def report_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            assert False
        else:
            self.logger.info("Covered all operations")
            assert True


class Scoreboard(uvm_component):

    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)
        self.result_get_port = uvm_get_port("result_get_port", self)
        self.cmd_export = self.cmd_fifo.analysis_export
        self.result_export = self.result_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.result_get_port.connect(self.result_fifo.get_export)

    def check_phase(self):
        while self.result_get_port.can_get():
            _, actual_result = self.result_get_port.try_get()
            cmd_success, cmd = self.cmd_get_port.try_get()
            if not cmd_success:
                self.logger.critical(f"result {actual_result} had no command")
            else:
                (A, B, op_numb) = cmd
                op = Ops(op_numb)
                predicted_result = alu_prediction(A, B, op)
                if predicted_result == actual_result:
                    self.logger.info(f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} ="
                                     f" 0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                                      f"= 0x{actual_result:04x} "
                                      f"expected 0x{predicted_result:04x}")


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.bfm = TinyAluBfm()
        self.get_method = getattr(self.bfm, method_name)

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        while True:
            datum = await self.get_method()
            self.logger.debug(f"MONITORED {datum}")
            self.ap.write(datum)