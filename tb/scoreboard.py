"""
Scoreboard

The scoreboard has two analysis ports, one from the input monitor and one
from the output monitor.

Its job is to read the input, use the DUT's golden reference to get the
expected output, and then compare it with the actual output.
"""

from common.help import config_db_get
from pyuvm import (
    UVMConfigItemNotFound,
    uvm_get_port,
    uvm_scoreboard,
    uvm_tlm_analysis_fifo,
)


class Scoreboard(uvm_scoreboard):
    """
    Compares the DUT's output with the expected output.
    """

    def build_phase(self):
        """
        Creates two analysis fifos, one for the input analysis export
        and one for the output.

        Then, it creates two get ports to connect to those fifos from inside.
        """
        self.input_monitor_fifo = uvm_tlm_analysis_fifo("input_monitor_fifo", self)
        self.output_monitor_fifo = uvm_tlm_analysis_fifo("output_monitor_fifo", self)

        self.input_get_port = uvm_get_port("input_get_port", self)
        self.output_get_port = uvm_get_port("output_get_port", self)

    def connect_phase(self):
        """
        Connect TLM FIFOs `get_export`s to the Scoreboard's internal `get_port`s.
        """
        self.input_get_port.connect(self.input_monitor_fifo.get_export)
        self.output_get_port.connect(self.output_monitor_fifo.get_export)

    def end_of_elaboration_phase(self):
        """Get the golden reference model from the ConfigDB"""
        self.golden_ref = config_db_get("golden_ref")
        try:
            self.on_pass = config_db_get("scoreboard_on_pass")
        except UVMConfigItemNotFound:
            self.on_pass = Scoreboard.default_on_pass

        try:
            self.on_fail = config_db_get("scoreboard_on_fail")
        except UVMConfigItemNotFound:
            self.on_fail = Scoreboard.default_on_fail

        self.passed_count = 0
        self.failed_count = 0

    def check_phase(self):
        """Gets an element from the input, runs it through the golden
        reference model, reads and element from the output, and then compares
        expected vs. actual output values.
        """
        while self.input_get_port.can_get():
            _, input = self.input_get_port.try_get()
            expected_output = self.golden_ref(input)

            ok, output = self.output_get_port.try_get()
            if not ok:
                self.logger.warning(
                    f"Input {input} didn't have an associated output."
                )
                continue

            if expected_output == output:
                self.logger.debug(self.on_pass(input, output))
                self.passed_count += 1
            else:
                self.logger.error(self.on_fail(input, output, expected_output))
                self.failed_count += 1


    def report_phase(self):
        """Checks the amount failed and passed tests.

        Fails the test on anything other than a perfect score (0 errors)
        """
        self.logger.info(
            f"Total tests: {self.passed_count + self.failed_count}\n"
            f"Passed: {self.passed_count}. Failed: {self.failed_count}"
        )

        if (self.failed_count > 0):
            self.logger.error(f"Failed tests: {self.failed_count}")
            assert False

    def default_on_pass(input, output) -> str:
        """Default string to be printed when output and expected output match"""
        return (
            f"PASSED:\n"
            f"Input: {input}\n"
            f"Output: {output}\n"
        )

    def default_on_fail(input, output, expected_output) -> str:
        """Default string to be printed when the output and expected output differ"""
        return (
            f"FAILED:\n"
            f"Input: {input}\n"
            f"Output: {output}\n"
            f"Expected output: {expected_output}"
        )