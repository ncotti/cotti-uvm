## Golden reference model for the tinyALU module.

from dataclasses import dataclass
from enum import IntEnum

class AluMode(IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4

@dataclass(slots=True)
class AluInput:
    aa: int = 0
    bb: int = 0
    mode: AluMode = AluMode.ADD

def dut_golden_ref(op: AluInput):
    """DUT golden reference model"""
    if op.mode == AluMode.ADD:
        result = op.aa + op.bb
    elif op.mode == AluMode.AND:
        result = op.aa & op.bb
    elif op.mode == AluMode.XOR:
        result = op.aa ^ op.bb
    elif op.mode == AluMode.MUL:
        result = op.aa * op.bb
    return result
