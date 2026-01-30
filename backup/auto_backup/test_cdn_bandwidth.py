"""
测试CDN带宽API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_manager import QiniuAPIManager
from qiniu_dashboard import parse_cdn_bandwidth
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
    }
]

print("测试不同时间范围的CDN计费带宽数据...")
print("=" * 60)

for test_range in ranges_to_test:
    print(f"\n测试: {test_range['name']}")
    print(f"时间范围: {test_range['start']} 到 {test_range['end']}")
    
    cdn_result = api_manager.get_cdn_bandwidth_stats(
        start_date=test_range['start'],
        end_date=test_range['end'],
        granularity='day'
    )
    
    print(f"API响应状态码: {cdn_result.get('status_code')}")
    print(f"API响应数据代码: {cdn_result.get('data', {}).get('code', 'N/A')}")
    
    if cdn_result.get('status_code') == 200 and cdn_result.get('data', {}).get('code') == 200:
        parsed_data = parse_cdn_bandwidth(cdn_result)
        print(f"解析后的数据点数量: {len(parsed_data) if parsed_data else 0}")
        
        if parsed_data:
            # 检查是否有非零带宽
            non_zero_values = [item for item in parsed_data if item['value'] > 0]
            if non_zero_values:
                print(f"非零带宽数据点: {len(non_zero_values)}")
                print("非零带宽示例:")
                for item in non_zero_values[:3]:
                    print(f"  {item['time']}: {item['value']:,} bps ({item['value']/1000000:.2f} Mbps)")
            else:
                print("⚠️  所有数据点均为0 - 可能是时间段内没有CDN带宽或数据尚未生成")
        else:
            print("⚠️  解析后的数据为空")
    else:
        print(f"❌ API调用失败: {cdn_result.get('data', {}).get('error', 'Unknown error')}")
    
    print("-" * 40)

print("\n测试完成！")