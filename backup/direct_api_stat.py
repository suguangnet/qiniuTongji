"""
直接调用七牛云API获取请求统计信息
"""

import time
import json
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from calendar import monthrange


def create_qiniu_auth_header(access_key, secret_key, path, body='', content_type=''):
    """
    生成七牛云认证头
    """
    # 构建待签名字符串
    if content_type:
        to_sign = f"POST {path}\nHost: api.qiniu.com\nContent-Type: {content_type}\n\n{body}"
    else:
        to_sign = f"POST {path}\nHost: api.qiniu.com\n\n{body}"

    # 生成签名
    signature = hmac.new(
        secret_key.encode('utf-8'),
        to_sign.encode('utf-8'),
        digestmod=hashlib.sha1
    ).digest()
    
    encoded_signature = base64.b64encode(signature).decode('utf-8')
    auth_header = f"Qiniu {access_key}:{encoded_signature}"
    
    return auth_header, to_sign


def get_current_month_range():
    """获取当前月份的开始和结束时间"""
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 获取本月最后一天
    _, last_day = monthrange(now.year, now.month)
    end_of_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    
    return start_of_month, end_of_month


def get_last_month_range():
    """获取上个月的开始和结束时间"""
    now = datetime.now()
    # 获取上个月的年份和月份
    if now.month == 1:
        prev_month = 12
        prev_year = now.year - 1
    else:
        prev_month = now.month - 1
        prev_year = now.year
    
    # 获取上个月的最后一天
    _, last_day = monthrange(prev_year, prev_month)
    
    start_of_last_month = datetime(prev_year, prev_month, 1, 0, 0, 0, 0)
    end_of_last_month = datetime(prev_year, prev_month, last_day, 23, 59, 59, 999999)
    
    return start_of_last_month, end_of_last_month


def format_datetime_for_api(dt):
    """将datetime对象格式化为API所需的时间格式 YYYYMMDDHHMMSS"""
    return dt.strftime('%Y%m%d%H%M%S')


def query_bucket_stat(access_key, secret_key, bucket_name, begin_time, end_time):
    """
    查询存储桶统计信息
    """
    url = "http://api.qiniu.com/v6/bucket/stat"
    
    # 构造请求体
    params = {
        '$bucket': bucket_name,
        'begin': format_datetime_for_api(begin_time),
        'end': format_datetime_for_api(end_time),
        'g': 'day'  # 按天粒度
    }
    
    # 将参数转换为查询字符串
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    # 构造路径和请求体
    path = f"/v6/bucket/stat?{query_string}"
    
    # 生成认证头
    auth_header, to_sign = create_qiniu_auth_header(access_key, secret_key, path)
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(url + '?' + query_string, headers=headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.content else {}
        }
    except Exception as e:
        return {
            'status_code': 0,
            'error': str(e),
            'data': {}
        }


def query_api_request_stat(access_key, secret_key, bucket_name, begin_time, end_time, metric_type='hits'):
    """
    查询API请求统计
    """
    url = "http://api.qiniu.com/v6/blob_io"
    
    # 构造请求参数
    params = {
        '$bucket': bucket_name,
        'begin': format_datetime_for_api(begin_time),
        'end': format_datetime_for_api(end_time),
        'g': 'day'  # 按天粒度
    }
    
    if metric_type == 'hits':
        # 查询GET请求次数
        params['select'] = 'hits'
        params['$metric'] = 'hits'
    elif metric_type == 'put':
        # 查询PUT请求次数
        params['select'] = 'ops'
        params['$metric'] = 'put'
    else:
        params['select'] = metric_type
        params['$metric'] = metric_type
    
    # 将参数转换为查询字符串
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    # 构造路径
    path = f"/v6/blob_io?{query_string}"
    
    # 生成认证头
    auth_header, to_sign = create_qiniu_auth_header(access_key, secret_key, path)
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(url + '?' + query_string, headers=headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.content else {}
        }
    except Exception as e:
        return {
            'status_code': 0,
            'error': str(e),
            'data': {}
        }


