# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti
"""BFM: Bus functional model.

The BFM is responsible for direct access to the DUT's signals.
No other class in the whole UVM testbench is allowed to access the
DUT, or to wait on simulation time or clock edges.
"""

from abc import abstractmethod

import cocotb
import pyuvm
from cocotb.queue import Queue

from cotti_uvm.sequencer import Item


class Bfm(metaclass=pyuvm.Singleton):
    """BFM: Bus functional model base class.

    This is an abstract class, and each DUT must define its own BFM.
    """

    def __init__(self) -> None:
        """Create three queues for IO.

        1. `input_driver_queue`: Receives the input signal for the DUT.
        2. `input_monitor_queue`: Constantly reads the input, and puts in the
        queue any "transaction". A transaction is interpreted as a valid
        input which should generate a meaningful output.
        3. `output_monitor_queue`: Constantly reads the output, and puts in
        the queue the result of a "transaction".

        Also, starts the BFM co-routines in the background.

        The BFM consists of three processes:
        1. Input data injector.
        2. Input signals' monitor.
        3. Output signals' monitor.
        """
        self.dut = cocotb.top
        self.input_driver_queue = Queue(maxsize=1)
        self.input_monitor_queue = Queue(maxsize=0)
        self.output_monitor_queue = Queue(maxsize=0)

        cocotb.start_soon(self.input_driver())
        cocotb.start_soon(self.input_monitor())
        cocotb.start_soon(self.output_monitor())
        self.on_start()

    async def get_input(self) -> Item:
        """Retrieve the input transaction."""
        return await self.input_monitor_queue.get()

    async def get_output(self) -> object:
        """Retrieve the transaction's output result."""
        return await self.output_monitor_queue.get()

    async def set_input(self, value: object) -> None:
        """Send an input transaction to the DUT.

        The values received will be written to the DUT, but they might be seen
        by the input monitor if they are not a valid transaction.
        """
        await self.input_driver_queue.put(value)

    @abstractmethod
    def on_start(self) -> None:
        """Execute hook right after the BFM is created.

        That is, at the start of the `build_phase()` of the whole UVM testbench.

        In this hook you normally drive continuous or constant signals, e.g.
        the clock, but also add the DUT's parameters to the ConfigDB.

        Parameters must be defined here, since the BFM is the only one allowed
        to interact with the DUT.

        The following is a typical implementation that starts the clock and also
        sets the parameter `DATA_WIDTH` in the database.

        ```
        c = Clock(cocotb.top.clk, 2, "ns")
        c.start()
        config_db_set("DATA_WIDTH", self.dut.DATA_WIDTH.value)
        ```
        """

    @abstractmethod
    async def reset(self) -> None:
        """DUT's reset condition."""

    @abstractmethod
    async def input_driver(self) -> None:
        """Wait for sequence items to be fed from the `input_driver_queue` and excite the DUT.

        This function must fulfill two requisites:

        1. It must execute in a `while True:`, i.e., it must not exit.
        2. It retrieves sequence items by calling `self.input_driver_queue.get_nowait()`.

        A standard implementation looks as follows:
        ```
        self.dut.a.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                item = self.input_driver_queue.get_nowait()
            except QueueEmpty:
                continue
            self.dut.a.value = item.a
        ```
        """
        error_msg = "BFM must implement input_driver()."
        raise (NotImplementedError(error_msg))

    @abstractmethod
    async def input_monitor(self) -> None:
        """Read the DUT's input signals and send out any valid "transaction".

        Through the `self.input_monitor_queue`.

        Its the user's choice as to what a "valid transaction" entails, and
        its data type.

        This function must fulfill two requisites:

        1. It must execute in a `while True:`, i.e., it must not exit.
        2. It sends valid items to the input monitor by calling
        `self.input_monitor_queue.put_nowait(item)`.

        A standard implementation looks as follows:

        ```
        while True:
            await FallingEdge(self.dut.clk)
            if (bool(self.dut.new_cmd.value) == True):
                item = Item(self.dut.a.value)
                self.input_monitor_queue.put_nowait(item)
        ```
        """
        error_msg = "BFM must implement input_monitor()."
        raise (NotImplementedError(error_msg))

    @abstractmethod
    async def output_monitor(self) -> None:
        """Read the DUT's output signals and send out any valid "transaction".

        Through the `self.output_monitor_queue`.

        It is the user's choice as to what a "valid transaction" entails, and
        its data type.

        This function must fulfill two requisites:

        1. It must execute in a `while True:`, i.e., it must not exit.
        2. It sends valid items to the output monitor by calling
        `self.output_monitor_queue.put_nowait(item)`.

        A standard implementation looks as follows:

        ```
        while True:
            await FallingEdge(self.dut.clk)
            if (bool(self.dut.new_cmd_done.value) == True):
                self.output_monitor_queue.put_nowait(self.dut.out.value)
        ```
        """
        error_msg = "BFM must implement output_monitor()."
        raise (NotImplementedError(error_msg))
