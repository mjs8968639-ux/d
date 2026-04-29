"""
天猫平台搜索服务（模拟数据）
TODO: 后续接入天猫联盟 API
"""
from typing import List
from models import Product
import random


async def search_tmall(keyword: str, page: int, page_size: int) -> List[Product]:
    """
    搜索天猫商品
    目前返回模拟数据，后续可替换为真实 API 调用
    """
    import asyncio
    await asyncio.sleep(0.3)
    
    base_id = (page - 1) * page_size
    products = []
    
    for i in range(page_size):
        price = round(random.uniform(80, 800), 2)
        original_price = round(price * random.uniform(1.2, 1.6), 2)
        sales = random.randint(300, 60000)
        
        products.append(Product(
            id=f"tmall_{base_id + i}",
            title=f"【天猫】{keyword} 品牌授权 正品保障 {i+1}",
            price=price,
            original_price=original_price,
            platform="tmall",
            image_url="https://via.placeholder.com/300x300?text=Tmall",
            sales=sales,
            detail_url=f"https://list.tmall.com/search_product.htm?q={keyword}",
            shop_name=f"天猫旗舰店{i+1}",
            tags=["天猫", "品牌", "正品"]
        ))
    
    return products

