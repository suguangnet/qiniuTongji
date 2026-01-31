"""
七牛云API请求次数统计表格显示
显示GET和PUT请求次数的表格
"""

import time
import datetime
from flask import Flask, render_template_string
from api_manager import QiniuAPIManager


app = Flask(__name__)

# 使用独立配置（recordingmini 空间）
ACCESS_KEY = 'viamdhr9ySWyYE3vj-Mkg7Eaedo0L7q8X05KWiRa'
SECRET_KEY = 'TI8BcbpbzxEIX8rVUpPWxBP3IMvwdmAvP48OQrdB'
BUCKET_NAME = 'recordingmini'


# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API 请求次数统计表格</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }

        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .stat-label {
            color: #666;
            font-size: 1.1em;
            margin-bottom: 10px;
        }

        .stat-value {
            color: #333;
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .table-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow-x: auto;
            margin-bottom: 30px;
        }

        .table-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 600;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 1em;
        }

        th, td {
            padding: 15px;
            text-align: center;
            border: 1px solid #ddd;
        }

        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        tr:hover {
            background-color: #f5f5f5;
        }

        .info-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .info-title {
            font-size: 1.3em;
            color: #333;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 600;
        }

        .info-content {
            color: #666;
            text-align: center;
            line-height: 1.6;
        }

        .highlight {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 API 请求次数统计表格</h1>
            <p>存储空间: {{ bucket_name }} | 本月数据</p>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🔍</div>
                <div class="stat-label">本月 GET 请求次数</div>
                <div class="stat-value">{{ current_get_total }}</div>
                <div class="info-text">本月累计GET请求</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">📤</div>
                <div class="stat-label">本月 PUT 请求次数</div>
                <div class="stat-value">{{ current_put_total }}</div>
                <div class="info-text">本月累计PUT请求</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-label">总 API 请求次数</div>
                <div class="stat-value">{{ total_requests }}</div>
                <div class="info-text">GET + PUT 总计</div>
            </div>
        </div>

        <!-- 表格显示 -->
        <div class="table-container">
            <div class="table-title">📋 本月 API 请求次数详细统计</div>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>GET 请求次数</th>
                        <th>PUT 请求次数</th>
                        <th>总计</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                    <tr>
                        <td>{{ row.date }}</td>
                        <td>{{ "{:,}".format(row.get_requests) }}</td>
                        <td>{{ "{:,}".format(row.put_requests) }}</td>
                        <td>{{ "{:,}".format(row.total) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- 信息区 -->
        <div class="info-section">
            <div class="info-title">ℹ️ 数据说明</div>
            <div class="info-content">
                <p>• <span class="highlight">GET 请求</span>: 读取操作，如下载文件、获取元数据等</p>
                <p>• <span class="highlight">PUT 请求</span>: 写入操作，如上传文件、更新数据等</p>
                <p>• 数据延迟约 <span class="highlight">5分钟</span>，显示为本月1日至今的统计</p>
                <p>• 查询接口: <span class="highlight">blob_io</span> (GET) 和 <span class="highlight">rs_put</span> (PUT)</p>
            </div>
        </div>
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    """首页 - 显示 API 请求统计表格"""
    # 创建 API 管理器
    api_manager = QiniuAPIManager(ACCESS_KEY, SECRET_KEY)

    # 设置时间范围（本月数据：从本月1号到今天）
    now = datetime.datetime.now()
    # 本月第一天
    first_day_of_month = datetime.datetime(now.year, now.month, 1)

    begin_time = first_day_of_month.strftime('%Y%m%d000000')
    end_time = now.strftime('%Y%m%d235959')

    print(f"查询时间范围: {begin_time} - {end_time}")

    # 查询 GET 请求次数统计
    print("正在查询GET请求次数...")
    get_result = api_manager.get_blob_io_stats(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day',
        select='hits',
        metric='hits',
        region='z2'  # 华南-广东区域
    )

    print(f"GET请求API响应状态码: {get_result.get('status_code')}")

    # 查询 PUT 请求次数统计
    print("正在查询PUT请求次数...")
    put_result = api_manager.get_put_requests_stats(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day',
        region='z2'  # 华南-广东区域
    )

    print(f"PUT请求API响应状态码: {put_result.get('status_code')}")

    # 初始化数据结构
    daily_data = {}
    current_get_total = 0
    current_put_total = 0

    # 处理 GET 请求数据
    if get_result.get('status_code') == 200 and get_result.get('data'):
        api_data = get_result['data']
        if isinstance(api_data, list):
            for item in api_data:
                if item and item.get('values'):
                    # 提取时间
                    time_str = item.get('time', '')
                    if 'T' in time_str:
                        # 格式: 2017-08-18T00:00:00+08:00
                        date_part = time_str.split('T')[0]
                        # 转换为 MM-DD 格式
                        month_day = '-'.join(date_part.split('-')[1:3])
                        date_key = month_day
                    else:
                        date_key = time_str

                    # 提取 hits 值
                    hits = item['values'].get('hits', 0)
                    if date_key not in daily_data:
                        daily_data[date_key] = {'get_requests': 0, 'put_requests': 0}
                    daily_data[date_key]['get_requests'] = hits
                    current_get_total += hits

    # 处理 PUT 请求数据
    if put_result.get('status_code') == 200 and put_result.get('data'):
        api_data = put_result['data']
        if isinstance(api_data, list):
            for item in api_data:
                if item and item.get('values'):
                    # 提取时间
                    time_str = item.get('time', '')
                    if 'T' in time_str:
                        # 格式: 2017-08-18T00:00:00+08:00
                        date_part = time_str.split('T')[0]
                        # 转换为 MM-DD 格式
                        month_day = '-'.join(date_part.split('-')[1:3])
                        date_key = month_day
                    else:
                        date_key = time_str

                    # 提取 put 值
                    put_requests = item['values'].get('put', 0)
                    if date_key not in daily_data:
                        daily_data[date_key] = {'get_requests': 0, 'put_requests': 0}
                    daily_data[date_key]['put_requests'] = put_requests
                    current_put_total += put_requests

    # 构建表格数据
    table_data = []
    for date, counts in daily_data.items():
        row = {
            'date': date,
            'get_requests': counts['get_requests'],
            'put_requests': counts['put_requests'],
            'total': counts['get_requests'] + counts['put_requests']
        }
        table_data.append(row)

    # 按日期排序
    table_data.sort(key=lambda x: x['date'])

    # 计算总请求数
    total_requests = current_get_total + current_put_total

    print(f"GET总次数: {current_get_total}, PUT总次数: {current_put_total}, 总计: {total_requests}")

    return render_template_string(
        HTML_TEMPLATE,
        bucket_name=BUCKET_NAME,
        current_get_total=f"{current_get_total:,}",
        current_put_total=f"{current_put_total:,}",
        total_requests=f"{total_requests:,}",
        table_data=table_data
    )


if __name__ == '__main__':
    print("=" * 60)
    print("七牛云 API 请求次数统计表格")
    print("=" * 60)
    print(f"存储空间: {BUCKET_NAME}")
    print(f"AccessKey: {ACCESS_KEY[:8]}...{ACCESS_KEY[-4:]}")
    print("-" * 60)
    print("请在浏览器中访问: http://localhost:5003")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5003, debug=False)