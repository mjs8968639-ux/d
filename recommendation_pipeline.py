"""
AI 购物推荐系统的核心流程。
每一步都拆分为独立函数，便于后续替换真实 API 与 AI 模型。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import List, Tuple

from urllib import error, request

from ai_prompts import INTENT_PARSE_PROMPT_TEMPLATE, PRODUCT_SELECTION_PROMPT_TEMPLATE
from recommendation_models import (
    ProductCandidate,
    RecommendedProduct,
    RecommendationResponse,
    SearchKeywordPlan,
    UserIntent,
)


FOOD_DATA: List[dict] = [
    {
        "title": "川味麻辣火锅",
        "price": 68,
        "score": 98,
        "reason": "香辣过瘾，适合想吃重口味、喜欢火锅的用户",
        "tag": "辣",
        "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "经典麻辣烫",
        "price": 26,
        "score": 96,
        "reason": "麻辣鲜香，辣味突出，适合想快速解馋",
        "tag": "辣",
        "image_url": "https://images.unsplash.com/photo-1569058242252-92c7e3c1b7b7?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "重庆小面",
        "price": 18,
        "score": 93,
        "reason": "汤面带辣，口味浓郁，适合喜欢面食和辣味的人",
        "tag": "辣",
        "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "湘菜剁椒鱼头",
        "price": 88,
        "score": 95,
        "reason": "剁椒风味鲜辣，湘菜代表口味，适合重辣偏好",
        "tag": "辣",
        "image_url": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "香辣冒菜",
        "price": 32,
        "score": 91,
        "reason": "配菜丰富又香辣，适合想吃辣但又想吃得饱",
        "tag": "辣",
        "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "清汤牛肉粉",
        "price": 24,
        "score": 90,
        "reason": "清淡顺口，汤底鲜而不辣，适合胃口清爽的选择",
        "tag": "清淡",
        "image_url": "https://images.unsplash.com/photo-1562967916-eb82221dfb92?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "鸡胸肉轻食沙拉",
        "price": 35,
        "score": 94,
        "reason": "低油低盐，口味清淡，适合想吃轻食的人",
        "tag": "清淡",
        "image_url": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "日式三文鱼饭团",
        "price": 19,
        "score": 88,
        "reason": "口味清淡，方便轻盈，适合不想吃重辣的时候",
        "tag": "清淡",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "清炒时蔬套餐",
        "price": 22,
        "score": 89,
        "reason": "家常清淡，少油少辣，适合想吃得舒服一点",
        "tag": "清淡",
        "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "番茄鸡蛋盖饭",
        "price": 20,
        "score": 87,
        "reason": "酸甜开胃但不辣，适合清淡口味和日常简餐",
        "tag": "清淡",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "兰州牛肉面",
        "price": 21,
        "score": 86,
        "reason": "面食经典，汤清味足，适合不想吃太重口的午餐",
        "tag": "面食",
        "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
    },
    {
        "title": "煎饺拼小吃套餐",
        "price": 28,
        "score": 84,
        "reason": "小吃组合丰富，适合想随便吃点、口味中等的人",
        "tag": "小吃",
        "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=800&q=80",
    },
]

MOCK_PRODUCTS: List[ProductCandidate] = [
    ProductCandidate(
        id="taobao-1001",
        title="200元预算 游戏耳机 头戴式 7.1声道",
        price=189,
        original_price=259,
        platform="taobao",
        image_url="https://example.com/taobao-1001.jpg",
        sales=35210,
        detail_url="https://example.com/taobao-1001",
        shop_name="旗舰店A",
        tags=["游戏", "耳机", "头戴式"],
        rating=4.8,
    ),
    ProductCandidate(
        id="jd-2001",
        title="轻量化电竞耳机 低延迟麦克风",
        price=219,
        original_price=299,
        platform="jd",
        image_url="https://example.com/jd-2001.jpg",
        sales=24880,
        detail_url="https://example.com/jd-2001",
        shop_name="自营",
        tags=["电竞", "耳机"],
        rating=4.7,
    ),
    ProductCandidate(
        id="pdd-3001",
        title="有线游戏耳机 高保真立体声",
        price=129,
        original_price=199,
        platform="pdd",
        image_url="https://example.com/pdd-3001.jpg",
        sales=51890,
        detail_url="https://example.com/pdd-3001",
        shop_name="数码专营店",
        tags=["游戏", "有线", "高性价比"],
        rating=4.6,
    ),
    ProductCandidate(
        id="tmall-4001",
        title="无线蓝牙降噪耳机 通勤办公",
        price=269,
        original_price=399,
        platform="tmall",
        image_url="https://example.com/tmall-4001.jpg",
        sales=18420,
        detail_url="https://example.com/tmall-4001",
        shop_name="品牌旗舰店",
        tags=["降噪", "无线", "通勤"],
        rating=4.9,
    ),
    ProductCandidate(
        id="jd-2002",
        title="游戏耳麦 直播收音 降噪麦克风",
        price=199,
        original_price=279,
        platform="jd",
        image_url="https://example.com/jd-2002.jpg",
        sales=12110,
        detail_url="https://example.com/jd-2002",
        shop_name="电竞配件店",
        tags=["游戏", "耳麦", "麦克风"],
        rating=4.5,
    ),
    ProductCandidate(id="taobao-1002", title="蓝牙降噪耳机 通勤办公长续航", price=259, original_price=329, platform="taobao", image_url="https://example.com/taobao-1002.jpg", sales=28640, detail_url="https://example.com/taobao-1002", shop_name="数码旗舰店", tags=["耳机", "降噪", "通勤"], rating=4.7),
    ProductCandidate(id="taobao-1003", title="学习台灯 护眼可调色温", price=89, original_price=129, platform="taobao", image_url="https://example.com/taobao-1003.jpg", sales=41200, detail_url="https://example.com/taobao-1003", shop_name="家居生活馆", tags=["学习", "护眼", "台灯"], rating=4.8),
    ProductCandidate(id="taobao-1004", title="机械键盘 68键 无线三模", price=239, original_price=319, platform="taobao", image_url="https://example.com/taobao-1004.jpg", sales=19850, detail_url="https://example.com/taobao-1004", shop_name="键鼠专营店", tags=["键盘", "机械", "无线"], rating=4.6),
    ProductCandidate(id="taobao-1005", title="拍照手机云台 稳定器 便携折叠", price=179, original_price=239, platform="taobao", image_url="https://example.com/taobao-1005.jpg", sales=15680, detail_url="https://example.com/taobao-1005", shop_name="影像器材店", tags=["拍照", "云台", "手机"], rating=4.5),
    ProductCandidate(id="taobao-1006", title="平板支架 追剧学习 金属可调节", price=49, original_price=79, platform="taobao", image_url="https://example.com/taobao-1006.jpg", sales=58320, detail_url="https://example.com/taobao-1006", shop_name="配件小铺", tags=["平板", "支架", "学习"], rating=4.7),
    ProductCandidate(id="taobao-1007", title="运动蓝牙耳机 耳挂式 防汗", price=159, original_price=219, platform="taobao", image_url="https://example.com/taobao-1007.jpg", sales=27400, detail_url="https://example.com/taobao-1007", shop_name="运动数码馆", tags=["运动", "耳机", "蓝牙"], rating=4.4),
    ProductCandidate(id="taobao-1008", title="人体工学办公椅 久坐腰靠", price=499, original_price=699, platform="taobao", image_url="https://example.com/taobao-1008.jpg", sales=10320, detail_url="https://example.com/taobao-1008", shop_name="办公家具店", tags=["办公", "椅子", "人体工学"], rating=4.6),
    ProductCandidate(id="jd-2003", title="京东自营 游戏显示器 27英寸 2K 165Hz", price=1199, original_price=1499, platform="jd", image_url="https://example.com/jd-2003.jpg", sales=8820, detail_url="https://example.com/jd-2003", shop_name="京东自营", tags=["显示器", "游戏", "2K"], rating=4.8),
    ProductCandidate(id="jd-2004", title="笔记本散热支架 可折叠 金属", price=69, original_price=99, platform="jd", image_url="https://example.com/jd-2004.jpg", sales=23410, detail_url="https://example.com/jd-2004", shop_name="京东自营", tags=["笔记本", "散热", "支架"], rating=4.7),
    ProductCandidate(id="jd-2005", title="学习平板 11英寸 8G+128G", price=1499, original_price=1899, platform="jd", image_url="https://example.com/jd-2005.jpg", sales=6610, detail_url="https://example.com/jd-2005", shop_name="数码自营", tags=["学习", "平板", "办公"], rating=4.6),
    ProductCandidate(id="jd-2006", title="拍照补光灯 手机直播美颜灯", price=129, original_price=169, platform="jd", image_url="https://example.com/jd-2006.jpg", sales=14500, detail_url="https://example.com/jd-2006", shop_name="直播器材店", tags=["拍照", "直播", "补光"], rating=4.5),
    ProductCandidate(id="jd-2007", title="无线鼠标 静音办公 便携", price=59, original_price=89, platform="jd", image_url="https://example.com/jd-2007.jpg", sales=35120, detail_url="https://example.com/jd-2007", shop_name="办公外设店", tags=["鼠标", "办公", "无线"], rating=4.8),
    ProductCandidate(id="jd-2008", title="游戏手柄 PC/手机双模", price=149, original_price=199, platform="jd", image_url="https://example.com/jd-2008.jpg", sales=17650, detail_url="https://example.com/jd-2008", shop_name="游戏外设店", tags=["游戏", "手柄", "双模"], rating=4.6),
    ProductCandidate(id="pdd-3002", title="性价比机械键盘 RGB背光", price=129, original_price=179, platform="pdd", image_url="https://example.com/pdd-3002.jpg", sales=76430, detail_url="https://example.com/pdd-3002", shop_name="数码工厂店", tags=["键盘", "机械", "RGB"], rating=4.5),
    ProductCandidate(id="pdd-3003", title="学生平板支架 可旋转 追剧学习", price=39, original_price=59, platform="pdd", image_url="https://example.com/pdd-3003.jpg", sales=91820, detail_url="https://example.com/pdd-3003", shop_name="学生好物店", tags=["学习", "支架", "平板"], rating=4.4),
    ProductCandidate(id="pdd-3004", title="拍照三脚架 手机直播支架", price=89, original_price=129, platform="pdd", image_url="https://example.com/pdd-3004.jpg", sales=39210, detail_url="https://example.com/pdd-3004", shop_name="影像配件店", tags=["拍照", "三脚架", "直播"], rating=4.5),
    ProductCandidate(id="pdd-3005", title="通勤真无线耳机 轻巧降噪", price=199, original_price=259, platform="pdd", image_url="https://example.com/pdd-3005.jpg", sales=52780, detail_url="https://example.com/pdd-3005", shop_name="耳机优选店", tags=["耳机", "通勤", "降噪"], rating=4.6),
    ProductCandidate(id="pdd-3006", title="办公显示器支架 升降旋转", price=169, original_price=229, platform="pdd", image_url="https://example.com/pdd-3006.jpg", sales=24650, detail_url="https://example.com/pdd-3006", shop_name="办公装备店", tags=["办公", "显示器", "支架"], rating=4.7),
    ProductCandidate(id="pdd-3007", title="运动水杯 大容量吸管杯", price=29, original_price=49, platform="pdd", image_url="https://example.com/pdd-3007.jpg", sales=112300, detail_url="https://example.com/pdd-3007", shop_name="日用百货店", tags=["运动", "水杯", "便携"], rating=4.4),
    ProductCandidate(id="pdd-3008", title="蓝牙音箱 便携低音炮", price=99, original_price=149, platform="pdd", image_url="https://example.com/pdd-3008.jpg", sales=68450, detail_url="https://example.com/pdd-3008", shop_name="音频小铺", tags=["音箱", "蓝牙", "便携"], rating=4.5),
    ProductCandidate(id="tmall-4002", title="旗舰拍照手机 影像算法升级", price=3999, original_price=4599, platform="tmall", image_url="https://example.com/tmall-4002.jpg", sales=14320, detail_url="https://example.com/tmall-4002", shop_name="品牌旗舰店", tags=["手机", "拍照", "旗舰"], rating=4.9),
    ProductCandidate(id="tmall-4003", title="轻薄办公笔记本 14英寸 高色域", price=3299, original_price=3899, platform="tmall", image_url="https://example.com/tmall-4003.jpg", sales=9320, detail_url="https://example.com/tmall-4003", shop_name="品牌专营店", tags=["笔记本", "办公", "轻薄"], rating=4.8),
    ProductCandidate(id="tmall-4004", title="儿童学习桌椅套装 护脊", price=799, original_price=1099, platform="tmall", image_url="https://example.com/tmall-4004.jpg", sales=6210, detail_url="https://example.com/tmall-4004", shop_name="家居旗舰店", tags=["学习", "桌椅", "儿童"], rating=4.7),
    ProductCandidate(id="tmall-4005", title="降噪头戴耳机 高保真 音质提升", price=459, original_price=599, platform="tmall", image_url="https://example.com/tmall-4005.jpg", sales=18440, detail_url="https://example.com/tmall-4005", shop_name="音频旗舰店", tags=["耳机", "降噪", "头戴式"], rating=4.8),
    ProductCandidate(id="tmall-4006", title="直播摄像头 1080P 自动对焦", price=229, original_price=299, platform="tmall", image_url="https://example.com/tmall-4006.jpg", sales=11280, detail_url="https://example.com/tmall-4006", shop_name="直播设备店", tags=["直播", "摄像头", "办公"], rating=4.6),
    ProductCandidate(id="tmall-4007", title="跑步臂包 手机收纳防水", price=39, original_price=69, platform="tmall", image_url="https://example.com/tmall-4007.jpg", sales=27100, detail_url="https://example.com/tmall-4007", shop_name="运动旗舰店", tags=["运动", "跑步", "手机"], rating=4.5),
    ProductCandidate(id="tmall-4008", title="智能路由器 WiFi6 全屋覆盖", price=299, original_price=399, platform="tmall", image_url="https://example.com/tmall-4008.jpg", sales=16520, detail_url="https://example.com/tmall-4008", shop_name="网络设备店", tags=["路由器", "网络", "WiFi6"], rating=4.7),
    ProductCandidate(id="douyin-5001", title="短视频直播支架 俯拍补光套装", price=119, original_price=169, platform="douyin", image_url="https://example.com/douyin-5001.jpg", sales=48320, detail_url="https://example.com/douyin-5001", shop_name="直播好物店", tags=["直播", "支架", "补光"], rating=4.6),
    ProductCandidate(id="douyin-5002", title="手机拍照镜头套装 广角微距", price=99, original_price=149, platform="douyin", image_url="https://example.com/douyin-5002.jpg", sales=21450, detail_url="https://example.com/douyin-5002", shop_name="拍摄器材店", tags=["拍照", "手机", "镜头"], rating=4.4),
    ProductCandidate(id="douyin-5003", title="桌面小音箱 电脑外放 立体声", price=79, original_price=109, platform="douyin", image_url="https://example.com/douyin-5003.jpg", sales=32560, detail_url="https://example.com/douyin-5003", shop_name="音频甄选店", tags=["音箱", "电脑", "桌面"], rating=4.5),
    ProductCandidate(id="douyin-5004", title="学生单词耳机 英语听力学习", price=69, original_price=99, platform="douyin", image_url="https://example.com/douyin-5004.jpg", sales=14580, detail_url="https://example.com/douyin-5004", shop_name="学习装备店", tags=["学习", "耳机", "英语"], rating=4.3),
    ProductCandidate(id="douyin-5005", title="电竞鼠标 高DPI 编程游戏双适用", price=149, original_price=199, platform="douyin", image_url="https://example.com/douyin-5005.jpg", sales=29640, detail_url="https://example.com/douyin-5005", shop_name="外设优选店", tags=["鼠标", "电竞", "游戏"], rating=4.7),
    ProductCandidate(id="douyin-5006", title="轻量跑鞋 男士缓震透气", price=259, original_price=339, platform="douyin", image_url="https://example.com/douyin-5006.jpg", sales=20110, detail_url="https://example.com/douyin-5006", shop_name="运动鞋服店", tags=["运动", "跑鞋", "缓震"], rating=4.6),
    ProductCandidate(id="douyin-5007", title="办公机械键盘 静音红轴", price=209, original_price=279, platform="douyin", image_url="https://example.com/douyin-5007.jpg", sales=16740, detail_url="https://example.com/douyin-5007", shop_name="键鼠优选店", tags=["键盘", "办公", "静音"], rating=4.6),
    ProductCandidate(id="douyin-5008", title="家庭投影仪 便携观影 4K解码", price=699, original_price=999, platform="douyin", image_url="https://example.com/douyin-5008.jpg", sales=8420, detail_url="https://example.com/douyin-5008", shop_name="影音旗舰店", tags=["投影仪", "观影", "家庭"], rating=4.5),
    ProductCandidate(id="amazon-6001", title="Wireless Noise Cancelling Headphones", price=89, original_price=129, platform="amazon", image_url="https://example.com/amazon-6001.jpg", sales=45210, detail_url="https://example.com/amazon-6001", shop_name="Amazon Global", tags=["earphones", "noise cancelling", "travel"], rating=4.6),
    ProductCandidate(id="amazon-6002", title="Portable Bluetooth Speaker Waterproof", price=39, original_price=59, platform="amazon", image_url="https://example.com/amazon-6002.jpg", sales=78300, detail_url="https://example.com/amazon-6002", shop_name="Amazon Global", tags=["speaker", "bluetooth", "outdoor"], rating=4.5),
    ProductCandidate(id="amazon-6003", title="Mechanical Keyboard Compact 75%", price=74, original_price=99, platform="amazon", image_url="https://example.com/amazon-6003.jpg", sales=36420, detail_url="https://example.com/amazon-6003", shop_name="Amazon Global", tags=["keyboard", "mechanical", "compact"], rating=4.7),
    ProductCandidate(id="amazon-6004", title="Webcam Full HD Auto Focus", price=49, original_price=69, platform="amazon", image_url="https://example.com/amazon-6004.jpg", sales=26880, detail_url="https://example.com/amazon-6004", shop_name="Amazon Global", tags=["webcam", "office", "video call"], rating=4.4),
    ProductCandidate(id="amazon-6005", title="Laptop Stand Adjustable Aluminum", price=27, original_price=39, platform="amazon", image_url="https://example.com/amazon-6005.jpg", sales=50120, detail_url="https://example.com/amazon-6005", shop_name="Amazon Global", tags=["laptop", "stand", "office"], rating=4.8),
    ProductCandidate(id="amazon-6006", title="Phone Gimbal Stabilizer for Vlog", price=99, original_price=139, platform="amazon", image_url="https://example.com/amazon-6006.jpg", sales=11940, detail_url="https://example.com/amazon-6006", shop_name="Amazon Global", tags=["camera", "gimbal", "vlog"], rating=4.5),
    ProductCandidate(id="amazon-6007", title="E-reader 6 inch Eye-friendly Display", price=109, original_price=129, platform="amazon", image_url="https://example.com/amazon-6007.jpg", sales=14350, detail_url="https://example.com/amazon-6007", shop_name="Amazon Global", tags=["reading", "study", "tablet"], rating=4.7),
    ProductCandidate(id="amazon-6008", title="Gaming Mouse RGB Programmable", price=29, original_price=49, platform="amazon", image_url="https://example.com/amazon-6008.jpg", sales=69200, detail_url="https://example.com/amazon-6008", shop_name="Amazon Global", tags=["gaming", "mouse", "rgb"], rating=4.6),

    # 手机类
    ProductCandidate(id="phone-7001", title="旗舰拍照手机 1亿像素 夜景增强", price=4299, original_price=4999, platform="jd", image_url="https://example.com/phone-7001.jpg", sales=22100, detail_url="https://example.com/phone-7001", shop_name="手机自营旗舰店", tags=["手机", "拍照", "旗舰"], rating=4.9),
    ProductCandidate(id="phone-7002", title="轻薄5G手机 大电池 长续航", price=1799, original_price=2199, platform="taobao", image_url="https://example.com/phone-7002.jpg", sales=48120, detail_url="https://example.com/phone-7002", shop_name="数码专卖店", tags=["手机", "5G", "续航"], rating=4.6),
    ProductCandidate(id="phone-7003", title="千元拍照手机 5000mAh 电池", price=999, original_price=1299, platform="pdd", image_url="https://example.com/phone-7003.jpg", sales=86230, detail_url="https://example.com/phone-7003", shop_name="手机工厂店", tags=["手机", "拍照", "千元机"], rating=4.5),
    ProductCandidate(id="phone-7004", title="游戏手机 144Hz 高刷屏 液冷散热", price=2999, original_price=3499, platform="tmall", image_url="https://example.com/phone-7004.jpg", sales=16340, detail_url="https://example.com/phone-7004", shop_name="品牌旗舰店", tags=["手机", "游戏", "高刷"], rating=4.8),
    ProductCandidate(id="phone-7005", title="小屏旗舰手机 便携单手操作", price=3899, original_price=4399, platform="jd", image_url="https://example.com/phone-7005.jpg", sales=10420, detail_url="https://example.com/phone-7005", shop_name="品牌自营", tags=["手机", "小屏", "旗舰"], rating=4.7),
    ProductCandidate(id="phone-7006", title="长辈智能手机 大字体 简洁模式", price=799, original_price=999, platform="pdd", image_url="https://example.com/phone-7006.jpg", sales=55210, detail_url="https://example.com/phone-7006", shop_name="百货优选店", tags=["手机", "长辈", "易用"], rating=4.4),
    ProductCandidate(id="phone-7007", title="学生手机 性价比高 大内存", price=1299, original_price=1599, platform="douyin", image_url="https://example.com/phone-7007.jpg", sales=35190, detail_url="https://example.com/phone-7007", shop_name="数码优选店", tags=["手机", "学生", "性价比"], rating=4.5),
    ProductCandidate(id="phone-7008", title="折叠屏手机 大屏办公 影像升级", price=7999, original_price=8999, platform="tmall", image_url="https://example.com/phone-7008.jpg", sales=8420, detail_url="https://example.com/phone-7008", shop_name="品牌旗舰店", tags=["手机", "折叠屏", "办公"], rating=4.8),
    ProductCandidate(id="phone-7009", title="直播拍照手机 前后双摄 美颜优化", price=2499, original_price=2999, platform="taobao", image_url="https://example.com/phone-7009.jpg", sales=27460, detail_url="https://example.com/phone-7009", shop_name="直播数码馆", tags=["手机", "直播", "拍照"], rating=4.6),
    ProductCandidate(id="phone-7010", title="防水三防手机 户外耐用", price=1599, original_price=1899, platform="jd", image_url="https://example.com/phone-7010.jpg", sales=12660, detail_url="https://example.com/phone-7010", shop_name="户外数码店", tags=["手机", "户外", "防水"], rating=4.5),
    ProductCandidate(id="phone-7011", title="影像旗舰手机 专业人像模式", price=5699, original_price=6499, platform="jd", image_url="https://example.com/phone-7011.jpg", sales=18320, detail_url="https://example.com/phone-7011", shop_name="影像旗舰店", tags=["手机", "影像", "人像"], rating=4.9),
    ProductCandidate(id="phone-7012", title="高刷直屏手机 游戏体验流畅", price=2199, original_price=2599, platform="pdd", image_url="https://example.com/phone-7012.jpg", sales=44210, detail_url="https://example.com/phone-7012", shop_name="手机专营店", tags=["手机", "高刷", "游戏"], rating=4.6),
    ProductCandidate(id="phone-7013", title="商务手机 安全加密 双卡双待", price=3399, original_price=3999, platform="tmall", image_url="https://example.com/phone-7013.jpg", sales=9120, detail_url="https://example.com/phone-7013", shop_name="商务旗舰店", tags=["手机", "商务", "安全"], rating=4.7),
    ProductCandidate(id="phone-7014", title="入门智能手机 适合备用机", price=599, original_price=799, platform="douyin", image_url="https://example.com/phone-7014.jpg", sales=70410, detail_url="https://example.com/phone-7014", shop_name="入门数码店", tags=["手机", "入门", "备用"], rating=4.3),
    ProductCandidate(id="phone-7015", title="超长续航手机 6000mAh 大电池", price=1499, original_price=1899, platform="taobao", image_url="https://example.com/phone-7015.jpg", sales=39480, detail_url="https://example.com/phone-7015", shop_name="续航优选店", tags=["手机", "续航", "电池"], rating=4.6),
    ProductCandidate(id="phone-7016", title="拍照手机 光学防抖 夜景人像", price=2799, original_price=3299, platform="jd", image_url="https://example.com/phone-7016.jpg", sales=28850, detail_url="https://example.com/phone-7016", shop_name="拍照旗舰店", tags=["手机", "拍照", "防抖"], rating=4.7),
    ProductCandidate(id="phone-7017", title="儿童智能手机 家长管控模式", price=899, original_price=1099, platform="pdd", image_url="https://example.com/phone-7017.jpg", sales=13920, detail_url="https://example.com/phone-7017", shop_name="亲子数码店", tags=["手机", "儿童", "管控"], rating=4.4),
    ProductCandidate(id="phone-7018", title="轻奢商务手机 金属中框 高质感", price=4999, original_price=5599, platform="tmall", image_url="https://example.com/phone-7018.jpg", sales=5120, detail_url="https://example.com/phone-7018", shop_name="高端手机店", tags=["手机", "商务", "高端"], rating=4.8),
    ProductCandidate(id="phone-7019", title="双卡双待手机 兼容主流平台", price=1199, original_price=1499, platform="douyin", image_url="https://example.com/phone-7019.jpg", sales=26780, detail_url="https://example.com/phone-7019", shop_name="性价比数码店", tags=["手机", "双卡", "实用"], rating=4.5),
    ProductCandidate(id="phone-7020", title="学生备用手机 低价实用", price=499, original_price=699, platform="taobao", image_url="https://example.com/phone-7020.jpg", sales=92800, detail_url="https://example.com/phone-7020", shop_name="手机超市", tags=["手机", "学生", "低价"], rating=4.2),

    # 耳机类
    ProductCandidate(id="ear-8001", title="游戏耳机 7.1声道 低延迟麦克风", price=199, original_price=269, platform="jd", image_url="https://example.com/ear-8001.jpg", sales=52340, detail_url="https://example.com/ear-8001", shop_name="电竞外设店", tags=["耳机", "游戏", "麦克风"], rating=4.7),
    ProductCandidate(id="ear-8002", title="降噪头戴耳机 通勤办公", price=459, original_price=599, platform="tmall", image_url="https://example.com/ear-8002.jpg", sales=21780, detail_url="https://example.com/ear-8002", shop_name="音频旗舰店", tags=["耳机", "降噪", "通勤"], rating=4.8),
    ProductCandidate(id="ear-8003", title="真无线蓝牙耳机 轻巧防汗", price=129, original_price=169, platform="pdd", image_url="https://example.com/ear-8003.jpg", sales=86520, detail_url="https://example.com/ear-8003", shop_name="耳机工厂店", tags=["耳机", "无线", "蓝牙"], rating=4.5),
    ProductCandidate(id="ear-8004", title="耳麦 直播收音 高清降噪", price=189, original_price=239, platform="taobao", image_url="https://example.com/ear-8004.jpg", sales=18420, detail_url="https://example.com/ear-8004", shop_name="直播设备店", tags=["耳机", "直播", "耳麦"], rating=4.6),
    ProductCandidate(id="ear-8005", title="运动骨传导耳机 防水防汗", price=299, original_price=399, platform="jd", image_url="https://example.com/ear-8005.jpg", sales=23950, detail_url="https://example.com/ear-8005", shop_name="运动数码店", tags=["耳机", "运动", "骨传导"], rating=4.5),
    ProductCandidate(id="ear-8006", title="入耳式耳机 高解析音质", price=79, original_price=109, platform="douyin", image_url="https://example.com/ear-8006.jpg", sales=65210, detail_url="https://example.com/ear-8006", shop_name="音频优选店", tags=["耳机", "入耳式", "音质"], rating=4.4),
    ProductCandidate(id="ear-8007", title="ANC主动降噪耳机 飞行通勤", price=529, original_price=699, platform="amazon", image_url="https://example.com/ear-8007.jpg", sales=19860, detail_url="https://example.com/ear-8007", shop_name="Amazon Global", tags=["耳机", "降噪", "旅行"], rating=4.7),
    ProductCandidate(id="ear-8008", title="电竞入耳耳机 双动圈", price=159, original_price=219, platform="tmall", image_url="https://example.com/ear-8008.jpg", sales=32450, detail_url="https://example.com/ear-8008", shop_name="电竞旗舰店", tags=["耳机", "电竞", "入耳"], rating=4.6),
    ProductCandidate(id="ear-8009", title="学生英语听力耳机 轻便有线", price=39, original_price=59, platform="pdd", image_url="https://example.com/ear-8009.jpg", sales=112200, detail_url="https://example.com/ear-8009", shop_name="学习用品店", tags=["耳机", "学习", "有线"], rating=4.3),
    ProductCandidate(id="ear-8010", title="会议耳机 带麦克风 长续航", price=249, original_price=329, platform="jd", image_url="https://example.com/ear-8010.jpg", sales=14670, detail_url="https://example.com/ear-8010", shop_name="办公音频店", tags=["耳机", "会议", "麦克风"], rating=4.5),
    ProductCandidate(id="ear-8011", title="开放式耳机 不入耳 舒适佩戴", price=349, original_price=449, platform="taobao", image_url="https://example.com/ear-8011.jpg", sales=20430, detail_url="https://example.com/ear-8011", shop_name="新锐音频店", tags=["耳机", "开放式", "舒适"], rating=4.7),
    ProductCandidate(id="ear-8012", title="HiFi头戴耳机 监听级音质", price=699, original_price=899, platform="tmall", image_url="https://example.com/ear-8012.jpg", sales=9120, detail_url="https://example.com/ear-8012", shop_name="HiFi旗舰店", tags=["耳机", "HiFi", "头戴式"], rating=4.8),
    ProductCandidate(id="ear-8013", title="儿童耳机 限音保护 安全听力", price=89, original_price=129, platform="taobao", image_url="https://example.com/ear-8013.jpg", sales=38320, detail_url="https://example.com/ear-8013", shop_name="母婴数码店", tags=["耳机", "儿童", "限音"], rating=4.4),
    ProductCandidate(id="ear-8014", title="电竞头戴耳机 RGB灯效 震动反馈", price=259, original_price=329, platform="douyin", image_url="https://example.com/ear-8014.jpg", sales=27410, detail_url="https://example.com/ear-8014", shop_name="外设直播店", tags=["耳机", "电竞", "RGB"], rating=4.6),
    ProductCandidate(id="ear-8015", title="便携蓝牙耳机 口袋充电仓", price=119, original_price=159, platform="pdd", image_url="https://example.com/ear-8015.jpg", sales=78450, detail_url="https://example.com/ear-8015", shop_name="无线耳机店", tags=["耳机", "蓝牙", "便携"], rating=4.5),
    ProductCandidate(id="ear-8016", title="直播监听耳机 低音增强", price=219, original_price=289, platform="jd", image_url="https://example.com/ear-8016.jpg", sales=11240, detail_url="https://example.com/ear-8016", shop_name="直播音频店", tags=["耳机", "监听", "直播"], rating=4.5),
    ProductCandidate(id="ear-8017", title="通勤小耳机 超轻量 半入耳", price=99, original_price=129, platform="amazon", image_url="https://example.com/ear-8017.jpg", sales=46220, detail_url="https://example.com/ear-8017", shop_name="Amazon Global", tags=["耳机", "通勤", "轻量"], rating=4.6),
    ProductCandidate(id="ear-8018", title="游戏耳麦 可拆卸麦克风", price=169, original_price=229, platform="taobao", image_url="https://example.com/ear-8018.jpg", sales=29650, detail_url="https://example.com/ear-8018", shop_name="游戏配件店", tags=["耳机", "耳麦", "游戏"], rating=4.6),
    ProductCandidate(id="ear-8019", title="降噪耳塞 旅行睡眠专用", price=59, original_price=89, platform="tmall", image_url="https://example.com/ear-8019.jpg", sales=31670, detail_url="https://example.com/ear-8019", shop_name="旅行好物店", tags=["耳机", "降噪", "睡眠"], rating=4.4),
    ProductCandidate(id="ear-8020", title="无线电竞耳机 低延迟 立体声", price=329, original_price=429, platform="jd", image_url="https://example.com/ear-8020.jpg", sales=18640, detail_url="https://example.com/ear-8020", shop_name="电竞自营店", tags=["耳机", "电竞", "无线"], rating=4.7),

    # 电脑类
    ProductCandidate(id="pc-9001", title="轻薄办公笔记本 14英寸 高色域", price=3299, original_price=3899, platform="tmall", image_url="https://example.com/pc-9001.jpg", sales=9320, detail_url="https://example.com/pc-9001", shop_name="品牌专营店", tags=["电脑", "笔记本", "办公"], rating=4.8),
    ProductCandidate(id="pc-9002", title="游戏本 RTX显卡 144Hz 高刷屏", price=6999, original_price=7999, platform="jd", image_url="https://example.com/pc-9002.jpg", sales=12840, detail_url="https://example.com/pc-9002", shop_name="游戏本自营", tags=["电脑", "游戏本", "高刷"], rating=4.9),
    ProductCandidate(id="pc-9003", title="台式主机 性能办公 多开稳定", price=2499, original_price=2899, platform="taobao", image_url="https://example.com/pc-9003.jpg", sales=16420, detail_url="https://example.com/pc-9003", shop_name="装机优选店", tags=["电脑", "台式机", "办公"], rating=4.6),
    ProductCandidate(id="pc-9004", title="迷你主机 省空间 低功耗", price=1699, original_price=1999, platform="pdd", image_url="https://example.com/pc-9004.jpg", sales=28760, detail_url="https://example.com/pc-9004", shop_name="主机工厂店", tags=["电脑", "迷你主机", "省空间"], rating=4.5),
    ProductCandidate(id="pc-9005", title="高性能游戏台式机 32G内存", price=5699, original_price=6399, platform="jd", image_url="https://example.com/pc-9005.jpg", sales=8420, detail_url="https://example.com/pc-9005", shop_name="整机自营店", tags=["电脑", "游戏", "台式机"], rating=4.8),
    ProductCandidate(id="pc-9006", title="大学生学习笔记本 便携续航", price=2799, original_price=3299, platform="douyin", image_url="https://example.com/pc-9006.jpg", sales=19640, detail_url="https://example.com/pc-9006", shop_name="学习电脑店", tags=["电脑", "学习", "便携"], rating=4.6),
    ProductCandidate(id="pc-9007", title="设计师笔记本 高色域 独显", price=7999, original_price=8999, platform="tmall", image_url="https://example.com/pc-9007.jpg", sales=5120, detail_url="https://example.com/pc-9007", shop_name="设计旗舰店", tags=["电脑", "设计", "高色域"], rating=4.9),
    ProductCandidate(id="pc-9008", title="二手办公电脑 性价比主机", price=899, original_price=1299, platform="pdd", image_url="https://example.com/pc-9008.jpg", sales=40810, detail_url="https://example.com/pc-9008", shop_name="电脑超市", tags=["电脑", "二手", "办公"], rating=4.3),
    ProductCandidate(id="pc-9009", title="Mac风轻薄本 长续航 无风扇", price=4599, original_price=5299, platform="amazon", image_url="https://example.com/pc-9009.jpg", sales=10420, detail_url="https://example.com/pc-9009", shop_name="Amazon Global", tags=["电脑", "轻薄本", "续航"], rating=4.7),
    ProductCandidate(id="pc-9010", title="直播编译主机 高速SSD", price=3599, original_price=4099, platform="jd", image_url="https://example.com/pc-9010.jpg", sales=7410, detail_url="https://example.com/pc-9010", shop_name="创作电脑店", tags=["电脑", "直播", "编译"], rating=4.6),
    ProductCandidate(id="pc-9011", title="办公一体机 27英寸 大屏", price=4299, original_price=4799, platform="tmall", image_url="https://example.com/pc-9011.jpg", sales=5620, detail_url="https://example.com/pc-9011", shop_name="办公旗舰店", tags=["电脑", "一体机", "办公"], rating=4.6),
    ProductCandidate(id="pc-9012", title="入门笔记本 学生网课 轻便", price=1999, original_price=2399, platform="taobao", image_url="https://example.com/pc-9012.jpg", sales=36210, detail_url="https://example.com/pc-9012", shop_name="学习数码店", tags=["电脑", "笔记本", "入门"], rating=4.4),
    ProductCandidate(id="pc-9013", title="图形工作站 大内存 高稳定", price=12999, original_price=14999, platform="jd", image_url="https://example.com/pc-9013.jpg", sales=1240, detail_url="https://example.com/pc-9013", shop_name="专业电脑店", tags=["电脑", "工作站", "设计"], rating=4.9),
    ProductCandidate(id="pc-9014", title="游戏主机 Mini ITX 便携", price=3899, original_price=4399, platform="douyin", image_url="https://example.com/pc-9014.jpg", sales=11920, detail_url="https://example.com/pc-9014", shop_name="DIY电脑店", tags=["电脑", "游戏", "主机"], rating=4.7),
    ProductCandidate(id="pc-9015", title="学生党轻薄本 16G内存", price=2599, original_price=2999, platform="pdd", image_url="https://example.com/pc-9015.jpg", sales=27460, detail_url="https://example.com/pc-9015", shop_name="学生电脑馆", tags=["电脑", "学生", "轻薄"], rating=4.5),
    ProductCandidate(id="pc-9016", title="编程开发本 多接口 扩展强", price=3699, original_price=4299, platform="taobao", image_url="https://example.com/pc-9016.jpg", sales=9320, detail_url="https://example.com/pc-9016", shop_name="程序员电脑店", tags=["电脑", "编程", "开发"], rating=4.7),
    ProductCandidate(id="pc-9017", title="显卡台式机 2K游戏 高帧率", price=5899, original_price=6599, platform="jd", image_url="https://example.com/pc-9017.jpg", sales=6800, detail_url="https://example.com/pc-9017", shop_name="电竞整机店", tags=["电脑", "显卡", "游戏"], rating=4.8),
    ProductCandidate(id="pc-9018", title="长续航商务本 指纹识别", price=4399, original_price=4899, platform="tmall", image_url="https://example.com/pc-9018.jpg", sales=9820, detail_url="https://example.com/pc-9018", shop_name="商务电脑旗舰店", tags=["电脑", "商务", "续航"], rating=4.8),
    ProductCandidate(id="pc-9019", title="平价台式电脑 上网办公", price=1499, original_price=1799, platform="pdd", image_url="https://example.com/pc-9019.jpg", sales=45230, detail_url="https://example.com/pc-9019", shop_name="平价电脑店", tags=["电脑", "台式机", "平价"], rating=4.2),
    ProductCandidate(id="pc-9020", title="便携二合一笔记本 触控屏", price=4999, original_price=5599, platform="amazon", image_url="https://example.com/pc-9020.jpg", sales=6140, detail_url="https://example.com/pc-9020", shop_name="Amazon Global", tags=["电脑", "二合一", "触控"], rating=4.7),

    # 配件类
    ProductCandidate(id="acc-10001", title="手机支架 桌面可调节", price=39, original_price=59, platform="taobao", image_url="https://example.com/acc-10001.jpg", sales=128400, detail_url="https://example.com/acc-10001", shop_name="配件小铺", tags=["配件", "支架", "手机"], rating=4.7),
    ProductCandidate(id="acc-10002", title="电脑散热支架 金属折叠", price=69, original_price=99, platform="jd", image_url="https://example.com/acc-10002.jpg", sales=43720, detail_url="https://example.com/acc-10002", shop_name="办公配件店", tags=["配件", "电脑", "散热"], rating=4.6),
    ProductCandidate(id="acc-10003", title="Type-C数据线 100W快充", price=29, original_price=49, platform="pdd", image_url="https://example.com/acc-10003.jpg", sales=219500, detail_url="https://example.com/acc-10003", shop_name="数码配件店", tags=["配件", "数据线", "快充"], rating=4.5),
    ProductCandidate(id="acc-10004", title="无线鼠标垫 超大桌垫", price=49, original_price=79, platform="tmall", image_url="https://example.com/acc-10004.jpg", sales=58210, detail_url="https://example.com/acc-10004", shop_name="桌面配件店", tags=["配件", "鼠标垫", "桌垫"], rating=4.7),
    ProductCandidate(id="acc-10005", title="机械键盘手托 木质护腕", price=59, original_price=89, platform="douyin", image_url="https://example.com/acc-10005.jpg", sales=26180, detail_url="https://example.com/acc-10005", shop_name="外设配件店", tags=["配件", "键盘", "手托"], rating=4.4),
    ProductCandidate(id="acc-10006", title="手机壳 防摔透明", price=19, original_price=29, platform="taobao", image_url="https://example.com/acc-10006.jpg", sales=342900, detail_url="https://example.com/acc-10006", shop_name="手机配件店", tags=["配件", "手机壳", "防摔"], rating=4.6),
    ProductCandidate(id="acc-10007", title="充电宝 20000mAh 大容量", price=129, original_price=169, platform="jd", image_url="https://example.com/acc-10007.jpg", sales=95620, detail_url="https://example.com/acc-10007", shop_name="移动电源店", tags=["配件", "充电宝", "移动电源"], rating=4.7),
    ProductCandidate(id="acc-10008", title="显示器支架 升降旋转", price=179, original_price=239, platform="tmall", image_url="https://example.com/acc-10008.jpg", sales=17640, detail_url="https://example.com/acc-10008", shop_name="显示器配件店", tags=["配件", "显示器", "支架"], rating=4.8),
    ProductCandidate(id="acc-10009", title="耳机收纳盒 硬壳便携", price=25, original_price=39, platform="pdd", image_url="https://example.com/acc-10009.jpg", sales=41230, detail_url="https://example.com/acc-10009", shop_name="收纳好物店", tags=["配件", "耳机", "收纳"], rating=4.5),
    ProductCandidate(id="acc-10010", title="路由器信号放大器", price=49, original_price=69, platform="douyin", image_url="https://example.com/acc-10010.jpg", sales=29120, detail_url="https://example.com/acc-10010", shop_name="网络配件店", tags=["配件", "路由器", "信号"], rating=4.3),
    ProductCandidate(id="acc-10011", title="摄像头遮挡盖 隐私保护", price=9, original_price=19, platform="taobao", image_url="https://example.com/acc-10011.jpg", sales=78800, detail_url="https://example.com/acc-10011", shop_name="隐私配件店", tags=["配件", "摄像头", "隐私"], rating=4.6),
    ProductCandidate(id="acc-10012", title="直播补光灯 三色可调", price=89, original_price=129, platform="jd", image_url="https://example.com/acc-10012.jpg", sales=22100, detail_url="https://example.com/acc-10012", shop_name="直播配件店", tags=["配件", "补光灯", "直播"], rating=4.5),
    ProductCandidate(id="acc-10013", title="耳机延长线 2米 编织线", price=15, original_price=25, platform="pdd", image_url="https://example.com/acc-10013.jpg", sales=104500, detail_url="https://example.com/acc-10013", shop_name="音频配件店", tags=["配件", "耳机", "延长线"], rating=4.4),
    ProductCandidate(id="acc-10014", title="电脑理线器 桌面收纳", price=35, original_price=49, platform="tmall", image_url="https://example.com/acc-10014.jpg", sales=36220, detail_url="https://example.com/acc-10014", shop_name="桌面收纳店", tags=["配件", "电脑", "理线"], rating=4.7),
    ProductCandidate(id="acc-10015", title="手机镜头保护膜 高清", price=12, original_price=19, platform="douyin", image_url="https://example.com/acc-10015.jpg", sales=145700, detail_url="https://example.com/acc-10015", shop_name="手机膜店", tags=["配件", "手机", "镜头膜"], rating=4.5),
    ProductCandidate(id="acc-10016", title="键盘防尘罩 防水防灰", price=22, original_price=35, platform="taobao", image_url="https://example.com/acc-10016.jpg", sales=32150, detail_url="https://example.com/acc-10016", shop_name="外设配件铺", tags=["配件", "键盘", "防尘"], rating=4.6),
    ProductCandidate(id="acc-10017", title="鼠标脚贴 特氟龙耐磨", price=18, original_price=29, platform="jd", image_url="https://example.com/acc-10017.jpg", sales=26980, detail_url="https://example.com/acc-10017", shop_name="电竞配件铺", tags=["配件", "鼠标", "脚贴"], rating=4.4),
    ProductCandidate(id="acc-10018", title="笔记本电脑包 防震防泼水", price=79, original_price=119, platform="pdd", image_url="https://example.com/acc-10018.jpg", sales=51680, detail_url="https://example.com/acc-10018", shop_name="电脑收纳店", tags=["配件", "电脑包", "防震"], rating=4.7),
    ProductCandidate(id="acc-10019", title="平板触控笔 书写绘画", price=99, original_price=149, platform="tmall", image_url="https://example.com/acc-10019.jpg", sales=19840, detail_url="https://example.com/acc-10019", shop_name="平板配件店", tags=["配件", "触控笔", "平板"], rating=4.6),
    ProductCandidate(id="acc-10020", title="多口USB扩展坞 电脑拓展", price=149, original_price=199, platform="amazon", image_url="https://example.com/acc-10020.jpg", sales=28410, detail_url="https://example.com/acc-10020", shop_name="Amazon Global", tags=["配件", "扩展坞", "USB"], rating=4.7),
]

PRODUCT_CATEGORY_MAP = {
    "手机": ["手机", "phone"],
    "耳机": ["耳机", "ear", "headphone", "headphones"],
    "电脑": ["电脑", "笔记本", "主机", "pc", "laptop"],
    "配件": ["配件", "支架", "充电", "数据线", "壳", "扩展坞", "鼠标垫"],
}

PRODUCT_HINTS = ["耳机", "键盘", "鼠标", "手机", "平板", "显示器", "路由器", "音箱"]
SCENE_HINTS = ["游戏", "通勤", "办公", "学习", "运动", "出差", "直播"]
AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter").lower()
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-4o-mini")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS", "300"))
_AI_CACHE: dict[str, tuple[float, str]] = {}


def parse_user_intent(query: str) -> UserIntent:
    """解析用户输入，优先调用 AI，失败后回退到规则解析。"""

    normalized = query.strip()
    if not normalized:
        return UserIntent(raw_query="", features=[], extra_keywords=[])

    try:
        intent_data = _call_ai_parse_intent(normalized)
        return _merge_intent_with_fallback(normalized, intent_data)
    except Exception:
        return _parse_user_intent_fallback(normalized)


def _call_ai_parse_intent(query: str) -> dict:
    prompt = INTENT_PARSE_PROMPT_TEMPLATE.format(query=query)
    raw = _call_ai_chat(prompt, temperature=0.1)
    data = _extract_json_object(raw)
    if not isinstance(data, dict):
        raise ValueError("AI 返回的意图结果不是 JSON 对象")
    return data


def _merge_intent_with_fallback(query: str, intent_data: dict) -> UserIntent:
    fallback_intent = _parse_user_intent_fallback(query)
    budget = intent_data.get("budget", {}) if isinstance(intent_data.get("budget"), dict) else {}
    features = intent_data.get("features", []) or []
    combined_features = _normalize_keyword_list(features + fallback_intent.features)

    return UserIntent(
        raw_query=query,
        product_type=_choose_primary_term(intent_data.get("product"), fallback_intent.product_type, query),
        budget_min=budget.get("min", fallback_intent.budget_min),
        budget_max=budget.get("max", fallback_intent.budget_max),
        scene=_choose_primary_term(intent_data.get("scenario"), fallback_intent.scene, query),
        features=combined_features,
        extra_keywords=_build_extra_keywords(query, intent_data, fallback_intent),
    )


def _parse_user_intent_fallback(query: str) -> UserIntent:
    budget_min, budget_max = _parse_budget(query)
    product_type = next((item for item in PRODUCT_HINTS if item in query), None)
    scene = next((item for item in SCENE_HINTS if item in query), None)
    extra_keywords = _build_extra_keywords(query, {}, None)
    features = _normalize_keyword_list([item for item in query if item in "降噪无线蓝牙轻量麦克风高性价比"])

    return UserIntent(
        raw_query=query,
        product_type=product_type,
        budget_min=budget_min,
        budget_max=budget_max,
        scene=scene,
        features=features,
        extra_keywords=extra_keywords,
    )


def _food_match_score(item: dict, query: str) -> int:
    title = str(item.get("title", ""))
    reason = str(item.get("reason", ""))
    tag = str(item.get("tag", ""))
    score = int(item.get("score", 0))
    haystack = f"{title} {reason} {tag}"

    if "辣" in query and tag == "辣":
        score += 25
    if "清淡" in query and tag == "清淡":
        score += 25
    if "火锅" in query and ("火锅" in title or tag == "辣"):
        score += 15
    if any(keyword in query for keyword in ["面", "小吃", "粉", "饭"]):
        if any(keyword in haystack for keyword in ["面", "小吃", "粉", "饭"]):
            score += 10
    if any(keyword in title for keyword in ["火锅", "麻辣烫", "川菜", "湘菜"]):
        score += 5
    return score


def _build_food_recommendations(query: str, top_k: int = 3) -> List[RecommendedProduct]:
    if "辣" in query:
        candidates = [item for item in FOOD_DATA if item.get("tag") == "辣"]
    elif "清淡" in query:
        candidates = [item for item in FOOD_DATA if item.get("tag") == "清淡"]
    else:
        candidates = FOOD_DATA[:]

    candidates = sorted(candidates, key=lambda item: _food_match_score(item, query), reverse=True)
    selected = candidates[:top_k]

    return [
        RecommendedProduct(
            title=str(item.get("title", "")),
            price=float(item.get("price", 0)),
            platform="food",
            reason=str(item.get("reason", "")),
            score=max(80, min(100, int(item.get("score", 80)))),
            ranking_score=max(80, min(100, int(item.get("score", 80)))),
            ranking_reason="基于口味关键词和评分优先筛选的 food 推荐",
            pros=[str(item.get("tag", ""))] if item.get("tag") else [],
            cons=None,
            buy_link=str(item.get("image_url", "")),
            commission=None,
        )
        for item in selected
    ]


def _build_food_summary(query: str, recommendations: List[RecommendedProduct]) -> str:
    if "辣" in query:
        return f"根据“{query}”匹配到更偏辣口味的食物推荐"
    if "清淡" in query:
        return f"根据“{query}”匹配到更清淡的食物推荐"
    return f"根据“{query}”返回评分更高的食物推荐（共 {len(recommendations)} 条）"


def _build_food_response(user_input: str, top_k: int = 3) -> RecommendationResponse:
    recommendations = _build_food_recommendations(user_input, top_k=top_k)
    intent = UserIntent(raw_query=user_input, mode="food")
    return RecommendationResponse(
        query=user_input,
        summary=_build_food_summary(user_input, recommendations),
        intent=intent,
        keywords=["food"],
        total_candidates=len(FOOD_DATA),
        recommendations=recommendations,
    )


def _call_ai_chat(prompt: str, temperature: float = 0.2) -> str:
    if not AI_API_KEY:
        raise RuntimeError("未配置 AI_API_KEY")

    cache_key = _build_ai_cache_key(prompt, temperature)
    cached_value = _get_ai_cache(cache_key)
    if cached_value is not None:
        return cached_value

    if AI_PROVIDER == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
    else:
        url = AI_BASE_URL
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost"),
            "X-Title": os.getenv("OPENROUTER_TITLE", "AI Shopping Recommender"),
        }
        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

    req = request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
        parsed = json.loads(body)
        content = parsed["choices"][0]["message"]["content"]
        _set_ai_cache(cache_key, content)
        return content
    except error.URLError as exc:
        raise RuntimeError(f"AI 请求失败: {exc}") from exc


def _build_ai_cache_key(prompt: str, temperature: float) -> str:
    fingerprint = {
        "provider": AI_PROVIDER,
        "model": AI_MODEL,
        "temperature": temperature,
        "prompt": prompt,
    }
    raw = json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _get_ai_cache(cache_key: str) -> str | None:
    cached = _AI_CACHE.get(cache_key)
    if not cached:
        return None
    expires_at, value = cached
    if expires_at < time.time():
        _AI_CACHE.pop(cache_key, None)
        return None
    return value


def _set_ai_cache(cache_key: str, value: str) -> None:
    _AI_CACHE[cache_key] = (time.time() + AI_CACHE_TTL_SECONDS, value)


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("未找到 JSON 对象")
    return json.loads(text[start : end + 1])


def _parse_budget(query: str) -> Tuple[float | None, float | None]:
    budget_min = None
    budget_max = None

    match = re.search(r"预算\s*(\d+(?:\.\d+)?)", query)
    if match:
        budget_max = float(match.group(1))

    match = re.search(r"(\d+(?:\.\d+)?)\s*[-到~]\s*(\d+(?:\.\d+)?)", query)
    if match:
        budget_min = float(match.group(1))
        budget_max = float(match.group(2))
        if budget_min > budget_max:
            budget_min, budget_max = budget_max, budget_min

    match = re.search(r"(\d+(?:\.\d+)?)\s*以内", query)
    if match:
        budget_max = float(match.group(1))

    match = re.search(r"(\d+(?:\.\d+)?)\s*以上", query)
    if match:
        budget_min = float(match.group(1))

    return budget_min, budget_max


def generate_search_keywords(intent: UserIntent) -> SearchKeywordPlan:
    """根据用户意图生成稳定的搜索关键词组合。"""

    keywords: List[str] = []
    product = (intent.product_type or "").strip()
    scene = (intent.scene or "").strip()
    budget_phrase = _build_budget_phrase(intent.budget_min, intent.budget_max)
    feature_terms = _normalize_keyword_list(intent.features)
    raw_terms = _extract_query_terms(intent.raw_query)

    if scene and product:
        keywords.extend([
            f"{scene}{product}",
            f"{product}{scene}",
            f"{scene}用{product}",
        ])
    elif product:
        keywords.append(product)
    elif scene:
        keywords.append(scene)

    if budget_phrase:
        keywords.extend(_budget_variants(budget_phrase, product, scene))

    if feature_terms:
        keywords.extend(feature_terms[:4])

    keywords.extend(_build_fuzzy_query_keywords(raw_terms, product, scene, intent.extra_keywords))

    if product and scene:
        keywords.append(f"{scene}{product}推荐")
    if product and budget_phrase:
        keywords.append(f"{product}{budget_phrase}")

    stable_keywords = _stable_unique_keywords(keywords)
    return SearchKeywordPlan(keywords=stable_keywords[:8])


def fetch_products_by_keywords(keywords: List[str]) -> List[ProductCandidate]:
    """根据关键词获取商品列表，当前使用 mock 数据。"""

    matched: List[ProductCandidate] = []
    for keyword in keywords:
        matched.extend(search_ecommerce_api_mock(keyword))

    return deduplicate_products(matched)


def search_ecommerce_api_mock(keyword: str) -> List[ProductCandidate]:
    """模拟电商 API 搜索结果。"""

    normalized = keyword.strip()
    if not normalized:
        return []

    query_terms = _extract_query_terms(normalized)
    results: List[ProductCandidate] = []
    for product in MOCK_PRODUCTS:
        score = 0
        title = product.title
        title_terms = [title] + product.tags + [product.shop_name or ""]
        for term in query_terms or [normalized]:
            if term in title:
                score += 3
            elif any(term in text for text in title_terms):
                score += 1
        if score > 0:
            results.append(product)

    if results:
        return results

    # 分类兜底：根据关键词所属品类返回对应商品，避免完全空结果
    category = _detect_category_from_query(normalized)
    if category:
        category_products = [product for product in MOCK_PRODUCTS if _product_in_category(product, category)]
        if category_products:
            return category_products

    return []


def deduplicate_products(products: List[ProductCandidate]) -> List[ProductCandidate]:
    """按商品 ID 去重。"""

    seen = set()
    unique_products: List[ProductCandidate] = []
    for product in products:
        if product.id in seen:
            continue
        seen.add(product.id)
        unique_products.append(product)
    return unique_products


def select_best_products(products: List[ProductCandidate], intent: UserIntent, top_k: int = 5) -> List[RecommendedProduct]:
    """优先调用 AI 选择商品，失败后回退到打分逻辑。"""

    try:
        ai_result = _call_ai_select_products(products, intent, top_k=top_k)
        return _build_recommended_products_from_ai(ai_result, products, intent, top_k=top_k)
    except Exception:
        return _select_best_products_fallback(products, intent, top_k=top_k)


def _call_ai_select_products(products: List[ProductCandidate], intent: UserIntent, top_k: int = 5) -> dict:
    candidate_payload = [
        {
            "id": product.id,
            "title": product.title,
            "price": product.price,
            "platform": product.platform,
            "sales": product.sales,
            "rating": product.rating,
            "shop_name": product.shop_name,
        }
        for product in products
    ]

    prompt = PRODUCT_SELECTION_PROMPT_TEMPLATE.format(
        intent_json=_serialize_intent(intent),
        candidate_json=json.dumps(candidate_payload, ensure_ascii=False),
        top_k=top_k,
    )
    raw = _call_ai_chat(prompt, temperature=0.2)
    data = _extract_json_object(raw)
    validated = _validate_ai_selection_output(data, products)
    return validated


def _build_recommended_products_from_ai(ai_result: dict, products: List[ProductCandidate], intent: UserIntent, top_k: int = 5) -> List[RecommendedProduct]:
    product_map = {product.id: product for product in products}
    selected_ids = ai_result.get("selected_ids", []) or []
    reasons = ai_result.get("reasons", {}) or {}
    pros_map = ai_result.get("pros", {}) or {}
    cons_map = ai_result.get("cons", {}) or {}
    scores_map = ai_result.get("scores", {}) or {}

    recommendations: List[RecommendedProduct] = []
    for product_id in selected_ids:
        product = product_map.get(product_id)
        if not product:
            continue
        score = _normalize_score(scores_map.get(product_id), product, intent)
        ranking_score, ranking_reason = _calculate_ranking_info(product, intent, score)
        recommendations.append(
            _to_frontend_recommendation(
                product=product,
                reason=str(reasons.get(product_id, "AI 认为该商品最符合需求")),
                pros=_normalize_pros(pros_map.get(product_id, [])),
                cons=_normalize_cons(cons_map.get(product_id)),
                score=score,
                ranking_score=ranking_score,
                ranking_reason=ranking_reason,
            )
        )
        if len(recommendations) >= 5:
            break

    if not recommendations:
        return _select_best_products_fallback(products, intent, top_k=top_k, strict=True)

    if len(recommendations) < 3:
        fallback = _select_best_products_fallback(products, intent, top_k=top_k, strict=True)
        merged: List[RecommendedProduct] = []
        seen_titles = set()
        for item in recommendations + fallback:
            if item.title in seen_titles:
                continue
            seen_titles.add(item.title)
            merged.append(item)
            if len(merged) >= top_k:
                break
        return merged[: max(1, min(top_k, len(merged)))]

    return recommendations


def _select_best_products_fallback(products: List[ProductCandidate], intent: UserIntent, top_k: int = 5, strict: bool = False) -> List[RecommendedProduct]:
    scored_products = sorted(products, key=lambda item: _score_product(item, intent), reverse=True)
    threshold = 1.4 if strict else 0.0
    filtered = [product for product in scored_products if _score_product(product, intent) >= threshold]

    if not filtered:
        filtered = scored_products[: min(top_k, len(scored_products))]

    if strict:
        selected = filtered[: max(1, min(top_k, 2 if len(filtered) >= 2 else 1))]
    else:
        selected = filtered[: max(3, min(top_k, len(filtered)))]

    recommendations: List[RecommendedProduct] = []
    for product in selected:
        score = _calculate_recommendation_score(product, intent)
        ranking_score, ranking_reason = _calculate_ranking_info(product, intent, score)
        recommendations.append(
            _to_frontend_recommendation(
                product,
                _build_reason(product, intent),
                _build_pros(product, intent),
                _build_cons(product, intent),
                score=score,
                ranking_score=ranking_score,
                ranking_reason=ranking_reason,
            )
        )
    return recommendations


def _to_frontend_recommendation(
    product: ProductCandidate,
    reason: str,
    pros: List[str],
    cons: str | None,
    score: int = 0,
    ranking_score: int = 0,
    ranking_reason: str | None = None,
) -> RecommendedProduct:
    return RecommendedProduct(
        title=product.title,
        price=product.price,
        platform=product.platform,
        reason=reason,
        score=score,
        ranking_score=ranking_score,
        ranking_reason=ranking_reason,
        pros=pros[:3],
        cons=cons,
        buy_link=_build_taobao_affiliate_link(product),
        commission=_estimate_commission(product),
    )


def _build_taobao_affiliate_link(product: ProductCandidate) -> str:
    platform = (product.platform or "").lower()
    if platform == "jd":
        return _build_jd_affiliate_link(product)
    if platform == "douyin":
        return _build_douyin_affiliate_link(product)
    return _build_taobao_affiliate_link_inner(product)


def _build_taobao_affiliate_link_inner(product: ProductCandidate) -> str:
    tracking_id = os.getenv("TAOBAO_TRACKING_ID", "").strip()
    commission = os.getenv("TAOBAO_COMMISSION", "").strip()
    pid = os.getenv("TAOBAO_PID", "").strip()
    app_key = os.getenv("TAOBAO_APP_KEY", "").strip()
    base_url = os.getenv("TAOBAO_BASE_URL", "").strip() or "https://item.taobao.com/item.htm"
    params = {
        "id": product.id,
    }
    if pid:
        params["pid"] = pid
    if app_key:
        params["app_key"] = app_key
    if tracking_id:
        params["tracking_id"] = tracking_id
    if commission:
        params["commission"] = commission
    query = "&".join(f"{key}={value}" for key, value in params.items() if value)
    joiner = "&" if "?" in base_url else "?"
    return f"{base_url}{joiner}{query}"


def _build_jd_affiliate_link(product: ProductCandidate) -> str:
    base_url = os.getenv("JD_BASE_URL", "").strip() or "https://u.jd.com/"
    app_key = os.getenv("JD_APP_KEY", "").strip()
    union_id = os.getenv("JD_UNION_ID", "").strip()
    tracking_id = os.getenv("JD_TRACKING_ID", "").strip()
    commission = os.getenv("JD_COMMISSION", "").strip()
    params = {
        "skuId": product.id,
    }
    if app_key:
        params["appKey"] = app_key
    if union_id:
        params["unionId"] = union_id
    if tracking_id:
        params["trackingId"] = tracking_id
    if commission:
        params["commission"] = commission
    query = "&".join(f"{key}={value}" for key, value in params.items() if value)
    joiner = "&" if "?" in base_url else "?"
    return f"{base_url}{joiner}{query}"


def _build_douyin_affiliate_link(product: ProductCandidate) -> str:
    base_url = os.getenv("DOUYIN_BASE_URL", "").strip() or "https://haohuo.jinritemai.com/views/product/item2"
    tracking_id = os.getenv("DOUYIN_TRACKING_ID", "").strip()
    commission = os.getenv("DOUYIN_COMMISSION", "").strip()
    author_id = os.getenv("DOUYIN_AUTHOR_ID", "").strip()
    promotion_id = os.getenv("DOUYIN_PROMOTION_ID", "").strip()
    params = {
        "id": product.id,
    }
    if author_id:
        params["authorId"] = author_id
    if promotion_id:
        params["promotionId"] = promotion_id
    if tracking_id:
        params["trackingId"] = tracking_id
    if commission:
        params["commission"] = commission
    query = "&".join(f"{key}={value}" for key, value in params.items() if value)
    joiner = "&" if "?" in base_url else "?"
    return f"{base_url}{joiner}{query}"


def _estimate_commission(product: ProductCandidate) -> float | None:
    try:
        percent = float(os.getenv("TAOBAO_COMMISSION_PERCENT", "0"))
    except Exception:
        percent = 0.0
    if percent <= 0:
        return None
    return round(product.price * (percent / 100.0), 2)


def _normalize_pros(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()][:3]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_cons(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _serialize_intent(intent: UserIntent) -> dict:
    return {
        "raw_query": intent.raw_query,
        "product_type": intent.product_type,
        "budget_min": intent.budget_min,
        "budget_max": intent.budget_max,
        "scene": intent.scene,
        "mode": intent.mode,
        "features": intent.features,
        "extra_keywords": intent.extra_keywords,
    }


def _validate_ai_selection_output(data: object, products: List[ProductCandidate]) -> dict:
    if not isinstance(data, dict):
        raise ValueError("AI 输出必须是 JSON 对象")

    selected_ids = data.get("selected_ids")
    if not isinstance(selected_ids, list):
        raise ValueError("selected_ids 必须是数组")

    product_ids = {product.id for product in products}
    cleaned_ids: List[str] = []
    for item in selected_ids:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if value and value in product_ids and value not in cleaned_ids:
            cleaned_ids.append(value)

    if not cleaned_ids:
        raise ValueError("AI 未返回有效商品 ID")

    reasons = _validate_ai_text_map(data.get("reasons"), cleaned_ids, "推荐理由")
    pros = _validate_ai_list_map(data.get("pros"), cleaned_ids)
    cons = _validate_ai_text_map(data.get("cons"), cleaned_ids, default_value="")
    scores = _validate_ai_score_map(data.get("scores"), cleaned_ids)
    commissions = _validate_ai_commission_map(data.get("commissions"), cleaned_ids)

    return {
        "selected_ids": cleaned_ids,
        "reasons": reasons,
        "pros": pros,
        "cons": cons,
        "scores": scores,
        "commissions": commissions,
    }


def _validate_ai_text_map(value: object, keys: List[str], default_value: str = "") -> dict:
    result: dict[str, str] = {}
    source = value if isinstance(value, dict) else {}
    for key in keys:
        text = source.get(key, default_value)
        result[key] = str(text).strip() if str(text).strip() else default_value
    return result


def _validate_ai_list_map(value: object, keys: List[str]) -> dict:
    result: dict[str, List[str]] = {}
    source = value if isinstance(value, dict) else {}
    for key in keys:
        item = source.get(key, [])
        result[key] = _normalize_pros(item)
    return result


def _validate_ai_score_map(value: object, keys: List[str]) -> dict:
    result: dict[str, int] = {}
    source = value if isinstance(value, dict) else {}
    for key in keys:
        raw_score = source.get(key, 0)
        try:
            score = int(float(raw_score))
        except Exception:
            score = 0
        result[key] = max(0, min(100, score))
    return result


def _validate_ai_commission_map(value: object, keys: List[str]) -> dict:
    result: dict[str, float | None] = {}
    source = value if isinstance(value, dict) else {}
    for key in keys:
        raw_commission = source.get(key)
        try:
            result[key] = round(float(raw_commission), 2) if raw_commission is not None else None
        except Exception:
            result[key] = None
    return result


def _normalize_score(raw_score: object, product: ProductCandidate, intent: UserIntent) -> int:
    try:
        score = int(float(raw_score))
    except Exception:
        score = _calculate_recommendation_score(product, intent)
    return max(0, min(100, score))


def _score_product(product: ProductCandidate, intent: UserIntent) -> float:
    score = 0.0
    title = product.title

    if intent.product_type and intent.product_type in title:
        score += 3.0
    if intent.scene and intent.scene in title:
        score += 2.0

    score += min(product.sales / 50000.0, 1.0)

    if intent.budget_max is not None:
        if product.price <= intent.budget_max:
            score += 2.0
        else:
            over_ratio = (product.price - intent.budget_max) / max(intent.budget_max, 1.0)
            score -= min(over_ratio * 4.0, 4.0)

    if intent.budget_min is not None and product.price >= intent.budget_min:
        score += 0.5

    if product.rating is not None:
        score += product.rating / 5.0

    return score


def _calculate_recommendation_score(product: ProductCandidate, intent: UserIntent) -> int:
    price_match = _score_price_match(product, intent)
    scene_match = _score_scene_match(product, intent)
    value_for_money = _score_value_for_money(product, intent)
    total = round(price_match * 0.35 + scene_match * 0.4 + value_for_money * 0.25)

    mode = _normalize_mode(intent.mode)
    if mode == "brand":
        total += 10 if product.rating and product.rating >= 4.7 else 0
    elif mode == "cheap":
        total += 12 if intent.budget_max is not None and product.price <= intent.budget_max else -8
    elif mode == "value":
        total += 8 if product.rating and product.rating >= 4.5 else 0

    return max(0, min(100, int(total)))


def _score_price_match(product: ProductCandidate, intent: UserIntent) -> float:
    if intent.budget_max is None and intent.budget_min is None:
        return 70.0

    if intent.budget_max is not None and product.price <= intent.budget_max:
        gap = intent.budget_max - product.price
        if intent.budget_max == 0:
            return 100.0
        return 100.0 - min((gap / intent.budget_max) * 40.0, 40.0)

    if intent.budget_max is not None and product.price > intent.budget_max:
        over_ratio = (product.price - intent.budget_max) / max(intent.budget_max, 1.0)
        return max(5.0, 60.0 - over_ratio * 120.0)

    if intent.budget_min is not None and product.price >= intent.budget_min:
        return 75.0

    return 50.0


def _score_scene_match(product: ProductCandidate, intent: UserIntent) -> float:
    title = product.title
    scene = (intent.scene or "").strip()
    product_type = (intent.product_type or "").strip()
    if not scene and not product_type:
        return 70.0

    score = 0.0
    if scene and scene in title:
        score += 60.0
    if product_type and product_type in title:
        score += 30.0
    for keyword in intent.features[:3]:
        if keyword and keyword in title:
            score += 10.0
    return min(100.0, score if score > 0 else 10.0)


def _calculate_ranking_info(product: ProductCandidate, intent: UserIntent, score: int) -> tuple[int, str]:
    ranking_score = score
    ranking_score += 8 if intent.scene and intent.scene in product.title else 0
    ranking_score += 6 if intent.product_type and intent.product_type in product.title else 0
    ranking_score += 6 if intent.budget_max is not None and product.price <= intent.budget_max else 0
    ranking_score += 4 if product.rating is not None and product.rating >= 4.6 else 0
    ranking_score = max(0, min(100, ranking_score))

    if ranking_score >= 90:
        reason = "综合匹配度最高，场景、预算与口碑都非常贴合，因此排在前列"
    elif ranking_score >= 80:
        reason = "场景匹配和预算表现都较好，综合评分靠前"
    elif ranking_score >= 70:
        reason = "满足核心需求，但在价格/口碑/场景完整度上略逊于更高分商品"
    else:
        reason = "虽然符合基本需求，但综合匹配度不如前面的商品"

    return ranking_score, reason


def _score_value_for_money(product: ProductCandidate, intent: UserIntent) -> float:
    base = 50.0
    if product.rating is not None:
        base += (product.rating - 4.0) * 12.5
    base += min(product.sales / 10000.0, 20.0)
    if intent.budget_max is not None and product.price <= intent.budget_max:
        base += 20.0
    if product.original_price and product.original_price > product.price:
        discount = (product.original_price - product.price) / max(product.original_price, 1.0)
        base += min(discount * 20.0, 20.0)
    return max(0.0, min(100.0, base))


def _normalize_mode(mode: object) -> str:
    text = str(mode).strip().lower() if mode is not None else ""
    aliases = {
        "性价比模式": "value",
        "value": "value",
        "brand": "brand",
        "品牌优先模式": "brand",
        "cheap": "cheap",
        "极致便宜模式": "cheap",
    }
    return aliases.get(text, "")


def _extract_query_terms(query: str) -> List[str]:
    if not query:
        return []
    terms = re.split(r"[\s、,，+/]+", query.strip())
    return [term for term in terms if term]


def _normalize_keyword_list(values: object) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def _choose_primary_term(ai_term: object, fallback_term: object, query: str) -> str | None:
    for term in (ai_term, fallback_term):
        text = str(term).strip() if term is not None else ""
        if text:
            return text
    return _detect_keyword_from_query(query)


def _detect_keyword_from_query(query: str) -> str | None:
    for term in PRODUCT_HINTS + SCENE_HINTS + ["辣", "清淡", "火锅", "麻辣烫", "川菜", "湘菜", "面食", "小吃"]:
        if term in query:
            return term
    return None


def _detect_category_from_query(query: str) -> str | None:
    for category, aliases in PRODUCT_CATEGORY_MAP.items():
        if any(alias.lower() in query.lower() for alias in aliases):
            return category
    return None


def _product_in_category(product: ProductCandidate, category: str) -> bool:
    aliases = PRODUCT_CATEGORY_MAP.get(category, [])
    haystack = f"{product.title} {product.shop_name or ''}".lower()
    return any(alias.lower() in haystack for alias in aliases)


def _build_extra_keywords(query: str, intent_data: dict, fallback_intent: UserIntent | None) -> List[str]:
    keywords: List[str] = []
    keywords.extend(_extract_query_terms(query))
    if isinstance(intent_data.get("features"), list):
        keywords.extend([str(item) for item in intent_data["features"] if str(item).strip()])
    if fallback_intent:
        keywords.extend(fallback_intent.extra_keywords)
    return _stable_unique_keywords(keywords)[:8]


def _build_budget_phrase(budget_min: float | None, budget_max: float | None) -> str | None:
    if budget_min is not None and budget_max is not None:
        if budget_min == budget_max:
            return f"{int(budget_max)}元"
        return f"{int(budget_min)}-{int(budget_max)}元"
    if budget_max is not None:
        return f"{int(budget_max)}元以内"
    if budget_min is not None:
        return f"{int(budget_min)}元以上"
    return None


def _budget_variants(budget_phrase: str, product: str, scene: str) -> List[str]:
    variants = [budget_phrase]
    if product:
        variants.append(f"{product}{budget_phrase}")
    if scene:
        variants.append(f"{scene}{budget_phrase}")
    return variants


def _build_fuzzy_query_keywords(raw_terms: List[str], product: str, scene: str, extra_keywords: List[str]) -> List[str]:
    keywords: List[str] = []
    all_terms = raw_terms + list(extra_keywords or [])
    for term in all_terms:
        normalized = term.strip()
        if not normalized:
            continue
        if len(normalized) <= 1:
            continue
        keywords.append(normalized)
        if "的" in normalized:
            pieces = [piece for piece in re.split(r"的|用|适合|便宜点|便宜|预算", normalized) if len(piece.strip()) > 1]
            keywords.extend(pieces)
    if scene:
        keywords.append(f"{scene}推荐")
    if product:
        keywords.append(f"{product}推荐")
    return _stable_unique_keywords(keywords)


def _stable_unique_keywords(keywords: List[str]) -> List[str]:
    stable: List[str] = []
    seen = set()
    for keyword in keywords:
        cleaned = keyword.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        stable.append(cleaned)
    return stable


def _build_reason(product: ProductCandidate, intent: UserIntent) -> str:
    parts: List[str] = []

    parts.append(_build_reason_for_user_fit(product, intent))
    parts.append(_build_reason_against_others(product, intent))
    parts.append(_build_budget_reason(product, intent))

    cleaned = [part for part in parts if part]
    if not cleaned:
        return "与用户需求整体匹配"
    return "；".join(cleaned)


def _build_reason_for_user_fit(product: ProductCandidate, intent: UserIntent) -> str:
    reasons: List[str] = []
    if intent.scene:
        reasons.append(f"适合{intent.scene}场景")
    if intent.product_type:
        reasons.append(f"商品类型匹配“{intent.product_type}”")

    mode = _normalize_mode(intent.mode)
    if mode == "value":
        reasons.append("在价格、评价与功能之间更均衡")
    elif mode == "brand":
        reasons.append("品牌口碑和稳定性更突出")
    elif mode == "cheap":
        reasons.append("更符合低预算优先的购买目标")

    if product.rating is not None:
        reasons.append(f"评分 {product.rating:.1f}")
    if product.sales:
        reasons.append(f"销量较高（{product.sales}）")

    if not reasons:
        return "这个商品与用户需求整体匹配"

    return "为什么适合你：" + "，".join(reasons[:3])


def _build_reason_against_others(product: ProductCandidate, intent: UserIntent) -> str:
    competitors = [item for item in MOCK_PRODUCTS if item.id != product.id]
    if not competitors:
        return "为什么不推荐其他商品：当前候选较少，已选出最接近需求的商品"

    better_matches = 0
    for other in competitors:
        if _calculate_recommendation_score(other, intent) > _calculate_recommendation_score(product, intent):
            better_matches += 1

    if better_matches == 0:
        return "为什么不推荐其他商品：当前商品在候选中综合匹配度最高"

    return f"为什么不推荐其他商品：其他商品要么场景不够贴合，要么预算匹配度/性价比不如它（还有 {better_matches} 个候选更弱）"


def _build_budget_reason(product: ProductCandidate, intent: UserIntent) -> str:
    if intent.budget_max is not None:
        if product.price <= intent.budget_max:
            gap = int(intent.budget_max - product.price)
            return f"预算匹配说明：价格 {int(product.price)} 元，在预算内，剩余约 {gap} 元"
        over = int(product.price - intent.budget_max)
        return f"预算匹配说明：价格 {int(product.price)} 元，略超预算 {over} 元，但综合表现更好"
    if intent.budget_min is not None:
        if product.price >= intent.budget_min:
            return f"预算匹配说明：价格 {int(product.price)} 元，满足最低预算要求"
        gap = int(intent.budget_min - product.price)
        return f"预算匹配说明：价格 {int(product.price)} 元，低于最低预算约 {gap} 元"
    return f"预算匹配说明：当前未明确预算，按整体性价比优先推荐"


def _build_pros(product: ProductCandidate, intent: UserIntent) -> List[str]:
    pros: List[str] = []

    if intent.budget_max is not None and product.price <= intent.budget_max:
        pros.append("符合预算")
    if intent.scene and intent.scene in product.title:
        pros.append(f"适合{intent.scene}")
    if product.sales >= 20000:
        pros.append("销量表现不错")
    if product.rating is not None and product.rating >= 4.6:
        pros.append("用户评价较好")
    return pros[:3]


def _build_cons(product: ProductCandidate, intent: UserIntent) -> str | None:
    if intent.budget_max is not None and product.price > intent.budget_max:
        return "价格略超预算"
    if product.rating is not None and product.rating < 4.6:
        return "评价略低于同类热门商品"
    if product.sales and product.sales < 15000:
        return "销量相对一般"
    return None


def build_recommendation_response(user_input: str, top_k: int = 5, mode: str | None = None) -> RecommendationResponse:
    """端到端推荐流程。"""

    intent = parse_user_intent(user_input)
    intent.raw_query = user_input
    intent.mode = _normalize_mode(mode) or _normalize_mode(intent.mode) or _detect_mode_from_query(user_input)

    if intent.mode == "food":
        return _build_food_response(user_input, top_k=min(top_k, 3))

    keyword_plan = generate_search_keywords(intent)
    candidates = fetch_products_by_keywords(keyword_plan.keywords)
    recommendations = select_best_products(candidates, intent, top_k=top_k)
    if not recommendations:
        recommendations = _build_safe_fallback_recommendations(intent, top_k=top_k)
    summary = _build_summary(intent, keyword_plan.keywords, len(candidates), recommendations)

    return RecommendationResponse(
        query=user_input,
        summary=summary,
        intent=intent,
        keywords=keyword_plan.keywords,
        total_candidates=len(candidates),
        recommendations=recommendations,
    )


def _build_safe_fallback_recommendations(intent: UserIntent, top_k: int = 5) -> List[RecommendedProduct]:
    fallback_candidates = sorted(MOCK_PRODUCTS, key=lambda item: _calculate_recommendation_score(item, intent), reverse=True)
    selected = fallback_candidates[: max(1, min(top_k, 3))]
    return [
        _to_frontend_recommendation(
            product=item,
            reason=_build_reason(item, intent),
            pros=_build_pros(item, intent),
            cons=_build_cons(item, intent),
            score=_calculate_recommendation_score(item, intent),
        )
        for item in selected
    ]


def _build_summary(intent: UserIntent, keywords: List[str], total_candidates: int, recommendations: List[RecommendedProduct]) -> str:
    parts: List[str] = []
    if intent.product_type:
        parts.append(f"围绕“{intent.product_type}”进行筛选")
    if intent.scene:
        parts.append(f"重点匹配“{intent.scene}”使用场景")
    if intent.mode:
        parts.append(f"当前推荐模式：{_mode_label(intent.mode)}")
    if intent.budget_max is not None:
        parts.append(f"优先控制在 {int(intent.budget_max)} 元以内")
    if recommendations:
        parts.append(f"从 {total_candidates} 个候选中筛出更合适的 {len(recommendations)} 个商品")
    if keywords:
        parts.append(f"基于关键词：{'、'.join(keywords[:3])}")
    return "；".join(parts) if parts else "根据用户输入综合筛选并返回最匹配的商品"


def _mode_label(mode: str) -> str:
    mapping = {"value": "性价比模式", "brand": "品牌优先模式", "cheap": "极致便宜模式"}
    return mapping.get(mode, mode)


def _detect_mode_from_query(query: str) -> str | None:
    if any(term in query for term in ["吃", "餐", "火锅", "辣", "清淡", "美食", "饭", "面", "小吃"]):
        return "food"
    if any(term in query for term in ["手机", "电脑", "耳机", "商品"]):
        return "product"
    if any(term in query for term in ["电影", "电视剧", "看"]):
        return "movie"
    return "product"
