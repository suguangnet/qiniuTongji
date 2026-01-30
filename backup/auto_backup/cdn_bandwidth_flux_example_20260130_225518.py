"""
七牛云CDN流量带宽API调用示例
用于查询指定域名的CDN带宽和流量数据
"""

import json
import time
from datetime import datetime, timedelta
import requests
from qiniu import Auth


def get_cdn_bandwidth_and_flux(access_key, secret_key, domains, start_date=None, end_date=None, granularity='day'):
    """
    获取CDN带宽和流量数据
    
    Args:
        access_key (str): 七牛云Access Key
        secret_key (str): 七牛云Secret Key
        domains (list): 域名列表
        start_date (str): 开始日期，格式：'YYYY-MM-DD'，默认为7天前
        end_date (str): 结束日期，格式：'YYYY-MM-DD'，默认为今天
        granularity (str): 时间粒度，可选值：'5min', 'hour', 'day'
    """
    
    # 初始化认证
    q = Auth(access_key, secret_key)
    
    # 如果未提供日期，则使用默认值
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 域名列表转为字符串，用分号分割
    domains_str = ';'.join(domains)
    
    # API基础配置
    base_url = 'http://fusion.qiniuapi.com'
    
    # 1. 查询CDN计费带宽
    print("=" * 60)
    print("正在查询CDN计费带宽数据...")
    print(f"域名: {domains_str}")
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"时间粒度: {granularity}")
    print("-" * 60)
    
    bandwidth_url = f"{base_url}/v2/tune/bandwidth"
    bandwidth_payload = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": granularity,
        "domains": domains_str
    }
    
    try:
        # 生成认证token - 使用正确的API调用方式
        token = q.token_of_request(bandwidth_url, body=json.dumps(bandwidth_payload))
        
        headers = {
            'Authorization': f'QBox {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(bandwidth_url, headers=headers, json=bandwidth_payload)
        
        if response.status_code == 200:
            bandwidth_data = response.json()
            print("✅ CDN计费带宽数据获取成功!")
            
            if bandwidth_data.get('code') == 200:
                time_points = bandwidth_data.get('time', [])
                data_points = bandwidth_data.get('data', {})
                
                print(f"时间点数量: {len(time_points)}")
                print(f"域名数据: {list(data_points.keys())}")
                
                # 输出带宽数据概览
                for domain, domain_data in data_points.items():
                    china_data = domain_data.get('china', [])
                    oversea_data = domain_data.get('oversea', [])
                    
                    print(f"\n域名: {domain}")
                    print(f"  国内带宽数据点: {len(china_data)}")
                    print(f"  海外带宽数据点: {len(oversea_data)}")
                    
                    if china_data:
                        avg_china = sum(china_data) / len(china_data) if china_data else 0
                        max_china = max(china_data) if china_data else 0
                        print(f"  国内平均带宽: {avg_china:.2f} bps")
                        print(f"  国内最高带宽: {max_china} bps")
                    
                    if oversea_data:
                        avg_oversea = sum(oversea_data) / len(oversea_data) if oversea_data else 0
                        max_oversea = max(oversea_data) if oversea_data else 0
                        print(f"  海外平均带宽: {avg_oversea:.2f} bps")
                        print(f"  海外最高带宽: {max_oversea} bps")
            else:
                print(f"❌ API返回错误: {bandwidth_data.get('error', '未知错误')}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询CDN带宽时发生错误: {str(e)}")
    
    print("\n" + "=" * 60)
    
    # 2. 查询CDN计费流量
    print("正在查询CDN计费流量数据...")
    print(f"域名: {domains_str}")
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"时间粒度: {granularity}")
    print("-" * 60)
    
    flux_url = f"{base_url}/v2/tune/flux"
    flux_payload = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": granularity,
        "domains": domains_str
    }
    
    try:
        # 生成认证token
        token = q.token_of_request(flux_url, body=json.dumps(flux_payload))
        
        headers = {
            'Authorization': f'QBox {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(flux_url, headers=headers, json=flux_payload)
        
        if response.status_code == 200:
            flux_data = response.json()
            print("✅ CDN计费流量数据获取成功!")
            
            if flux_data.get('code') == 200:
                time_points = flux_data.get('time', [])
                data_points = flux_data.get('data', {})
                
                print(f"时间点数量: {len(time_points)}")
                print(f"域名数据: {list(data_points.keys())}")
                
                # 输出流量数据概览
                for domain, domain_data in data_points.items():
                    china_data = domain_data.get('china', [])
                    oversea_data = domain_data.get('oversea', [])
                    
                    print(f"\n域名: {domain}")
                    print(f"  国内流量数据点: {len(china_data)}")
                    print(f"  海外流量数据点: {len(oversea_data)}")
                    
                    if china_data:
                        total_china = sum(china_data)
                        avg_china = total_china / len(china_data) if china_data else 0
                        print(f"  国内总流量: {format_bytes(total_china)}")
                        print(f"  国内平均流量: {format_bytes(avg_china)}")
                    
                    if oversea_data:
                        total_oversea = sum(oversea_data)
                        avg_oversea = total_oversea / len(oversea_data) if oversea_data else 0
                        print(f"  海外总流量: {format_bytes(total_oversea)}")
                        print(f"  海外平均流量: {format_bytes(avg_oversea)}")
            else:
                print(f"❌ API返回错误: {flux_data.get('error', '未知错误')}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询CDN流量时发生错误: {str(e)}")
    
    print("\n" + "=" * 60)
    
    # 3. 查询CDN监控带宽（实时数据）
    print("正在查询CDN监控带宽数据...")
    print(f"域名: {domains_str}")
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"时间粒度: {granularity}")
    print("-" * 60)
    
    monitoring_bandwidth_url = f"{base_url}/v2/tune/monitoring/bandwidth"
    monitoring_payload = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": granularity,
        "domains": domains_str
    }
    
    try:
        # 生成认证token
        token = q.token_of_request(monitoring_bandwidth_url, body=json.dumps(monitoring_payload))
        
        headers = {
            'Authorization': f'QBox {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(monitoring_bandwidth_url, headers=headers, json=monitoring_payload)
        
        if response.status_code == 200:
            monitoring_data = response.json()
            print("✅ CDN监控带宽数据获取成功!")
            
            if monitoring_data.get('code') == 200:
                time_points = monitoring_data.get('time', [])
                data_points = monitoring_data.get('data', {})
                
                print(f"时间点数量: {len(time_points)}")
                print(f"域名数据: {list(data_points.keys())}")
                
                # 输出监控带宽数据概览
                for domain, domain_data in data_points.items():
                    china_data = domain_data.get('china', [])
                    oversea_data = domain_data.get('oversea', [])
                    
                    print(f"\n域名: {domain}")
                    print(f"  国内监控带宽数据点: {len(china_data)}")
                    print(f"  海外监控带宽数据点: {len(oversea_data)}")
                    
                    if china_data:
                        avg_china = sum(china_data) / len(china_data) if china_data else 0
                        max_china = max(china_data) if china_data else 0
                        print(f"  国内平均监控带宽: {avg_china:.2f} bps")
                        print(f"  国内最高监控带宽: {max_china} bps")
                    
                    if oversea_data:
                        avg_oversea = sum(oversea_data) / len(oversea_data) if oversea_data else 0
                        max_oversea = max(oversea_data) if oversea_data else 0
                        print(f"  海外平均监控带宽: {avg_oversea:.2f} bps")
                        print(f"  海外最高监控带宽: {max_oversea} bps")
            else:
                print(f"❌ API返回错误: {monitoring_data.get('error', '未知错误')}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询CDN监控带宽时发生错误: {str(e)}")


def format_bytes(bytes_value):
    """
    将字节数转换为人类可读的格式
    """
    if bytes_value is None:
        return "N/A"
    
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
    print("七牛云CDN流量带宽API调用示例")
    print("=" * 60)
    print(f"✅ 从配置文件获取凭证成功")
    print(f"AccessKey: {access_key[:8]}...{access_key[-4:]}")
    
    # 目标域名
    domains = [
        "cdn.mshcodeadventure.top",
        "cdnv.mshcodeadventure.top"
    ]
    
    print(f"目标域名: {', '.join(domains)}")
    print("-" * 60)
    
    # 调用API
    get_cdn_bandwidth_and_flux(
        access_key=access_key,
        secret_key=secret_key,
        domains=domains,
        start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),  # 7天前
        end_date=datetime.now().strftime('%Y-%m-%d'),  # 今天
        granularity='day'  # 按天粒度
    )
    
except ImportError:
    print("❌ 未找到配置文件，请确保config.py存在并包含正确的AK/SK配置")
except Exception as e:
    print(f"❌ 发生错误: {str(e)}")