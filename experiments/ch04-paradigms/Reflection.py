"""
Reflection Agent — 你的实现任务

这次不一样：你要实现的是 Reflection 的核心逻辑，不只是解析。

任务：
1. [TODO 1] Memory 类：一个存储"执行→反思→执行→反思"轨迹的记忆模块
2. [TODO 2] ReflectionAgent.run()：执行-反思-优化 三步迭代循环

已提供的（不需要修改）：
- llm_client.py: HelloAgentsLLM 类
- 三个 Prompt 模板
"""

from llm_client import HelloAgentsLLM
from typing import List, Dict, Any, Optional

# --- 三个 Prompt 模板 ---

INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在算法效率上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种算法上更优的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答"无需改进"。

请直接输出你的反馈，不要包含任何额外的解释。
"""

REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
{last_code_attempt}

# 评审员的反馈：
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""


# ================================================================
# [TODO 1] Memory 类
# ================================================================

class Memory:
    """
    短期记忆模块：记录"执行-反思"循环的完整轨迹。

    需要的方法：
    - add_record(record_type, content): 添加一条记录，type 是 "execution" 或 "reflection"
    - get_trajectory(): 把所有记录格式化为一个文本，用于构建 Prompt
    - get_last_execution(): 获取最近一次执行结果（最近一条 type="execution" 的 content）
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        向记忆中添加一条新记录。

        参数:
        - record_type: "execution" 或 "reflection"
        - content: 记录内容（代码字符串或反馈字符串）
        """
        # [TODO] 实现：创建一个 dict 并 append 到 self.records
        record = {"type": record_type, "content": content}
        self.records.append(record)
        print(f"记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self) -> str:
        """
        将所有记忆格式化为可嵌入 Prompt 的文本。

        格式提示:
        --- 上一轮尝试 (代码) ---
        {execution的content}

        --- 评审员反馈 ---
        {reflection的content}

        遍历 self.records，根据 type 加上不同的标题。
        """
        # [TODO] 实现
        trajectory_parts = []
        for record in self.records:
            if record["type"] == "execution":
                trajectory_parts.append(f"---上一轮尝试(代码)---\n{record['content']}")
            elif record["type"] == "reflection":
                trajectory_parts.append(f"---评审员反馈---\n{record['content']}")

        return "\n\n".join(trajectory_parts)
    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次执行结果。从 records 末尾往前找第一条 type="execution"。
        如果不存在则返回 None。
        """
        # [TODO] 实现
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]

        return None


# ================================================================
# [TODO 2] ReflectionAgent.run() 主循环
# ================================================================

class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def _get_llm_response(self, prompt: str) -> str:
        """调用 LLM 并返回文本响应（已实现）"""
        messages = [{"role": "user", "content": prompt}]
        response = self.llm_client.think(messages=messages)
        return response or ""

    def run(self, task: str):
        """
        执行-反思-优化的迭代循环。

        流程：
        1. 初始执行：用 INITIAL_PROMPT_TEMPLATE 生成初版代码
           → 存入 memory (type="execution")

        2. for 循环 max_iterations 次:
           a. 反思：取 latest execution → 用 REFLECT_PROMPT_TEMPLATE 生成反馈
              → 存入 memory (type="reflection")
              → 如果反馈是"无需改进"，跳出循环

           b. 优化：用 REFINE_PROMPT_TEMPLATE（参考 feedback）生成新代码
              → 存入 memory (type="execution")

        3. 返回最后一次执行的代码

        提示：
        - 每一步用 self._get_llm_response(prompt)
        - 用 self.memory.add_record() 记录每一步
        - 用 self.memory.get_last_execution() 获取最新代码供反思和优化
        - 用 self.memory.get_trajectory() 在需要时回顾整条轨迹
        """
        print(f"\n--- 开始 Reflection 任务 ---\n任务: {task}")

        # [TODO] 实现上面描述的流程
        print("\n--- 正在进行初始尝试 ---")

        init_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        init_code = self._get_llm_response(init_prompt)
        self.memory.add_record("execution", init_code)

        for i in range(self.max_iterations):
            print(f"\n--- 第 {i + 1}/{self.max_iterations} 轮迭代 ---")

            print("\n开始进行反思...")

            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            if "无需改进" in feedback:
                print("\n反思认为代码已无需改进，任务完成。")
                break

            print("\n-> 正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(task=task, last_code_attempt=last_code,feedback=feedback)
            reflect_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", reflect_code)

        final_code = self.memory.get_last_execution()
        print(f"\n--- 任务完成 ---\n最终生成的代码:\n```python\n{final_code}\n```")
        return final_code

# ================================================================
# 测试代码
# ================================================================

if __name__ == '__main__':
    llm = HelloAgentsLLM()
    agent = ReflectionAgent(llm, max_iterations=2)

    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    result = agent.run(task)

    print("\n" + "=" * 50)
    print("最终输出:")
    if result:
        print(result)
    else:
        print("未能生成有效输出")
