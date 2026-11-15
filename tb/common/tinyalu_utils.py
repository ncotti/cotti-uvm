import cocotb
from cocotb.triggers import FallingEdge
from cocotb.queue import QueueEmpty, Queue
import enum
import pyuvm

from dataclasses import dataclass


@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


def alu_prediction(A, B, op):
    """Python model of the TinyALU"""
    assert isinstance(op, Ops), "The tinyalu op must be of type Ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    return result


@dataclass(slots=True)
class AluInput:
    aa: int = 0
    bb: int = 0
    mode: Ops = Ops.ADD


class TinyAluBfm(metaclass=pyuvm.Singleton):
    """BFM: Bus functional model

    The BFM is responsible for direct access to the DUT's signals.
    No other class in the whole UVM testbench is allowed to access the
    DUT, or to wait on simulation time or clock edges.
    """
    def __init__(self):
        """Creates three queues for IO:

        1. `cmd_driver_queue`: [in] Receives the input signal for the DUT.
        2. `cmd_mon_queue`: [out] Constantly reads the input, and puts in the
        queue any valid input arguments.
        3. `result_mon_queue`: [out] Constantly reads the output, and puts in
        the queue any valid result.
        """
        self.dut = cocotb.top
        self.cmd_driver_queue = Queue(maxsize=1)
        self.cmd_mon_queue = Queue(maxsize=0)
        self.result_mon_queue = Queue(maxsize=0)

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 1

    async def result_mon(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            done = int(self.dut.done.value)
            if prev_done == 0 and done == 1:
                result = int(self.dut.result.value)
                self.result_mon_queue.put_nowait(result)
            prev_done = done


    async def cmd_mon(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            start = int(self.dut.start.value)
            if start == 1 and prev_start == 0:
                cmd_tuple = (int(self.dut.A.value),
                             int(self.dut.B.value),
                             int(self.dut.op.value))
                self.cmd_mon_queue.put_nowait(cmd_tuple)
            prev_start = start


    async def cmd_driver(self):
        self.dut.start.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            st = int(self.dut.start.value)
            dn = int(self.dut.done.value)
            if st == 0 and dn == 0:
                try:
                    op = self.cmd_driver_queue.get_nowait()
                    self.dut.A.value = op.aa
                    self.dut.B.value = op.bb
                    self.dut.op.value = op.mode
                    self.dut.start.value = 1
                except QueueEmpty:
                    continue
            elif st == 1 and dn == 1:
                self.dut.start.value = 0

    def start(self):
        """Starts the BFM co-routines in the background.

        The BFM consists of three processes:
        1. Input data injector.
        2. Monitor of input arguments.
        3. Monitor of output results.
        """
        cocotb.start_soon(self.cmd_driver())
        cocotb.start_soon(self.cmd_mon())
        cocotb.start_soon(self.result_mon())

    async def get_cmd(self):
        """Retrieves the input command"""
        cmd = await self.cmd_mon_queue.get()
        return cmd

    async def get_result(self):
        """Retrieves the output result"""
        result = await self.result_mon_queue.get()
        return result

    async def send_op(self, op:AluInput) -> None:
        """Sends an input transaction to the DUT"""
        await self.cmd_driver_queue.put(op)