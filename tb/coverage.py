from pyuvm import *
from common.tinyalu_ref import *

class Coverage(uvm_subscriber):

    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        self.cvg.add(cmd.mode)

    def report_phase(self):
        if len(set(AluMode) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(AluMode)-self.cvg}")
            assert False
        else:
            self.logger.info("Covered all operations")
            assert True
