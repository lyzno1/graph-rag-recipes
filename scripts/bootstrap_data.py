"""准备 HowToCook 数据或示例样本。"""
from __future__ import annotations

import argparse

from graph_rag_recipes.data_ingest import HowToCookIngestor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载或准备数据集占位文件")
    parser.add_argument("--force", action="store_true", help="强制重新生成占位文件")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingestor = HowToCookIngestor()
    placeholder = ingestor.prepare_local_copy(force=args.force)
    sample = ingestor.load_sample_records()
    print(f"数据占位文件: {placeholder}")
    print(f"示例菜谱数量: {len(sample)}")


if __name__ == "__main__":
    main()
