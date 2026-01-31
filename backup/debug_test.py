"""
调试七牛云API连接和权限状态
"""
import time
import datetime
from api_manager import QiniuAPIManager

# 使用当前配置
ACCESS_KEY = 'viamdhr9ySWyYE3vj-Mkg7Eaedo0L7q8X05KWiRa'
SECRET_KEY = 'TI8BcbpbzxEIX8rVUpPWxBP3IMvwdmAvP48OQrdB'
BUCKET_NAME = 'recordingmini'

def test_api_connection():
    print("=" * 60)
    print("七牛云API连接和权限调试")
    print("=" * 60)
    print(f"存储空间: {BUCKET_NAME}")
    print(f"AccessKey: {ACCESS_KEY[:8]}...{ACCESS_KEY[-4:]}")
    print("-" * 60)
    
    # 创建API管理器
    api_manager = QiniuAPIManager(ACCESS_KEY, SECRET_KEY)
    
    # 设置时间范围（最近一天）
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    
    begin_time = yesterday.strftime('%Y%m%d000000')
    end_time = now.strftime('%Y%m%d235959')
    
    print(f"查询时间范围: {begin_time} - {end_time}")
    print("-" * 60)
    
    # 测试各项API
    print("1. 测试存储用量查询...")
    storage_result = api_manager.get_storage_usage(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day'
    )
    print(f"   存储用量查询结果: 状态码 {storage_result.get('status_code')}")
    if storage_result.get('status_code') == 200:
        print(f"   数据: {storage_result.get('data')}")
    else:
        print(f"   错误: {storage_result.get('error')}")
    
    print("\n2. 测试文件数量查询...")
    files_result = api_manager.get_file_count(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day'
    )
    print(f"   文件数量查询结果: 状态码 {files_result.get('status_code')}")
    if files_result.get('status_code') == 200:
        print(f"   数据: {files_result.get('data')}")
    else:
        print(f"   错误: {files_result.get('error')}")
    
    print("\n3. 测试外网流出流量查询...")
    flow_out_result = api_manager.get_blob_io_stats(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day',
        select='flow',
        metric='flow_out'
    )
    print(f"   外网流出流量查询结果: 状态码 {flow_out_result.get('status_code')}")
    if flow_out_result.get('status_code') == 200:
        print(f"   数据: {flow_out_result.get('data')}")
    else:
        print(f"   错误: {flow_out_result.get('error')}")
    
    print("\n4. 测试CDN回源流量查询...")
    cdn_flow_result = api_manager.get_blob_io_stats(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day',
        select='flow',
        metric='cdn_flow_out'
    )
    print(f"   CDN回源流量查询结果: 状态码 {cdn_flow_result.get('status_code')}")
    if cdn_flow_result.get('status_code') == 200:
        print(f"   数据: {cdn_flow_result.get('data')}")
    else:
        print(f"   错误: {cdn_flow_result.get('error')}")
    
    print("\n5. 测试GET请求次数查询...")
    get_requests_result = api_manager.get_blob_io_stats(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day',
        select='hits',
        metric='hits'
    )
    print(f"   GET请求次数查询结果: 状态码 {get_requests_result.get('status_code')}")
    if get_requests_result.get('status_code') == 200:
        print(f"   数据: {get_requests_result.get('data')}")
    else:
        print(f"   错误: {get_requests_result.get('error')}")
    
    print("-" * 60)
    print("调试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_api_connection()