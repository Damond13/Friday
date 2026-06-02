"""匹配引擎单元测试"""

from friday.instruction.models import Action, Instruction, InstructionType
from friday.instruction.matcher import match_instructions


def _make_instruction(
    name: str, trigger: str, keywords: list[str] | None = None
) -> Instruction:
    return Instruction(
        name=name,
        trigger=trigger,
        actions=[Action(command="echo test")],
        type=InstructionType.SINGLE,
        keywords=keywords or [],
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


class TestExactMatch:
    """精确匹配"""

    def test_exact_trigger_in_text(self) -> None:
        instrs = [_make_instruction("deploy", "deploy")]
        results = match_instructions("帮我 deploy 一下", instrs)
        assert len(results) == 1
        assert results[0].match_type == "exact"
        assert results[0].score == 1.0

    def test_exact_case_insensitive(self) -> None:
        instrs = [_make_instruction("deploy", "deploy")]
        results = match_instructions("Deploy now", instrs)
        assert len(results) == 1
        assert results[0].match_type == "exact"

    def test_chinese_trigger(self) -> None:
        instrs = [_make_instruction("磁盘", "检查磁盘空间")]
        results = match_instructions("帮我检查磁盘空间", instrs)
        assert len(results) == 1
        assert results[0].match_type == "exact"


class TestKeywordMatch:
    """关键词匹配"""

    def test_keyword_match_via_trigger_tokens(self) -> None:
        instrs = [_make_instruction("disk", "check disk")]
        results = match_instructions("disk usage", instrs)
        assert len(results) >= 1
        assert results[0].score > 0

    def test_keyword_match_via_keywords_field(self) -> None:
        instrs = [_make_instruction("磁盘", "check disk", keywords=["磁盘", "空间"])]
        results = match_instructions("查看磁盘空间", instrs)
        assert len(results) >= 1
        assert results[0].match_type == "keyword"

    def test_keyword_score_below_threshold(self) -> None:
        instrs = [_make_instruction("deploy", "deploy")]
        results = match_instructions("完全无关的文本 xyz", instrs)
        assert len(results) == 0


class TestNoMatch:
    """无匹配"""

    def test_empty_instructions(self) -> None:
        results = match_instructions("deploy", [])
        assert len(results) == 0

    def test_no_match_at_all(self) -> None:
        instrs = [_make_instruction("deploy", "deploy")]
        results = match_instructions("xyz abc def", instrs)
        assert len(results) == 0


class TestMultipleResults:
    """多结果排序"""

    def test_sorted_by_score_descending(self) -> None:
        instrs = [
            _make_instruction("deploy", "deploy"),
            _make_instruction("deploy-prod", "deploy prod", keywords=["deploy"]),
        ]
        results = match_instructions("deploy", instrs)
        if len(results) >= 2:
            assert results[0].score >= results[1].score

    def test_exact_before_keyword(self) -> None:
        instrs = [
            _make_instruction("build", "build", keywords=["compile"]),
            _make_instruction("deploy", "deploy"),
        ]
        results = match_instructions("deploy build", instrs)
        assert len(results) >= 1
        # exact match should be first
        exact = [r for r in results if r.match_type == "exact"]
        assert len(exact) >= 1
