"""
第 1 章 动手体验：第一个智能体（DeepSeek 版）
改编自 Hello-Agents 教材 FirstAgentTest.py

核心学习点：
1. Agent Loop 是怎么运转的：感知→思考→行动→观察，反复循环
2. Thought-Action-Observation 格式：LLM 不是随便输出，而是按"协议"说话
3. 工具是 Agent 的"手"：LLM 不自己查天气，它"决定"调用 get_weather 工具
4. 正则解析：Action 字段被解析出来，真实执行函数，结果喂回 LLM
"""

import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --- 加载 .env ---
# Path(__file__) = experiments/ch01-first-agent/travel_assistant.py
# .parents[2]  = smart-cs-agent/（项目根目录）
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# --- System Prompt：Agent 的"说明书" ---
# 关键设计点：
# 1. 告诉 LLM 它有什么工具可用（就像给员工发了工具箱）
# 2. 规定输出格式（Thought + Action），Agent 和 Parser 之间需要协议
# 3. 强制"每次只输出一对 Thought-Action"——防止 LLM 一次性输出所有步骤（不靠谱）
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 工具说明

你拥有以下工具，每个工具都有明确的用途和限制：

| 工具 | 参数 | 用途 | 返回 |
|---|---|---|---|
| get_weather | city: 城市名称（中文，如"北京"） | 查询该城市当前实时天气 | 自然语言描述，如"北京当前天气：晴，气温25摄氏度" |

# 决策原则

1. 先理解用户要什么 → 再决定是否需要工具 → 如果需要就调用 → 根据结果决定下一步
2. 如果工具返回了错误信息（如"网络问题"），在 Thought 中分析原因，必要时重试一次或告知用户
3. 如果你对某个信息不确定（如用户说的城市名是否存在），直接告知用户你不确定，不要猜测
4. 如果用户的问题不需要工具（如"你好"、"你能做什么"），直接在 Finish 中回复

# 输出格式要求

每次回复必须严格包含一对 Thought 和 Action，格式如下：

Thought: [分析当前情况：已知什么、还缺什么、下一步做什么、为什么这样选择]
Action: [执行的具体操作，必须在同一行写完]

Action 只能是以下两种形式：
- 调用工具：function_name(arg_name="arg_value")
- 结束任务：Finish[完整的最终回复，包含用户需要的所有信息]

# Few-shot 示例

以下是两个完整示例，展示了正确的思考和行为模式：

## 示例 1：需要调用工具

用户请求: "帮我查一下上海今天天气"

Thought: 用户想知道上海今天天气。我需要调用 get_weather 工具获取实时数据。参数 city 应为"上海"。
Action: get_weather(city="上海")

Observation: 上海当前天气：多云，气温22摄氏度

Thought: 已经拿到上海的天气数据，可以直接回复用户。
Action: Finish[上海今天天气为多云，气温22摄氏度。]

## 示例 2：不需要工具

用户请求: "你好，你能帮我做什么？"

Thought: 这是一个问候和功能询问，不需要调用任何工具。我可以直接回复。
Action: Finish[你好！我是智能旅行助手，可以帮你查询世界各地城市的实时天气，并根据天气推荐合适的旅游景点。请告诉我你想了解哪个城市？]

# 重要规则

