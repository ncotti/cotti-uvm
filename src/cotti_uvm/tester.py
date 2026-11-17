from abc import abstractmethod

from pyuvm import uvm_test
from cotti_uvm.env import Env
import inspect
from cotti_uvm.bfm import Bfm
from cotti_uvm.common.help import config_db_set

class Tester(uvm_test):

    bfm = None
    golden_ref = None
    sequence_type = None
    coverage = None
    coverage_set = None
    coverage_percentage = 100.0
    end_delay_ns = 1

    def build_phase(self):
        """Build phase for the tests.

        Here, only the environment should be instantiated.
        """
        self._check_attributes()

        config_db_set("coverage_set", self.coverage_set)
        config_db_set("coverage_percentage", self.coverage_percentage)
        golden_ref = inspect.getattr_static(self, "golden_ref")

        self.env = Env(self,
            bfm=self.bfm(),
            golden_ref=golden_ref,
            sequence_type=self.sequence_type,
            coverage_type=self.coverage,
            end_delay_ns=self.end_delay_ns
        )

    def _check_attributes(self):
        """Checks that whichever class inherits this one defines
        valid parameters
        """
        # `bfm` is a subclass of `Bfm`
        if not (isinstance(self.bfm, type) and issubclass(self.bfm, Bfm)):
            raise(TypeError("When creating a tester, \"bfm\" should be a class inherited from \"Bfm\"."))

        # `golden_ref` is defined and is a callable function
        if self.golden_ref is None:
            raise(TypeError("Golden reference function must be defined"))

        # Delay must be at least 1ns
        self.end_delay_ns = self.end_delay_ns if (self.end_delay_ns > 0) else 1

