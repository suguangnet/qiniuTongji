"""
七牛云API接口模块

此模块提供统一的API接口用于获取七牛云存储数据
"""

from api_manager import QiniuAPIManager
from config import QINIU_CONFIG
import json
from datetime import datetime, timedelta


class QiniuDataAPI:
    """
    七牛云数据API接口
    """
    def __init__(self):
        self.api_manager = QiniuAPIManager(
            QINIU_CONFIG['access_key'],
            QINIU_CONFIG['secret_key']
        )
    
    def get_storage_usage(self, bucket_name=None, days=1, file_type=None):
        """
        获取存储用量信息
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
            file_type (str): 存储类型
        
        Returns:
            dict: 包含时间和存储用量信息的字典
        """
        # 计算查询时间段
        end_time = datetime.now() + timedelta(days=1)
        begin_time = end_time - timedelta(days=days)
        
        begin_str = begin_time.strftime('%Y%m%d') + '000000'
        end_str = end_time.strftime('%Y%m%d') + '000000'
        
        result = self.api_manager.get_storage_usage(
            bucket_name=bucket_name or QINIU_CONFIG['bucket_name'],
            begin_time=begin_str,
            end_time=end_str,
            granularity='day',
            file_type=file_type
        )
        
        if result['status_code'] == 200 and result['data']:
            return {
                'success': True,
                'data': result['data']
            }
        else:
            return {
                'success': False,
                'error': result.get('data', {}).get('error', 'API调用失败'),
                'status_code': result['status_code']
            }
    
    def get_file_count(self, bucket_name=None, days=1, file_type=None):
        """
        获取文件数量统计
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
            file_type (str): 存储类型
        
        Returns:
            dict: 包含时间和文件数量信息的字典
        """
        # 计算查询时间段
        end_time = datetime.now() + timedelta(days=1)
        begin_time = end_time - timedelta(days=days)
        
        begin_str = begin_time.strftime('%Y%m%d') + '000000'
        end_str = end_time.strftime('%Y%m%d') + '000000'
        
        result = self.api_manager.get_file_count(
            bucket_name=bucket_name or QINIU_CONFIG['bucket_name'],
            begin_time=begin_str,
            end_time=end_str,
            granularity='day',
            file_type=file_type
        )
        
        if result['status_code'] == 200 and result['data']:
            return {
                'success': True,
                'data': result['data']
            }
        else:
            return {
                'success': False,
                'error': result.get('data', {}).get('error', 'API调用失败'),
                'status_code': result['status_code']
            }
    
    def format_bytes(self, bytes_size):
        """
        将字节大小转换为人类可读的格式
        
        Args:
            bytes_size (int): 字节数
            
        Returns:
            str: 格式化后的大小字符串
        """
        if bytes_size is None:
            return "N/A"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(bytes_size)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    
    def get_formatted_storage_usage(self, bucket_name=None, days=1):
        """
        获取格式化的存储用量信息
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
        
        Returns:
            list: 包含格式化存储用量信息的列表
        """
        result = self.get_storage_usage(bucket_name, days)
        
        if not result['success']:
            return result
        
        data = result['data']
        formatted_data = []
        
        for i in range(len(data['times'])):
            timestamp = data['times'][i]
            size_bytes = data['datas'][i]
            date = datetime.fromtimestamp(timestamp)
            
            formatted_data.append({
                'time': date.strftime('%Y/%m/%d %H:%M:%S'),
                'storage_display': self.format_bytes(size_bytes),
                'bytes': size_bytes
            })
        
        return {
            'success': True,
            'data': formatted_data
        }
    
    def get_formatted_file_count(self, bucket_name=None, days=1):
        """
        获取格式化的文件数量统计信息
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
        
        Returns:
            list: 包含格式化文件数量信息的列表
        """
        result = self.get_file_count(bucket_name, days)
        
        if not result['success']:
            return result
        
        data = result['data']
        formatted_data = []
        
        for i in range(len(data['times'])):
            timestamp = data['times'][i]
            count = data['datas'][i]
            date = datetime.fromtimestamp(timestamp)
            
            formatted_data.append({
                'time': date.strftime('%Y/%m/%d %H:%M:%S'),
                'count': count,
                'count_display': f"{count:,}"
            })
        
        return {
            'success': True,
            'data': formatted_data
        }
    

    
    def get_blob_io_stats(self, bucket_name=None, days=1, select='flow', metric='flow_out', domain=None, file_type=None):
        """
        获取流量和请求次数统计
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
            select (str): 选择字段(flow/hits)
            metric (str): 指标类型(flow_out/cdn_flow_out/hits)
            domain (str): 访问域名
            file_type (str): 存储类型
        
        Returns:
            dict: 包含时间和流量/请求次数信息的字典
        """
        # 计算查询时间段
        end_time = datetime.now() + timedelta(days=1)
        begin_time = end_time - timedelta(days=days)
        
        begin_str = begin_time.strftime('%Y%m%d') + '000000'
        end_str = end_time.strftime('%Y%m%d') + '000000'
        
        result = self.api_manager.get_blob_io_stats(
            bucket_name=bucket_name or QINIU_CONFIG['bucket_name'],
            begin_time=begin_str,
            end_time=end_str,
            granularity='day',
            select=select,
            metric=metric,
            domain=domain,
            file_type=file_type
        )
        
        if result['status_code'] == 200 and result['data']:
            return {
                'success': True,
                'data': result['data']
            }
        else:
            return {
                'success': False,
                'error': result.get('data', {}).get('error', 'API调用失败'),
                'status_code': result['status_code']
            }
    
    def get_formatted_blob_io_stats(self, bucket_name=None, days=1, select='flow', metric='flow_out', domain=None, file_type=None):
        """
        获取格式化的流量和请求次数统计信息
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
            select (str): 选择字段(flow/hits)
            metric (str): 指标类型(flow_out/cdn_flow_out/hits)
            domain (str): 访问域名
            file_type (str): 存储类型
        
        Returns:
            list: 包含格式化流量/请求次数信息的列表
        """
        result = self.get_blob_io_stats(bucket_name, days, select, metric, domain, file_type)
        
        if not result['success']:
            return result
        
        # 处理响应数据格式 - blob_io接口返回格式与其他接口略有不同
        data = result['data']
        formatted_data = []
        
        if isinstance(data, list):
            # 数组格式
            for item in data:
                if 'time' in item and 'values' in item:
                    if select == 'flow':
                        # 流量数据
                        flow = item['values']['flow'] if 'flow' in item['values'] else 0
                        formatted_data.append({
                            'time': item['time'],
                            'flow': flow,
                            'flow_display': self.format_bytes(flow)
                        })
                    elif select == 'hits':
                        # 请求次数数据
                        hits = item['values']['hits'] if 'hits' in item['values'] else 0
                        formatted_data.append({
                            'time': item['time'],
                            'hits': hits,
                            'hits_display': f"{hits:,}"
                        })
        
        return {
            'success': True,
            'data': formatted_data
        }
    
    def get_put_requests_stats(self, bucket_name=None, days=1, file_type=None):
        """
        获取PUT请求次数统计
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
            file_type (str): 存储类型
        
        Returns:
            dict: 包含时间和PUT请求次数信息的字典
        """
        # 计算查询时间段
        end_time = datetime.now() + timedelta(days=1)
        begin_time = end_time - timedelta(days=days)
        
        begin_str = begin_time.strftime('%Y%m%d') + '000000'
        end_str = end_time.strftime('%Y%m%d') + '000000'
        
        result = self.api_manager.get_put_requests_stats(
            bucket_name=bucket_name or QINIU_CONFIG['bucket_name'],
            begin_time=begin_str,
            end_time=end_str,
            granularity='day',
            file_type=file_type
        )
        
        if result['status_code'] == 200 and result['data']:
            return {
                'success': True,
                'data': result['data']
            }
        else:
            return {
                'success': False,
                'error': result.get('data', {}).get('error', 'API调用失败'),
                'status_code': result['status_code']
            }
    
    def get_formatted_put_requests_stats(self, bucket_name=None, days=1, file_type=None):
        """
        获取格式化的PUT请求次数统计信息
        
        Args:
            bucket_name (str): 存储空间名称，默认使用配置文件中的值
            days (int): 查询天数，默认1天
            file_type (str): 存储类型
        
        Returns:
            list: 包含格式化PUT请求次数信息的列表
        """
        result = self.get_put_requests_stats(bucket_name, days, file_type)
        
        if not result['success']:
            return result
        
        # 处理响应数据格式 - rs_put接口返回格式与其他接口略有不同
        data = result['data']
        formatted_data = []
        
        if isinstance(data, list):
            # 数组格式
            for item in data:
                if 'time' in item and 'values' in item:
                    hits = item['values']['hits'] if 'hits' in item['values'] else 0
                    formatted_data.append({
                        'time': item['time'],
                        'hits': hits,
                        'hits_display': f"{hits:,}"
                    })
        
        return {
            'success': True,
            'data': formatted_data
        }


