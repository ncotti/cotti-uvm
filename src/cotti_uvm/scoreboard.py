# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""Scoreboard.

The scoreboard has two analysis ports, one from the input monitor and one
from the output monitor.

Its job is to read the input, use the DUT's golden reference to get the
expected output, and then compare it with the actual output.
"""

from pyuvm import (
    UVMConfigItemNotFound,
    uvm_get_port,
    uvm_scoreboard,
    uvm_tlm_analysis_fifo,
)

from cotti_uvm.common.help import config_db_get
from cotti_uvm.sequencer import Item


class Scoreboard(uvm_scoreboard):
    """Compare the DUT's output with the expected output."""

    def build_phase(self) -> None:
        """Create two analysis fifos.

        One for the input analysis export and one for the output. Then,
        create two get ports to connect to those fifos from inside.
        """
        self.input_monitor_fifo = uvm_tlm_analysis_fifo("input_monitor_fifo", self)
        self.output_monitor_fifo = uvm_tlm_analysis_fifo("output_monitor_fifo", self)

        self.input_get_port = uvm_get_port("input_get_port", self)
        self.output_get_port = uvm_get_port("output_get_port", self)

    def connect_phase(self) -> None:
        """Connect TLM FIFOs `get_export`s to the Scoreboard's internal `get_port`s."""
        self.input_get_port.connect(self.input_monitor_fifo.get_export)
        self.output_get_port.connect(self.output_monitor_fifo.get_export)

    def end_of_elaboration_phase(self) -> None:
        """Get the golden reference model from the ConfigDB."""
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

    def check_phase(self) -> None:
        """Compare expected vs. actual output.

        Get an element from the input, run it through the golden
        reference model, read and element from the output, and then compare
        expected vs. actual output values.
        """
        while self.input_get_port.can_get():
            _, item = self.input_get_port.try_get()
            expected_output = self.golden_ref(item)

            ok, output = self.output_get_port.try_get()
            if not ok:
                self.logger.warning("Input %s didn't have an associated output.", item)
                continue

            if expected_output == output:
                self.logger.debug(self.on_pass(item, output))
                self.passed_count += 1
            else:
                self.logger.error(self.on_fail(item, output, expected_output))
                self.failed_count += 1

    def report_phase(self) -> None:
        """Check the amount failed and passed tests.

        Fails the test on anything other than a perfect score (0 errors).
        """
        self.logger.info(
            "Total tests: %d\nPassed: %d\nFailed: %d",
            self.passed_count + self.failed_count,
            self.passed_count,
            self.failed_count,
        )

        if self.failed_count > 0:
            error_str = f"Failed tests: {self.failed_count}"
            self.logger.error(error_str)

            raise AssertionError(error_str)

    @staticmethod
    def default_on_pass(input_arg: Item, output: object) -> str:
        """Default string to be printed when output and expected output match."""
        return f"PASSED:\nInput: {input_arg}\nOutput: {output}\n"

    @staticmethod
    def default_on_fail(input_arg: Item, output: object, expected_output: object) -> str:
        """Default string to be printed when output and expected output differ."""
        return f"FAILED:\nInput: {input_arg}\nOutput: {output}\nExpected output: {expected_output}"
