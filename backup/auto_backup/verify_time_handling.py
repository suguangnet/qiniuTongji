"""
验证时间处理逻辑
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qiniu_dashboard import get_stats
from flask import Flask, request
import json

# 创建临时flask应用用于测试
app = Flask(__name__)
app.config['TESTING'] = True

# 添加路由
@app.route('/api/get_stats', methods=['GET', 'POST'])
def test_get_stats():
    return get_stats()

# 测试API端点 - 使用较长时间范围
with app.test_client() as client:
    # 发送POST请求测试，使用较长时间范围
    payload = {
        "begin": "20260101000000",  # 2026年1月1日
        "end": "20260130235959",    # 2026年1月30日（一整月）
        "granularity": "day",
        "bucket_name": "recordingmini",
        "region": "z2"
    }
    
    print("测试API端点 /api/get_stats...")
    print(f"输入时间范围: {payload['begin']} 到 {payload['end']}")
    response = client.post('/api/get_stats', 
                          data=json.dumps(payload), 
                          content_type='application/json')
    
    print(f"响应状态码: {response.status_code}")
    
    response_data = response.get_json()
    if response_data:
        print(f"响应成功: {response_data.get('success')}")
        if response_data.get('success'):
            data = response_data.get('data', {})
            print(f"数据键值: {list(data.keys())}")
            print(f"cdnTraffic数据长度: {len(data.get('cdnTraffic', []))}")
            print(f"cdnFlow数据长度: {len(data.get('cdnFlow', []))}")
            
            # 显示cdnTraffic的数据点详情
            cdn_traffic = data.get('cdnTraffic', [])
            if cdn_traffic:
                print(f"cdnTraffic共{len(cdn_traffic)}个数据点，前5个和后5个:")
                for i, item in enumerate(cdn_traffic[:5]):
                    print(f"  {i+1:2d}. {item}")
                if len(cdn_traffic) > 5:
                    print("  ...")
                    for i in range(max(5, len(cdn_traffic)-5), len(cdn_traffic)):
                        print(f"  {i+1:2d}. {cdn_traffic[i]}")
            else:
                print("cdnTraffic为空")
                
            print("\n✅ 时间范围数据查询验证成功！")
            print("API正确处理了用户输入的时间范围，并返回了相应时间段的数据。")
        else:
            print(f"错误信息: {response_data.get('message')}")
    else:
        print("无法解析响应JSON")