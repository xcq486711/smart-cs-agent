"""
ReAct Agent — 你的实现任务

任务：补全 ReActAgent 类中标记了 [TODO] 的三个方法。
这三个方法负责解析 LLM 的输出，把自然语言文本变成可执行的操作。

提供的工具（不需要修改）：
- llm_client.py: HelloAgentsLLM 类，.think(messages) 调用 DeepSeek
- tools.py: ToolExecutor 类，注册和调用工具

你需要实现的方法（按难度排序）：
1. _parse_action_input() — 最简单的，已有提示
2. _parse_action() — 中等，解析工具调用的格式
3. _parse_output() — 最复杂的，解析完整的 Thought + Action
"""

import re
from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search

# LLM 输出的关键格式：
# Thought: [任意文本，可能多行]
# Action: [具体操作]
#
# Action 的两种形式：
#   工具调用: Search[搜索内容]
#   结束任务: Finish[最终答案]

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `Finish[最终答案]` 来输出最终答案。

现在，请开始解决以下问题：
Question: {question}
History: {history}
"""


class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        """主循环：不需要修改"""
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc, question=question, history=history_str
            )

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("错误：LLM 未能返回有效响应。")
                break

            thought, action = self._parse_output(response_text)
            if thought:
                print(f"[Thought] {thought}")
            if not action:
                print("警告：未能解析出有效的 Action，流程终止。")
                break

            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"[Done] 最终答案: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                self.history.append("Observation: 无效的 Action 格式，请检查。")
                continue

            print(f"[Action] {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = (
                tool_function(tool_input)
                if tool_function
                else f"错误：未找到名为 '{tool_name}' 的工具。"
            )

            print(f"[Observation] {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None

    # ================================================================
    # 以下是你要实现的三个方法
    # ================================================================

    def _parse_output(self, text: str):
        """
        [TODO] 从 LLM 的输出文本中解析出 Thought 和 Action。

        输入示例:
            "Thought: 用户想知道华为最新手机。我需要搜索一下。\nAction: Search[华为最新手机]"

        返回:
            (thought_text, action_text)
            例如: ("用户想知道华为最新手机。我需要搜索一下。", "Search[华为最新手机]")

        提示:
            - Thought: 后面一直到 Action: 之前（或文本末尾）是思考内容
            - Action: 后面一直到文本末尾是行动指令
            - 用 re.search + re.DOTALL 处理多行文本
        """
        # [TODO] 在这里写你的代码
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text,re.DOTALL)
        action_match  = re.search(r"Action:\s*(.*?)$",text,re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action


    def _parse_action(self, action_text: str):
        """
        [TODO] 解析 Action 文本，提取工具名和输入参数。

        输入示例:
            "Search[华为最新手机]"

        返回:
            (tool_name, tool_input)
            例如: ("Search", "华为最新手机")

        提示:
            - 格式是 ToolName[input_content]
            - ToolName 只包含字母和数字
            - 用 re.match 从字符串开头匹配（不是 re.search）
        """
        # [TODO] 在这里写你的代码
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)

    def _parse_action_input(self, action_text: str):
        """
        [TODO] 从 Finish[xxx] 中提取最终答案文本。

        输入示例:
            "Finish[华为最新旗舰手机是Mate 70系列...]"

        返回:
            "华为最新旗舰手机是Mate 70系列..."

        提示:
            - 这和 _parse_action 很像，但只需要方括号里的内容
            - 用 re.match + group(1)
        """
        # [TODO] 在这里写你的代码
        final_answer = re.match(r"Finish\[(.*)\]", action_text).group(1)
        return final_answer

# ================================================================
# 测试代码：等你实现了上面三个方法后，去掉注释运行
# ================================================================

if __name__ == '__main__':
    # 初始化 LLM 客户端
    llm = HelloAgentsLLM()

    # 初始化工具执行器，注册搜索工具
    tool_executor = ToolExecutor()
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("Search", search_desc, search)

    # 创建 ReAct Agent
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)

    # 测试问题
    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    result = agent.run(question)
