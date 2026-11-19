# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""Coverage.

Coverage is tracked by the `coverage_set` received from the ConfigDB. The
`coverage_set` is a Python set, which must hold an enum type `set(<enum_type>)`.

The user will read the input transactions from the analysis port,
and add the specific transaction done to the coverage checklist.

Then, in the `report_phase()`, the checklist is compared against the whole
`coverage_set`, and the coverage percentage is determined.
"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from pyuvm import uvm_sequence_item, uvm_subscriber

if TYPE_CHECKING:
    from cotti_uvm.sequencer import Item

MAX_PERCENTAGE = 100.0


class Coverage(uvm_subscriber):
    """Coverage reporter.

    Subscribes to an analysis port, and determines coverage goals in the
    report phase.

    It is an abstract class, the user must define the `write()` method.
    """

    # Minimum coverage required for the test to pass
    min_coverage_percentage: float = MAX_PERCENTAGE
    coverage_enum: Enum = None

    def _check_attributes(self) -> None:
        if self.min_coverage_percentage < 0 or self.min_coverage_percentage > MAX_PERCENTAGE:
            error_msg = f"0 <= coverage_percentage <= 100, but was {self.min_coverage_percentage}."
            raise (ValueError(error_msg))

        if not (isinstance(self.coverage_enum, type) and issubclass(self.coverage_enum, Enum)):
            error_msg = f"Coverage set must be an Enum, but is {type(self.coverage_enum)}"
            raise (TypeError(error_msg))

    def build_phase(self) -> None:
        """Check that all attributes are ok, and create coverage set from enum."""
        self._check_attributes()
        self.coverage = set(self.coverage_enum)
        self.coverage_checklist = set()

    def report_phase(self) -> None:
        """Check whether the coverage percentage has been met.

        The test will fail if the coverage goal was not achieved.
        """
        percentage = (float(len(self.coverage_checklist)) / float(len(self.coverage))) * 100
        if percentage < self.min_coverage_percentage:
            error_str = (
                f"Coverage error: {percentage:.2f}% / "
                f"{self.min_coverage_percentage:.2f}%.\n"
                f"Missed: {self.coverage - self.coverage_checklist}"
            )

            self.logger.error(error_str)
            raise AssertionError(error_str)

        self.logger.info("Coverage OK: %.2f%% / %.2f%%", percentage, self.min_coverage_percentage)

    @abstractmethod
    def item_to_coverage(self, item: uvm_sequence_item) -> Enum | list[Enum] | None:
        """Read the item provided and return which coverage case is representing, or `None`.

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
        error_str = "Coverage must implement the item_to_coverage() method."
        raise (NotImplementedError(error_str))

    def write(self, item: Item) -> None:
        """Is called whenever a new element arrives from the analysis port.

        It is mandatory for any `uvm_subscriber`.
        """
        coverage_list = self.item_to_coverage(item)
        if coverage_list:
            if coverage_list is list:
                for element in coverage_list:
                    self.coverage_checklist.add(element)
            else:
                self.coverage_checklist.add(coverage_list)
