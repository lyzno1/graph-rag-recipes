"""HowToCook 数据集的获取与最小清洗逻辑。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .config import ProjectConfig
from .data_models import RecipeRecord


class HowToCookIngestor:
    """负责下载/缓存 HowToCook 数据并提供结构化记录。"""

    SAMPLE_FILE = "sample_recipes.json"

    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self.paths = self.config.paths
        self.paths.ensure()

    def prepare_local_copy(self, force: bool = False) -> Path:
        """预留接口：未来可在此处加入 git clone 或 API 下载。"""

        placeholder = self.paths.raw_data_dir / "DATASET_PLACEHOLDER.txt"
        if force or not placeholder.exists():
            placeholder.write_text(
                "请将 HowToCook 数据放入此目录，或实现自动下载逻辑。\n",
                encoding="utf-8",
            )
        return placeholder

    def load_sample_records(self) -> list[RecipeRecord]:
        """提供一组迷你示例，便于快速验证图构建逻辑。"""

        sample_path = self.paths.processed_data_dir / self.SAMPLE_FILE
        if not sample_path.exists():
            sample = [
                {
                    "recipe_id": "U123",
                    "title": "番茄炒蛋",
                    "ingredients": ["番茄", "鸡蛋", "葱", "盐"],
                    "instructions": "将鸡蛋炒熟后与番茄同炒，调味即可。",
                    "tags": ["家常", "酸甜"],
                },
                {
                    "recipe_id": "R456",
                    "title": "番茄豆腐汤",
                    "ingredients": ["番茄", "豆腐", "香菜"],
                    "instructions": "番茄炖煮出汁后放入豆腐，煮沸加盐。",
                    "tags": ["清淡", "汤品"],
                },
                {
                    "recipe_id": "R789",
                    "title": "蛋炒西红柿饭",
                    "ingredients": ["米饭", "鸡蛋", "番茄"],
                    "instructions": "先炒鸡蛋再放米饭番茄，翻炒均匀。",
                    "tags": ["主食", "酸甜"],
                },
            ]
            sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

        with sample_path.open(encoding="utf-8") as fh:
            payload = json.load(fh)

        return [self._to_record(item) for item in payload]

    @staticmethod
    def _to_record(payload: dict) -> RecipeRecord:
        return RecipeRecord(
            recipe_id=str(payload.get("recipe_id")),
            title=payload.get("title", "未知菜谱"),
            ingredients=tuple(payload.get("ingredients", [])),
            instructions=payload.get("instructions", ""),
            tags=tuple(payload.get("tags", [])),
        )

    def iter_records(self) -> Iterable[RecipeRecord]:
        yield from self.load_sample_records()


__all__ = ["HowToCookIngestor"]
