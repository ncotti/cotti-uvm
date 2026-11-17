from __future__ import annotations

from collections.abc import Callable

from cocotb.triggers import Timer
from pyuvm import uvm_env, uvm_get_port, uvm_sequence_item

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
        bfm: Bfm,
        golden_ref: Callable[[uvm_sequence_item], object],
        sequence_type: type[Sequence],
        name:str="env",
        coverage_type: type[Coverage] | None = None,
        coverage_set: set | None = None,
        coverage_percentage: float=100.0,
        end_delay_ns: int=50):

        super().__init__(name, parent)
        self.bfm = bfm
        self.golden_ref = golden_ref
        self.sequence_type = sequence_type
        self.coverage_type = coverage_type
        self.coverage_set = coverage_set
        self.coverage_percentage = coverage_percentage
        self.end_delay_ns = end_delay_ns if (end_delay_ns > 0) else 1

    def build_phase(self):
        config_db_set("coverage_set", self.coverage_set)
        config_db_set("bfm", self.bfm)
        config_db_set("coverage_percentage", self.coverage_percentage)
        config_db_set("golden_ref", self.golden_ref)

        self.driver = Driver("driver", self)
        self.input_monitor = InputMonitor("input_monitor", self)
        self.output_monitor = OutputMonitor("output_monitor", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.sequencer = Sequencer("sequencer", self, self.sequence_type)

        if (self.coverage_type and self.coverage_set):
            self.coverage = self.coverage_type("coverage", self)
        else:
            self.logger.warning("No coverage was provided.")

        self.sequencer_end_get_port = uvm_get_port("sequencer_end_get_port", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)

        self.input_monitor.ap.connect(self.scoreboard.input_monitor_fifo.analysis_export)

        if (self.coverage_set):
            self.input_monitor.ap.connect(self.coverage.analysis_export)

        self.output_monitor.ap.connect(self.scoreboard.output_monitor_fifo.analysis_export)

        self.sequencer_end_get_port.connect(self.sequencer.fifo.get_export)

    async def run_phase(self):
        self.raise_objection()
        await self.sequencer_end_get_port.get()
        await Timer(self.end_delay_ns, "ns")
        self.drop_objection()