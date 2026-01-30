"""
测试API端点返回的数据
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

# 测试API端点
with app.test_client() as client:
    # 发送POST请求测试
    payload = {
        "begin": "20260101000000",
        "end": "20260130235959",
        "granularity": "day",
        "bucket_name": "recordingmini",
        "region": "z2"
    }
    
    print("测试API端点 /api/get_stats...")
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
            
            # 显示cdnTraffic的前几个数据点
            cdn_traffic = data.get('cdnTraffic', [])
            if cdn_traffic:
                print("cdnTraffic前3个数据点:")
                for i, item in enumerate(cdn_traffic[:3]):
                    print(f"  {i+1}. {item}")
            else:
                print("cdnTraffic为空")
        else:
            print(f"错误信息: {response_data.get('message')}")
    else:
        print("无法解析响应JSON")