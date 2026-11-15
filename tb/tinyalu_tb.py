from pyuvm import *
import pyuvm
from cocotb.triggers import ClockCycles
from common.tinyalu_ref import *
from cocotb.clock import Clock
import cocotb
from driver import Driver
from scoreboard import Scoreboard
from coverage import Coverage
from sequencer import *
from monitor import InputMonitor, OutputMonitor
from bfm import TinyAluBfm
from common.help import *

class AluEnv(uvm_env):

    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        config_db_set("SEQR", self.seqr)
        config_db_set("coverage_set", set(AluMode))
        config_db_set("bfm", TinyAluBfm())

        self.driver = Driver("driver", self)
        self.cmd_mon = InputMonitor("cmd_mon", self)
        self.result_mon = OutputMonitor("result_mon", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        c = Clock(cocotb.top.clk, 4, "ns")
        c.start()

    def connect_phase(self):
        self.driver.seq_item_port.connect(
            self.seqr.seq_item_export)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.result_mon.ap.connect(self.scoreboard.result_export)


        self.cmd_mon.ap.connect(self.coverage.analysis_export)

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



