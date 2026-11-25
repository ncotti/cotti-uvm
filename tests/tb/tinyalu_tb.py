# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import logging
import random
from enum import IntEnum

import cocotb
import pyuvm
from cocotb.clock import Clock
from cocotb.queue import QueueEmpty
from cocotb.triggers import FallingEdge, Timer

from cotti_uvm import Bfm, Coverage, Item, Sequence, Tester


class AluMode(IntEnum):
    """Legal ops for the TinyALU."""

    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


class AluSeqItem(Item):
    """TinyAlu sequence item"""

    def __init__(self, a: int = 0, b: int = 0, mode: AluMode = AluMode.ADD):
        super().__init__("alu_sequence_item")
        self.a = a
        self.b = b
        self.mode = mode

    async def delay(self, item) -> None:
        await Timer(20, "ns")

    def __eq__(self, other):
        return (
            (self.a == other.a)
            and (self.b == other.b)
            and (self.mode == other.mode)
        )

    def __str__(self):
        return (f"{self.get_name()}: A: 0x{self.a:02x} "
        f"OP: {self.mode.name} ({self.mode.value}) B: 0x{self.b:02x}")


def golden_ref(op: AluSeqItem):
    """DUT's golden reference model"""
    if op.mode == AluMode.ADD:
        result = op.a + op.b
    elif op.mode == AluMode.AND:
        result = op.a & op.b
    elif op.mode == AluMode.XOR:
        result = op.a ^ op.b
    elif op.mode == AluMode.MUL:
        result = op.a * op.b
    return result


class TinyAluBfm(Bfm):
    """TinyAlu BFM"""

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 1

    def on_start(self):
        c = Clock(cocotb.top.clk, 4, "ns")
        c.start()

    async def input_driver(self) -> None:
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
                    op = self.input_driver_queue.get_nowait()
                    self.dut.A.value = op.a
                    self.dut.B.value = op.b
                    self.dut.op.value = op.mode
                    self.dut.start.value = 1
                except QueueEmpty:
                    continue
            elif st == 1 and dn == 1:
                self.dut.start.value = 0

    async def input_monitor(self) -> None:
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            start = int(self.dut.start.value)
            if start == 1 and prev_start == 0:
                cmd_tuple = AluSeqItem(
                    int(self.dut.A.value),
                    int(self.dut.B.value),
                    AluMode(self.dut.op.value),
                )
                self.input_monitor_queue.put_nowait(cmd_tuple)
            prev_start = start

    async def output_monitor(self) -> None:
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            done = int(self.dut.done.value)
            if prev_done == 0 and done == 1:
                result = int(self.dut.result.value)
                self.output_monitor_queue.put_nowait(result)
            prev_done = done


class TinyAluCoverage(Coverage):
    """Coverage for the TinyAlu."""

    coverage_enum = AluMode
    min_coverage_percentage = 100

    def item_to_coverage(self, item:AluSeqItem, output) -> AluMode:
        return item.mode


class RandomSeq(Sequence):
    def items(self) -> list[AluSeqItem]:
        out = []
        for mode in list(AluMode):
            item = AluSeqItem(
                a=random.randint(0, 255), b=random.randint(0, 255), mode=mode
            )
            out.append(item)
        return out


class MaxSeq(Sequence):
    def items(self) -> list[AluSeqItem]:
        out = []
        for mode in list(AluMode):
            item = AluSeqItem(a=0xFF, b=0xFF, mode=mode)
            out.append(item)
        return out

class ShortSeq(Sequence):
    def items(self):
        return [AluSeqItem(a=0xAA, b=0xBB, mode=AluMode.ADD)]


@pyuvm.test()
class RandomTest(Tester):
    bfm = TinyAluBfm
    golden_ref = golden_ref
    sequence = RandomSeq
    coverage = TinyAluCoverage
    end_delay_ns = 40
    log_level = logging.INFO


@pyuvm.test()
class MaxTest(Tester):
    bfm = TinyAluBfm
    golden_ref = golden_ref
    sequence = [MaxSeq, RandomSeq, ShortSeq]
    coverage = TinyAluCoverage
    end_delay_ns = 40
    log_level = logging.DEBUG
