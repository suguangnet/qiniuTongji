"""
七牛云API接口长期范围测试脚本
用于验证长时间范围内的三个关键指标
"""

import requests
import time
from urllib.parse import urlencode
from qiniu import Auth
import json

# 从配置文件导入配置
from config import QINIU_CONFIG

def test_long_range_api():
    """测试长时间范围的API连接"""
    print("=" * 60)
    print("七牛云API接口长时间范围测试")
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
    
    # 测试从2026-01-01到今天的三个关键指标
    test_three_metrics(access_key, secret_key, bucket_name)

def test_three_metrics(access_key, secret_key, bucket_name):
    """测试三个关键指标"""
    print("\n测试三个关键指标 (2026-01-01 至今):")
    
    # 设置查询时间范围（从2026-01-01到现在）
    begin_time = "20260101000000"
    now = time.time()
    end_time = time.strftime('%Y%m%d%H%M%S', time.localtime(now))
    
    print(f"查询范围: {begin_time[:4]}-{begin_time[4:6]}-{begin_time[6:8]} 至 {end_time[:4]}-{end_time[4:6]}-{end_time[6:8]}")
    print(f"时间粒度: 5min")
    
    # 测试不同类型的查询
    test_types = [
        {'select': 'flow', 'metric': 'flow_out', 'desc': '外网流出流量'},
        {'select': 'flow', 'metric': 'cdn_flow_out', 'desc': 'CDN回源流量'},
        {'select': 'hits', 'metric': 'hits', 'desc': 'GET请求次数'}
    ]
    
    for test_config in test_types:
        print(f"\n测试{test_config['desc']}: select={test_config['select']}&metric={test_config['metric']}")
        
        # 构建查询参数
        params = {
            'begin': begin_time,
            'end': end_time,
            'g': '5min',  # 5分钟粒度
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
                    
                    # 分析响应数据
                    if isinstance(response_data, list) and len(response_data) > 0:
                        # 检查是否有非零数据
                        has_non_zero = False
                        total_value = 0
                        
                        for item in response_data:
                            if 'values' in item:
                                values = item['values']
                                for key, value in values.items():
                                    if value != 0:
                                        has_non_zero = True
                                    total_value += value
                        
                        if has_non_zero:
                            print(f"  ✓ 检测到非零数据，总计: {total_value}")
                        else:
                            print(f"  ⚠ 所有数据点均为0，总计: {total_value}")
                    elif isinstance(response_data, dict) and 'times' in response_data and 'datas' in response_data:
                        # times/datas格式
                        datas = response_data['datas']
                        non_zero_count = sum(1 for x in datas if x != 0)
                        total_value = sum(datas)
                        
                        if non_zero_count > 0:
                            print(f"  ✓ 检测到{non_zero_count}个非零数据点，总计: {total_value}")
                        else:
                            print(f"  ⚠ 所有数据点均为0，总计: {total_value}")
                    else:
                        print("  ⚠ 响应格式异常或无数据")
                except:
                    print(f"  响应文本: {response.text}")
            else:
                print("  响应为空")
                
        except Exception as e:
            print(f"  API调用失败: {str(e)}")

if __name__ == "__main__":
    test_long_range_api()