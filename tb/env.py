from collections.abc import Callable

from bfm import Bfm
from common.help import config_db_set
from coverage import Coverage
from driver import Driver
from monitor import InputMonitor, OutputMonitor
from pyuvm import uvm_env, uvm_sequence_item
from scoreboard import Scoreboard
from sequencer import Sequencer


class Env(uvm_env):
    def __init__(self,
        parent,
        bfm: Bfm,
        golden_ref: Callable[[uvm_sequence_item], object],
        name:str="env",
        coverage_set: set | None = None,
        coverage_percentage: float=100.0):

        super().__init__(name, parent)
        self.bfm = bfm
        self.golden_ref = golden_ref
        self.coverage_set = coverage_set
        self.coverage_percentage = coverage_percentage

    def build_phase(self):
        config_db_set("coverage_set", self.coverage_set)
        config_db_set("bfm", self.bfm)
        config_db_set("coverage_percentage", self.coverage_percentage)
        config_db_set("golden_ref", self.golden_ref)

        self.driver = Driver("driver", self)
        self.input_monitor = InputMonitor("input_monitor", self)
        self.output_monitor = OutputMonitor("output_monitor", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.sequencer = Sequencer("sequencer", self)

        if (self.coverage_set):
            self.coverage = Coverage.create("coverage", self)
        else:
            self.logger.warning("No coverage was provided.")

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)

        self.input_monitor.ap.connect(self.scoreboard.input_monitor_fifo.analysis_export)

        if (self.coverage_set):
            self.input_monitor.ap.connect(self.coverage.analysis_export)

        self.output_monitor.ap.connect(self.scoreboard.output_monitor_fifo.analysis_export)