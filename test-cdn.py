"""
CDN 流量/带宽接口测试脚本

调用七牛 CDN API（流量带宽文档）：
- 批量查询 CDN 计费带宽 POST /v2/tune/bandwidth
- 批量查询 CDN 计费流量 POST /v2/tune/flux

域名参数使用 config.py 中的 cdn_domains。
"""

import datetime
import json

from config import QINIU_CONFIG
from api_manager import QiniuAPIManager


def format_bytes(bytes_val):
    """字节转为可读格式"""
    if bytes_val is None:
        return "N/A"
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {u}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def bytes_to_gb(bytes_val):
    """字节转 GB，用于按 GB 统计"""
    if bytes_val is None:
        return 0.0
    return float(bytes_val) / (1024 ** 3)


def format_gb(bytes_val):
    """字节转为 GB 显示"""
    return f"{bytes_to_gb(bytes_val):.4f} GB"


def format_bps(bps_val):
    """bps 转为可读格式"""
    if bps_val is None:
        return "N/A"
    for u in ['bps', 'Kbps', 'Mbps', 'Gbps']:
        if bps_val < 1000:
            return f"{bps_val:.2f} {u}"
        bps_val /= 1000
    return f"{bps_val:.2f} Gbps"


def main():
    # 域名使用 config 中的 cdn_domains
    domains = QINIU_CONFIG.get('cdn_domains', [])
    if not domains:
        print("错误: config.py 中未配置 cdn_domains")
        return

    # 时间范围: 2026-01-01 ~ 2026-01-31（带宽接口不超过 31 天，流量不超过 30 天）
    start_str = '2026-01-01'
    end_str = '2026-01-31'
    granularity = 'day'

    print("=" * 60)
    print("CDN 流量/带宽 API 测试")
    print("=" * 60)
    print(f"域名列表 (cdn_domains): {domains}")
    print(f"时间范围: {start_str} ~ {end_str}")
    print(f"粒度: {granularity}")
    print("-" * 60)

    api = QiniuAPIManager(
        access_key=QINIU_CONFIG['access_key'],
        secret_key=QINIU_CONFIG['secret_key']
    )

    # 1. CDN 计费带宽 /v2/tune/bandwidth
    print("\n【1】批量查询 CDN 计费带宽 POST /v2/tune/bandwidth")
    bw_result = api.get_cdn_bandwidth_stats(
        domains=domains,
        start_date=start_str,
        end_date=end_str,
        granularity=granularity
    )
    if bw_result['status_code'] == 200 and bw_result.get('data'):
        data = bw_result['data']
        code = data.get('code', 0)
        if code == 200:
            times = data.get('time', [])
            print(f"  时间点数量: {len(times)}")
            for domain, vals in data.get('data', {}).items():
                china = vals.get('china', [])
                oversea = vals.get('oversea', [])
                print(f"  域名: {domain}")
                print(f"    国内带宽点数: {len(china)}, 海外: {len(oversea)}")
                if times and china:
                    for i, t in enumerate(times[:5]):
                        c = china[i] if i < len(china) else 0
                        o = oversea[i] if i < len(oversea) else 0
                        print(f"      {t} -> 国内 {format_bps(c)}, 海外 {format_bps(o)}")
                    if len(times) > 5:
                        print(f"      ... 共 {len(times)} 个时间点")
            print("\n  原始响应 data 片段:")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1200] + "\n  ...")
        else:
            print(f"  接口返回 code={code}, error={data.get('error', '')}")
    else:
        print(f"  请求失败: status_code={bw_result.get('status_code')}, error={bw_result.get('error', '')}")
        if bw_result.get('data'):
            print("  响应:", json.dumps(bw_result['data'], ensure_ascii=False, indent=2))

    # 2. CDN 计费流量 /v2/tune/flux（按 GB 统计）
    print("\n【2】批量查询 CDN 计费流量 POST /v2/tune/flux（按 GB 统计）")
    flux_result = api.get_cdn_traffic_stats(
        domains=domains,
        start_date=start_str,
        end_date=end_str,
        granularity=granularity
    )
    if flux_result['status_code'] == 200 and flux_result.get('data'):
        data = flux_result['data']
        code = data.get('code', 0)
        if code == 200:
            times = data.get('time', [])
            print(f"  时间点数量: {len(times)}")
            total_china_gb = 0.0
            total_oversea_gb = 0.0
            for domain, vals in data.get('data', {}).items():
                china = vals.get('china', [])
                oversea = vals.get('oversea', [])
                china_sum = sum(china)
                oversea_sum = sum(oversea)
                china_gb = bytes_to_gb(china_sum)
                oversea_gb = bytes_to_gb(oversea_sum)
                total_china_gb += china_gb
                total_oversea_gb += oversea_gb
                print(f"  域名: {domain}")
                print(f"    国内总流量: {format_gb(china_sum)}  |  海外总流量: {format_gb(oversea_sum)}")
                print(f"    国内总流量(GB): {china_gb:.4f} GB  |  海外总流量(GB): {oversea_gb:.4f} GB")
                if times and china:
                    for i, t in enumerate(times[:5]):
                        c = china[i] if i < len(china) else 0
                        o = oversea[i] if i < len(oversea) else 0
                        print(f"      {t} -> 国内 {format_gb(c)}, 海外 {format_gb(o)}")
                    if len(times) > 5:
                        print(f"      ... 共 {len(times)} 个时间点（单位均为 GB）")
            print("\n  ---------- 按 GB 汇总 ----------")
            print(f"  国内总流量(所有域名): {total_china_gb:.4f} GB")
            print(f"  海外总流量(所有域名): {total_oversea_gb:.4f} GB")
            print(f"  合计总流量: {total_china_gb + total_oversea_gb:.4f} GB")
            print("\n  原始响应 data 片段:")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1200] + "\n  ...")
        else:
            print(f"  接口返回 code={code}, error={data.get('error', '')}")
    else:
        print(f"  请求失败: status_code={flux_result.get('status_code')}, error={flux_result.get('error', '')}")
        if flux_result.get('data'):
            print("  响应:", json.dumps(flux_result['data'], ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("测试结束")
    print("=" * 60)


if __name__ == '__main__':
    main()
