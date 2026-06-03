"""
ELIZA 非交互式测试 —— 验证规则引擎的行为

测试重点：
1. 正确匹配：I am sad → 正确捕获并回复
2. 语义盲区：I am NOT happy → 仍然按"I am happy"处理
3. 无记忆：同一句话问两次，回答可能不同，但不会参考历史
4. ELIZA 效应：看起来像在倾听，其实只是在匹配正则
"""

import eliza

test_cases = [
    # [描述, 输入, 预期行为]
    ("正确匹配: 表达情绪", "I am feeling sad today",
     "会匹配 'I am (.*)' 规则，回复类似于 'How long have you been...'"),

    ("语义盲区: 否定句", "I am not happy",
     "会匹配 'I am (.*)' 规则，把 'not happy' 当捕获内容，完全忽略否定含义"),

    ("家庭成员触发词", "My mother is angry with me",
     "会匹配 '.* mother .*' 规则，回复关于 mother 的问题"),

    ("兜底规则: 无关键词", "Today is Tuesday",
     "没有特定规则匹配，走 .* 通配符，回复 'Please tell me more.' 之类"),

    ("无记忆: 重复问题", "I am sad",
     "两次可能回复不同（因为 random.choice），但不会说'你刚才已经说过了'"),

    ("代词转换: 第一人称变第二人称", "I need you to help me",
     "捕获 'you to help me' → 代词转换: 'i to help you' → 套模板"),
]

print("=" * 60)
print("ELIZA 行为测试 —— 验证规则引擎的核心特性")
print("=" * 60)

for desc, user_input, expected in test_cases:
    response = eliza.respond(user_input)
    print(f"\n{'=' * 60}")
    print(f"测试: {desc}")
    print(f"输入: {user_input}")
    print(f"输出: {response}")
    print(f"预期: {expected}")
