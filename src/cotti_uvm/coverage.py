"""
Coverage

Coverage is tracked by the `coverage_set` received from the ConfigDB. The
`coverate_set` is a Python set, which must hold an enum type `set(<enum_type>)`.

The user will read the input transactions from the analysis port,
and add the specific transaction done to the coverage checklist.

Then, in the `report_phase()`, the checklist is compared against the whole
`coverage_set`, and the coverage percentage is determined.
"""

from abc import abstractmethod

from pyuvm import UVMConfigItemNotFound, uvm_subscriber

from cotti_uvm.common.help import config_db_get


class Coverage(uvm_subscriber):
    """Coverage reporter.

    Subscribes to an analysis port, and determines coverage goals in the
    report phase.

    It is an abstract class, the user must define the `write()` method.
    """
    def end_of_elaboration_phase(self):
        """Loads the `coverage_set` and the `coverage_percentage` from the
        ConfigDB
        """
        self.coverage_set = config_db_get("coverage_set")
        try:
            self.min_coverage_percentage = float(config_db_get("coverage_percentage"))
        except UVMConfigItemNotFound:
            self.min_coverage_percentage = 100.0

        self.coverage_checklist = set()

    def report_phase(self):
        """Checks whether the coverage percentage has been met.

        The test will fail if the coverage goal was not achieved.
        """
        percentage = (float(len(self.coverage_checklist)) / float(len(self.coverage_set))) * 100
        if (percentage < self.min_coverage_percentage):
            self.logger.error(
                f"Coverage error: {percentage:.2f}% / {self.min_coverage_percentage:.2f}%.\n"
                f"Missed: {self.coverage_set - self.coverage_checklist}"
            )
            assert False
        else:
            self.logger.info(
                f"Coverage OK: {percentage:.2f}% / {self.min_coverage_percentage:.2f}%"
            )
            assert True

    @abstractmethod
    def write(self, value):
        """Given the input `value`, this function should determine if any
         element from the `coverage_set` has been fulfilled, and it to the
         `self.coverage_checklist`
        """
        raise (NotImplementedError)

