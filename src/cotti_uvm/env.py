"""UVM environment."""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
from __future__ import annotations

from typing import TYPE_CHECKING

from cocotb.triggers import Timer
from pyuvm import uvm_env, uvm_get_port

from cotti_uvm.driver import Driver
from cotti_uvm.monitor import InputMonitor, OutputMonitor
from cotti_uvm.scoreboard import Scoreboard
from cotti_uvm.sequencer import Sequence, Sequencer

if TYPE_CHECKING:
    from cotti_uvm.coverage import Coverage


class Env(uvm_env):
    """UVM environment."""

    def __init__(
        self,
        parent: object | None,
        sequence: type[Sequence],
        coverage: type[Coverage] | None = None,
        end_delay_ns: int = 50,
        name: str = "env",
    ) -> None:
        """Create an UVM environment."""
        super().__init__(name, parent)
        self.sequence = sequence
        self.coverage = coverage
        self.end_delay_ns = end_delay_ns

    def build_phase(self) -> None:
        """Instanciate all UVM components."""
        self.driver = Driver("driver", self)
        self.input_monitor = InputMonitor("input_monitor", self)
        self.output_monitor = OutputMonitor("output_monitor", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.sequencer = Sequencer("sequencer", self, self.sequence)

        if self.coverage:
            self.coverage = self.coverage("coverage", self)
        else:
            self.logger.warning("No coverage was provided.")

        self.sequencer_end_get_port = uvm_get_port("sequencer_end_get_port", self)

    def connect_phase(self) -> None:
        """Connect all analysis ports and classes with one another."""
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)

        self.input_monitor.ap.connect(self.scoreboard.input_monitor_fifo.analysis_export)

        if self.coverage:
            self.input_monitor.ap.connect(self.coverage.analysis_export)

        self.output_monitor.ap.connect(self.scoreboard.output_monitor_fifo.analysis_export)

        self.sequencer_end_get_port.connect(self.sequencer.fifo.get_export)

    async def run_phase(self) -> None:
        """Run phase main execution point from the UVM environment.

        Raises an objection to keep the run_phase() going, until the last
        sequencer transaction has been sent an `end_delay_ns` have passed.
        """
        self.raise_objection()
        await self.sequencer_end_get_port.get()
        await Timer(self.end_delay_ns, "ns")
        self.drop_objection()
