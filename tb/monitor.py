from pyuvm import *
from common.help import *

class InputMonitor(uvm_component):
    """Reads the BFM input and posts it through an analysis port."""

    def end_of_elaboration_phase(self):
        self.bfm = config_db_get("bfm")

    def build_phase(self):
        """Create the analysis port"""
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """Wait for an input transaction to be published from the BFM, and
            write it to the analysis port."""
        while True:
            datum = await self.bfm.get_input()
            self.ap.write(datum)

class OutputMonitor(uvm_component):
    """Reads the BFM output and posts it through an analysis port."""
    def end_of_elaboration_phase(self):
        self.bfm = config_db_get("bfm")

    def build_phase(self):
        """Create the analysis port"""
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """Wait for an output result to be published from the BFM, and
        write it to the analysis port."""
        while True:
            datum = await self.bfm.get_output()
            self.ap.write(datum)
