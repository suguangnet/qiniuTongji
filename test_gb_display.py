"""
测试GB单位显示
"""

# 计算流量数据
main_domain_tb = 29.69  # 主域名流量 (TB)
main_domain_gb = main_domain_tb * 1024  # 转换为GB
sub_domain_gb = 6.91  # 辅域名流量 (GB)

print("CDN流量数据显示测试")
print("="*40)
print(f"主域名流量: {main_domain_tb} TB = {main_domain_gb:.2f} GB")
print(f"辅域名流量: {sub_domain_gb:.2f} GB")
print()
print(f"显示格式: 主: {main_domain_gb:.2f} GB, 辅: {sub_domain_gb:.2f} GB")
print()
print("数据来源:")
print(f"- cdn.mshcodeadventure.top: {main_domain_tb} TB ({main_domain_gb:.2f} GB)")
print(f"- cdnv.mshcodeadventure.top: {sub_domain_gb:.2f} GB")