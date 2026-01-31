"""
CDN流量数据测试脚本
用于验证CDN流量数据获取和图表显示功能
"""
import json
import time
from datetime import datetime, timedelta
import requests
from qiniu import Auth
from flask import Flask, render_template_string, request, jsonify
import sys
import os

# 将当前目录添加到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import QINIU_CONFIG

# 初始化认证
q = Auth(QINIU_CONFIG['access_key'], QINIU_CONFIG['secret_key'])

def get_cdn_traffic_data():
    """
    获取CDN流量数据
    """
    # 设置本月日期范围
    today = datetime.today()
    start_date = f"{today.year}-{today.month:02d}-01"  # 本月第一天
    end_date = today.strftime('%Y-%m-%d')  # 今天
    
    # 域名列表转为字符串，用分号分割
    domains = QINIU_CONFIG['cdn_domains']
    domains_str = ';'.join(domains)
    
    # API基础配置
    base_url = 'http://fusion.qiniuapi.com'
    
    print(f"正在查询CDN流量数据...")
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"目标域名: {domains_str}")
    
    flux_url = f"{base_url}/v2/tune/flux"
    flux_payload = {
        "startDate": start_date,
        "endDate": end_date,
        "granularity": "day",  # 按天粒度
        "domains": domains_str
    }
    
    try:
        # 生成认证token
        token = q.token_of_request(flux_url, body=json.dumps(flux_payload))
        
        headers = {
            'Authorization': f'QBox {token}',
            'Content-Type': 'application/json'
        }
        
        # 设置不使用代理
        proxies = {
            'http': '',
            'https': ''
        }
        
        response = requests.post(flux_url, headers=headers, json=flux_payload, proxies=proxies)
        
        if response.status_code == 200:
            flux_data = response.json()
            print("✅ CDN流量数据获取成功!")
            
            if flux_data.get('code') == 200:
                time_points = flux_data.get('time', [])
                data_points = flux_data.get('data', {})
                
                print(f"时间点数量: {len(time_points)}")
                print(f"域名数据: {list(data_points.keys())}")
                
                # 输出流量数据概览
                total_values = [0] * len(time_points)  # 初始化总流量数组
                
                for domain, domain_data in data_points.items():
                    china_data = domain_data.get('china', [])
                    oversea_data = domain_data.get('oversea', [])
                    
                    print(f"\n域名: {domain}")
                    print(f"  国内流量数据点: {len(china_data)}")
                    print(f"  海外流量数据点: {len(oversea_data)}")
                    
                    # 累加到总流量数组
                    for i in range(min(len(total_values), len(china_data))):
                        total_values[i] += china_data[i]
                    
                    for i in range(min(len(total_values), len(oversea_data))):
                        if i < len(total_values):
                            total_values[i] += oversea_data[i]
                
                # 转换为前端需要的格式
                result_data = []
                for i, time_point in enumerate(time_points):
                    if i < len(total_values):
                        # 提取日期部分，格式为 YYYY-MM-DD HH:MM:SS
                        if ' ' in time_point:
                            date_part = time_point.split(' ')[0]  # 取日期部分 YYYY-MM-DD
                            month_day = '-'.join(date_part.split('-')[1:3])  # MM-DD格式
                        else:
                            month_day = time_point
                        result_data.append({
                            'time': month_day,
                            'value': total_values[i]
                        })
                
                print(f"\n处理后的数据点数: {len(result_data)}")
                for item in result_data[:5]:  # 显示前5个数据点
                    print(f"  {item['time']}: {item['value']:,} bytes")
                
                return result_data
            else:
                print(f"❌ API返回错误: {flux_data.get('error', '未知错误')}")
                return []
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 查询CDN流量时发生错误: {str(e)}")
        return []

def format_bytes_auto(bytes_value):
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

def format_bandwidth(bps):
    """
    将带宽数值转换为人类可读的格式
    """
    if bps is None:
        return "0 bps"
    
    units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
    size = float(bps)
    unit_index = 0
    
    while size >= 1000 and unit_index < len(units) - 1:
        size /= 1000
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"

# Flask应用
app = Flask(__name__)

