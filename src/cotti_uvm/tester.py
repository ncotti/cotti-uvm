# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""Tester.

Top-level test representation for an UVM testbench.
"""

import inspect
import logging

from pyuvm import uvm_test

from cotti_uvm.bfm import Bfm
from cotti_uvm.common.help import config_db_set
from cotti_uvm.env import Env
from cotti_uvm.sequencer import Sequence


class Tester(uvm_test):
    """Generic UVM test.

    This is the "main" test module. A user should only provide the values
    for the attributes and the whole UVM environment will be generated for you.

    E.g.:
    ```
    @pyuvm.test()
    class MyTest(Tester):
        bfm = MyBfm
        golden_ref = golden_ref
        sequence = MySeq
        coverage = MyCoverage
    ```
    """

    bfm = None
    golden_ref = None
    sequence = None
    coverage = None
    end_delay_ns = 10
    log_level = logging.INFO

    def build_phase(self) -> None:
        """Build phase for the tests.

        Here, only the environment should be instantiated.
        """
        self._check_attributes()

        # Let the tester create the first instance of the BFM, so anything that
        # was defined in its `on_start()` can be seen in other build phases.
        config_db_set("bfm", self.bfm)
        self.bfm()

        golden_ref = inspect.getattr_static(self, "golden_ref")
        config_db_set("golden_ref", golden_ref)

        self.env = Env(
            self,
            sequence=self.sequence,
            coverage=self.coverage,
            end_delay_ns=self.end_delay_ns,
        )

    def end_of_elaboration_phase(self) -> None:
        """Set log level."""
        self.set_logging_level_hier(self.log_level)

    def _check_attributes(self) -> None:
        """Check whether the attributes' values are valid."""
        # `bfm` is a subclass of `Bfm`
        if not (isinstance(self.bfm, type) and issubclass(self.bfm, Bfm)):
            error_str = "When creating a tester, "
            '"bfm" should be a class inherited from "Bfm".'
            raise (TypeError(error_str))

        # `golden_ref` is defined and is a callable function
        if self.golden_ref is None:
            error_str = "Golden reference function must be defined"
            raise (TypeError(error_str))

        # Sequence must be defined, either as a single Sequence type, or a list
        # of Sequence types
        if (not (isinstance(self.sequence, type) and issubclass(self.sequence, Sequence))) and (
            not (
                isinstance(self.sequence, list)
                and len(self.sequence) > 0
                and issubclass(self.sequence[0], Sequence)
            )
        ):
            error_str = "A sequence must be provided."
            raise (TypeError(error_str))

        # Delay must be at least 1ns
        self.end_delay_ns = self.end_delay_ns if (self.end_delay_ns > 0) else 1
