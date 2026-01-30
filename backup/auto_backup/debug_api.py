import time
from urllib.parse import urlencode
import requests
from qiniu import Auth, QiniuMacAuth
from config import QINIU_CONFIG, DATA_STAT_API, DEFAULT_PARAMS

# 创建认证对象
access_key = QINIU_CONFIG['access_key']
secret_key = QINIU_CONFIG['secret_key']
auth = Auth(access_key, secret_key)
mac_auth = QiniuMacAuth(access_key, secret_key)

def test_direct_request():
    """直接测试API请求"""
    print("=== 直接API请求测试 ===")
    
    # 构建查询参数
    begin_time = '20260128000000'  # 使用前一天的数据
    end_time = '20260129000000'    # 使用今天的数据
    granularity = 'day'
    
    params = {
        'begin': begin_time,
        'end': end_time,
        'g': granularity,
        '$region': DEFAULT_PARAMS.get('region', 'z1')
    }
    
    # 构建完整URL
    query_parts = []
    for key, value in params.items():
        query_parts.append(f'{key}={value}')
    query_string = '&'.join(query_parts)
    
    path = f"/v6/space?{query_string}"
    full_url = f"{QINIU_CONFIG['base_url']}{path}"
    
    print(f"请求URL: {full_url}")
    
    # 生成时间戳，用于X-Qiniu-Date头部
    date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
    
    print(f"X-Qiniu-Date: {date_header}")
    
    # 使用QiniuMacAuth生成包含X-Qiniu-Date的认证令牌
    try:
        token = mac_auth.token_of_request(
            method="GET",
            host="api.qiniuapi.com",
            url=path,
            qheaders=f"X-Qiniu-Date: {date_header}",
            content_type="application/x-www-form-urlencoded"
        )
        
        print(f"生成的Token: {token[:20]}...")
        
        # 设置请求头
        headers = {
            'Authorization': f"Qiniu {token}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Qiniu-Date': date_header
        }
        
        print(f"请求头: {dict((k, v if k != 'Authorization' else v[:50] + '...') for k, v in headers.items())}")
        
        # 尝试发送请求
        print("正在发送请求...")
        response = requests.get(full_url, headers=headers, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        return response.status_code, response.json() if response.content else None
        
    except Exception as e:
        print(f"请求异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, None

def test_network_connectivity():
    """测试网络连通性"""
    print("\n=== 网络连通性测试 ===")
    
    # 测试能否连接到外部网络
    try:
        import socket
        sock = socket.create_connection(("api.qiniuapi.com", 443), timeout=10)
        print("✅ 能够连接到 api.qiniuapi.com:443")
        sock.close()
    except Exception as e:
        print(f"❌ 无法连接到 api.qiniuapi.com:443, 错误: {e}")
    
    # 测试requests库
    try:
        resp = requests.get("https://httpbin.org/get", timeout=10)
        print(f"✅ 能够通过requests访问外部网站, 状态码: {resp.status_code}")
    except Exception as e:
        print(f"❌ 无法通过requests访问外部网站, 错误: {e}")

def test_auth():
    """测试认证"""
    print("\n=== 认证测试 ===")
    
    try:
        # 尝试创建认证令牌
        date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
        token = mac_auth.token_of_request(
            method="GET",
            host="api.qiniuapi.com",
            url="/v6/space?begin=20260128000000&end=20260129000000&g=day",
            qheaders=f"X-Qiniu-Date: {date_header}",
            content_type="application/x-www-form-urlencoded"
        )
        print(f"✅ 认证令牌生成成功: {token[:30]}...")
    except Exception as e:
        print(f"❌ 认证令牌生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始调试API连接问题...")
    
    test_network_connectivity()
    test_auth()
    test_direct_request()