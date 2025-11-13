# data/raw

此目录用于缓存 HowToCook 原始数据。默认忽略其中的大部分文件，只保留：

- `howtocook_sample/`：若尚未下载完整数据，可参考其中的 Markdown 示范结构。
- 本 README：说明目录用途，避免空目录被清理。

在联网环境中，可以运行 `uv run python scripts/bootstrap_data.py` 自动克隆或下载最新的 HowToCook 仓库，数据会被放置到 `data/raw/howtocook_repo/`。如需清理重新下载，可添加 `--force-repo` 选项。
