from __future__ import annotations

from cocotb.triggers import Timer
from pyuvm import uvm_env, uvm_get_port

from cotti_uvm.bfm import Bfm
from cotti_uvm.common.help import config_db_set
from cotti_uvm.coverage import Coverage
from cotti_uvm.driver import Driver
from cotti_uvm.monitor import InputMonitor, OutputMonitor
from cotti_uvm.scoreboard import Scoreboard
from cotti_uvm.sequencer import Sequence, Sequencer


class Env(uvm_env):
    def __init__(self,
        parent,
        sequence: type[Sequence],
        coverage: type[Coverage] | None = None,
        end_delay_ns: int=50,
        name:str="env"):

        super().__init__(name, parent)
        self.sequence = sequence
        self.coverage = coverage
        self.end_delay_ns = end_delay_ns

    def build_phase(self):
        self.driver = Driver("driver", self)
        self.input_monitor = InputMonitor("input_monitor", self)
        self.output_monitor = OutputMonitor("output_monitor", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.sequencer = Sequencer("sequencer", self, self.sequence)

        if (self.coverage):
            self.coverage = self.coverage("coverage", self)
        else:
            self.logger.warning("No coverage was provided.")

        self.sequencer_end_get_port = uvm_get_port("sequencer_end_get_port", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)

        self.input_monitor.ap.connect(self.scoreboard.input_monitor_fifo.analysis_export)

        if (self.coverage):
            self.input_monitor.ap.connect(self.coverage.analysis_export)

        self.output_monitor.ap.connect(self.scoreboard.output_monitor_fifo.analysis_export)

        self.sequencer_end_get_port.connect(self.sequencer.fifo.get_export)

    async def run_phase(self):
        self.raise_objection()
        await self.sequencer_end_get_port.get()
        await Timer(self.end_delay_ns, "ns")
        self.drop_objection()