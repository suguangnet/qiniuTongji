"""
七牛云配置文件

此文件包含七牛云服务的基本配置信息
"""

# 七牛云服务配置
QINIU_CONFIG = {
    'access_key': 'viamdhr9ySWyYE3vj-Mkg7Eaedo0L7q8X05KWiRa',
    'secret_key': 'TI8BcbpbzxEIX8rVUpPWxBP3IMvwdmAvP48OQrAB',
    'bucket_name': 'recordingmini',
    'region': 'z2',  # 华南-广东
    'base_url': 'https://api.qiniuapi.com',
    'cdn_domains': [
        'cdn.mshcodeadventure.top',
        'cdnv.mshcodeadventure.top'
    ]
}

# 数据统计API配置
DATA_STAT_API = {
    'space': {
        'endpoint': '/v6/space',
        'description': '存储量统计'
    },
    'count': {
        'endpoint': '/v6/count',
        'description': '文件数量统计'
    },
    'blob_io': {
        'endpoint': '/v6/blob_io',
        'description': '流量和请求次数统计'
    },
    'rs_put': {
        'endpoint': '/v6/rs_put',
        'description': 'PUT请求次数统计'
    }
}

# 时间格式配置
TIME_FORMAT = {
    'date_format': '%Y-%m-%d',
    'datetime_format': '%Y%m%d%H%M%S',
    'timestamp_format': '%Y-%m-%d %H:%M:%S'
}

# 默认参数配置
DEFAULT_PARAMS = {
    'granularity': 'day',  # 默认时间粒度
    'region': 'z1'  # 默认区域
}
