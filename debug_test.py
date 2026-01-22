# 调试测试 - 检查CDN回源流量API返回的完整数据
import requests
import time
from urllib.parse import urlencode
from config import QINIU_CONFIG

access_key = QINIU_CONFIG['access_key']
secret_key = QINIU_CONFIG['secret_key']
bucket_name = QINIU_CONFIG['bucket_name']

# 设置查询时间范围（使用Web应用中的相同范围）
# 从2026-01-01到今天
import datetime
now = datetime.datetime.now()
begin_time = '20260101000000'
end_time = now.strftime('%Y%m%d%H%M%S')

print(f'查询范围: {begin_time[:8]} to {end_time[:8]}')
print(f'时间粒度: 5min')

# 测试CDN回源流量
test_config = {'select': 'flow', 'metric': 'cdn_flow_out', 'desc': 'CDN回源流量'}

params = {
    'begin': begin_time,
    'end': end_time,
    'g': '5min',  # 5分钟粒度
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
    print(f'状态码: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'总数据点数: {len(data)}')
        
        # 查找接近2026-01-21T23:55:00+08:00的数据点
        target_time = '2026-01-21T23:55:00+08:00'
        print(f'\n查找时间点 {target_time} 附近的数据:')
        
        found_target = False
        for i, item in enumerate(data):
            time_str = item['time']
            if target_time[:16] in time_str:  # 检查小时和分钟部分
                value = 0
                if 'values' in item:
                    for k, v in item['values'].items():
                        value = v
                print(f'  位置 {i+1}/{len(data)}: 时间={time_str}, 值={value}')
                found_target = True
                
        if not found_target:
            print(f'  未找到 {target_time[:16]} 附近的数据')
        
        # 显示最后几个数据点
        print(f'\n最后5个数据点:')
        for i in range(max(0, len(data)-5), len(data)):
            item = data[i]
            value = 0
            if 'values' in item:
                for k, v in item['values'].items():
                    value = v
            print(f'  位置 {i+1}/{len(data)}: 时间={item["time"]}, 值={value}')
            
        # 检查是否存在非零数据
        non_zero_items = []
        for item in data:
            if 'values' in item:
                for k, v in item['values'].items():
                    if v != 0:
                        non_zero_items.append((item['time'], v))
                        
        print(f'\n非零数据点总数: {len(non_zero_items)}')
        if non_zero_items:
            print('前10个非零数据点:')
            for i, (time_str, value) in enumerate(non_zero_items[:10]):
                print(f'  {i+1}. 时间={time_str}, 值={value}')
    else:
        print(f'错误: {response.text}')
except Exception as e:
    print(f'请求异常: {str(e)}')