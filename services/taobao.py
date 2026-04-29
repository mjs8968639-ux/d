"""
淘宝平台搜索服务（模拟数据）
TODO: 后续接入淘宝联盟 API 或开放平台
"""
from typing import List
from models import Product
import random


async def search_taobao(keyword: str, page: int, page_size: int) -> List[Product]:
    """
    搜索淘宝商品
    目前返回模拟数据，后续可替换为真实 API 调用
    """
    # 模拟网络延迟
    import asyncio
    await asyncio.sleep(0.3)
    
    base_id = (page - 1) * page_size
    products = []
    
    for i in range(page_size):
        price = round(random.uniform(50, 500), 2)
        original_price = round(price * random.uniform(1.2, 1.5), 2)
        sales = random.randint(100, 50000)
        
        products.append(Product(
            id=f"tb_{base_id + i}",
            title=f"【淘宝】{keyword} 正品保障 包邮 {i+1}",
            price=price,
            original_price=original_price,
            platform="taobao",
            image_url="https://via.placeholder.com/300x300?text=Taobao",
            sales=sales,
            detail_url=f"https://s.taobao.com/search?q={keyword}&s={base_id + i}",
            shop_name=f"淘宝店铺{i+1}",
            tags=["淘宝", "包邮", "正品"]
        ))
    
    return products

