"""
测试配置文件和API管理器
"""

from config import QINIU_CONFIG, DATA_STAT_API, DEFAULT_PARAMS
from api_manager import QiniuAPIManager, test_api_connection


def main():
    print("=" * 60)
    print("七牛云配置测试")
    print("=" * 60)
    
    print("\n1. 配置信息:")
    print(f"   AccessKey: {QINIU_CONFIG['access_key'][:8]}...{QINIU_CONFIG['access_key'][-4:]}")
    print(f"   SecretKey: {QINIU_CONFIG['secret_key'][:8]}...{QINIU_CONFIG['secret_key'][-4:]}")
    print(f"   Bucket: {QINIU_CONFIG['bucket_name']}")
    print(f"   Region: {QINIU_CONFIG['region']} (华北-河北)")
    print(f"   Base URL: {QINIU_CONFIG['base_url']}")
    
    print("\n2. 数据统计API配置:")
    for api_name, api_info in DATA_STAT_API.items():
        print(f"   {api_name}: {api_info['endpoint']} - {api_info['description']}")
    
    print("\n3. 默认参数配置:")
    print(f"   时间粒度: {DEFAULT_PARAMS['granularity']}")
    print(f"   默认区域: {DEFAULT_PARAMS['region']}")
    
    print("\n4. 测试API连接:")
    success = test_api_connection()
    
    if success:
        print("\n5. 初始化API管理器并测试API调用:")
        api_manager = QiniuAPIManager()
        
        print("   测试存储用量查询...")
        result = api_manager.get_storage_usage()
        print(f"   存储量查询状态码: {result['status_code']}")
        
        print("   测试文件数量查询...")
        result = api_manager.get_file_count()
        print(f"   文件数量查询状态码: {result['status_code']}")
        
        print("   测试低频存储用量查询...")
        result = api_manager.get_low_freq_storage_usage()
        print(f"   低频存储查询状态码: {result['status_code']}")
    
    print("\n" + "=" * 60)
    print("配置测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()