def main():
    """
    示例用法
    """
    print("=" * 60)
    print("七牛云数据API示例")
    print("=" * 60)
    
    # 创建API实例
    qiniu_api = QiniuDataAPI()
    
    print("\n1. 获取格式化的文件数量信息:")
    count_result = qiniu_api.get_formatted_file_count()
    
    if count_result['success']:
        print("时间\t\t\t文件数量")
        print("-" * 40)
        for item in count_result['data']:
            print(f"{item['time']}\t{item['count_display']}")
    else:
        print(f"获取文件数量失败: {count_result['error']}")
    
    print("\n2. 获取格式化的存储类型转换请求次数信息:")
    ch_type_result = qiniu_api.get_formatted_storage_type_changes()
    
    if ch_type_result['success']:
        print("时间\t\t\t\t\t\t请求次数")
        print("-" * 60)
        for item in ch_type_result['data']:
            print(f"{item['time']}\t{item['hits_display']}")
    else:
        print(f"获取存储类型转换请求次数失败: {ch_type_result['error']}")
    
    print("\n3. 获取格式化的外网流出流量统计信息:")
    blob_io_result = qiniu_api.get_formatted_blob_io_stats(select='flow', metric='flow_out')
    
    if blob_io_result['success']:
        print("时间\t\t\t\t\t流量")
        print("-" * 60)
        for item in blob_io_result['data']:
            print(f"{item['time']}\t{item['flow_display']}")
    else:
        print(f"获取外网流出流量统计失败: {blob_io_result['error']}")
    
    print("\n4. 获取格式化的GET请求次数统计信息:")
    hits_result = qiniu_api.get_formatted_blob_io_stats(select='hits', metric='hits')
    
    if hits_result['success']:
        print("时间\t\t\t\t\t请求次数")
        print("-" * 60)
        for item in hits_result['data']:
            print(f"{item['time']}\t{item['hits_display']}")
    else:
        print(f"获取GET请求次数统计失败: {hits_result['error']}")
    
    print("\n5. 获取格式化的PUT请求次数统计信息:")
    put_result = qiniu_api.get_formatted_put_requests_stats()
    
    if put_result['success']:
        print("时间\t\t\t\t\t请求次数")
        print("-" * 60)
        for item in put_result['data']:
            print(f"{item['time']}\t{item['hits_display']}")
    else:
        print(f"获取PUT请求次数统计失败: {put_result['error']}")


if __name__ == "__main__":
    main()