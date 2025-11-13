"""菜谱知识图谱构建相关逻辑。"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

import networkx as nx

from .data_models import RecipeRecord


class RecipeGraphBuilder:
    """根据共享食材/标签构建图结构，并写入相似度权重。"""

    def __init__(self, similarity_threshold: float = 0.35) -> None:
        self.similarity_threshold = similarity_threshold

    def build_graph(self, recipes: Iterable[RecipeRecord]) -> nx.Graph:
        recipe_list = list(recipes)
        graph = nx.Graph()
        for recipe in recipe_list:
            graph.add_node(
                recipe.recipe_id,
                title=recipe.title,
                ingredients=tuple(recipe.ingredients),
                tags=tuple(recipe.tags),
                instructions=recipe.instructions,
            )

        for left, right in combinations(recipe_list, 2):
            score = self._compute_similarity(left, right)
            if score >= self.similarity_threshold:
                graph.add_edge(left.recipe_id, right.recipe_id, weight=score)
        return graph

    @staticmethod
    def _compute_similarity(left: RecipeRecord, right: RecipeRecord) -> float:
        ingredients_left = set(left.ingredients)
        ingredients_right = set(right.ingredients)
        tags_left = set(left.tags)
        tags_right = set(right.tags)

        def safe_jaccard(a: set[str], b: set[str]) -> float:
            union = a | b
            return 0.0 if not union else len(a & b) / len(union)

        return 0.7 * safe_jaccard(ingredients_left, ingredients_right) + 0.3 * safe_jaccard(tags_left, tags_right)


__all__ = ["RecipeGraphBuilder"]
