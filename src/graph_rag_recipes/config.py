"""集中管理项目配置与常量。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - 可选依赖
    load_dotenv = None  # type: ignore

if load_dotenv:
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env", override=False)


@dataclass(slots=True)
class ProjectPaths:
    """统一管理项目目录，方便脚本与模块共享。"""

    root: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path

    @classmethod
    def from_project_root(cls, root: Path | None = None) -> "ProjectPaths":
        root = root or Path(__file__).resolve().parents[2]
        data_dir = root / "data"
        return cls(
            root=root,
            data_dir=data_dir,
            raw_data_dir=data_dir / "raw",
            processed_data_dir=data_dir / "processed",
        )

    def ensure(self) -> None:
        for path in (self.data_dir, self.raw_data_dir, self.processed_data_dir):
            path.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class ModelSettings:
    """Embedding 与 LLM 相关的默认配置。"""

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"


@dataclass(slots=True)
class ProjectConfig:
    """项目全局配置，供管线与 CLI 调用。"""

    paths: ProjectPaths = field(default_factory=ProjectPaths.from_project_root)
    models: ModelSettings = field(default_factory=ModelSettings)
    howtocook_repo: str = "https://github.com/Anduin2017/HowToCook"
    max_neighbors: int = 10
    similarity_threshold: float = 0.2

    def llm_api_key(self) -> str | None:
        env_key = {
            "openai": "OPENAI_API_KEY",
            "ollama": "OLLAMA_API_KEY",
            "glm": "ZHIPU_API_KEY",
        }.get(self.models.llm_provider.lower())
        return os.getenv(env_key) if env_key else None


__all__ = ["ProjectConfig", "ProjectPaths", "ModelSettings"]
