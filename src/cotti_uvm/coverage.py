# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""
Coverage

Coverage is tracked by the `coverage_set` received from the ConfigDB. The
`coverage_set` is a Python set, which must hold an enum type `set(<enum_type>)`.

The user will read the input transactions from the analysis port,
and add the specific transaction done to the coverage checklist.

Then, in the `report_phase()`, the checklist is compared against the whole
`coverage_set`, and the coverage percentage is determined.
"""
from __future__ import annotations

from abc import abstractmethod

from pyuvm import uvm_subscriber, uvm_sequence_item
from enum import Enum


class Coverage(uvm_subscriber):
    """Coverage reporter.

    Subscribes to an analysis port, and determines coverage goals in the
    report phase.

    It is an abstract class, the user must define the `write()` method.
    """

    # Minimum coverage required for the test to pass
    min_coverage_percentage :float = 100.0
    coverage_enum: Enum = None

    def _check_attributes(self):
        if (self.min_coverage_percentage < 0 or self.min_coverage_percentage > 100):
            raise(ValueError(f"0 <= coverage_percentage <= 100, but was {self.min_coverage_percentage}."))

        if not (isinstance(self.coverage_enum, type) and issubclass(self.coverage_enum, Enum)):
            raise(TypeError(f"Coverage set must be an Enum, but is {type(self.coverage_enum)}"))

    def build_phase(self):
        self._check_attributes()
        self.coverage = set(self.coverage_enum)
        self.coverage_checklist = set()

    def report_phase(self):
        """Checks whether the coverage percentage has been met.

        The test will fail if the coverage goal was not achieved.
        """
        percentage = (float(len(self.coverage_checklist)) / float(len(self.coverage))) * 100
        if (percentage < self.min_coverage_percentage):
            self.logger.error(
                f"Coverage error: {percentage:.2f}% / {self.min_coverage_percentage:.2f}%.\n"
                f"Missed: {self.coverage - self.coverage_checklist}"
            )
            assert False
        else:
            self.logger.info(
                f"Coverage OK: {percentage:.2f}% / {self.min_coverage_percentage:.2f}%"
            )

    @abstractmethod
    def item_to_coverage(self, item: uvm_sequence_item) -> Enum | None:
        """This function must read the item provided and return which
        coverage case is representing, or `None`.

        The following is an example that checks whether the input argument "a"
        was tested for negative, positive and zero values:

        ```
        if (item.a == 0):
            return ZERO_COVERAGE
        elif (item.a < 0)
            return NEGATIVE_COVERAGE
        elif (item.a > 0)
            return POSITIVE_COVERAGE
        ```
        """
        raise (NotImplementedError("Coverage must implement the item_to_coverage() method."))

    @abstractmethod
    def write(self, item):
        """The write method is called whenever a new element arrives from the
        analysis port.
        """
        coverage_element = self.item_to_coverage(item)
        if (coverage_element is not None):
            self.coverage_checklist.add(coverage_element)

