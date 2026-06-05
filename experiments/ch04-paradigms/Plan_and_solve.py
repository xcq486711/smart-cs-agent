"""
Plan-and-Solve Agent — 你的实现任务

任务：补全 Planner 类中的 plan() 方法。
LLM 会输出一个 Python 列表格式的计划，你需要解析它。

已提供的（不需要修改）：
- llm_client.py: HelloAgentsLLM 类
- Executor 类: 按计划逐步执行
- PlanAndSolveAgent 类: 协调规划和执行
"""

import ast
from llm_client import HelloAgentsLLM

# Planner 的 Prompt——告诉 LLM 输出 Python 列表格式的计划
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的：
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

# Executor 的 Prompt——告诉 LLM 专注解决当前这一步
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""


class Planner:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        """
        根据用户问题生成一个行动计划。

        需要你实现的部分：从 LLM 响应中提取计划列表。

        LLM 输出的格式如下（在自然语言中间嵌入代码块）：
        ```python
        ["步骤1", "步骤2", "步骤3"]
        ```

        你的任务是提取 ```python 和 ``` 之间的内容，然后用 ast.literal_eval
        把它从字符串转换成真正的 Python 列表。

        步骤：
        1. 用 self.llm_client.think() 拿到 LLM 响应
        2. 从响应中提取 ```python ... ``` 之间的内容
        3. 用 ast.literal_eval() 把字符串转成列表
        4. 返回列表（出错则返回空列表 []）

        提示：
        - 用 response_text.split("```python") 切割，取 [1]
        - 再用 .split("```") 切割，取 [0]
        - .strip() 清理空白
        - ast.literal_eval() 安全地解析字符串为 Python 对象
        - 用 try/except 包裹整个解析逻辑
        """
        # [TODO] 在这里写你的代码
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        print("--- 正在生成计划 ---")
        response_text = self.llm_client.think(messages=messages) or ""

        print(f"[OK] 计划已生成:\n{response_text}")

        # [TODO] 从这里开始：解析 response_text，提取列表
        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan,list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"[ERROR] 解析计划时出错: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] 解析计划时发生未知错误: {e}")
            return []


class Executor:
    """执行器：不需要修改"""
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        print("\n--- 正在执行计划 ---")

        for i, step in enumerate(plan):
            print(f"\n-> 正在执行步骤 {i+1}/{len(plan)}: {step}")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step,
            )

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages) or ""

            history += f"步骤 {i+1}: {step}\n结果: {response_text}\n\n"
            print(f"[OK] 步骤 {i+1} 已完成，结果: {response_text}")

        return response_text  # 最后一步的响应就是最终答案


class PlanAndSolveAgent:
    """协调器：不需要修改"""
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        print(f"\n--- 开始处理问题 ---\n问题: {question}")

        plan = self.planner.plan(question)
        if not plan:
            print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return None

        final_answer = self.executor.execute(question, plan)
        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")
        return final_answer


# ================================================================
# 测试：等你实现了 plan() 方法后运行
# ================================================================
if __name__ == '__main__':
    llm = HelloAgentsLLM()
    agent = PlanAndSolveAgent(llm)

    question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
    result = agent.run(question)
