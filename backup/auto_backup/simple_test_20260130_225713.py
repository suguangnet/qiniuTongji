import requests
import json

# 简单测试Web API端点
url = "http://localhost:5000/api/get_stats"
    
payload = {
    "begin": "20260101000000",  # 2026年1月1日
    "end": "20260129235959",    # 今天
    "granularity": "day",
    "bucket_name": "recordingmini",
    "region": "z2"
}
    
headers = {'Content-Type': 'application/json'}
    
try:
    print("测试Web API端点...")
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ API调用成功!")
            stats = data.get('data', {})
            for key, value in stats.items():
                print(f"  {key}: {len(value) if isinstance(value, list) else 'N/A'} 项数据")
        else:
            print(f"API调用失败: {data.get('message', '未知错误')}")
    else:
        print(f"请求失败: {response.status_code}")
        print(f"响应内容: {response.text}")
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到Web服务器，请先启动qiniu_dashboard.py")
except Exception as e:
    print(f"错误: {e}")