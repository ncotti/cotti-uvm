# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""
Driver

The driver exposes a `seq_item_port` from where it receives sequence items,
which then sends to the DUT through the BFM.

The only thing the driver needs is a copy of the BFM, which
must be put by the environment during its `build_phase()` in the ConfigDB.
"""

from pyuvm import uvm_driver

from cotti_uvm.common.help import config_db_get


class Driver(uvm_driver):
    """
    The driver is responsible for getting sequence items and feeding them
    to the DUT through the BFM (Bus Functional Model).
    """

    def start_of_simulation_phase(self):
        """Get a valid BFM before starting the `run_phase()`."""
        self.bfm = config_db_get("bfm")()

    async def run_phase(self):
        """Perform the following actions, as defined in the BFM:

        1. Reset the DUT.
        2. Start the BFM coroutines.
        3. Receive sequence items and send them to the BFM.
        """
        await self.bfm.reset()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.set_input(cmd)
            self.seq_item_port.item_done()