def calculate_total_requests(data):
    """计算总请求数"""
    total = 0
    if isinstance(data, list) and len(data) > 0:
        for item in data:
            if item and item.get('values'):
                # 查找hits或put的值
                for key in item['values']:
                    if key in ['hits', 'put', 'get', 'post', 'requests']:
                        total += item['values'][key]
    elif data.get('times') and data.get('datas'):
        # 处理times/datas格式
        for value in data['datas']:
            total += value
    
    return total


def main():
    print("=" * 70)
    print("七牛云API请求次数统计查询工具（直连API版）")
    print("=" * 70)

    # 使用提供的AK/SK配置
    ACCESS_KEY = 'viamdhr9ySWyYE3vj-Mkg7Eaedo0L7q8X05KWiRa'
    SECRET_KEY = 'TI8BcbpbzxEIX8rVUpPWxBP3IMvwdmAvP48OQrdB'
    BUCKET_NAME = 'recordingmini'

    print(f"AccessKey: {ACCESS_KEY[:8]}...{ACCESS_KEY[-4:]}")
    print(f"SecretKey: {SECRET_KEY[:8]}...{SECRET_KEY[-4:]}")
    print(f"存储空间: {BUCKET_NAME}")
    print("-" * 70)

    # 获取当前月份和上个月的时间范围
    current_start, current_end = get_current_month_range()
    last_start, last_end = get_last_month_range()

    print(f"查询当前月份: {current_start.strftime('%Y-%m-%d')} 到 {current_end.strftime('%Y-%m-%d')}")
    print(f"查询上个月: {last_start.strftime('%Y-%m-%d')} 到 {last_end.strftime('%Y-%m-%d')}")
    print("-" * 70)

    try:
        # 查询当前月份的GET请求次数
        print("正在查询当前月份的GET请求次数...")
        get_current_result = query_api_request_stat(ACCESS_KEY, SECRET_KEY, BUCKET_NAME, current_start, current_end, 'hits')
        
        # 查询当前月份的PUT请求次数
        print("正在查询当前月份的PUT请求次数...")
        put_current_result = query_api_request_stat(ACCESS_KEY, SECRET_KEY, BUCKET_NAME, current_start, current_end, 'put')
        
        # 查询上个月的GET请求次数
        print("正在查询上个月的GET请求次数...")
        get_last_result = query_api_request_stat(ACCESS_KEY, SECRET_KEY, BUCKET_NAME, last_start, last_end, 'hits')
        
        # 查询上个月的PUT请求次数
        print("正在查询上个月的PUT请求次数...")
        put_last_result = query_api_request_stat(ACCESS_KEY, SECRET_KEY, BUCKET_NAME, last_start, last_end, 'put')

        # 计算总请求数
        current_get_total = calculate_total_requests(get_current_result.get('data', {}))
        current_put_total = calculate_total_requests(put_current_result.get('data', {}))
        last_get_total = calculate_total_requests(get_last_result.get('data', {}))
        last_put_total = calculate_total_requests(put_last_result.get('data', {}))

        # 显示结果
        print("\nAPI请求次数统计结果:")
        print("-" * 70)
        
        print(f"本月 API 请求次数（GET/PUT）: {current_get_total}/{current_put_total}")
        print(f"上月 API 请求次数（GET/PUT）: {last_get_total}/{last_put_total}")
        
        print(f"\n详细数据:")
        print(f"- 本月GET请求次数: {current_get_total:,}")
        print(f"- 本月PUT请求次数: {current_put_total:,}")
        print(f"- 上月GET请求次数: {last_get_total:,}")
        print(f"- 上月PUT请求次数: {last_put_total:,}")
        
        # 检查是否有错误
        for result, desc in [(get_current_result, "本月GET"), (put_current_result, "本月PUT"), 
                              (get_last_result, "上月GET"), (put_last_result, "上月PUT")]:
            if result.get('status_code') != 200:
                print(f"\n⚠️  {desc}请求查询失败，状态码: {result.get('status_code', 'Unknown')}")
                if result.get('data'):
                    print(f"   响应数据: {result['data']}")
                if result.get('error'):
                    print(f"   错误信息: {result['error']}")
        
    except Exception as e:
        print(f"发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

    print("=" * 70)


if __name__ == '__main__':
    main()