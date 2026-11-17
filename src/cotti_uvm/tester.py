from abc import abstractmethod

from pyuvm import uvm_test


class Tester(uvm_test):
    @abstractmethod
    def build_phase(self):
        """Build phase for the tests.

        Here, only the environment should be instantiated.
        """
        raise(NotImplementedError)

    @abstractmethod
    async def run_phase(self):
        """Mock run_phase().
        The user might re-implement this function to add anything to the
        testbench.
        """
        self.raise_objection()
        self.drop_objection()
