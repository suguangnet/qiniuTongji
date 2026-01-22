"""
七牛云存储用量查询工具

该脚本用于查询七牛云存储空间的用量信息
API文档参考：https://developer.qiniu.com/kodo/api/3807/the-storage-of-usage-queries
"""

import time
import datetime
from urllib.parse import urlencode
import requests
from qiniu import Auth


class QiniuStorageUsage:
    def __init__(self, access_key, secret_key):
        """
        初始化七牛云用量查询类
        
        Args:
            access_key (str): 七牛云Access Key
            secret_key (str): 七牛云Secret Key
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.auth = Auth(access_key, secret_key)
        self.base_url = "https://api.qiniuapi.com/v6/space"
    
    def _create_token(self, path, body=None):
        """
        创建访问令牌（使用七牛云官方SDK）
        
        Args:
            path (str): 请求路径
            body (str, optional): 请求体内容
            
        Returns:
            str: 访问令牌
        """
        # 使用七牛云SDK生成管理凭证
        full_url = f"https://api.qiniuapi.com{path}"
        token = self.auth.token_of_request(url=full_url)
        
        return f"Qiniu {token}"
    
    def get_storage_usage(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """
        获取存储用量信息
        
        Args:
            bucket_name (str, optional): 存储空间名称
            region (str, optional): 存储区域ID
            begin_time (str): 起始日期字符串，格式如：20060102150405
            end_time (str): 结束日期字符串，格式如：20060102150405
            granularity (str): 时间粒度，支持 day/hour/5min
        
        Returns:
            dict: 包含存储用量信息的字典
        """
        # 如果没有提供时间，则使用今天的日期
        if not begin_time or not end_time:
            now = time.strftime('%Y%m%d%H%M%S', time.localtime())
            today = time.strftime('%Y%m%d', time.localtime()) + '000000'
            tomorrow = time.strftime('%Y%m%d', time.localtime(time.time() + 86400)) + '000000'
            
            begin_time = today
            end_time = tomorrow
        
        # 构建查询参数
        params = {
            'begin': begin_time,
            'end': end_time,
            'g': granularity
        }
        
        if bucket_name:
            params['bucket'] = bucket_name
        if region:
            params['region'] = region
        
        # 构建完整URL
        query_string = urlencode(params)
        path = f"/v6/space?{query_string}"
        full_url = f"https://api.qiniuapi.com{path}"
        
        # 创建访问令牌
        token = self._create_token(path)  # 传递路径而非完整URL
        
        # 设置请求头
        headers = {
            'Authorization': token,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Qiniu-Date': time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'
        }
        
        # 发送请求
        response = requests.get(full_url, headers=headers, timeout=30)
        
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'data': response.json() if response.content else None
        }


def format_bytes(bytes_size):
    """
    将字节大小转换为人类可读的格式
    
    Args:
        bytes_size (int): 字节数
        
    Returns:
        str: 格式化后的大小字符串
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def main():
    """
    主函数 - 演示如何使用七牛云存储用量查询功能
    """
    # 从您提供的信息中获取AK/SK和存储空间名
    ACCESS_KEY = "DsHpVVa6tSra_zAUrFHg9dAejTdoRRHTU3Lo9cBP"
    SECRET_KEY = "sLBgW7INeM_N9jKaJz7bzakqv0sherpAhtXMNPpK"
    BUCKET_NAME = "shoposssuguangnetcom"  # 从您提供的URL推断
    
    print("七牛云存储用量查询工具")
    print("=" * 50)
    
    # 创建用量查询实例
    qiniu_usage = QiniuStorageUsage(ACCESS_KEY, SECRET_KEY)
    
    try:
        # 查询今天的存储用量
        print(f"正在查询存储空间 '{BUCKET_NAME}' 的用量信息...")
        result = qiniu_usage.get_storage_usage(bucket_name=BUCKET_NAME)
        
        if result['status_code'] == 200:
            print(f"API调用成功！状态码: {result['status_code']}")
            
            data = result['data']
            if data and 'times' in data and 'datas' in data:
                times = data['times']
                datas = data['datas']
                
                print("\n存储用量详情:")
                print("-" * 30)
                
                for i, (timestamp, size) in enumerate(zip(times, datas)):
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    readable_size = format_bytes(size)
                    
                    print(f"时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"存储量: {readable_size} ({size} 字节)")
                    print("-" * 30)
            else:
                print("未找到用量数据或响应格式不正确")
                print(f"响应内容: {data}")
        else:
            print(f"API调用失败！状态码: {result['status_code']}")
            print(f"响应头: {result['headers']}")
            if result['data']:
                print(f"错误信息: {result['data']}")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()