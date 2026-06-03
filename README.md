# Smart CS Agent — 多领域智能客服

基于大语言模型的多领域智能客服系统，支持医疗咨询、旅游规划等场景。

## 目标

- 理解 Agent 核心原理（非 demo，可生产使用）
- 支持多领域、多 Agent 协作
- 具备记忆、RAG、MCP 工具调用、评估等完整能力

## 学习路径

以 [Hello-Agents](https://github.com/datawhalechina/Hello-Agents) 为教材，每学一章应用到本项目。

## 进度

| 章节 | 状态 | 完成日期 |
|------|------|----------|
| 第1章 初识智能体 | ✅ 完成 | 2026-06-03 |
| 第2章 智能体发展史 | ✅ 完成 | 2026-06-03 |
| 第3章 大语言模型基础 | ⏳ 待开始 | - |

## 快速开始

1. 安装依赖：`pip install openai requests python-dotenv`
2. 配置 `.env`（已配置好 DeepSeek API）
3. 运行：`python experiments/ch01-first-agent/travel_assistant.py`
