"""LLM 接口封装，负责生成推荐理由。"""

from __future__ import annotations

from typing import Sequence

from .config import ProjectConfig
from .data_models import RecipeRecord

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 仅在未安装 openai 时触发
    OpenAI = None  # type: ignore


class LLMGenerator:
    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self._client = None
        api_key = self.config.llm_api_key()
        if OpenAI and api_key:
            self._client = OpenAI(api_key=api_key)

    def build_prompt(
        self,
        reference: RecipeRecord,
        candidates: Sequence[RecipeRecord],
        user_input: str,
    ) -> str:
        parts = [
            "你是一名善于解释口味风格的智能厨房助手。",
            f"用户输入: {user_input}",
            "参考菜谱:",
            reference.as_prompt_chunk(),
            "候选菜谱:",
        ]
        parts.extend(recipe.as_prompt_chunk() for recipe in candidates)
        parts.append("请用中文生成推荐理由，突出共同食材或口味，并给出建议。")
        return "\n\n".join(parts)

    def generate(
        self,
        reference: RecipeRecord,
        candidates: Sequence[RecipeRecord],
        user_input: str,
    ) -> str:
        prompt = self.build_prompt(reference, candidates, user_input)
        if not self._client:
            return self._fallback_reason(reference, candidates)

        response = self._client.responses.create(
            model=self.config.models.llm_model,
            input=prompt,
        )
        return response.output[0].content[0].text  # type: ignore[return-value]

    @staticmethod
    def _fallback_reason(
        reference: RecipeRecord, candidates: Sequence[RecipeRecord]
    ) -> str:
        candidate_titles = ", ".join(
            recipe.title for recipe in candidates if recipe.title
        )
        if candidate_titles:
            return (
                f"你提到的 {reference.title} 与 {candidate_titles} 共享典型食材，"
                "因此可以尝试这些菜式来保持相似的风味。"
            )
        return f"根据你对 {reference.title} 的偏好，我们建议继续探索相同食材/口味的菜式，保持熟悉的风味体验。"


__all__ = ["LLMGenerator"]
