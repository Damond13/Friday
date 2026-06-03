"""集成测试 — 指令学习"""

import pytest

from friday.instruction import teach, match, list_instructions, remove, reload
from friday.instruction.store import INSTRUCTIONS_DIR


@pytest.fixture(autouse=True)
def _cleanup_test_instructions():
    """测试后清理测试指令文件"""
    yield
    for f in INSTRUCTIONS_DIR.glob("*.yaml"):
        try:
            text = f.read_text(encoding="utf-8")
            if "inttest_" in text:
                f.unlink()
        except Exception:
            pass


class TestInstructionTeachAndMatch:
    """指令创建与匹配"""

    def test_teach_single(self) -> None:
        """创建单步指令"""
        instr = teach(
            name="inttest_查看时间",
            trigger="看时间",
            actions=[{"command": "date", "description": "查看当前时间"}],
            keywords=["时间", "date", "clock"],
        )
        assert instr.name == "inttest_查看时间"
        assert instr.trigger == "看时间"
        assert instr.type.value == "single"
        assert len(instr.actions) == 1

    def test_teach_workflow_auto(self) -> None:
        """多步操作自动推断为 workflow"""
        instr = teach(
            name="inttest_部署流程",
            trigger="部署",
            actions=[
                {"command": "git pull", "description": "拉取代码"},
                {"command": "docker build .", "description": "构建镜像"},
            ],
        )
        assert instr.type.value == "workflow"

    def test_exact_match(self) -> None:
        """精确匹配 trigger"""
        teach(
            name="inttest_精确匹配",
            trigger="查磁盘",
            actions=[{"command": "df -h", "description": "查看磁盘"}],
        )
        results = match("查磁盘")
        assert len(results) > 0
        assert results[0].score == 1.0
        assert results[0].match_type == "exact"

    def test_keyword_match(self) -> None:
        """关键词匹配"""
        teach(
            name="inttest_关键词匹配",
            trigger="网络状态",
            actions=[{"command": "ifconfig", "description": "查看网络"}],
            keywords=["网络", "network", "网卡"],
        )
        results = match("查看 network 配置")
        assert len(results) > 0
        assert results[0].score > 0

    def test_no_match(self) -> None:
        """不匹配返回空"""
        teach(
            name="inttest_不匹配",
            trigger="天气查询",
            actions=[{"command": "curl weather.api", "description": "查天气"}],
        )
        results = match("今天吃什么好呢")
        # 可能匹配到也可能不匹配，但不应精确匹配
        exact = [r for r in results if r.match_type == "exact"]
        assert len(exact) == 0


class TestInstructionManagement:
    """指令管理"""

    def test_list_instructions(self) -> None:
        """列出指令"""
        teach(
            name="inttest_列表测试",
            trigger="列表触发",
            actions=[{"command": "echo list", "description": "列表测试"}],
        )
        instrs = list_instructions()
        names = [i.name for i in instrs]
        assert "inttest_列表测试" in names

    def test_remove_instruction(self) -> None:
        """删除指令"""
        teach(
            name="inttest_删除测试",
            trigger="删除触发",
            actions=[{"command": "echo del", "description": "删除测试"}],
        )
        ok = remove("inttest_删除测试")
        assert ok is True

    def test_remove_nonexistent(self) -> None:
        """删除不存在的指令返回 False"""
        ok = remove("inttest_nonexistent_instruction")
        assert ok is False

    def test_reload(self) -> None:
        """重新加载指令"""
        count = reload()
        assert isinstance(count, int)
        assert count >= 0


class TestInstructionValidation:
    """指令输入校验"""

    def test_trigger_too_short(self) -> None:
        """触发词过短抛异常"""
        with pytest.raises(ValueError, match="触发词"):
            teach(name="inttest_短", trigger="x", actions=[{"command": "echo"}])

    def test_empty_actions(self) -> None:
        """空动作列表抛异常"""
        with pytest.raises(ValueError, match="动作列表"):
            teach(name="inttest_空", trigger="测试", actions=[])

    def test_action_missing_command(self) -> None:
        """动作缺少 command 字段抛异常"""
        with pytest.raises(ValueError, match="command"):
            teach(name="inttest_缺命令", trigger="测试", actions=[{"description": "无命令"}])