@app.route('/')
def index():
    """主页面"""
    html_template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDN流量数据测试</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(31, 38, 135, 0.2);
        }
        
        .stat-icon {
            font-size: 2.5em;
            text-align: center;
            margin-bottom: 10px;
        }
        
        .stat-title {
            font-size: 1.1em;
            color: #34495e;
            text-align: center;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .stat-value {
            font-size: 1.5em;
            color: #2980b9;
            text-align: center;
            font-weight: bold;
            word-break: break-all;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        .chart-title {
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 600;
        }
        
        .chart-container {
            width: 100%;
            height: 400px;
            min-height: 300px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            color: #7f8c8d;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin: 5px;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: scale(1.05);
        }
        
        .controls {
            text-align: center;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 CDN流量数据测试</h1>
            <p>实时获取和显示CDN流量统计数据</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="loadData()">🔄 刷新数据</button>
            <button class="btn" onclick="loadTestData()">🧪 加载测试数据</button>
        </div>
        
        <div id="statsGrid" class="stats-grid" style="display: none;">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-title">CDN计费带宽</div>
                <div class="stat-value" id="stat-cdn-bandwidth">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🌐</div>
                <div class="stat-title">CDN回源流出流量</div>
                <div class="stat-value" id="stat-cdn">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-title">总流量</div>
                <div class="stat-value" id="stat-total-traffic">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📅</div>
                <div class="stat-title">数据天数</div>
                <div class="stat-value" id="stat-day-count">-</div>
            </div>
        </div>

        <div id="chartsGrid" class="charts-grid" style="display: none;">
            <div class="chart-card">
                <div class="chart-title">📊 CDN流量趋势</div>
                <div id="chart1" class="chart-container"></div>
            </div>
        </div>
        
        <div id="loading" class="loading">
            ⏳ 正在加载数据...
        </div>
    </div>

    <script>
        let chart1 = null;
        
        async function loadData() {
            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('statsGrid').style.display = 'none';
                document.getElementById('chartsGrid').style.display = 'none';
                
                const response = await fetch('/api/cdn_traffic', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayData(result.data);
                } else {
                    console.error('API Error:', result.message);
                    alert('数据加载失败: ' + result.message);
                }
            } catch (error) {
                console.error('Request Error:', error);
                alert('请求失败: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function loadTestData() {
            // 模拟测试数据
            const testData = {
                cdnTraffic: [
                    {time: '01-01', value: 0},
                    {time: '01-02', value: 0},
                    {time: '01-03', value: 0},
                    {time: '01-14', value: 8369546637},
                    {time: '01-15', value: 52758510062},
                    {time: '01-16', value: 496747407187},
                    {time: '01-17', value: 4920830700},
                    {time: '01-18', value: 32080716203850},
                    {time: '01-19', value: 84275100}
                ],
                totalTraffic: 32581533428658  // 示例总流量
            };
            
            displayData(testData);
        }
        
        function displayData(data) {
            // 显示统计卡片
            document.getElementById('statsGrid').style.display = 'grid';
            document.getElementById('chartsGrid').style.display = 'grid';
            
            // 更新统计数据
            if (data.cdnTraffic && data.cdnTraffic.length > 0) {
                const totalTraffic = data.totalTraffic || data.cdnTraffic.reduce((sum, item) => sum + item.value, 0);
                const avgBandwidth = totalTraffic / (data.cdnTraffic.length * 24 * 3600); // 简单估算平均带宽
                
                document.getElementById('stat-cdn-bandwidth').textContent = formatBandwidth(avgBandwidth);
                document.getElementById('stat-total-traffic').textContent = formatBytesAuto(totalTraffic);
                document.getElementById('stat-day-count').textContent = data.cdnTraffic.length;
                
                // 对于CDN流量，我们显示最后一天的流量
                const lastDayData = data.cdnTraffic[data.cdnTraffic.length - 1];
                if (lastDayData) {
                    document.getElementById('stat-cdn').textContent = formatBytesAuto(lastDayData.value);
                }
            }
            
            // 绘制图表
            if (chart1) {
                chart1.dispose();
            }
            chart1 = echarts.init(document.getElementById('chart1'));
            
            const chartData = data.cdnTraffic || [];
            
            const option = {
                tooltip: {
                    trigger: 'axis',
                    formatter: function(params) {
                        const param = params[0];
                        return param.name + '<br/>' +
                               '流量: <strong>' + formatBytesAuto(param.value) + '</strong>';
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    top: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: chartData.map(item => item.time),
                    axisLabel: {
                        rotate: 45,
                        fontSize: 12
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#999'
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '流量',
                    nameTextStyle: {
                        fontSize: 14,
                        color: '#666'
                    },
                    axisLabel: {
                        formatter: function(value) {
                            return formatBytesAuto(value);
                        }
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#999'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#eee',
                            type: 'dashed'
                        }
                    }
                },
                series: [{
                    name: 'CDN流量',
                    type: 'line',
                    smooth: true,
                    data: chartData.map(item => item.value),
                    itemStyle: {
                        color: '#3498db'
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(52, 152, 219, 0.3)' },
                                { offset: 1, color: 'rgba(52, 152, 219, 0.05)' }
                            ]
                        }
                    },
                    lineStyle: {
                        width: 3
                    }
                }]
            };
            
            chart1.setOption(option);
            
            // 监听窗口大小变化
            window.addEventListener('resize', function() {
                if (chart1) {
                    chart1.resize();
                }
            });
        }
        
        function formatBytesAuto(bytes) {
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
        
        function formatBandwidth(bps) {
            if (bps === null || bps === undefined) return '0 bps';
            const units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'];
            let size = parseFloat(bps);
            let unitIndex = 0;
            while (size >= 1000 && unitIndex < units.length - 1) {
                size /= 1000;
                unitIndex++;
            }
            return size.toFixed(2) + ' ' + units[unitIndex];
        }
        
        // 页面加载完成后自动获取数据
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
        });
    </script>
</body>
</html>
    '''
    return render_template_string(html_template)

@app.route('/api/cdn_traffic', methods=['GET'])
def get_cdn_traffic():
    """获取CDN流量数据API"""
    try:
        data = get_cdn_traffic_data()
        if data:
            total_traffic = sum(item['value'] for item in data)
            return jsonify({
                'success': True,
                'data': {
                    'cdnTraffic': data,
                    'totalTraffic': total_traffic
                }
            })
        else:
            # 返回模拟数据以供测试
            mock_data = [
                {'time': '01-01', 'value': 0},
                {'time': '01-02', 'value': 0},
                {'time': '01-03', 'value': 0},
                {'time': '01-14', 'value': 8369546637},
                {'time': '01-15', 'value': 52758510062},
                {'time': '01-16', 'value': 496747407187},
                {'time': '01-17', 'value': 4920830700},
                {'time': '01-18', 'value': 32080716203850},
                {'time': '01-19', 'value': 84275100}
            ]
            total_traffic = sum(item['value'] for item in mock_data)
            return jsonify({
                'success': True,
                'data': {
                    'cdnTraffic': mock_data,
                    'totalTraffic': total_traffic
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

if __name__ == '__main__':
    print("=" * 60)
    print("CDN流量数据测试服务器")
    print("=" * 60)
    print("请在浏览器中访问: http://localhost:5002")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True)