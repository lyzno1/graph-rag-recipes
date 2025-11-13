"""命令行入口：体验 GraphRAG 推荐流程。"""
from __future__ import annotations

import argparse

from graph_rag_recipes.config import ProjectConfig
from graph_rag_recipes.pipeline import GraphRAGPipeline
from graph_rag_recipes.ui_components import format_cli_block


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 GraphRAG 推荐示例")
    parser.add_argument("query", nargs="?", default="番茄炒蛋", help="用户输入或历史喜欢的菜")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = GraphRAGPipeline(ProjectConfig())
    result = pipeline.recommend(args.query)
    print(format_cli_block(result))


if __name__ == "__main__":
    main()
