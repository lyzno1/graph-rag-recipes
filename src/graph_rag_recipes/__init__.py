"""GraphRAG 菜谱推荐系统包。"""

from __future__ import annotations

from .config import ProjectConfig
from .pipeline import GraphRAGPipeline
from .ui_components import format_cli_block

__all__ = ["GraphRAGPipeline", "ProjectConfig", "format_cli_block", "main"]


def main() -> None:
    """允许通过 `uv run graph-rag-recipes` 快速演示推荐流程。"""

    pipeline = GraphRAGPipeline(ProjectConfig())
    result = pipeline.run_demo()
    print(format_cli_block(result))
