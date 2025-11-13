"""准备 HowToCook 数据或示例样本。"""

from __future__ import annotations

import argparse
from pathlib import Path

from graph_rag_recipes.data_ingest import HowToCookIngestor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载 HowToCook 仓库并生成结构化样本")
    parser.add_argument(
        "--force-repo", action="store_true", help="删除并重新下载仓库副本"
    )
    parser.add_argument(
        "--force-processed", action="store_true", help="重新生成 processed JSON"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="最多解析多少条菜谱（0 表示全部，默认 500 条以加快调试）",
    )
    parser.add_argument(
        "--strategy",
        choices=("auto", "git", "archive"),
        default="auto",
        help="指定数据拉取方式，默认 auto 优先 git",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="跳过远程下载，仅使用现有仓库/示例数据",
    )
    parser.add_argument(
        "--show",
        type=int,
        default=3,
        help="生成完成后展示前 N 条记录，默认 3",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingestor = HowToCookIngestor()

    repo_path: Path | str = "跳过下载（使用现有缓存或示例）"
    if not args.skip_download:
        repo_path = ingestor.prepare_local_copy(
            force=args.force_repo, strategy=args.strategy
        )
    elif ingestor.repo_dir.exists():
        repo_path = ingestor.repo_dir

    limit = None if args.limit == 0 else args.limit
    processed_path = ingestor.build_processed_dataset(
        limit=limit,
        force=args.force_processed,
        ensure_dataset=not args.skip_download,
    )
    preview_records = ingestor.load_processed_records(
        limit=args.show
    ) or ingestor.load_sample_records(limit=args.show)

    print("=== HowToCook 数据准备完成 ===")
    print(f"数据源目录: {repo_path}")
    print(f"结构化数据: {processed_path}")
    print(f"示例展示（最多 {args.show} 条）:")
    for record in preview_records:
        ingredient_str = ", ".join(record.ingredients[:5])
        print(f"- {record.title} | 食材: {ingredient_str}")


if __name__ == "__main__":
    main()
