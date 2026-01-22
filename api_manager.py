"""
七牛云API管理器

此模块管理各种七牛云API接口的调用
"""

import time
from urllib.parse import urlencode
import requests
from qiniu import Auth, QiniuMacAuth
from config import QINIU_CONFIG, DATA_STAT_API, DEFAULT_PARAMS


class QiniuAPIManager:
    """
    七牛云API管理器，统一管理各种API接口
    """
    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key or QINIU_CONFIG['access_key']
        self.secret_key = secret_key or QINIU_CONFIG['secret_key']
        self.auth = Auth(self.access_key, self.secret_key)
        self.mac_auth = QiniuMacAuth(self.access_key, self.secret_key)
        self.base_url = QINIU_CONFIG['base_url']
    
    def _make_request(self, api_endpoint, params=None, method='GET'):
        """
        通用API请求方法，使用官方SDK进行认证
        """
        if params is None:
            params = {}
        
        # 构建完整URL
        query_string = urlencode(params)
        path = f"{DATA_STAT_API[api_endpoint]['endpoint']}?{query_string}"
        full_url = f"{self.base_url}{path}"

        # 生成时间戳，用于X-Qiniu-Date头部
        date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'

        # 使用QiniuMacAuth生成包含X-Qiniu-Date的认证令牌
        token = self.mac_auth.token_of_request(
            method=method,
            host="api.qiniuapi.com",
            url=path,
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
        try:
            response = requests.get(full_url, headers=headers, timeout=30)
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response.json() if response.content else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'status_code': 0,
                'error': str(e),
                'data': None
            }
    
    def get_storage_usage(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', file_type=None):
        """获取存储用量信息"""
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
        else:
            params['region'] = DEFAULT_PARAMS['region']  # 使用默认区域
        if file_type is not None:
            params['$ftype'] = file_type

        return self._make_request('space', params)
    
    def get_file_count(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', file_type=None):
        """获取文件数量统计"""
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
        else:
            params['region'] = DEFAULT_PARAMS['region']  # 使用默认区域
        if file_type is not None:
            params['$ftype'] = file_type

        return self._make_request('count', params)
    

    

    
    def get_blob_io_stats(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', select='flow', metric='flow_out', domain=None, file_type=None):
        """获取流量和请求次数统计
        
        Args:
            bucket_name (str): 存储空间名称
            region (str): 区域
            begin_time (str): 开始时间
            end_time (str): 结束时间
            granularity (str): 时间粒度
            select (str): 选择字段(flow/hits)
            metric (str): 指标类型(flow_out/cdn_flow_out/hits)
            domain (str): 访问域名
            file_type (str): 存储类型(0-标准存储,1-低频存储,2-归档存储等)
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
            'g': granularity,
            'select': select  # 选择字段：flow(流量) 或 hits(GET请求次数)
        }
        
        # 根据select和metric参数设置指标
        if metric:
            params['$metric'] = metric
        
        # blob_io接口使用$bucket参数格式
        if bucket_name:
            params['$bucket'] = bucket_name
        if region:
            params['$region'] = region
        else:
            params['$region'] = DEFAULT_PARAMS['region']  # 使用默认区域
        if domain:
            params['$domain'] = domain
        if file_type is not None:
            params['$ftype'] = file_type

        return self._make_request('blob_io', params)
    
    def get_put_requests_stats(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', file_type=None):
        """获取PUT请求次数统计
        
        Args:
            bucket_name (str): 存储空间名称
            region (str): 区域
            begin_time (str): 开始时间
            end_time (str): 结束时间
            granularity (str): 时间粒度
            file_type (str): 存储类型(0-标准存储,1-低频存储,2-归档存储等)
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
            'g': granularity,
            'select': 'hits'  # 根据文档，select参数值必须为hits
        }
        
        # rs_put接口使用$bucket参数格式
        if bucket_name:
            params['$bucket'] = bucket_name
        if region:
            params['$region'] = region
        else:
            params['$region'] = DEFAULT_PARAMS['region']  # 使用默认区域
        if file_type is not None:
            params['$ftype'] = file_type

        return self._make_request('rs_put', params)

    def get_bucket_info(self, bucket_name=None):
        """
        获取存储空间信息
        """
        from qiniu import BucketManager
        
        # 使用七牛云官方SDK的BucketManager
        bucket_manager = BucketManager(self.auth)
        
        bucket_name = bucket_name or QINIU_CONFIG['bucket_name']
        
        # 获取存储空间的基本信息
        ret, info = bucket_manager.stat(bucket_name, '')  # 空字符串代表根目录
        
        return {
            'status_code': info.status_code,
            'data': ret,
            'info': info
        }

    def get_bucket_domains(self, bucket_name=None):
        """
        获取存储空间绑定的域名
        """
        from qiniu import BucketManager
        
        # 使用七牛云官方SDK的BucketManager
        bucket_manager = BucketManager(self.auth)
        
        bucket_name = bucket_name or QINIU_CONFIG['bucket_name']
        
        # 获取存储空间绑定的域名
        ret, info = bucket_manager.list_domains(bucket_name)
        
        return {
            'status_code': info.status_code,
            'data': ret,
            'info': info
        }


# 便捷函数
def get_default_api_manager():
    """获取默认的API管理器实例"""
    return QiniuAPIManager()


# 测试函数
def test_api_connection():
    """测试API连接"""
    api_manager = get_default_api_manager()
    
    print("测试API连接...")
    result = api_manager.get_storage_usage()
    
    if result['status_code'] == 200:
        print("✅ API连接成功")
        return True
    else:
        print(f"❌ API连接失败，状态码: {result['status_code']}")
        if result.get('data') and 'error' in result['data']:
            print(f"错误信息: {result['data']['error']}")
        return False