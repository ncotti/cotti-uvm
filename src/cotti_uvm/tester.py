# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
import inspect

from pyuvm import uvm_test

from cotti_uvm.bfm import Bfm
from cotti_uvm.common.help import config_db_set
from cotti_uvm.env import Env
from cotti_uvm.sequencer import Sequence


class Tester(uvm_test):
    bfm = None
    golden_ref = None
    sequence = None
    coverage = None
    end_delay_ns = 1

    def build_phase(self):
        """Build phase for the tests.

        Here, only the environment should be instantiated.
        """
        self._check_attributes()

        # Let the tester create the first instance of the BFM, so anything
        # that was defined in its `on_start()` can be seen in other build phases.
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

    def _check_attributes(self):
        """Checks that whichever class inherits this one defines
        valid parameters
        """
        # `bfm` is a subclass of `Bfm`
        if not (isinstance(self.bfm, type) and issubclass(self.bfm, Bfm)):
            raise (
                TypeError(
                    'When creating a tester, "bfm" should be a class inherited from "Bfm".'
                )
            )

        # `golden_ref` is defined and is a callable function
        if self.golden_ref is None:
            raise (TypeError("Golden reference function must be defined"))

        # Sequence must be defined
        if not (
            isinstance(self.sequence, type)
            and issubclass(self.sequence, Sequence)
        ):
            raise (TypeError("A sequence must be provided."))

        # Delay must be at least 1ns
        self.end_delay_ns = self.end_delay_ns if (self.end_delay_ns > 0) else 1
