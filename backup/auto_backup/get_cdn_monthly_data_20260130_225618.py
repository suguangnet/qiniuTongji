"""
获取本月两个域名的CDN流量带宽数据
"""

import json
from datetime import datetime
import requests
from qiniu import Auth


def get_cdn_monthly_data(access_key, secret_key, domains):
    """
    获取本月CDN数据
    
    Args:
        access_key (str): 七牛云Access Key
        secret_key (str): 七牛云Secret Key
        domains (list): 域名列表
    """
    
    # 初始化认证
    q = Auth(access_key, secret_key)
    
    # 设置本月日期范围
    today = datetime.today()
    start_date = f"{today.year}-{today.month:02d}-01"  # 本月第一天
    end_date = today.strftime('%Y-%m-%d')  # 今天
    
    # 域名列表转为字符串，用分号分割
    domains_str = ';'.join(domains)
    
    # API基础配置
    base_url = 'http://fusion.qiniuapi.com'
    
    print(f"正在查询本月CDN数据...")
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"目标域名: {domains_str}")
    print("-" * 60)
    
    # 1. 查询CDN计费流量
    print("1. CDN计费流量数据:")
    flux_url = f"{base_url}/v2/tune/flux"
    flux_payload = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": "day",  # 按天粒度
        "domains": domains_str
    }
    
    try:
        token = q.token_of_request(flux_url, body=json.dumps(flux_payload))
        
        headers = {
            'Authorization': f'QBox {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(flux_url, headers=headers, json=flux_payload)
        
        if response.status_code == 200 and response.json().get('code') == 200:
            flux_data = response.json()
            data_points = flux_data.get('data', {})
            
            for domain, domain_data in data_points.items():
                china_data = domain_data.get('china', [])
                oversea_data = domain_data.get('oversea', [])
                
                total_china = sum(china_data) if china_data else 0
                total_oversea = sum(oversea_data) if oversea_data else 0
                total_all = total_china + total_oversea
                
                print(f"  域名: {domain}")
                print(f"    总流量: {format_bytes(total_all)}")
                print(f"    国内流量: {format_bytes(total_china)}")
                print(f"    海外流量: {format_bytes(total_oversea)}")
                print(f"    日均流量: {format_bytes(total_all/len(china_data)) if china_data else '0 B'}")
        else:
            print(f"    ❌ 流量数据查询失败: {response.text}")
    except Exception as e:
        print(f"    ❌ 查询流量数据时发生错误: {str(e)}")
    
    print()
    
    # 2. 查询CDN计费带宽
    print("2. CDN计费带宽数据:")
    bandwidth_url = f"{base_url}/v2/tune/bandwidth"
    bandwidth_payload = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": "day",
        "domains": domains_str
    }
    
    try:
        token = q.token_of_request(bandwidth_url, body=json.dumps(bandwidth_payload))
        
        headers = {
            'Authorization': f'QBox {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(bandwidth_url, headers=headers, json=bandwidth_payload)
        
        if response.status_code == 200 and response.json().get('code') == 200:
            bandwidth_data = response.json()
            data_points = bandwidth_data.get('data', {})
            
            for domain, domain_data in data_points.items():
                china_data = domain_data.get('china', [])
                oversea_data = domain_data.get('oversea', [])
                
                total_china = sum(china_data) if china_data else 0
                total_oversea = sum(oversea_data) if oversea_data else 0
                avg_china = total_china / len(china_data) if china_data else 0
                avg_oversea = total_oversea / len(oversea_data) if oversea_data else 0
                max_china = max(china_data) if china_data else 0
                max_oversea = max(oversea_data) if oversea_data else 0
                
                print(f"  域名: {domain}")
                print(f"    平均带宽: {avg_china:.2f} bps (国内), {avg_oversea:.2f} bps (海外)")
                print(f"    最高带宽: {max_china} bps (国内), {max_oversea} bps (海外)")
        else:
            print(f"    ❌ 带宽数据查询失败: {response.text}")
    except Exception as e:
        print(f"    ❌ 查询带宽数据时发生错误: {str(e)}")


def format_bytes(bytes_value):
    """
    将字节数转换为人类可读的格式
    """
    if bytes_value is None:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_value)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


# 从配置文件获取AK/SK
try:
    from config import QINIU_CONFIG
    access_key = QINIU_CONFIG['access_key']
    secret_key = QINIU_CONFIG['secret_key']
    
    # 目标域名
    domains = [
        "cdn.mshcodeadventure.top",
        "cdnv.mshcodeadventure.top"
    ]
    
    # 调用API获取本月数据
    get_cdn_monthly_data(access_key, secret_key, domains)
    
except ImportError:
    print("❌ 未找到配置文件，请确保config.py存在并包含正确的AK/SK配置")
except Exception as e:
    print(f"❌ 发生错误: {str(e)}")