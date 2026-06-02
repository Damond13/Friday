"""指令学习模块 — YAML 存储层"""

import logging
import re
from pathlib import Path

import yaml

from friday.config import CONFIG_DIR
from friday.instruction.models import Action, Instruction, InstructionType

logger = logging.getLogger(__name__)

INSTRUCTIONS_DIR = CONFIG_DIR / "instructions"


def _slugify(trigger: str) -> str:
    """将触发词转为文件名：小写 + 连字符"""
    slug = trigger.strip().lower()
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"[^a-z0-9一-鿿\-]", "", slug)
    slug = slug.strip("-")
    return slug or "instruction"


def _yaml_path(slug: str) -> Path:
    """获取 YAML 文件路径"""
    return INSTRUCTIONS_DIR / f"{slug}.yaml"


def ensure_dir() -> None:
    """确保指令存储目录存在"""
    INSTRUCTIONS_DIR.mkdir(parents=True, exist_ok=True)


def save(instruction: Instruction) -> Path:
    """保存指令到 YAML 文件，返回文件路径"""
    ensure_dir()
    slug = _slugify(instruction.trigger)
    path = _yaml_path(slug)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            instruction.to_dict(),
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    return path


def load(slug: str) -> Instruction | None:
    """从 YAML 文件加载单条指令，失败返回 None"""
    path = _yaml_path(slug)
    if not path.exists():
        return None
    return _load_file(path)


def load_all() -> list[Instruction]:
    """扫描目录加载所有指令，跳过格式错误的文件"""
    ensure_dir()
    instructions: list[Instruction] = []
    for path in sorted(INSTRUCTIONS_DIR.glob("*.yaml")):
        instr = _load_file(path)
        if instr is not None:
            instructions.append(instr)
    return instructions


def delete(slug: str) -> bool:
    """删除指令文件，返回是否成功"""
    path = _yaml_path(slug)
    if not path.exists():
        return False
    path.unlink()
    return True


def _load_file(path: Path) -> Instruction | None:
    """从单个 YAML 文件加载指令"""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or "name" not in data:
            logger.warning("跳过无效指令文件: %s", path)
            return None
        return Instruction.from_dict(data)
    except (yaml.YAMLError, KeyError, ValueError) as exc:
        logger.warning("跳过格式错误的指令文件 %s: %s", path, exc)
        return None
