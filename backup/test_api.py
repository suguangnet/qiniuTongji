"""测试七牛云API连接和数据获取"""

from qiniu_dashboard import QiniuDataStatAPI, ACCESS_KEY, SECRET_KEY, BUCKET_NAME
import time

print("=" * 60)
print("测试七牛云API连接")
print("=" * 60)

# 创建API实例
qiniu_api = QiniuDataStatAPI(ACCESS_KEY, SECRET_KEY)

# 设置时间范围（最近7天）
now = time.time()
seven_days_ago = now - 7 * 24 * 60 * 60

begin_time = time.strftime('%Y%m%d000000', time.localtime(seven_days_ago))
end_time = time.strftime('%Y%m%d235959', time.localtime(now))

print(f"查询时间范围: {begin_time} - {end_time}")
print("-" * 60)

# 测试1: 存储用量
print("\n1. 测试存储用量查询...")
storage_result = qiniu_api.get_storage_usage(
    bucket_name=BUCKET_NAME,
    begin_time=begin_time,
    end_time=end_time,
    granularity='day'
)
print(f"状态码: {storage_result.get('status_code')}")
if storage_result.get('data'):
    print(f"数据: {str(storage_result['data'])[:200]}...")
else:
    print(f"错误: {storage_result.get('error', '无数据')}")

# 测试2: 文件数量
print("\n2. 测试文件数量查询...")
file_count_result = qiniu_api.get_file_count(
    bucket_name=BUCKET_NAME,
    begin_time=begin_time,
    end_time=end_time,
    granularity='day'
)
print(f"状态码: {file_count_result.get('status_code')}")
if file_count_result.get('data'):
    print(f"数据: {str(file_count_result['data'])[:200]}...")
else:
    print(f"错误: {file_count_result.get('error', '无数据')}")

# 测试3: 外网流出流量
print("\n3. 测试外网流出流量查询...")
flow_out_result = qiniu_api.get_blob_io_stats(
    bucket_name=BUCKET_NAME,
    begin_time=begin_time,
    end_time=end_time,
    granularity='day',
    select='flow',
    metric='flow_out'
)
print(f"状态码: {flow_out_result.get('status_code')}")
if flow_out_result.get('data'):
    print(f"数据: {str(flow_out_result['data'])[:200]}...")
else:
    print(f"错误: {flow_out_result.get('error', '无数据')}")

# 测试4: CDN回源流量
print("\n4. 测试CDN回源流量查询...")
cdn_flow_result = qiniu_api.get_blob_io_stats(
    bucket_name=BUCKET_NAME,
    begin_time=begin_time,
    end_time=end_time,
    granularity='day',
    select='flow',
    metric='cdn_flow_out'
)
print(f"状态码: {cdn_flow_result.get('status_code')}")
if cdn_flow_result.get('data'):
    print(f"数据: {str(cdn_flow_result['data'])[:200]}...")
else:
    print(f"错误: {cdn_flow_result.get('error', '无数据')}")

# 测试5: GET请求次数
print("\n5. 测试GET请求次数查询...")
get_requests_result = qiniu_api.get_blob_io_stats(
    bucket_name=BUCKET_NAME,
    begin_time=begin_time,
    end_time=end_time,
    granularity='day',
    select='hits',
    metric='hits'
)
print(f"状态码: {get_requests_result.get('status_code')}")
if get_requests_result.get('data'):
    print(f"数据: {str(get_requests_result['data'])[:200]}...")
else:
    print(f"错误: {get_requests_result.get('error', '无数据')}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
