# data/processed

存放已经结构化的菜谱结果：

- `sample_recipes.json`：内置小样本，GraphRAG 管线在尚未解析完整数据时会加载它。
- `recipes_index.json`：运行 `scripts/bootstrap_data.py` 后生成的主数据文件（已被 `.gitignore` 忽略）。

你可以多次运行 `uv run scripts/bootstrap_data.py --force-processed` 来刷新 `recipes_index.json`，示例文件将保持不变，便于写测试或演示。
