"""
测试不同时间范围的CDN流量数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_manager import QiniuAPIManager
from qiniu_dashboard import parse_cdn_traffic
import datetime

api_manager = QiniuAPIManager()

# 测试不同的时间范围
ranges_to_test = [
    {
        'name': '最近3天',
        'start': (datetime.date.today() - datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
        'end': datetime.date.today().strftime('%Y-%m-%d')
    },
    {
        'name': '最近7天',
        'start': (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        'end': datetime.date.today().strftime('%Y-%m-%d')
    },
    {
        'name': '本月',
        'start': f"{datetime.date.today().year}-{datetime.date.today().month:02d}-01",
        'end': datetime.date.today().strftime('%Y-%m-%d')
    },
    {
        'name': '上个月',
        'start': f"{datetime.date.today().year}-{datetime.date.today().month-1:02d}-01" if datetime.date.today().month > 1 else f"{datetime.date.today().year-1}-12-01",
        'end': f"{datetime.date.today().year}-{datetime.date.today().month:02d}-01" if datetime.date.today().month > 1 else f"{datetime.date.today().year}-01-01"
    }
]

print("测试不同时间范围的CDN流量数据...")
print("=" * 60)

for test_range in ranges_to_test:
    print(f"\n测试: {test_range['name']}")
    print(f"时间范围: {test_range['start']} 到 {test_range['end']}")
    
    cdn_result = api_manager.get_cdn_traffic_stats(
        start_date=test_range['start'],
        end_date=test_range['end'],
        granularity='day'
    )
    
    print(f"API响应状态码: {cdn_result.get('status_code')}")
    print(f"API响应数据代码: {cdn_result.get('data', {}).get('code', 'N/A')}")
    
    if cdn_result.get('status_code') == 200 and cdn_result.get('data', {}).get('code') == 200:
        parsed_data = parse_cdn_traffic(cdn_result)
        print(f"解析后的数据点数量: {len(parsed_data) if parsed_data else 0}")
        
        if parsed_data:
            # 检查是否有非零流量
            non_zero_values = [item for item in parsed_data if item['value'] > 0]
            if non_zero_values:
                print(f"非零流量数据点: {len(non_zero_values)}")
                print("非零流量示例:")
                for item in non_zero_values[:3]:
                    print(f"  {item['time']}: {item['value']:,} bytes ({item['value']/1024/1024/1024:.2f} GB)")
            else:
                print("⚠️  所有数据点均为0 - 可能是时间段内没有CDN流量或数据尚未生成")
        else:
            print("⚠️  解析后的数据为空")
    else:
        print(f"❌ API调用失败: {cdn_result.get('data', {}).get('error', 'Unknown error')}")
    
    print("-" * 40)

# 同时测试存储空间数据以作对比
print(f"\n存储空间数据对比:")
try:
    storage_result = api_manager.get_storage_usage(
        begin_time=(datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y%m%d') + '000000',
        end_time=datetime.date.today().strftime('%Y%m%d') + '235959',
        granularity='day'
    )
    print(f"存储API响应状态: {storage_result.get('status_code')}")
    if storage_result.get('status_code') == 200 and storage_result.get('data'):
        # 解析存储数据
        storage_data = storage_result['data']
        if isinstance(storage_data, list) and len(storage_data) > 0:
            latest_storage = storage_data[-1]  # 最新数据
            if isinstance(latest_storage, dict):
                # 查找space字段的值
                space_value = None
                for key, value in latest_storage.items():
                    if 'space' in key.lower() or 'storage' in key.lower():
                        space_value = value
                        break
                if space_value:
                    print(f"最新存储空间: {space_value:,} bytes ({space_value/1024/1024/1024/1024:.2f} TB)")
                else:
                    print(f"存储数据格式: {latest_storage}")
            else:
                print(f"存储数据格式: {type(latest_storage)}")
        else:
            print(f"存储数据格式: {type(storage_data)} - {storage_data}")
    else:
        print("无法获取存储数据")
except Exception as e:
    print(f"获取存储数据时出错: {e}")