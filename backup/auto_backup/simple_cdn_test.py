"""
简单CDN流量数据测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_manager import QiniuAPIManager
from qiniu_dashboard import parse_cdn_traffic

# 测试CDN流量数据获取
api_manager = QiniuAPIManager()

print("正在测试CDN流量数据获取...")

# 获取当前月份的数据
import datetime
today = datetime.date.today()
start_date = f"{today.year}-{today.month:02d}-01"  # 本月第一天
end_date = today.strftime('%Y-%m-%d')  # 今天

print(f"查询时间范围: {start_date} 到 {end_date}")

cdn_result = api_manager.get_cdn_traffic_stats(
    start_date=start_date,
    end_date=end_date,
    granularity='day'
)

print(f"API响应状态码: {cdn_result.get('status_code')}")
print(f"API响应数据: {cdn_result.get('data', {}).get('code', 'N/A')}")

# 解析数据
parsed_data = parse_cdn_traffic(cdn_result)
print(f"解析后的数据点数量: {len(parsed_data) if parsed_data else 0}")

if parsed_data:
    print("前5个数据点:")
    for i, item in enumerate(parsed_data[:5]):
        print(f"  {i+1}. 时间: {item['time']}, 流量: {item['value']:,} bytes ({item['value']/1024/1024/1024:.2f} GB)")

# 检查是否成功获取到数据
if parsed_data and len(parsed_data) > 0:
    print("\n✅ CDN流量数据获取测试成功！")
    print("数据已准备好用于图表显示")
else:
    print("\n⚠️  CDN流量数据获取可能存在问题")
    print("- 检查API密钥是否有效")
    print("- 检查域名是否在七牛云中有流量记录")
    print("- 确认账户是否有CDN流量统计权限")
    
    # 显示原始响应信息
    if cdn_result.get('data'):
        print(f"\n原始响应数据结构: {cdn_result['data'].keys() if isinstance(cdn_result['data'], dict) else type(cdn_result['data'])}")
    else:
        print(f"\nAPI返回错误或无数据")