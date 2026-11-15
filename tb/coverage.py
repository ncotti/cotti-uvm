from pyuvm import *
from common.tinyalu_ref import *
from common.help import *

class Coverage(uvm_subscriber):
    """Coverage reporter.

    Subscribes to an analysis port, and determines coverage goals in the
    report phase.
    """
    def end_of_elaboration_phase(self):

        self.coverage_set = config_db_get("coverage_set")
        self.cvg = set()

    def write(self, cmd):
        self.cvg.add(cmd.mode)

    def report_phase(self):
        if len(self.coverage_set - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {self.coverage_set - self.cvg}")
            assert False
        else:
            self.logger.info("Covered all operations")
            assert True
