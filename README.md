# GraphRAG 菜谱智能推荐系统

基于图结构和 RAG 思维的菜谱推荐项目。系统围绕 "检索用户节点 → 查找历史菜谱 → 图遍历得到相似菜谱 → LLM 生成推荐理由" 的流程打造面向展示的智能体验，数据来源为 [HowToCook](https://github.com/Anduin2017/HowToCook)。

## 功能目标
- 图结构建模：利用菜谱、食材、口味标签构建知识图谱。
- 图检索：根据用户节点或文本输入，查找相似菜谱节点。
- LLM 生成：调用大模型输出可解释的推荐理由。
- 前端/CLI 展示：Streamlit 或命令行入口渲染推荐结果。

## 技术架构
```
用户输入 → 数据/图检索 (R) → 语义补充 → LLM 生成 (G) → 展示
```
- **Data Layer**：`data_ingest` 下载/清洗 HowToCook，生成 `RecipeRecord`。
- **Graph Layer**：`graph_builder` 将菜谱节点与共享特征构成加权图。
- **Retrieval Layer**：`retrieval` 通过邻域遍历或文本匹配找出候选菜谱。
- **Generation Layer**：`llm_generator` 将检索结果拼成 prompt，并调用 LLM 或本地模板生成解释。
- **Interface Layer**：`pipeline` 串联上述模块，`scripts/run_pipeline.py`/Streamlit 负责交互展示。

## 目录结构
```
graph-rag-recipes/
├── data/
│   ├── raw/            # 原始数据（howtocook_repo）及 howtocook_sample 示例
│   └── processed/      # 清洗后的 JSON（sample_recipes / recipes_index）
├── scripts/
│   ├── bootstrap_data.py  # 准备 HowToCook 数据占位与示例
│   └── run_pipeline.py    # 命令行演示推荐流程
├── src/
│   └── graph_rag_recipes/
│       ├── __init__.py
│       ├── config.py
│       ├── data_ingest.py
│       ├── data_models.py
│       ├── graph_builder.py
│       ├── llm_generator.py
│       ├── pipeline.py
│       ├── retrieval.py
│       ├── ui_components.py
│       ├── embeddings.py
│       └── user_profiles.py
├── pyproject.toml
└── README.md
```

## 模块说明
- `config.py`：统一管理目录、模型及阈值等配置，可添加环境变量读取逻辑。
- `data_models.py`：`RecipeRecord`、`RecommendationResult` 等基础数据结构。
- `data_ingest.py`：处理 HowToCook 数据，当前提供示例样本与占位文件，后续可扩展 GitHub 拉取/增量清洗。
- `graph_builder.py`：基于共享食材与标签计算相似度，并生成 weighted graph。
- `retrieval.py`：从图中检索邻居节点或根据文本进行模糊匹配。
- `llm_generator.py`：封装 LLM 调用（OpenAI/Ollama/GLM 均可），未配置 API Key 时会返回模板化理由。
- `pipeline.py`：串联各层并输出 `RecommendationResult`，支持“用户节点 → 历史菜谱 → 相似菜谱”流程。
- `ui_components.py`：CLI 及 Streamlit 共享的展示辅助函数。
- `embeddings.py`：基于 sentence-transformers 维护菜谱向量索引，提升文本/用户检索的鲁棒性。
- `user_profiles.py`：内置示例用户画像，`U123` 等 ID 会自动映射到特定菜谱节点。

## 使用方式
所有命令均通过 `uv` 执行，确保依赖与解释器一致。

```bash
# 安装依赖
uv sync

# 复制并填写环境变量（用于真实 LLM 调用）
cp .env.example .env
# 编辑 .env，写入 OPENAI_API_KEY / 其他厂商 Key

# 准备/刷新数据
uv run python scripts/bootstrap_data.py \
  --limit 800 \
  --force-processed \
  --strategy auto

# 仅使用本地缓存或示例
uv run python scripts/bootstrap_data.py --skip-download

# 按项目要求体验“用户节点 → 智能推荐”
uv run python scripts/run_pipeline.py U123

# 仍可输入菜名进行检索
uv run python scripts/run_pipeline.py "番茄炒蛋"

# 也可直接使用入口脚本
uv run graph-rag-recipes
```

未来可添加 `uv run streamlit run app.py` 形式的前端，在 `streamlit_app.py` 中引用 `GraphRAGPipeline` 即可。

## LLM 配置与降级策略

- `.env` 中配置 `OPENAI_API_KEY`（或其他 Provider 对应字段，参见 `ProjectConfig.llm_api_key()`）后，`LLMGenerator` 会调用 `gpt-4o-mini` 输出完整的中文推荐解释。
- 如果未安装 OpenAI SDK 或未设置 API Key，系统仍会完成图检索并返回候选菜谱，只是推荐理由将回退为内置模板，描述共享食材/口味的固定文案。  
- 因此在需要展示“大模型生成”效果或提交作业截图时，请确保 `.env` 中的密钥有效，并在执行 `uv run python scripts/run_pipeline.py U123` 之前导出环境变量。

## 数据与环境说明
- `data/raw/howtocook_sample/`：内置 Markdown 小样本，可在离线环境下演示与编写测试。
- `data/processed/sample_recipes.json`：对应的结构化结果，`HowToCookIngestor` 会在缺少真实数据时使用它。
- `src/graph_rag_recipes/user_profiles.py`：示例用户节点（如 U123）关联到这些样本，以保证“番茄炒蛋 → 番茄豆腐汤”等演示稳定。
- `scripts/bootstrap_data.py`：提供 `--force-repo/--force-processed/--limit/--strategy` 等参数，自动拉取仓库并生成 `data/processed/recipes_index.json`。
- `.env.example`：给出 LLM 所需的环境变量模板，与 `python-dotenv` 配合自动加载，确保本地/部署环境不直接暴露密钥。

## 开发计划
1. **数据阶段**：实现 HowToCook 拉取、字段标准化、用户节点建模。
2. **图阶段**：完善多模相似度（向量 + 图结构），支持持久化缓存。
3. **检索阶段**：加入向量 KNN、多跳子图遍历、过滤器（口味、食材）。
4. **生成阶段**：引入 Prompt 模板、Memory、批量解释。
5. **展示阶段**：落地 Streamlit UI、图可视化与录屏 Demo。

## 验证与演示清单
1. `uv run python scripts/bootstrap_data.py --limit 800 --force-processed`：确保最新结构化数据存在。
2. 根据是否需要 LLM 真实输出决定是否在 `.env` 中配置 API Key；无 Key 也可演示完整 GraphRAG 流程，只是理由为模板文案。
3. `uv run python scripts/run_pipeline.py U123`：复现 Project 4 示例（“番茄炒蛋” → “番茄豆腐汤/蛋炒西红柿饭” → 推荐理由）。
4. 需要图示或报告时，可截图 CLI 输出或记录 `result.summary()`，并说明是否启用了 LLM。

该架构已满足课程项目“project 4: 基于 GraphRAG 的推理”需求，可在此基础上持续扩展能力与表现力。
