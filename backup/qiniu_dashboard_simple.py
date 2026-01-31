"""
七牛云存储统计可视化仪表盘 - 简化图表版
基于 qiniu_final_app.py 的稳定版本
"""

import time
import datetime
from flask import Flask, render_template_string, request, jsonify

from config import QINIU_CONFIG
from api_manager import QiniuAPIManager


def format_bytes(bytes_size):
    """将字节大小转换为人类可读的格式"""
    if bytes_size is None:
        return "N/A"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_size)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


# 从配置文件获取配置
ACCESS_KEY = QINIU_CONFIG['access_key']
SECRET_KEY = QINIU_CONFIG['secret_key']
BUCKET_NAME = QINIU_CONFIG['bucket_name']

app = Flask(__name__)

# HTML模板 - 简化图表版
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>七牛云存储数据可视化仪表盘</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
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
            max-width: 1400px;
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
            font-size: 2.2em;
            margin-bottom: 10px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .stat-title {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .stat-value {
            color: #333;
            font-size: 1.8em;
            font-weight: bold;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }

        .chart-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }

        .chart-title {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .chart-container {
            width: 100%;
            height: 350px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            margin: 20px 0;
        }

        .loading-spinner {
            border: 4px solid rgba(102, 126, 234, 0.1);
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☁️ 七牛云存储数据可视化仪表盘</h1>
            <p>当前空间: {{ bucket_name }} | 过去7天数据统计</p>
        </div>

        <div id="loading" class="loading">
            <div class="loading-spinner"></div>
            <p>正在加载数据，请稍候...</p>
        </div>

        <div id="statsGrid" class="stats-grid" style="display: none;">
            <div class="stat-card">
                <div class="stat-icon">💾</div>
                <div class="stat-title">存储空间</div>
                <div class="stat-value" id="stat-storage">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-title">文件数量</div>
                <div class="stat-value" id="stat-files">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🚀</div>
                <div class="stat-title">外网流出流量</div>
                <div class="stat-value" id="stat-flow-out">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🌐</div>
                <div class="stat-title">CDN回源流量</div>
                <div class="stat-value" id="stat-cdn">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-title">GET请求</div>
                <div class="stat-value" id="stat-get">-</div>
            </div>
        </div>

        <div id="chartsGrid" class="charts-grid" style="display: none;">
            <div class="chart-card">
                <div class="chart-title">📈 存储空间趋势</div>
                <div id="chart1" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">📁 文件数量变化</div>
                <div id="chart2" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">🚀 外网流出流量</div>
                <div id="chart3" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">🌐 CDN回源流量</div>
                <div id="chart4" class="chart-container"></div>
            </div>
        </div>
    </div>

    <script>
        // 页面加载后自动获取数据
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
        });

        async function loadData() {
            try {
                const response = await fetch('/api/get_stats');
                const result = await response.json();

                if (result.success) {
                    displayData(result.data);
                } else {
                    alert('加载数据失败: ' + result.message);
                }
            } catch (error) {
                alert('请求错误: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        function displayData(data) {
            // 显示统计卡片
            document.getElementById('statsGrid').style.display = 'grid';
            document.getElementById('chartsGrid').style.display = 'grid';

            // 更新统计数据
            if (data.storage.length > 0) {
                const latest = data.storage[data.storage.length - 1];
                document.getElementById('stat-storage').textContent = formatBytes(latest.value);
            }

            if (data.files.length > 0) {
                const latest = data.files[data.files.length - 1];
                document.getElementById('stat-files').textContent = latest.value.toLocaleString();
            }

            if (data.flowOut.length > 0) {
                const total = data.flowOut.reduce((sum, item) => sum + item.value, 0);
                document.getElementById('stat-flow-out').textContent = formatBytes(total);
            }

            if (data.cdnFlow.length > 0) {
                const total = data.cdnFlow.reduce((sum, item) => sum + item.value, 0);
                document.getElementById('stat-cdn').textContent = formatBytes(total);
            }

            if (data.getRequests.length > 0) {
                const total = data.getRequests.reduce((sum, item) => sum + item.value, 0);
                document.getElementById('stat-get').textContent = total.toLocaleString();
            }

            // 绘制图表
            drawChart1(data.storage);
            drawChart2(data.files);
            drawChart3(data.flowOut);
            drawChart4(data.cdnFlow);
        }

        function drawChart1(data) {
            const chart = echarts.init(document.getElementById('chart1'));
            chart.setOption({
                tooltip: { trigger: 'axis' },
                xAxis: {
                    type: 'category',
                    data: data.map(item => item.time)
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { formatter: value => formatBytes(value) }
                },
                series: [{
                    type: 'line',
                    smooth: true,
                    data: data.map(item => item.value),
                    areaStyle: { opacity: 0.3 },
                    lineStyle: { color: '#667eea', width: 3 },
                    itemStyle: { color: '#667eea' }
                }],
                grid: { left: '10%', right: '5%', bottom: '10%', top: '5%' }
            });
        }

        function drawChart2(data) {
            const chart = echarts.init(document.getElementById('chart2'));
            chart.setOption({
                tooltip: { trigger: 'axis' },
                xAxis: {
                    type: 'category',
                    data: data.map(item => item.time)
                },
                yAxis: { type: 'value' },
                series: [{
                    type: 'bar',
                    data: data.map(item => item.value),
                    itemStyle: { color: '#764ba2' }
                }],
                grid: { left: '10%', right: '5%', bottom: '10%', top: '5%' }
            });
        }

        function drawChart3(data) {
            const chart = echarts.init(document.getElementById('chart3'));
            chart.setOption({
                tooltip: { trigger: 'axis' },
                xAxis: {
                    type: 'category',
                    data: data.map(item => item.time)
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { formatter: value => formatBytes(value) }
                },
                series: [{
                    type: 'line',
                    smooth: true,
                    data: data.map(item => item.value),
                    areaStyle: { opacity: 0.3 },
                    lineStyle: { color: '#4facfe', width: 3 },
                    itemStyle: { color: '#4facfe' }
                }],
                grid: { left: '10%', right: '5%', bottom: '10%', top: '5%' }
            });
        }

        function drawChart4(data) {
            const chart = echarts.init(document.getElementById('chart4'));
            chart.setOption({
                tooltip: { trigger: 'axis' },
                xAxis: {
                    type: 'category',
                    data: data.map(item => item.time)
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { formatter: value => formatBytes(value) }
                },
                series: [{
                    type: 'line',
                    smooth: true,
                    data: data.map(item => item.value),
                    areaStyle: { opacity: 0.3 },
                    lineStyle: { color: '#f093fb', width: 3 },
                    itemStyle: { color: '#f093fb' }
                }],
                grid: { left: '10%', right: '5%', bottom: '10%', top: '5%' }
            });
        }

        function formatBytes(bytes) {
            if (!bytes) return '0 B';
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let size = parseFloat(bytes);
            let unitIndex = 0;
            while (size >= 1024 && unitIndex < units.length - 1) {
                size /= 1024;
                unitIndex++;
            }
            return size.toFixed(2) + ' ' + units[unitIndex];
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, bucket_name=BUCKET_NAME)

@app.route('/api/get_stats')
def get_stats():
    """获取所有统计数据"""
    try:
        # 创建API管理器
        api_manager = QiniuAPIManager(ACCESS_KEY, SECRET_KEY)

        # 设置时间范围（最近7天）
        now = time.time()
        seven_days_ago = now - 7 * 24 * 60 * 60

        begin_time = time.strftime('%Y%m%d000000', time.localtime(seven_days_ago))
        end_time = time.strftime('%Y%m%d235959', time.localtime(now))

        # 查询各项数据
        storage_result = api_manager.get_storage_usage(
            bucket_name=BUCKET_NAME,
            begin_time=begin_time,
            end_time=end_time,
            granularity='day'
        )

        files_result = api_manager.get_file_count(
            bucket_name=BUCKET_NAME,
            begin_time=begin_time,
            end_time=end_time,
            granularity='day'
        )

        flow_out_result = api_manager.get_blob_io_stats(
            bucket_name=BUCKET_NAME,
            begin_time=begin_time,
            end_time=end_time,
            granularity='day',
            select='flow',
            metric='flow_out'
        )

        cdn_flow_result = api_manager.get_blob_io_stats(
            bucket_name=BUCKET_NAME,
            begin_time=begin_time,
            end_time=end_time,
            granularity='day',
            select='flow',
            metric='cdn_flow_out'
        )

        get_requests_result = api_manager.get_blob_io_stats(
            bucket_name=BUCKET_NAME,
            begin_time=begin_time,
            end_time=end_time,
            granularity='day',
            select='hits',
            metric='hits'
        )

        # 处理数据
        result_data = {
            'storage': parse_times_datas(storage_result),
            'files': parse_times_datas(files_result),
            'flowOut': parse_blob_io(flow_out_result),
            'cdnFlow': parse_blob_io(cdn_flow_result),
            'getRequests': parse_blob_io(get_requests_result)
        }

        return jsonify({
            'success': True,
            'data': result_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def parse_times_datas(result):
    """解析 times/datas 格式"""
    data = []
    if result.get('status_code') == 200 and result.get('data'):
        api_data = result['data']
        if api_data.get('times') and api_data.get('datas'):
            for i in range(len(api_data['times'])):
                timestamp = api_data['times'][i]
                value = api_data['datas'][i]
                date = datetime.datetime.fromtimestamp(timestamp)
                data.append({
                    'time': date.strftime('%m-%d'),
                    'value': value
                })
    return data

def parse_blob_io(result):
    """解析 blob_io 格式"""
    data = []
    if result.get('status_code') == 200 and result.get('data'):
        api_data = result['data']
        if isinstance(api_data, list):
            for item in api_data:
                if item and item.get('values'):
                    value = item['values'].get('flow') or item['values'].get('hits') or 0
                    time_str = item.get('time', '')
                    # 提取日期部分
                    if 'T' in time_str:
                        date_part = time_str.split('T')[0]
                        month_day = '-'.join(date_part.split('-')[1:3])
                    else:
                        month_day = time_str
                    data.append({
                        'time': month_day,
                        'value': value
                    })
    return data

if __name__ == '__main__':
    print("=" * 60)
    print("七牛云存储数据可视化仪表盘 - 简化版")
    print("=" * 60)
    print(f"存储空间: {BUCKET_NAME}")
    print("-" * 60)
    print("请在浏览器中访问: http://localhost:5001")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=False)
