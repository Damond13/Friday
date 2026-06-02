"""文件记忆单元测试"""

from pathlib import Path

import pytest

from friday.memory import files


@pytest.fixture
def isolated_files(tmp_path: Path) -> None:
    """替换 MEMORY_DIR 为临时目录"""
    old_dir = files.MEMORY_DIR
    files.MEMORY_DIR = tmp_path
    try:
        yield
    finally:
        files.MEMORY_DIR = old_dir


class TestAddDecision:
    """add_decision() 写入决策"""

    def test_creates_file(self, isolated_files: None) -> None:
        d = files.add_decision("测试决策", "做某事", "背景说明")
        assert d.title == "测试决策"
        assert d.decision == "做某事"
        assert d.date != ""
        assert d.status == "已采纳"

    def test_file_contains_entry(self, isolated_files: None) -> None:
        files.add_decision("架构选择", "使用 adapter 模式")
        content = (files.MEMORY_DIR / "decisions.md").read_text(encoding="utf-8")
        assert "架构选择" in content
        assert "adapter" in content


class TestListDecisions:
    """list_decisions() 解析返回"""

    def test_returns_list(self, isolated_files: None) -> None:
        files.add_decision("决策A", "决定A")
        files.add_decision("决策B", "决定B")
        result = files.list_decisions()
        assert len(result) == 2
        assert result[0].title == "决策B"  # 倒序，新的在前

    def test_empty_file(self, isolated_files: None) -> None:
        assert files.list_decisions() == []


class TestAddLesson:
    """add_lesson() 写入经验"""

    def test_creates_file(self, isolated_files: None) -> None:
        l = files.add_lesson("测试经验", "不要这样做", "踩坑场景")
        assert l.title == "测试经验"
        assert l.lesson == "不要这样做"
        assert l.context == "踩坑场景"


class TestListLessons:
    """list_lessons() 解析返回"""

    def test_returns_list(self, isolated_files: None) -> None:
        files.add_lesson("经验A", "教训A")
        files.add_lesson("经验B", "教训B")
        result = files.list_lessons()
        assert len(result) == 2
        assert result[0].title == "经验B"  # 倒序

    def test_empty_file(self, isolated_files: None) -> None:
        assert files.list_lessons() == []


class TestGetConstitution:
    """get_constitution() 读取宪法"""

    def test_returns_content(self, isolated_files: None) -> None:
        const_path = files.MEMORY_DIR / "constitution.md"
        const_path.parent.mkdir(parents=True, exist_ok=True)
        const_path.write_text("# Constitution\n\ntest content", encoding="utf-8")
        result = files.get_constitution()
        assert "Constitution" in result

    def test_missing_file_returns_empty(self, isolated_files: None) -> None:
        assert files.get_constitution() == ""


class TestSearchFiles:
    """search_files() 关键词搜索"""

    def test_finds_matching_decision(self, isolated_files: None) -> None:
        files.add_decision("LLM 选择", "使用智谱 API", "需要国产 LLM")
        results = files.search_files("智谱")
        assert len(results) >= 1
        assert results[0].source == "files"
        assert results[0].score == 1.0

    def test_no_match_returns_empty(self, isolated_files: None) -> None:
        files.add_decision("测试", "内容")
        assert files.search_files("不存在的关键词xyz") == []
