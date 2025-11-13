"""Streamlit/CLI 共用的展示函数。"""

from __future__ import annotations

from typing import Sequence

from .data_models import RecommendationResult


def format_cli_block(result: RecommendationResult) -> str:
    lines = ["=== GraphRAG 推荐结果 ===", f"参考菜谱: {result.reference_recipe.title}"]
    if result.similar_recipes:
        lines.append("相似菜谱:")
        for recipe in result.similar_recipes:
            lines.append(f"- {recipe.title} ({', '.join(recipe.tags) or '未标注'})")
    else:
        lines.append("未找到相似菜谱，可尝试更换关键词。")
    lines.append(f"推荐理由: {result.explanation}")
    return "\n".join(lines)


def streamlit_render(
    result: RecommendationResult,
) -> Sequence[str]:  # pragma: no cover - 仅供 UI 调用
    """预留给 Streamlit 的轻量封装，暂以文本形式输出。"""

    return [
        f"参考菜谱: {result.reference_recipe.title}",
        f"推荐理由: {result.explanation}",
        "相似菜谱:" + ", ".join(recipe.title for recipe in result.similar_recipes),
    ]


__all__ = ["format_cli_block", "streamlit_render"]
