"""轻量数据模型定义，便于在各模块之间传递结构化信息。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(slots=True)
class RecipeRecord:
    """描述菜谱节点的最小必要字段。"""

    recipe_id: str
    title: str
    ingredients: Sequence[str] = field(default_factory=tuple)
    instructions: str = ""
    tags: Sequence[str] = field(default_factory=tuple)

    def as_prompt_chunk(self) -> str:
        """生成供 LLM 使用的文本片段。"""

        ingredient_str = ", ".join(self.ingredients)
        tags = ", ".join(self.tags)
        return (
            f"菜名: {self.title}\n"
            f"主要食材: {ingredient_str or '未知'}\n"
            f"口味/标签: {tags or '未标注'}\n"
            f"做法摘要: {self.instructions[:200]}..."
        )


@dataclass(slots=True)
class RecommendationResult:
    """封装推荐阶段需要向前端/LLM 输出的结构。"""

    reference_recipe: RecipeRecord
    similar_recipes: Sequence[RecipeRecord]
    explanation: str = ""

    def summary(self) -> str:
        similar_titles = ", ".join(r.title for r in self.similar_recipes)
        return (
            f"基于 {self.reference_recipe.title}，候选菜谱: {similar_titles}. "
            f"理由: {self.explanation or '待生成'}"
        )
