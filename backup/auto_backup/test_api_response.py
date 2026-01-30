"""
测试API响应结构
"""
import sys
sys.path.append('.')

from api_manager import QiniuAPIManager
from config import QINIU_CONFIG

# 测试CDN流量数据获取
api_manager = QiniuAPIManager()

# 测试获取CDN流量数据
cdn_result = api_manager.get_cdn_traffic_stats(
    start_date="2026-01-01",
    end_date="2026-01-30",
    granularity='day'
)

print("CDN流量API响应:")
print(f"状态码: {cdn_result.get('status_code')}")
print(f"数据: {cdn_result.get('data')}")
print()

# 检查数据结构
if cdn_result.get('data'):
    data = cdn_result['data']
    if isinstance(data, dict):
        print("数据结构:")
        for key, value in data.items():
            print(f"  {key}: {type(value)} -> {value if isinstance(value, (str, int, float)) else str(value)[:100]}")
    else:
        print(f"数据类型: {type(data)}")
        print(f"数据内容: {data}")
else:
    print("没有返回数据或请求失败")