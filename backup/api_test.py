"""
七牛云API接口测试脚本
用于验证API连接和数据获取功能
"""

import requests
import time
from urllib.parse import urlencode
from qiniu import Auth
import json

# 从配置文件导入配置
from config import QINIU_CONFIG

def test_api_connection():
    """测试API连接"""
    print("=" * 60)
    print("七牛云API接口测试")
    print("=" * 60)
    
    # 创建认证对象
    access_key = QINIU_CONFIG['access_key']
    secret_key = QINIU_CONFIG['secret_key']
    bucket_name = QINIU_CONFIG['bucket_name']
    
    print(f"AccessKey: {access_key[:8]}...{access_key[-4:]}")
    print(f"SecretKey: {secret_key[:8]}...{secret_key[-4:]}")
    print(f"Bucket: {bucket_name}")
    print(f"Region: {QINIU_CONFIG['region']}")
    print("-" * 60)
    
    # 测试不同的API接口
    test_space_api(access_key, secret_key, bucket_name)
    test_count_api(access_key, secret_key, bucket_name)
    test_blob_io_api(access_key, secret_key, bucket_name)
    test_rs_put_api(access_key, secret_key, bucket_name)

def test_space_api(access_key, secret_key, bucket_name):
    """测试存储用量API (/v6/space)"""
    print("\n1. 测试存储用量API (/v6/space)")
    
    # 计算查询时间范围（最近1天）
    now = time.time()
    one_day_ago = now - 86400  # 1天前
    
    begin_time = time.strftime('%Y%m%d%H%M%S', time.localtime(one_day_ago))
    end_time = time.strftime('%Y%m%d%H%M%S', time.localtime(now))
    
    # 构建查询参数
    params = {
        'begin': begin_time,
        'end': end_time,
        'g': 'day',
        'bucket': bucket_name,
        'region': QINIU_CONFIG['region']
    }
    
    # 构建完整URL
    base_url = QINIU_CONFIG['base_url']
    endpoint = '/v6/space'
    query_string = urlencode(params)
    full_url = f"{base_url}{endpoint}?{query_string}"
    
    print(f"请求URL: {full_url}")
    
    # 使用QiniuMacAuth进行认证
    try:
        from qiniu.services.storage.bucket import BucketManager
        from qiniu import QiniuMacAuth
        
        # 创建认证对象
        auth = QiniuMacAuth(access_key, secret_key)
        
        # 生成时间戳，用于X-Qiniu-Date头部
        date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
        
        # 生成包含X-Qiniu-Date的认证令牌
        token = auth.token_of_request(
            method="GET",
            host="api.qiniuapi.com",
            url=f"{endpoint}?{query_string}",
            qheaders=f"X-Qiniu-Date: {date_header}",
            content_type="application/x-www-form-urlencoded"
        )
        
        # 设置请求头
        headers = {
            'Authorization': f"Qiniu {token}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Qiniu-Date': date_header
        }
        
        print(f"请求头: {headers}")
        
        # 发送请求
        response = requests.get(full_url, headers=headers, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.content:
            try:
                response_data = response.json()
                print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
        else:
            print("响应为空")
            
    except ImportError:
        print("警告: 未安装qiniu官方SDK，使用基本认证方法")
        # 使用基本认证方法
        try:
            from qiniu import Auth
            auth = Auth(access_key, secret_key)
            
            # 设置请求头
            headers = {
                'Authorization': auth.authorization(full_url)[1],  # 获取Authorization头部值
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.get(full_url, headers=headers, timeout=30)
            
            print(f"状态码: {response.status_code}")
            if response.content:
                try:
                    response_data = response.json()
                    print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"响应文本: {response.text}")
            else:
                print("响应为空")
        except Exception as e:
            print(f"基本认证方法失败: {str(e)}")
    except Exception as e:
        print(f"API调用失败: {str(e)}")

def test_count_api(access_key, secret_key, bucket_name):
    """测试文件数量API (/v6/count)"""
    print("\n2. 测试文件数量API (/v6/count)")
    
    # 计算查询时间范围（最近1天）
    now = time.time()
    one_day_ago = now - 86400  # 1天前
    
    begin_time = time.strftime('%Y%m%d%H%M%S', time.localtime(one_day_ago))
    end_time = time.strftime('%Y%m%d%H%M%S', time.localtime(now))
    
    # 构建查询参数
    params = {
        'begin': begin_time,
        'end': end_time,
        'g': 'day',
        'bucket': bucket_name,
        'region': QINIU_CONFIG['region']
    }
    
    # 构建完整URL
    base_url = QINIU_CONFIG['base_url']
    endpoint = '/v6/count'
    query_string = urlencode(params)
    full_url = f"{base_url}{endpoint}?{query_string}"
    
    print(f"请求URL: {full_url}")
    
    # 使用QiniuMacAuth进行认证
    try:
        from qiniu import QiniuMacAuth
        
        # 创建认证对象
        auth = QiniuMacAuth(access_key, secret_key)
        
        # 生成时间戳，用于X-Qiniu-Date头部
        date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
        
        # 生成包含X-Qiniu-Date的认证令牌
        token = auth.token_of_request(
            method="GET",
            host="api.qiniuapi.com",
            url=f"{endpoint}?{query_string}",
            qheaders=f"X-Qiniu-Date: {date_header}",
            content_type="application/x-www-form-urlencoded"
        )
        
        # 设置请求头
        headers = {
            'Authorization': f"Qiniu {token}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Qiniu-Date': date_header
        }
        
        # 发送请求
        response = requests.get(full_url, headers=headers, timeout=30)
        
        print(f"状态码: {response.status_code}")
        if response.content:
            try:
                response_data = response.json()
                print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
        else:
            print("响应为空")
            
    except Exception as e:
        print(f"API调用失败: {str(e)}")

def test_blob_io_api(access_key, secret_key, bucket_name):
    """测试流量和请求次数API (/v6/blob_io)"""
    print("\n3. 测试流量和请求次数API (/v6/blob_io)")
    
    # 测试不同类型的查询
    test_types = [
        {'select': 'flow', 'metric': 'flow_out', 'desc': '外网流出流量'},
        {'select': 'flow', 'metric': 'cdn_flow_out', 'desc': 'CDN回源流量'},
        {'select': 'hits', 'metric': 'hits', 'desc': 'GET请求次数'}
    ]
    
    for test_config in test_types:
        print(f"\n  3.1 测试{test_config['desc']}: select={test_config['select']}&metric={test_config['metric']}")
        
        # 计算查询时间范围（最近1天）
        now = time.time()
        one_day_ago = now - 86400  # 1天前
        
        begin_time = time.strftime('%Y%m%d%H%M%S', time.localtime(one_day_ago))
        end_time = time.strftime('%Y%m%d%H%M%S', time.localtime(now))
        
        # 构建查询参数
        params = {
            'begin': begin_time,
            'end': end_time,
            'g': 'day',
            '$bucket': bucket_name,
            '$region': QINIU_CONFIG['region'],
            'select': test_config['select'],
            '$metric': test_config['metric']
        }
        
        # 构建完整URL
        base_url = QINIU_CONFIG['base_url']
        endpoint = '/v6/blob_io'
        query_string = urlencode(params)
        full_url = f"{base_url}{endpoint}?{query_string}"
        
        print(f"  请求URL: {full_url}")
        
        # 使用QiniuMacAuth进行认证
        try:
            from qiniu import QiniuMacAuth
            
            # 创建认证对象
            auth = QiniuMacAuth(access_key, secret_key)
            
            # 生成时间戳，用于X-Qiniu-Date头部
            date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
            
            # 生成包含X-Qiniu-Date的认证令牌
            token = auth.token_of_request(
                method="GET",
                host="api.qiniuapi.com",
                url=f"{endpoint}?{query_string}",
                qheaders=f"X-Qiniu-Date: {date_header}",
                content_type="application/x-www-form-urlencoded"
            )
            
            # 设置请求头
            headers = {
                'Authorization': f"Qiniu {token}",
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Qiniu-Date': date_header
            }
            
            # 发送请求
            response = requests.get(full_url, headers=headers, timeout=30)
            
            print(f"  状态码: {response.status_code}")
            if response.content:
                try:
                    response_data = response.json()
                    print(f"  响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"  响应文本: {response.text}")
            else:
                print("  响应为空")
                
        except Exception as e:
            print(f"  API调用失败: {str(e)}")

def test_rs_put_api(access_key, secret_key, bucket_name):
    """测试PUT请求次数API (/v6/rs_put)"""
    print("\n4. 测试PUT请求次数API (/v6/rs_put)")
    
    # 计算查询时间范围（最近1天）
    now = time.time()
    one_day_ago = now - 86400  # 1天前
    
    begin_time = time.strftime('%Y%m%d%H%M%S', time.localtime(one_day_ago))
    end_time = time.strftime('%Y%m%d%H%M%S', time.localtime(now))
    
    # 构建查询参数
    params = {
        'begin': begin_time,
        'end': end_time,
        'g': 'day',
        'select': 'hits',  # 根据文档，select参数值必须为hits
        '$bucket': bucket_name,
        '$region': QINIU_CONFIG['region']
    }
    
    # 构建完整URL
    base_url = QINIU_CONFIG['base_url']
    endpoint = '/v6/rs_put'
    query_string = urlencode(params)
    full_url = f"{base_url}{endpoint}?{query_string}"
    
    print(f"请求URL: {full_url}")
    
    # 使用QiniuMacAuth进行认证
    try:
        from qiniu import QiniuMacAuth
        
        # 创建认证对象
        auth = QiniuMacAuth(access_key, secret_key)
        
        # 生成时间戳，用于X-Qiniu-Date头部
        date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
        
        # 生成包含X-Qiniu-Date的认证令牌
        token = auth.token_of_request(
            method="GET",
            host="api.qiniuapi.com",
            url=f"{endpoint}?{query_string}",
            qheaders=f"X-Qiniu-Date: {date_header}",
            content_type="application/x-www-form-urlencoded"
        )
        
        # 设置请求头
        headers = {
            'Authorization': f"Qiniu {token}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Qiniu-Date': date_header
        }
        
        # 发送请求
        response = requests.get(full_url, headers=headers, timeout=30)
        
        print(f"状态码: {response.status_code}")
        if response.content:
            try:
                response_data = response.json()
                print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
        else:
            print("响应为空")
            
    except Exception as e:
        print(f"API调用失败: {str(e)}")

if __name__ == "__main__":
    test_api_connection()