"""基于图结构的检索逻辑。"""
from __future__ import annotations

from typing import Iterable, Sequence

import networkx as nx

from .data_models import RecipeRecord


class RecipeRetriever:
    """围绕图遍历与排序的轻量封装。"""

    def __init__(self, max_neighbors: int = 5) -> None:
        self.max_neighbors = max_neighbors

    def find_similar_recipes(self, graph: nx.Graph, recipe_id: str) -> Sequence[RecipeRecord]:
        if recipe_id not in graph:
            return []

        neighbors = (
            (neighbor, graph[recipe_id][neighbor]["weight"])
            for neighbor in graph.neighbors(recipe_id)
        )
        sorted_neighbors = sorted(neighbors, key=lambda item: item[1], reverse=True)[: self.max_neighbors]
        return [self._node_to_record(graph, node) for node, _ in sorted_neighbors]

    def recommend_from_text(self, graph: nx.Graph, query: str) -> tuple[RecipeRecord | None, Sequence[RecipeRecord]]:
        """Fallback：文本匹配最近的节点后再做邻域检索。"""

        reference = self.match_recipe_by_text(graph, query)
        if not reference:
            return None, []
        candidates = self.find_similar_recipes(graph, reference.recipe_id)
        return reference, candidates

    def match_recipe_by_text(self, graph: nx.Graph, query: str) -> RecipeRecord | None:
        anchor_id = self._fuzzy_match(graph, query)
        if not anchor_id:
            return None
        return self._node_to_record(graph, anchor_id)

    def get_recipe_record(self, graph: nx.Graph, node_id: str) -> RecipeRecord | None:
        if node_id not in graph:
            return None
        return self._node_to_record(graph, node_id)

    @staticmethod
    def _node_to_record(graph: nx.Graph, node_id: str) -> RecipeRecord:
        data = graph.nodes[node_id]
        return RecipeRecord(
            recipe_id=node_id,
            title=data.get("title", node_id),
            ingredients=data.get("ingredients", tuple()),
            instructions=data.get("instructions", ""),
            tags=data.get("tags", tuple()),
        )

    @staticmethod
    def _fuzzy_match(graph: nx.Graph, query: str) -> str | None:
        query_lower = query.lower()
        for node_id, payload in graph.nodes(data=True):
            if query_lower in payload.get("title", "").lower():
                return node_id
        return None


__all__ = ["RecipeRetriever"]
