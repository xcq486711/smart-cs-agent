"""
第 2 章 动手体验：ELIZA —— 1966 年的"AI 心理医生"

核心学习点：
1. ELIZA 不"理解"任何话——它只是正则匹配 + 模板替换
2. 规则驱动系统的优势：可预测、可审计、快速
3. 规则驱动系统的致命伤：没有语义理解、无记忆、规则爆炸
4. ELIZA 效应：用户会主动给机器"脑补"智能
"""

import re
import random


# =====================================================================
# 规则库：正则模式 → 可选回复模板
# 优先级从上到下递减（第一条匹配到的规则生效）
# =====================================================================
rules = {
    # 优先级 1：对"需求"的回应
    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?",
    ],

    # 优先级 2：反问"为什么不..."
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?",
    ],

    # 优先级 3：对"我做不到"的回应
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?",
    ],

    # 优先级 4：对"我是/我觉得"的回应
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?",
    ],

    # 优先级 5：提到家庭成员的回应
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?",
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?",
    ],

    # 优先级 6：通配符兜底（最后一条规则，匹配一切）
    r'.*': [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?",
    ],
}


# =====================================================================
# 代词转换：第一人称 ↔ 第二人称
# =====================================================================
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours",
}


def swap_pronouns(phrase):
    """将短语中的第一/第二人称代词互换"""
    words = phrase.lower().split()
    swapped_words = [pronoun_swap.get(word, word) for word in words]
    return " ".join(swapped_words)


def respond(user_input):
    """ELIZA 的核心引擎：逐条匹配规则，返回第一条命中的回复"""
    for pattern, responses in rules.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            captured_group = match.group(1) if match.groups() else ''
            swapped_group = swap_pronouns(captured_group)
            response = random.choice(responses).format(swapped_group)
            return response
    # 理论上是不会走到这的（因为最后一条 .* 会匹配一切）
    return random.choice(rules[r'.*'])


# =====================================================================
# 主程序
# =====================================================================
if __name__ == '__main__':
    print("=" * 50)
    print("ELIZA (1966) — 基于规则的心理治疗师聊天机器人")
    print("提示: 输入 quit/exit/bye 退出")
    print("=" * 50)
    print()
    print("Therapist: Hello! How can I help you today?")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        response = respond(user_input)
        print(f"Therapist: {response}")
