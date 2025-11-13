"""基于 sentence-transformers 的菜谱向量索引。"""
from __future__ import annotations

import logging
from typing import Iterable, Sequence

import numpy as np

from .data_models import RecipeRecord

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - sentence-transformers 为可选依赖
    SentenceTransformer = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class RecipeEmbeddingIndex:
    """维护菜谱向量，支持文本检索与语义相似度计算。"""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._records: dict[str, RecipeRecord] = {}
        self._ids: list[str] = []
        self._matrix: np.ndarray | None = None
        self._enabled = SentenceTransformer is not None

    def build(self, records: Sequence[RecipeRecord]) -> None:
        """根据传入菜谱生成或更新向量索引。"""

        self._records = {record.recipe_id: record for record in records}
        if not self._enabled:
            return
        self._ensure_model()
        if not self._model:
            return
        texts = [record.as_prompt_chunk() for record in records]
        try:
            embeddings = self._model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        except Exception as exc:  # pragma: no cover - 依赖模型下载
            LOGGER.warning("生成菜谱向量失败: %s", exc)
            self._matrix = None
            return

        self._matrix = embeddings
        self._ids = [record.recipe_id for record in records]

    def get_record(self, recipe_id: str) -> RecipeRecord | None:
        return self._records.get(recipe_id)

    def query(self, text: str, top_k: int = 5, exclude: Sequence[str] | None = None) -> list[RecipeRecord]:
        """根据任意文本检索最接近的菜谱。"""

        if not self._ready():
            return []
        vector = self._encode_text(text)
        if vector is None:
            return []
        exclude_set = set(exclude or [])
        scores = self._matrix @ vector

        for idx, recipe_id in enumerate(self._ids):
            if recipe_id in exclude_set:
                scores[idx] = -1.0

        top_k = min(top_k, len(self._ids))
        if top_k <= 0:
            return []

        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_sorted = top_indices[np.argsort(scores[top_indices])[::-1]]
        results: list[RecipeRecord] = []
        for idx in top_sorted:
            if scores[idx] <= 0:
                continue
            recipe_id = self._ids[idx]
            record = self._records.get(recipe_id)
            if record:
                results.append(record)
        return results

    def find_similar_to_recipe(self, recipe: RecipeRecord, top_k: int = 5) -> list[RecipeRecord]:
        """基于语义相似度寻找与特定菜谱接近的其他菜谱。"""

        query_text = recipe.as_prompt_chunk()
        return self.query(query_text, top_k=top_k + 2, exclude=[recipe.recipe_id])

    # ------------------------------------------------------------------ 内部方法
    def _ready(self) -> bool:
        return (
            self._enabled
            and self._model is not None
            and self._matrix is not None
            and len(self._ids) == len(self._matrix)
        )

    def _ensure_model(self) -> None:
        if self._model or not self._enabled:
            return
        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception as exc:  # pragma: no cover - 依赖外部模型
            LOGGER.warning("加载 SentenceTransformer(%s) 失败: %s", self.model_name, exc)
            self._enabled = False

    def _encode_text(self, text: str) -> np.ndarray | None:
        if not self._model:
            return None
        try:
            vector = self._model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("文本向量化失败: %s", exc)
            return None
        return vector


__all__ = ["RecipeEmbeddingIndex"]
