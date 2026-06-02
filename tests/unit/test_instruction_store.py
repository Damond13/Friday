"""存储层单元测试"""

from pathlib import Path

import pytest

from friday.instruction.models import Action, Instruction, InstructionType
from friday.instruction import store


def _make_instruction(name: str = "test", trigger: str = "test") -> Instruction:
    return Instruction(
        name=name,
        trigger=trigger,
        actions=[Action(command="echo hello")],
        type=InstructionType.SINGLE,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


@pytest.fixture
def isolated_store(tmp_path: Path) -> None:
    """替换 INSTRUCTIONS_DIR 为临时目录"""
    old_dir = store.INSTRUCTIONS_DIR
    store.INSTRUCTIONS_DIR = tmp_path
    yield
    store.INSTRUCTIONS_DIR = old_dir


class TestSlugify:
    """_slugify() 触发词转文件名"""

    def test_english(self) -> None:
        assert store._slugify("deploy") == "deploy"

    def test_with_spaces(self) -> None:
        assert store._slugify("check disk") == "check-disk"

    def test_chinese(self) -> None:
        result = store._slugify("部署")
        assert len(result) > 0

    def test_special_chars(self) -> None:
        result = store._slugify("test!@#$%")
        assert "!" not in result

    def test_emoji_no_leading_hyphen(self) -> None:
        result = store._slugify("🚀 deploy")
        assert not result.startswith("-")
        assert "deploy" in result


class TestSaveAndLoad:
    """save() 和 load() 正确性"""

    def test_save_creates_file(self, isolated_store: None) -> None:
        instr = _make_instruction()
        result = store.save(instr)
        assert result.exists()
        assert result.suffix == ".yaml"

    def test_load_returns_instruction(self, isolated_store: None) -> None:
        instr = _make_instruction()
        store.save(instr)
        loaded = store.load(store._slugify(instr.trigger))
        assert loaded is not None
        assert loaded.name == "test"
        assert loaded.trigger == "test"
        assert len(loaded.actions) == 1
        assert loaded.actions[0].command == "echo hello"

    def test_load_nonexistent_returns_none(self, isolated_store: None) -> None:
        assert store.load("nonexistent") is None


class TestLoadAll:
    """load_all() 扫描"""

    def test_load_all_returns_all(self, isolated_store: None) -> None:
        store.save(_make_instruction("a", "alpha"))
        store.save(_make_instruction("b", "beta"))
        result = store.load_all()
        assert len(result) == 2

    def test_load_all_skips_invalid(self, isolated_store: None) -> None:
        store.save(_make_instruction("valid", "valid"))
        bad_path = store.INSTRUCTIONS_DIR / "bad.yaml"
        bad_path.write_text("not: a\nvalid: instruction", encoding="utf-8")
        result = store.load_all()
        assert len(result) == 1

    def test_load_all_skips_bad_yaml(self, isolated_store: None) -> None:
        bad_path = store.INSTRUCTIONS_DIR / "broken.yaml"
        bad_path.write_text("name: [\n", encoding="utf-8")
        result = store.load_all()
        assert len(result) == 0


class TestDelete:
    """delete() 删除"""

    def test_delete_existing(self, isolated_store: None) -> None:
        store.save(_make_instruction("del", "delete-me"))
        assert store.delete("delete-me") is True
        assert store.load("delete-me") is None

    def test_delete_nonexistent(self, isolated_store: None) -> None:
        assert store.delete("nonexistent") is False
