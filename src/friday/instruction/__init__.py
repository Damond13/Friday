"""指令学习模块 — 公共 API"""

from friday.instruction.adapter import (
    list_instructions,
    match,
    reload,
    remove,
    teach,
)
from friday.instruction.models import (
    Action,
    Instruction,
    InstructionType,
    MatchResult,
)

__all__ = [
    "teach",
    "match",
    "list_instructions",
    "remove",
    "reload",
    "Instruction",
    "Action",
    "MatchResult",
    "InstructionType",
]
