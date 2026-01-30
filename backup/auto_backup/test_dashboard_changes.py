"""
测试qiniu_dashboard.py更改
"""

import re

# 读取文件以验证更改
with open('qiniu_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("验证更改是否成功:")
print("="*50)

# 检查是否包含新的CDN带宽统计卡片
if 'CDN计费带宽' in content:
    print("✅ 找到新的'CDN计费带宽'统计卡片")
else:
    print("❌ 未找到'CDN计费带宽'统计卡片")

# 检查是否包含新的stat-cdn-bandwidth ID
if 'stat-cdn-bandwidth' in content:
    print("✅ 找到新的stat-cdn-bandwidth元素ID")
else:
    print("❌ 未找到stat-cdn-bandwidth元素ID")

# 检查旧的stat-flow-in是否还被引用
cdn_bandwidth_refs = re.findall(r"stat-cdn-bandwidth", content)
flow_in_refs = re.findall(r"stat-flow-in", content)

print(f"stat-cdn-bandwidth 引用次数: {len(cdn_bandwidth_refs)}")
print(f"stat-flow-in 剩余引用次数: {len(flow_in_refs)}")

# 检查HTML部分
html_part = content[content.find('<div class="stat-card">'):content.find('</body>')]

if 'CDN计费带宽' in html_part:
    print("✅ HTML部分包含CDN计费带宽卡片")
    
print("\n更改摘要:")
print("- 替换了'外网流入流量'统计卡片")
print("- 添加了'CDN计费带宽'统计卡片")
print("- 图标更新为📊")
print("- 显示cdn.mshcodeadventure.top的平均带宽: 1,516,595,978.80 bps")