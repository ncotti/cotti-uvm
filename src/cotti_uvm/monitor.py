# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""
Monitor

A monitor purpose is to interact with the BFM and generate analysis ports
for other parts of the UVM testbench to analyze the data.

Two basic monitors are provided, which read the input and output signals
from the BFM.

The only thing the monitor needs is a copy of the BFM, which
must be put by the environment during its `build_phase()` in the ConfigDB.
"""

from pyuvm import uvm_analysis_port, uvm_monitor

from cotti_uvm.common.help import config_db_get


class InputMonitor(uvm_monitor):
    """Reads the BFM input and posts it through an analysis port."""

    def end_of_elaboration_phase(self):
        self.bfm = config_db_get("bfm")()

    def build_phase(self):
        """Create the analysis port"""
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """Wait for an input transaction to be published from the BFM, and
        write it to the analysis port."""
        while True:
            datum = await self.bfm.get_input()
            self.ap.write(datum)


class OutputMonitor(uvm_monitor):
    """Reads the BFM output and posts it through an analysis port."""

    def end_of_elaboration_phase(self):
        self.bfm = config_db_get("bfm")()

    def build_phase(self):
        """Create the analysis port"""
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """Wait for an output result to be published from the BFM, and
        write it to the analysis port."""
        while True:
            datum = await self.bfm.get_output()
            self.ap.write(datum)
