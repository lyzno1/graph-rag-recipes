"""HowToCook 数据集的获取与最小清洗逻辑。"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import requests

from .config import ProjectConfig
from .data_models import RecipeRecord

LOGGER = logging.getLogger(__name__)
EXCLUDED_DIR_PARTS = {
    ".github",
    "docs",
    "starsystem",
    "template",
    "templates",
    "guideline",
}


class DatasetAcquisitionError(RuntimeError):
    """表示在下载/刷新 HowToCook 数据集时出现的问题。"""


@dataclass(slots=True)
class SectionConfig:
    key: str
    aliases: Sequence[str]


SECTION_CONFIGS: tuple[SectionConfig, ...] = (
    SectionConfig("ingredients", ("原料", "食材", "主要原料", "需要准备", "材料")),
    SectionConfig("seasonings", ("配料", "辅料", "调料", "调味", "佐料")),
    SectionConfig("instructions", ("步骤", "做法", "制作步骤", "烹饪步骤", "操作步骤")),
    SectionConfig("tips", ("小贴士", "提示", "心得", "注意事项")),
)


class HowToCookIngestor:
    """负责下载/缓存 HowToCook 数据并提供结构化记录。"""

    SAMPLE_FILE = "sample_recipes.json"
    PROCESSED_FILE = "recipes_index.json"
    REPO_DIRNAME = "howtocook_repo"
    ARCHIVE_NAME = "howtocook_repo.zip"

    def __init__(self, config: ProjectConfig | None = None) -> None:
        self.config = config or ProjectConfig()
        self.paths = self.config.paths
        self.repo_dir = self.paths.raw_data_dir / self.REPO_DIRNAME
        self.paths.ensure()

    # ------------------------------------------------------------------ 数据准备
    def prepare_local_copy(self, force: bool = False, strategy: str = "auto") -> Path:
        """尝试以 git clone 或下载压缩包的方式获取 HowToCook 数据。"""

        if force and self.repo_dir.exists():
            shutil.rmtree(self.repo_dir)

        if self.repo_dir.exists() and (self.repo_dir / ".git").exists():
            self._git_update_repo()
            return self.repo_dir

        for method in self._resolve_strategy(strategy):
            try:
                if method == "git":
                    return self._git_clone_repo()
                if method == "archive":
                    return self._download_archive()
            except DatasetAcquisitionError as exc:
                LOGGER.warning("获取 HowToCook 数据失败（方法: %s）: %s", method, exc)

        placeholder = self.paths.raw_data_dir / "DATASET_PLACEHOLDER.txt"
        placeholder.write_text(
            "自动下载 HowToCook 数据失败，请手动将仓库内容放置于 data/raw/howtocook_repo。\n",
            encoding="utf-8",
        )
        return placeholder

    def build_processed_dataset(
        self,
        limit: int | None = None,
        force: bool = False,
        ensure_dataset: bool = True,
    ) -> Path:
        """将 Markdown 菜谱解析为结构化 JSON，便于管线加载。"""

        target = self.paths.processed_data_dir / self.PROCESSED_FILE
        if target.exists() and not force:
            return target

        dataset_root: Path | None = None
        if ensure_dataset:
            dataset_root = self.prepare_local_copy()
        elif self.repo_dir.exists():
            dataset_root = self.repo_dir

        records: list[RecipeRecord]
        if dataset_root and dataset_root.is_dir():
            records = list(self._iter_repo_records(dataset_root, limit))
        else:
            LOGGER.warning("未找到可用的 HowToCook 仓库，回退到内置示例数据。")
            records = self.load_sample_records(limit)

        if not records:
            records = self.load_sample_records(limit)

        payload = [record.to_dict() for record in records]
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return target

    # ------------------------------------------------------------------ 数据加载
    def load_processed_records(self, limit: int | None = None) -> list[RecipeRecord]:
        processed_path = self.paths.processed_data_dir / self.PROCESSED_FILE
        if not processed_path.exists():
            return []
        with processed_path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        records = [RecipeRecord.from_mapping(item) for item in payload]
        return records[:limit] if limit else records

    def load_sample_records(self, limit: int | None = None) -> list[RecipeRecord]:
        """提供一组迷你示例，便于快速验证图构建逻辑。"""

        sample_path = self.paths.processed_data_dir / self.SAMPLE_FILE
        if not sample_path.exists():
            sample_path.write_text(
                json.dumps(self._default_sample(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        with sample_path.open(encoding="utf-8") as fh:
            payload = json.load(fh)

        records = [RecipeRecord.from_mapping(item) for item in payload]
        return records[:limit] if limit else records

    def iter_records(self, limit: int | None = None) -> Iterable[RecipeRecord]:
        processed = self.load_processed_records(limit)
        samples = self.load_sample_records()
        seen: set[str] = set()
        emitted = 0

        def should_stop() -> bool:
            return limit is not None and emitted >= limit

        for record in processed:
            if record.recipe_id in seen:
                continue
            seen.add(record.recipe_id)
            emitted += 1
            yield record
            if should_stop():
                return

        for record in samples:
            if record.recipe_id in seen:
                continue
            seen.add(record.recipe_id)
            emitted += 1
            yield record
            if should_stop():
                return

    # ------------------------------------------------------------------ 仓库同步
    def _git_clone_repo(self) -> Path:
        git_bin = shutil.which("git")
        if not git_bin:
            raise DatasetAcquisitionError("系统未安装 git，无法克隆 HowToCook。")

        try:
            subprocess.run(
                [
                    git_bin,
                    "clone",
                    "--depth",
                    "1",
                    self.config.howtocook_repo,
                    str(self.repo_dir),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as exc:
            raise DatasetAcquisitionError(f"git clone 失败: {exc}") from exc
        return self.repo_dir

    def _git_update_repo(self) -> None:
        git_bin = shutil.which("git")
        if not git_bin:
            return
        try:
            subprocess.run(
                [git_bin, "-C", str(self.repo_dir), "pull", "--ff-only"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as exc:
            LOGGER.warning("git pull 失败，将保留本地缓存: %s", exc)

    def _download_archive(self) -> Path:
        archive_path = self.paths.raw_data_dir / self.ARCHIVE_NAME
        last_error: Exception | None = None

        for url in self._candidate_archive_urls():
            try:
                response = requests.get(url, timeout=90)
                response.raise_for_status()
                archive_path.write_bytes(response.content)
                break
            except requests.RequestException as exc:
                last_error = exc
        else:
            raise DatasetAcquisitionError(f"下载压缩包失败: {last_error}")

        try:
            with zipfile.ZipFile(archive_path) as zf:
                folder_name = zf.namelist()[0].split("/")[0]
                extract_root = self.paths.raw_data_dir / folder_name
                zf.extractall(self.paths.raw_data_dir)
        finally:
            archive_path.unlink(missing_ok=True)

        if self.repo_dir.exists():
            shutil.rmtree(self.repo_dir)
        extract_root.rename(self.repo_dir)
        return self.repo_dir

    def _candidate_archive_urls(self) -> list[str]:
        base = self.config.howtocook_repo.rstrip("/").removesuffix(".git")
        branches = ("main", "master", "HEAD")
        return [f"{base}/archive/refs/heads/{branch}.zip" for branch in branches]

    @staticmethod
    def _resolve_strategy(strategy: str) -> Sequence[str]:
        if strategy == "auto":
            return ("git", "archive")
        return (strategy,)

    # ------------------------------------------------------------------ Markdown 解析
    def _iter_repo_records(
        self, repo_dir: Path, limit: int | None = None
    ) -> Iterator[RecipeRecord]:
        search_root = repo_dir / "dishes"
        if not search_root.exists():
            search_root = repo_dir

        candidates = (
            path
            for path in search_root.rglob("*.md")
            if path.is_file()
            and path.name.lower() not in {"readme.md", "license.md"}
            and not self._should_skip_file(repo_dir, path)
        )
        counter = 0
        for md_file in candidates:
            record = self._parse_markdown_file(md_file, repo_dir)
            if not record:
                continue
            yield record
            counter += 1
            if limit and counter >= limit:
                break

    def _parse_markdown_file(
        self, md_file: Path, repo_dir: Path
    ) -> RecipeRecord | None:
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        title = self._extract_title(text) or md_file.stem
        sections = self._extract_sections(text)

        ingredients = self._normalize_list(sections.get("ingredients", []))
        seasonings = self._normalize_list(sections.get("seasonings", []))
        instructions_lines = sections.get("instructions", [])
        instructions = "\n".join(line for line in instructions_lines if line).strip()
        tags = self._derive_tags(md_file, repo_dir)

        if not instructions or not (ingredients or seasonings):
            return None

        recipe_id = "|".join(md_file.relative_to(repo_dir).with_suffix("").parts)
        merged_ingredients = tuple(dict.fromkeys(ingredients + seasonings))

        return RecipeRecord(
            recipe_id=recipe_id,
            title=title,
            ingredients=merged_ingredients,
            instructions=instructions,
            tags=tuple(tags),
            source_path=str(md_file),
        )

    @staticmethod
    def _extract_title(text: str) -> str | None:
        match = re.search(r"^\s*#\s+(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _extract_sections(self, text: str) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {"text": []}
        current_key = "text"
        heading_pattern = re.compile(r"^#{2,4}\s*(.+?)\s*$")

        for raw_line in text.splitlines():
            line = raw_line.strip()
            heading_match = heading_pattern.match(line)
            if heading_match:
                normalized = self._match_section_key(heading_match.group(1))
                current_key = normalized or "text"
                if current_key not in sections:
                    sections[current_key] = []
                continue

            if current_key not in sections:
                sections[current_key] = []
            sections[current_key].append(line)

        return sections

    @staticmethod
    def _normalize_list(lines: Sequence[str]) -> list[str]:
        items: list[str] = []
        for line in lines:
            stripped = re.sub(r"^[\-\*\d\.\u2022]+\s*", "", line).strip()
            if stripped:
                items.append(stripped)
        return items

    @staticmethod
    def _derive_tags(md_file: Path, repo_dir: Path) -> list[str]:
        relative_parts = md_file.relative_to(repo_dir).parts[:-1]
        tags = [part for part in relative_parts if not part.startswith(".")]
        return tags[-3:]

    def _should_skip_file(self, repo_dir: Path, file_path: Path) -> bool:
        relative_parts = file_path.relative_to(repo_dir).parts
        return any(
            part.lower() in EXCLUDED_DIR_PARTS or part.startswith(".")
            for part in relative_parts
        )

    def _match_section_key(self, heading: str) -> str | None:
        heading_normalized = heading.replace("：", "").replace(":", "")
        for section in SECTION_CONFIGS:
            if any(alias in heading_normalized for alias in section.aliases):
                return section.key
        return None

    # ------------------------------------------------------------------ 内置示例
    @staticmethod
    def _default_sample() -> list[dict]:
        return [
            {
                "recipe_id": "sample|tomato_egg",
                "title": "番茄炒蛋",
                "ingredients": ["番茄", "鸡蛋", "葱", "盐"],
                "instructions": "将鸡蛋炒熟后与番茄同炒，调味即可。",
                "tags": ["家常", "酸甜"],
            },
            {
                "recipe_id": "sample|tomato_tofu_soup",
                "title": "番茄豆腐汤",
                "ingredients": ["番茄", "豆腐", "香菜"],
                "instructions": "番茄炖煮出汁后放入豆腐，煮沸加盐。",
                "tags": ["清淡", "汤品"],
            },
            {
                "recipe_id": "sample|fried_rice",
                "title": "蛋炒西红柿饭",
                "ingredients": ["米饭", "鸡蛋", "番茄"],
                "instructions": "先炒鸡蛋再放米饭番茄，翻炒均匀。",
                "tags": ["主食", "酸甜"],
            },
        ]


__all__ = ["HowToCookIngestor"]
