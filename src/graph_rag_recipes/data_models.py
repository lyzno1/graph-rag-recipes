"""轻量数据模型定义，便于在各模块之间传递结构化信息。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(slots=True)
class RecipeRecord:
    """描述菜谱节点的最小必要字段。"""

    recipe_id: str
    title: str
    ingredients: Sequence[str] = field(default_factory=tuple)
    instructions: str = ""
    tags: Sequence[str] = field(default_factory=tuple)
    source_path: str | None = None

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "title": self.title,
            "ingredients": list(self.ingredients),
            "instructions": self.instructions,
            "tags": list(self.tags),
            "source_path": self.source_path,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RecipeRecord":
        return cls(
            recipe_id=str(payload.get("recipe_id")),
            title=payload.get("title", "未知菜谱"),
            ingredients=tuple(payload.get("ingredients", [])),
            instructions=payload.get("instructions", ""),
            tags=tuple(payload.get("tags", [])),
            source_path=payload.get("source_path"),
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


@dataclass(slots=True)
class UserProfile:
    """描述用户节点及其历史偏好。"""

    user_id: str
    liked_recipe_ids: Sequence[str] = field(default_factory=tuple)
    preferred_tags: Sequence[str] = field(default_factory=tuple)

    def primary_recipe(self) -> str | None:
        return self.liked_recipe_ids[0] if self.liked_recipe_ids else None
