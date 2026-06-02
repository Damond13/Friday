"""指令学习模块 — 匹配引擎"""

import re

from friday.instruction.models import Instruction, MatchResult


def match_instructions(
    text: str,
    instructions: list[Instruction],
    threshold: float = 0.3,
) -> list[MatchResult]:
    """两级匹配：精确匹配 + 关键词匹配，返回按评分降序的结果"""
    results: list[MatchResult] = []
    tokens = _tokenize(text)

    for instr in instructions:
        result = _match_one(tokens, text, instr)
        if result is not None and result.score >= threshold:
            results.append(result)

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def _match_one(
    tokens: set[str], text: str, instr: Instruction
) -> MatchResult | None:
    """对单条指令执行匹配"""
    # 精确匹配：trigger 完全出现在输入中
    if instr.trigger.lower() in text.lower():
        return MatchResult(instruction=instr, score=1.0, match_type="exact")

    # 关键词子串匹配（处理中文等无空格语言）
    substr_score = _substr_match(text, instr)
    if substr_score > 0:
        return MatchResult(instruction=instr, score=substr_score, match_type="keyword")

    # Token Jaccard 匹配（处理英文等有空格语言）
    trigger_tokens = _tokenize(instr.trigger)
    keyword_tokens: set[str] = set()
    for kw in instr.keywords:
        keyword_tokens.update(_tokenize(kw))

    all_instr_tokens = trigger_tokens | keyword_tokens
    if not all_instr_tokens:
        return None

    intersection = tokens & all_instr_tokens
    union = tokens | all_instr_tokens
    if not union:
        return None

    score = len(intersection) / len(union)
    if score > 0:
        return MatchResult(instruction=instr, score=score, match_type="keyword")

    return None


def _substr_match(text: str, instr: Instruction) -> float:
    """子串匹配：检查 keywords 是否出现在输入文本中"""
    if not instr.keywords:
        return 0.0
    text_lower = text.lower()
    matched = sum(1 for kw in instr.keywords if kw.lower() in text_lower)
    if matched == 0:
        return 0.0
    return matched / len(instr.keywords)


def _tokenize(text: str) -> set[str]:
    """分词：按空格和标点切分，转小写"""
    parts = re.split(r"[\s\-_/,.:;!?，。！？、；：]+", text.lower())
    return {p for p in parts if len(p) >= 2}