- 每次只输出一对 Thought-Action，不要一次输出多个
- Action 必须在同一行，不要换行（否则解析会失败）
- 不要预测 Observation 的内容——那是工具执行后由系统填入的
- 当拥有足够信息能回答用户时，立即使用 Finish，不要拖延
"""


# =====================================================================
# 工具函数：Agent 的"手"
# =====================================================================

def get_weather(city: str) -> str:
    """
    通过 wttr.in 免费 API 查询真实天气。
    这是 Agent 不能自己做的事——它需要"手"来帮它做。
    """
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp = current["temp_C"]
        return f"{city}当前天气：{desc}，气温{temp}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


# 工具注册表：Agent 只能调用这里注册的工具
available_tools = {
    "get_weather": get_weather,
}


# =====================================================================
# LLM 客户端：Agent 的"大脑"
# =====================================================================

class DeepSeekClient:
    """
    一个兼容 OpenAI SDK 的客户端。
    DeepSeek API 和 OpenAI API 格式一致，所以直接用 openai 库。

    这就是教材所说的 "OpenAI 兼容接口" 的实际应用——
    你可以把 MODEL_ID 换成任何兼容的服务商，代码不变。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        调用 LLM 生成下一步的 Thought + Action。

        参数：
        - prompt: 包含所有历史记录（用户请求 + 之前的 Thought/Action/Observation）
        - system_prompt: 固定的"说明书"，告诉 LLM 它是什么角色

        返回：LLM 生成的文本（Thought: ...\nAction: ...）
        """
        print("[Thinking] 正在调用 DeepSeek...")
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
            )
            answer = response.choices[0].message.content
            print("[OK] DeepSeek 响应成功。")
            return answer
        except Exception as e:
            print(f"[ERROR] 调用 API 时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


# =====================================================================
# 主程序：Agent Loop
# =====================================================================

def main():
    print("=" * 50)
    print("[START] 智能体启动中...")
    print("=" * 50)

    # 1. 从 .env 读取配置
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model_id = os.getenv("LLM_MODEL_ID")

    if not api_key:
        print("[ERROR] 错误：请在项目根目录的 .env 文件中设置 LLM_API_KEY")
        return

    # 2. 初始化 LLM 客户端
    llm = DeepSeekClient(model=model_id, api_key=api_key, base_url=base_url)

    # 3. 用户输入（任务起点）
    user_prompt = "你好，请帮我查询一下今天北京的天气。"
    prompt_history = [f"用户请求: {user_prompt}"]
    print(f"\n[USER] 用户输入: {user_prompt}\n")

    # 4. Agent Loop —— 核心！
    #    这是整个 Agent 系统的心脏，理解了这个循环就理解了 Agent
    for i in range(5):  # 最多循环 5 次，防止死循环
        print("-" * 40)
        print(f"[LOOP] 循环 {i + 1}（感知 → 思考 → 行动 → 观察）")
        print("-" * 40)

        # 4.1 构建 Prompt：把所有历史记录拼起来喂给 LLM
        full_prompt = "\n".join(prompt_history)

        # 4.2 思考阶段：调用 LLM，让它输出 Thought + Action
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)

        # 4.2.1 截断处理：LLM 可能一次输出多个 Thought-Action 对
        #     但我们只要第一个，保证步进式执行
        match = re.search(
            r"(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)",
            llm_output,
            re.DOTALL,
        )
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print("[WARN]  已截断多余的 Thought-Action 对")

        print(f"\n[MODEL] 模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)

        # 4.3 行动阶段：解析 Action 字段
        action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
        if not action_match:
            observation = "错误: 未能解析到 Action 字段。"
            obs_str = f"Observation: {observation}"
            print(f"[WARN]  {obs_str}")
            prompt_history.append(obs_str)
            continue

        action_str = action_match.group(1).strip()

        # 4.3.1 检查是否结束：Finish[答案]
        if action_str.startswith("Finish"):
            final = re.match(r"Finish\[(.*)\]", action_str)
            if final:
                print("=" * 50)
                print(f"[DONE] 任务完成！\n\n[RESULT] 最终答案:\n{final.group(1)}")
                print("=" * 50)
            break

        # 4.3.2 解析工具名和参数，真实执行函数
        tool_name = re.search(r"(\w+)\(", action_str).group(1)
        args_str = re.search(r"\((.*)\)", action_str).group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        print(f"[TOOL] 执行工具: {tool_name}({kwargs})")

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误：未定义的工具 '{tool_name}'"

        # 4.4 观察阶段：工具的执行结果，包装成 Observation 喂回 LLM
        obs_str = f"Observation: {observation}"
        print(f"[OBSERVE]  {obs_str}")
        prompt_history.append(obs_str)

    else:
        # for 循环正常结束（没 break）说明达到最大次数
        print("\n[WARN]  达到最大循环次数(5)，任务可能未完成。")


if __name__ == "__main__":
    main()
