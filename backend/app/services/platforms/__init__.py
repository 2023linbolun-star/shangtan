from app.services.platforms.base import PlatformAdapter, PlatformProduct
from app.services.platforms.taobao import TaobaoAdapter
from app.services.platforms.pinduoduo import PinduoduoAdapter
from app.services.platforms.douyin import DouyinAdapter
from app.services.platforms.xiaohongshu import XiaohongshuAdapter
from app.services.platforms.veapi import (
    VeapiTaobaoAdapter,
    VeapiPinduoduoAdapter,
    VeapiJingdongAdapter,
    VeapiDouyinAdapter,
)

__all__ = [
    "PlatformAdapter",
    "PlatformProduct",
    # 官方 API 适配器（后续切换用）
    "TaobaoAdapter",
    "PinduoduoAdapter",
    "DouyinAdapter",
    "XiaohongshuAdapter",
    # 维易 API 适配器（当前使用）
    "VeapiTaobaoAdapter",
    "VeapiPinduoduoAdapter",
    "VeapiJingdongAdapter",
    "VeapiDouyinAdapter",
]
