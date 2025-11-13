"""GraphRAG 菜谱推荐主流程。"""
from __future__ import annotations

from typing import Optional

import networkx as nx

from .config import ProjectConfig
from .data_ingest import HowToCookIngestor
from .data_models import RecommendationResult, RecipeRecord, UserProfile
from .embeddings import RecipeEmbeddingIndex
from .graph_builder import RecipeGraphBuilder
from .llm_generator import LLMGenerator
from .retrieval import RecipeRetriever
from .user_profiles import UserProfileRepository


class GraphRAGPipeline:
    """串联数据 → 图构建 → 检索 → 生成。"""

    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self.ingestor = HowToCookIngestor(self.config)
        self.graph_builder = RecipeGraphBuilder(self.config.similarity_threshold)
        self.retriever = RecipeRetriever(self.config.max_neighbors)
        self.llm_generator = LLMGenerator(self.config)
        self.user_repository = UserProfileRepository()
        self.embedding_index = RecipeEmbeddingIndex(self.config.models.embedding_model)
        self._graph: Optional[nx.Graph] = None
        self._records: list[RecipeRecord] = []

    @property
    def graph(self) -> nx.Graph:
        if self._graph is None:
            raise RuntimeError("图尚未构建，请先调用 bootstrap_graph().")
        return self._graph

    def bootstrap_graph(self) -> nx.Graph:
        records = list(self.ingestor.iter_records())
        self._records = records
        self._graph = self.graph_builder.build_graph(records)
        self.embedding_index.build(records)
        return self._graph

    def recommend(self, user_query: str) -> RecommendationResult:
        if self._graph is None:
            self.bootstrap_graph()

        user_profile = self.user_repository.get(user_query)
        if user_profile:
            return self._recommend_for_user(user_profile)

        reference = self._find_reference_recipe(user_query)
        if reference is None:
            reference = RecipeRecord(recipe_id="UNKNOWN", title=user_query, ingredients=(), instructions="")
            candidates = self.embedding_index.query(
                user_query,
                top_k=self.config.max_neighbors,
            )
        else:
            candidates = self.retriever.find_similar_recipes(self.graph, reference.recipe_id)
            if not candidates:
                candidates = self.embedding_index.find_similar_to_recipe(reference, self.config.max_neighbors)
        if not candidates:
            candidates = self._fallback_candidates(reference)
        explanation = self.llm_generator.generate(reference, candidates, user_query)
        return RecommendationResult(reference_recipe=reference, similar_recipes=candidates, explanation=explanation)

    def run_demo(self, user_query: str = "番茄炒蛋") -> RecommendationResult:
        result = self.recommend(user_query)
        print(result.summary())
        return result

    def _recommend_for_user(self, user_profile: UserProfile) -> RecommendationResult:
        """根据用户历史菜谱节点构建推荐结果。"""

        all_candidates: list[RecipeRecord] = []
        reference: RecipeRecord | None = None
        for recipe_id in user_profile.liked_recipe_ids:
            record = self.retriever.get_recipe_record(self.graph, recipe_id)
            if not record:
                continue
            if reference is None:
                reference = record
            neighbors = self.retriever.find_similar_recipes(self.graph, recipe_id)
            all_candidates.extend(neighbors)

        if reference is None:
            fallback_query = user_profile.preferred_tags[0] if user_profile.preferred_tags else user_profile.user_id
            reference = self._find_reference_recipe(fallback_query)
            if reference is None:
                reference = RecipeRecord(
                    recipe_id="UNKNOWN",
                    title=fallback_query,
                    ingredients=(),
                    instructions="",
                )
                candidates = self.embedding_index.query(fallback_query, top_k=self.config.max_neighbors)
            else:
                candidates = self.embedding_index.find_similar_to_recipe(reference, self.config.max_neighbors)
            if not candidates:
                candidates = self._fallback_candidates(reference)
            explanation = self.llm_generator.generate(
                reference,
                candidates,
                f"用户 {user_profile.user_id} 偏好 {fallback_query}",
            )
            return RecommendationResult(reference_recipe=reference, similar_recipes=candidates, explanation=explanation)

        deduped: list[RecipeRecord] = []
        seen_ids = set(user_profile.liked_recipe_ids)
        seen_ids.add(reference.recipe_id)
        candidate_seen: set[str] = set()
        for candidate in all_candidates:
            if candidate.recipe_id in seen_ids:
                continue
            if candidate.recipe_id in candidate_seen:
                continue
            deduped.append(candidate)
            candidate_seen.add(candidate.recipe_id)

        if not deduped:
            deduped = self.embedding_index.find_similar_to_recipe(reference, self.config.max_neighbors)
        if not deduped:
            deduped = self._fallback_candidates(reference)

        explanation_input = (
            f"用户 {user_profile.user_id} 偏好 {', '.join(user_profile.preferred_tags) or '家常菜'}，"
            f"曾做过 {reference.title}"
        )
        explanation = self.llm_generator.generate(reference, deduped, explanation_input)
        return RecommendationResult(reference_recipe=reference, similar_recipes=deduped, explanation=explanation)

    def _fallback_candidates(self, reference: RecipeRecord, limit: int | None = None) -> list[RecipeRecord]:
        """当图中缺乏相似节点时，使用示例菜谱作为兜底。"""

        candidate_pool = list(self._records)
        existing_ids = {record.recipe_id for record in candidate_pool}
        for sample in self.ingestor.load_sample_records():
            if sample.recipe_id not in existing_ids:
                candidate_pool.append(sample)
                existing_ids.add(sample.recipe_id)

        if not candidate_pool:
            candidate_pool = self.ingestor.load_sample_records()

        scores: list[tuple[float, RecipeRecord]] = []
        for record in candidate_pool:
            if record.recipe_id == reference.recipe_id:
                continue
            score = self._overlap_score(reference, record)
            scores.append((score, record))

        scores.sort(key=lambda pair: pair[0], reverse=True)
        filtered = [record for score, record in scores if score > 0][: limit or self.config.max_neighbors]
        if filtered:
            return filtered
        # 如果没有重叠，直接返回示例前几项
        fallback_pool = candidate_pool or self.ingestor.load_sample_records()
        return fallback_pool[: limit or self.config.max_neighbors]

    @staticmethod
    def _overlap_score(left: RecipeRecord, right: RecipeRecord) -> float:
        ingredients_left = set(left.ingredients)
        ingredients_right = set(right.ingredients)
        tags_left = set(left.tags)
        tags_right = set(right.tags)
        ingredient_overlap = len(ingredients_left & ingredients_right)
        tag_overlap = len(tags_left & tags_right)
        return ingredient_overlap * 2 + tag_overlap

    def _find_reference_recipe(self, query: str) -> RecipeRecord | None:
        """综合文本匹配与向量检索，定位最相关的菜谱。"""

        if query in self.graph:
            record = self.retriever.get_recipe_record(self.graph, query)
            if record:
                return record

        reference = self.retriever.match_recipe_by_text(self.graph, query)
        if reference:
            return reference

        embedding_matches = self.embedding_index.query(query, top_k=1)
        return embedding_matches[0] if embedding_matches else None


__all__ = ["GraphRAGPipeline"]
