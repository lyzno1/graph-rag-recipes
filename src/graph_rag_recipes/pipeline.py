"""GraphRAG 菜谱推荐主流程。"""
from __future__ import annotations

from typing import Optional

import networkx as nx

from .config import ProjectConfig
from .data_ingest import HowToCookIngestor
from .data_models import RecommendationResult, RecipeRecord
from .graph_builder import RecipeGraphBuilder
from .llm_generator import LLMGenerator
from .retrieval import RecipeRetriever


class GraphRAGPipeline:
    """串联数据 → 图构建 → 检索 → 生成。"""

    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self.ingestor = HowToCookIngestor(self.config)
        self.graph_builder = RecipeGraphBuilder(self.config.similarity_threshold)
        self.retriever = RecipeRetriever(self.config.max_neighbors)
        self.llm_generator = LLMGenerator(self.config)
        self._graph: Optional[nx.Graph] = None

    @property
    def graph(self) -> nx.Graph:
        if self._graph is None:
            raise RuntimeError("图尚未构建，请先调用 bootstrap_graph().")
        return self._graph

    def bootstrap_graph(self) -> nx.Graph:
        records = list(self.ingestor.iter_records())
        self._graph = self.graph_builder.build_graph(records)
        return self._graph

    def recommend(self, user_query: str) -> RecommendationResult:
        if self._graph is None:
            self.bootstrap_graph()

        reference, candidates = self.retriever.recommend_from_text(self.graph, user_query)
        if reference is None:
            reference = RecipeRecord(recipe_id="UNKNOWN", title=user_query, ingredients=(), instructions="")
            candidates = []
        explanation = self.llm_generator.generate(reference, candidates, user_query)
        return RecommendationResult(reference_recipe=reference, similar_recipes=candidates, explanation=explanation)

    def run_demo(self, user_query: str = "番茄炒蛋") -> RecommendationResult:
        result = self.recommend(user_query)
        print(result.summary())
        return result


__all__ = ["GraphRAGPipeline"]
