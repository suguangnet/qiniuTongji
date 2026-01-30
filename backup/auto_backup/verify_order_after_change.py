"""
验证统计卡片顺序
"""

# 读取文件内容
with open('qiniu_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找统计卡片部分
stats_start = content.find('<div id="statsGrid" class="stats-grid"')
next_div_after_stats = content.find('<div class="stat-card">', stats_start)
stats_end = content.find('</div>', content.rfind('<div class="stat-card">', next_div_after_stats, next_div_after_stats + content[next_div_after_stats:].find('</div>') + 1000))

# 从stats_start开始找到所有的stat-card块
import re
stat_blocks = re.findall(r'<div class="stat-card">.*?<div class="stat-title">(.*?)</div>', content[stats_start:], re.DOTALL)

# 提取前6个统计卡片的标题
titles = []
pattern = re.compile(r'<div class="stat-title">(.*?)</div>')
matches = pattern.findall(content[stats_start:])
titles = matches[:6]  # 只取前6个

print("当前统计卡片顺序:")
for i, title in enumerate(titles, 1):
    print(f"{i}. {title}")

print()
print("期望顺序:")
expected_order = [
    "CDN计费带宽",
    "CDN回源流出流量", 
    "GET请求",
    "PUT 请求次数",
    "存储空间",
    "文件数量"
]

for i, title in enumerate(expected_order, 1):
    print(f"{i}. {title}")

print()
if titles == expected_order:
    print("✅ 顺序验证通过！")
else:
    print("❌ 顺序验证失败！")
    print(f"实际顺序: {titles}")
    print(f"期望顺序: {expected_order}")