from api_manager import QiniuAPIManager
from config import QINIU_CONFIG

print('测试API连接...')
api_manager = QiniuAPIManager()
result = api_manager.get_storage_usage()

if result['status_code'] == 200:
    print('✅ API连接成功')
    print(f'状态码: {result["status_code"]}')
    print(f'数据: {result["data"]}')
else:
    print(f'❌ API连接失败，状态码: {result["status_code"]}')
    if result.get('data'):
        print(f'错误信息: {result["data"]}')
    if result.get('error'):
        print(f'请求错误: {result["error"]}')

print('\n测试blob_io API...')
result2 = api_manager.get_blob_io_stats(select='flow', metric='flow_out')

if result2['status_code'] == 200:
    print('✅ blob_io API连接成功')
    print(f'状态码: {result2["status_code"]}')
    print(f'数据: {result2["data"]}')
else:
    print(f'❌ blob_io API连接失败，状态码: {result2["status_code"]}')
    if result2.get('data'):
        print(f'错误信息: {result2["data"]}')
    if result2.get('error'):
        print(f'请求错误: {result2["error"]}')