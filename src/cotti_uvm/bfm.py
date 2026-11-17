"""
BFM: Bus functional model

The BFM is responsible for direct access to the DUT's signals.
No other class in the whole UVM testbench is allowed to access the
DUT, or to wait on simulation time or clock edges.
"""

from abc import abstractmethod

import cocotb
import pyuvm
from cocotb.queue import Queue


class Bfm(metaclass=pyuvm.Singleton):
    """BFM: Bus functional model base class.

    This is an abstract class, and each DUT must define its own BFM.
    """
    def __init__(self):
        """Creates three queues for IO:

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

    async def get_input(self):
        """Retrieves the input transaction"""
        cmd = await self.input_monitor_queue.get()
        return cmd

    async def get_output(self):
        """Retrieves the transaction's output result"""
        result = await self.output_monitor_queue.get()
        return result

    async def set_input(self, value:object) -> None:
        """Sends an input transaction to the DUT.

        The values received will be written to the DUT, but they might be seen
        by the input monitor if they are not a valid transaction.
        """
        await self.input_driver_queue.put(value)

    @abstractmethod
    def on_start(self):
        """Hook to be exectued right after the BFM is created.

        In this hook you normally place continous or constant signals, such
        as a clock.
        """

    @abstractmethod
    async def reset(self):
        """DUT's reset condition."""

    @abstractmethod
    async def input_driver(self):
        """Waits for sequence items to be fed from the `input_driver_queue()`
        and excites the DUT.
        """
        raise (NotImplementedError)

    @abstractmethod
    async def input_monitor(self):
        """Reads the DUT's input signals and sends out any valid "transaction"
        through the `self.input_monitor_queue`.

        Its the user's choice as to what a "valid transaction" entails, and
        its data type.
        """
        raise (NotImplementedError)

    @abstractmethod
    async def output_monitor(self):
        """Reads the DUT's output signals and sends out any valid "transaction"
        through the `self.output_monitor_queue`.

        It is the user's choice as to what a "valid transaction" entails, and
        its data type.
        """
        raise (NotImplementedError)
