"""
测试CDN流量数据解析
"""
import sys
sys.path.append('.')

from qiniu_dashboard import parse_cdn_traffic

# 模拟API返回的数据
mock_api_response = {
    'status_code': 200,
    'data': {
        'code': 200,
        'error': '',
        'time': [
            '2026-01-01 00:00:00', '2026-01-02 00:00:00', '2026-01-03 00:00:00',
            '2026-01-14 00:00:00', '2026-01-15 00:00:00'
        ],
        'data': {
            'cdn.mshcodeadventure.top': {
                'china': [0, 0, 0, 8363046637, 52755410062],
                'oversea': [0, 0, 0, 1000000, 2000000]
            },
            'cdnv.mshcodeadventure.top': {
                'china': [0, 0, 0, 5000000, 1000000],
                'oversea': [0, 0, 0, 500000, 100000]
            }
        }
    }
}

print("测试CDN流量数据解析:")
parsed_data = parse_cdn_traffic(mock_api_response)

print(f"解析结果: {parsed_data}")
print()
print("详细数据:")
for item in parsed_data:
    print(f"  时间: {item['time']}, 流量: {item['value']:,} bytes")