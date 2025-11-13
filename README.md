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
│   ├── raw/            # 原始数据或下载占位
│   └── processed/      # 清洗后的样本、向量缓存
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
│       └── ui_components.py
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
- `pipeline.py`：串联各层并输出 `RecommendationResult`，供脚本和 UI 调用。
- `ui_components.py`：CLI 及 Streamlit 共享的展示辅助函数。

## 使用方式
所有命令均通过 `uv` 执行，确保依赖与解释器一致。

```bash
# 安装依赖
uv sync

# 准备数据占位（可多次执行，--force 重新生成）
uv run python scripts/bootstrap_data.py [--force]

# 运行命令行 Demo（可替换查询词）
uv run python scripts/run_pipeline.py "番茄炒蛋"

# 也可直接使用入口脚本
uv run graph-rag-recipes
```

未来可添加 `uv run streamlit run app.py` 形式的前端，在 `streamlit_app.py` 中引用 `GraphRAGPipeline` 即可。

## 开发计划
1. **数据阶段**：实现 HowToCook 拉取、字段标准化、用户节点建模。
2. **图阶段**：完善多模相似度（向量 + 图结构），支持持久化缓存。
3. **检索阶段**：加入向量 KNN、多跳子图遍历、过滤器（口味、食材）。
4. **生成阶段**：引入 Prompt 模板、Memory、批量解释。
5. **展示阶段**：落地 Streamlit UI、图可视化与录屏 Demo。

该架构已满足课程项目“project 4: 基于 GraphRAG 的推理”需求，可在此基础上持续扩展能力与表现力。
