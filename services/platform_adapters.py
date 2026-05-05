"""
平台 API 接口映射与统一适配定义。
这里只负责记录平台接口名称与后续扩展点，不直接发起网络请求。
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformApiSpec:
    search: str
    detail: str
    promotion: str
    order: str


PLATFORM_API_SPECS = {
    "pdd": PlatformApiSpec(
        search="pdd.ddk.goods.search",
        detail="pdd.ddk.goods.detail",
        promotion="pdd.ddk.goods.promotion.url.generate",
        order="pdd.ddk.order.list.increment.get",
    ),
    "taobao": PlatformApiSpec(
        search="taobao.tbk.dg.material.optional",
        detail="taobao.tbk.item.info.get",
        promotion="taobao.tbk.tpwd.create",
        order="taobao.tbk.order.details.get",
    ),
    "jd": PlatformApiSpec(
        search="jd.union.open.goods.query",
        detail="jd.union.open.goods.detail.get",
        promotion="jd.union.open.promotion.common.get",
        order="jd.union.open.order.query",
    ),
}


def get_platform_api_spec(platform: str) -> PlatformApiSpec:
    return PLATFORM_API_SPECS[platform.lower().strip()]
