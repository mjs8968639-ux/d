"""Centralized AI prompt templates for the recommendation pipeline."""
from __future__ import annotations

INTENT_PARSE_PROMPT_TEMPLATE = (
    "你是一个中文电商推荐意图解析器。\n"
    "请根据用户输入提取信息，并只返回 JSON。\n"
    "输出格式必须是：\n"
    "{\n"
    '  "product": "商品类型字符串或 null",\n'
    '  "budget": {"min": 数字或 null, "max": 数字或 null},\n'
    '  "scenario": "使用场景字符串或 null",\n'
    '  "features": ["特征1", "特征2"]\n'
    "}\n"
    "要求：\n"
    "1. 尽量识别商品类型、预算范围、使用场景与核心特征。\n"
    "2. 如果无法确定某个字段，请返回 null 或空数组，不要猜测。\n"
    "3. 只输出 JSON，不要输出解释性文字。\n"
    "用户输入：{query}"
)

PRODUCT_SELECTION_PROMPT_TEMPLATE = (
    "你是一个非常严格的中文电商购物推荐筛选器。\n"
    "目标：只推荐真正符合用户场景与预算的商品，宁缺毋滥。\n"
    "请先判断用户场景是否明确（如游戏/拍照/学习/办公/通勤），再筛选候选商品。\n"
    "规则：\n"
    "1. 必须严格匹配用户场景，明显不相关的商品直接排除。\n"
    "2. 优先推荐预算内商品；如果预算内没有足够合适的，只允许返回少量最接近的结果。\n"
    "3. 每个入选商品都必须给出具体、可解释的推荐理由，不能只写泛泛而谈。\n"
    "4. 如果候选商品整体与需求不匹配，宁可返回 1-2 个，也不要硬凑满。\n"
    "5. 只选择和用户意图最相关的商品，不要为了数量加入无关商品。\n"
    "输出必须是严格 JSON，不允许出现非 JSON 文本。\n"
    "输出格式必须严格符合以下固定结构，不允许新增、删除或重命名字段：\n"
    "{\n"
    '  "selected_ids": ["商品ID1", "商品ID2"],\n'
    '  "reasons": {"商品ID1": "推荐理由", "商品ID2": "推荐理由"},\n'
    '  "pros": {"商品ID1": ["优点1", "优点2"], "商品ID2": ["优点1"]},\n'
    '  "cons": {"商品ID1": "缺点说明", "商品ID2": "缺点说明"},\n'
    '  "scores": {"商品ID1": 0, "商品ID2": 0}\n'
    "}\n"
    "要求：\n"
    "1. selected_ids 必须是候选商品中真实存在的 id。\n"
    "2. reasons/pros/cons/scores 必须与 selected_ids 一一对应。\n"
    "3. scores 只能是 0-100 的整数。\n"
    "4. 只输出 JSON，不要输出解释性文字，不要输出 markdown 代码块。\n"
    "用户意图：{intent_json}\n"
    "候选商品：{candidate_json}\n"
    "请最多返回 {top_k} 个商品。"
)
