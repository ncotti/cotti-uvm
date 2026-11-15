from pyuvm import *
from bfm import *

class InputMonitor(uvm_component):
    """Reads the BFM input and posts it through an analysis port."""
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.bfm = TinyAluBfm()

    def build_phase(self):
        """Create the analysis port"""
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """Wait for an input transaction to be published from the BFM, and
            write it to the analysis port."""
        while True:
            datum = await self.bfm.get_cmd()
            self.ap.write(datum)

class OutputMonitor(uvm_component):
    """Reads the BFM output and posts it through an analysis port."""
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.bfm = TinyAluBfm()

    def build_phase(self):
        """Create the analysis port"""
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """Wait for an output result to be published from the BFM, and
        write it to the analysis port."""
        while True:
            datum = await self.bfm.get_result()
            self.ap.write(datum)
