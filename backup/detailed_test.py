import requests
import time
from urllib.parse import urlencode
from config import QINIU_CONFIG

access_key = QINIU_CONFIG['access_key']
secret_key = QINIU_CONFIG['secret_key']
bucket_name = QINIU_CONFIG['bucket_name']

# 设置查询时间范围（从2026-01-21 23:50 到 2026-01-22 00:00）
begin_time = '20260121235000'
end_time = '20260122000000'

print('查询范围:', begin_time, 'to', end_time)

# 测试三个指标
test_types = [
    {'select': 'flow', 'metric': 'flow_out', 'desc': '外网流出流量'},
    {'select': 'flow', 'metric': 'cdn_flow_out', 'desc': 'CDN回源流量'},
    {'select': 'hits', 'metric': 'hits', 'desc': 'GET请求次数'}
]

for test_config in test_types:
    print(f'\n测试 {test_config["desc"]}')
    
    params = {
        'begin': begin_time,
        'end': end_time,
        'g': '5min',
        '$bucket': bucket_name,
        '$region': QINIU_CONFIG['region'],
        'select': test_config['select'],
        '$metric': test_config['metric']
    }
    
    base_url = QINIU_CONFIG['base_url']
    endpoint = '/v6/blob_io'
    query_string = urlencode(params)
    full_url = f'{base_url}{endpoint}?{query_string}'
    
    from qiniu import QiniuMacAuth
    auth = QiniuMacAuth(access_key, secret_key)
    date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
    token = auth.token_of_request(
        method='GET',
        host='api.qiniuapi.com',
        url=f'{endpoint}?{query_string}',
        qheaders=f'X-Qiniu-Date: {date_header}',
        content_type='application/x-www-form-urlencoded'
    )
    
    headers = {
        'Authorization': f'Qiniu {token}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Qiniu-Date': date_header
    }
    
    try:
        response = requests.get(full_url, headers=headers, timeout=30)
        print(f'  状态码: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('  API响应数据:')
            for i, item in enumerate(data):
                value = 0
                if 'values' in item:
                    for k, v in item['values'].items():
                        value = v
                print(f'    {i+1}. 时间: {item["time"]}, 值: {value}')
                if '23:55' in item['time']:  # 检查特定时间点
                    print(f'      -> 这是您看到的时间点，值为: {value}')
        else:
            print(f'  错误: {response.text}')
    except Exception as e:
        print(f'  请求异常: {str(e)}')