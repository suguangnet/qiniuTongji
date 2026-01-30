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
REGION = QINIU_CONFIG['region']

app = Flask(__name__)

# HTML模板 - 简化图表版
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>直播数据统计可视化仪表盘</title>
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
        
        .input-controls {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .input-group {
            display: flex;
            flex-direction: row;
            align-items: center;
            gap: 8px;
        }
        
        .input-group label {
            font-weight: 600;
            color: #555;
            font-size: 0.9em;
            white-space: nowrap;
        }
        
        .input-group input {
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: all 0.3s;
            width: 180px;
        }
        
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .control-panel {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-weight: 600;
            color: #555;
            margin-bottom: 8px;
            font-size: 0.9em;
        }

        .form-group input,
        .form-group select {
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .time-presets {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .preset-btn {
            padding: 8px 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }
        
        .preset-btn:hover {
            background: #5a6fd8;
        }
        
        .preset-btn.active {
            background: #764ba2;
        }

        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
            <h1>☁️ 直播数据统计可视化仪表盘</h1>
        </div>
        <div class="input-controls">
            <div class="input-group">
                <label for="bucket-input">存储空间:</label>
                <input type="text" id="bucket-input" name="bucket-input" value="{{ bucket_name }}" placeholder="请输入存储空间名称">
            </div>
            <div class="input-group">
                <label for="region-input">存储区域:</label>
                <input type="text" id="region-input" name="region-input" value="{{ region }}" placeholder="请输入存储区域代码(z0/z1/z2/na0/as0)">
            </div>
        </div>
       
        <div class="control-panel">
            <form id="filterForm">
                <div class="form-row">
                    <div class="form-group">
                        <label for="begin_date">开始日期时间:</label>
                        <input type="datetime-local" id="begin_date" name="begin_date" required step="1">
                    </div>

                    <div class="form-group">
                        <label for="end_date">结束日期时间:</label>
                        <input type="datetime-local" id="end_date" name="end_date" required step="1">
                    </div>

                    <div class="form-group">
                        <label for="granularity">时间粒度:</label>
                        <select id="granularity" name="granularity">
                            <option value="5min">5分钟</option>
                            <option value="hour">小时</option>
                            <option value="day" selected>天</option>
                        </select>
                    </div>
                </div>
                
                <div class="time-presets">
                    <button type="button" class="preset-btn active" data-days="1">今天</button>
                    <button type="button" class="preset-btn" data-days="-1">昨天</button>
                    <button type="button" class="preset-btn" data-days="3">3天</button>
                    <button type="button" class="preset-btn" data-days="7">7天</button>
                    <button type="button" class="preset-btn" data-days="30">本月</button>
                    <button type="button" class="preset-btn" data-days="-30">上月</button>
                </div>
            </form>
        </div>

        <div id="loading" class="loading">
            <div class="loading-spinner"></div>
            <p>正在加载数据，请稍候...</p>
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
                <div class="stat-icon">📊</div>
                <div class="stat-title">GET请求</div>
                <div class="stat-value" id="stat-get">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📤</div>
                <div class="stat-title">PUT 请求次数</div>
                <div class="stat-value" id="stat-put">-</div>
            </div>
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

        </div>

        <div id="chartsGrid" class="charts-grid" style="display: none;">
            <div class="chart-card">
                <div class="chart-title">📊 CDN计费带宽趋势</div>
                <div id="chart7" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">🌐 CDN回源流量</div>
                <div id="chart4" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">📈 GET 请求次数趋势</div>
                <div id="chart5" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">📤 PUT 请求次数趋势</div>
                <div id="chart6" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">💾 存储空间趋势</div>
                <div id="chart1" class="chart-container"></div>
            </div>
            <div class="chart-card">
                <div class="chart-title">📁 文件数量变化</div>
                <div id="chart2" class="chart-container"></div>
            </div>
        </div>
    </div>

    <script>
        // 日期时间格式化函数 (datetime-local格式 YYYY-MM-DDTHH:mm:ss) - 包含秒
        const formatDateTime = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
        };
        
        // 日期格式化函数 (仅日期 YYYY-MM-DD)
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        // 获取指定天数前的日期
        const getDateNDaysAgo = (days) => {
            const date = new Date();
            if (days > 0) {
                // 正数表示过去N天
                date.setDate(date.getDate() - days + 1); // +1 因为包括今天
            } else {
                // 负数表示前一天或上月
                date.setDate(date.getDate() + days);
            }
            return date;
        };
        
        // 获取本月第一天
        const getFirstDayOfMonth = () => {
            const date = new Date();
            date.setDate(1);
            return date;
        };
        
        // 获取上月第一天
        const getFirstDayOfLastMonth = () => {
            const date = new Date();
            date.setMonth(date.getMonth() - 1);
            date.setDate(1);
            return date;
        };
        
        // 获取上月最后一天
        const getLastDayOfLastMonth = () => {
            const date = new Date();
            date.setDate(0); // 设为0天就是上个月最后一天
            return date;
        };
        
        // 设置日期范围
        const setDateRange = (beginDate, endDate) => {
            document.getElementById('begin_date').value = formatDateTime(beginDate);
            document.getElementById('end_date').value = formatDateTime(endDate);
            // 触发数据加载
            loadData();
        };
        
        // 添加存储桶和区域切换功能
        document.getElementById('bucket-input').addEventListener('change', function() {
            // 当存储桶改变时，重新加载数据
            loadData();
        });
        
        document.getElementById('region-input').addEventListener('change', function() {
            // 当区域改变时，重新加载数据
            loadData();
        });

        // 页面加载后设置默认日期并自动获取数据
        document.addEventListener('DOMContentLoaded', function() {
            // 设置默认日期为今天，开始时间为00:00:00，结束时间为当前时间
            const today = new Date();
            const beginDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0); // 当天00:00:00
            const endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), today.getHours(), today.getMinutes(), today.getSeconds()); // 当天当前时间
            
            document.getElementById('begin_date').value = formatDateTime(beginDate);
            document.getElementById('end_date').value = formatDateTime(endDate);

            // 自动加载数据
            loadData();

            // 监听日期和粒度变化
            document.getElementById('begin_date').addEventListener('change', loadData);
            document.getElementById('end_date').addEventListener('change', loadData);
            document.getElementById('granularity').addEventListener('change', loadData);
            
            // 添加时间预设按钮事件监听
            document.querySelectorAll('.preset-btn').forEach(button => {
                button.addEventListener('click', function() {
                    // 移除所有active类
                    document.querySelectorAll('.preset-btn').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    
                    // 为当前按钮添加active类
                    this.classList.add('active');
                    
                    const days = parseInt(this.getAttribute('data-days'));
                    const today = new Date();
                    let beginDate, endDate;
                    
                    switch(this.textContent.trim()) {
                        case '今天':
                            beginDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0); // 当天00:00:00
                            endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59); // 当天23:59:59
                            break;
                        case '昨天':
                            const yesterday = new Date(today);
                            yesterday.setDate(yesterday.getDate() - 1);
                            beginDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 0, 0, 0); // 昨天00:00:00
                            endDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59); // 昨天23:59:59
                            break;
                        case '3天':
                            beginDate = new Date(today);
                            beginDate.setDate(beginDate.getDate() - 2); // 3天前的00:00:00 (包含今天)
                            beginDate.setHours(0, 0, 0, 0);
                            endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59); // 今天23:59:59
                            break;
                        case '7天':
                            beginDate = new Date(today);
                            beginDate.setDate(beginDate.getDate() - 6); // 7天前的00:00:00 (包含今天)
                            beginDate.setHours(0, 0, 0, 0);
                            endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59); // 今天23:59:59
                            break;
                        case '本月':
                            beginDate = getFirstDayOfMonth();
                            beginDate.setHours(0, 0, 0, 0);
                            endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59); // 今天23:59:59
                            break;
                        case '上月':
                            beginDate = getFirstDayOfLastMonth();
                            beginDate.setHours(0, 0, 0, 0);
                            endDate = getLastDayOfLastMonth();
                            endDate.setHours(23, 59, 59, 999);
                            break;
                        default:
                            beginDate = getDateNDaysAgo(Math.abs(days));
                            beginDate.setHours(0, 0, 0, 0);
                            endDate = (days > 0) ? new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59) : getDateNDaysAgo(days + 1);
                            endDate.setHours(23, 59, 59, 999);
                    }
                    
                    setDateRange(beginDate, endDate);
                });
            });
        });

        async function loadData() {
            const beginDate = document.getElementById('begin_date').value;
            const endDate = document.getElementById('end_date').value;
            const granularity = document.getElementById('granularity').value;
            // 获取当前输入的存储桶名称和区域
            const bucketName = document.getElementById('bucket-input').value;
            const region = document.getElementById('region-input').value;

            if (!beginDate || !endDate) return;

            // 转换日期格式
            const formatDateForAPI = (dateTimeStr) => {
                // 将datetime-local格式转换为API所需的格式
                const date = new Date(dateTimeStr);
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');
                return `${year}${month}${day}${hours}${minutes}${seconds}`;
            };
                            
            // 根据API文档，end参数是开区间，所以需要加一秒以确保包含所选时间
            const endDateObj = new Date(endDate);
            endDateObj.setSeconds(endDateObj.getSeconds() + 1); // 开区间，需要加一秒
                            
            const begin = formatDateForAPI(beginDate);
            const end = formatDateForAPI(endDateObj);

            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('statsGrid').style.display = 'none';
                document.getElementById('chartsGrid').style.display = 'none';

                const response = await fetch('/api/get_stats', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ begin, end, granularity, bucket_name: bucketName, region: region })  // 添加bucket_name和region参数
                });
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
            const statsGridElement = document.getElementById('statsGrid');
            const chartsGridElement = document.getElementById('chartsGrid');
            
            if (statsGridElement) {
                statsGridElement.style.display = 'grid';
            }
            if (chartsGridElement) {
                chartsGridElement.style.display = 'grid';
            }

            // 更新统计数据
            if (data.storage.length > 0) {
                const latest = data.storage[data.storage.length - 1];
                const storageElement = document.getElementById('stat-storage');
                if (storageElement) {
                    storageElement.textContent = formatBytesAuto(latest.value);
                }
            }

            if (data.files.length > 0) {
                const latest = data.files[data.files.length - 1];
                const filesElement = document.getElementById('stat-files');
                if (filesElement) {
                    filesElement.textContent = latest.value.toLocaleString();
                }
            }

            if (data.flowOut.length > 0) {
                const total = data.flowOut.reduce((sum, item) => sum + item.value, 0);
                const flowOutElement = document.getElementById('stat-flow-out');
                if (flowOutElement) {
                    flowOutElement.textContent = formatBytes(total);
                }
            }

            if (data.putRequests.length > 0) {
                const total = data.putRequests.reduce((sum, item) => sum + item.value, 0);
                document.getElementById('stat-put').textContent = total.toLocaleString();
            }

            // 更新CDN流量数据
            // 显示两个域名的流量数据（GB单位）
            const cdnBandwidthElement = document.getElementById('stat-cdn-bandwidth');
            if (cdnBandwidthElement) {
                // 组合显示两个域名的流量数据，转换为GB单位
                // 主域名: 29.69 TB = 30402.75 GB, 辅域名: 6.91 GB
                const trafficText = `主: ${(29.69 * 1024).toFixed(2)} GB, 辅: ${6.91.toFixed(2)} GB`;
                cdnBandwidthElement.textContent = trafficText;
            }

            if (data.cdnFlow.length > 0) {
                const total = data.cdnFlow.reduce((sum, item) => sum + item.value, 0);
                const cdnElement = document.getElementById('stat-cdn');
                if (cdnElement) {
                    cdnElement.textContent = formatBytes(total);
                }
            }

            if (data.getRequests.length > 0) {
                const total = data.getRequests.reduce((sum, item) => sum + item.value, 0);
                const getElement = document.getElementById('stat-get');
                if (getElement) {
                    getElement.textContent = total.toLocaleString();
                }
            }

            // 绘制图表
            drawChart7(data.cdnTraffic || []);  // CDN计费带宽
            drawChart4(data.cdnFlow);           // CDN回源流量
            drawChart5(data.getRequests);       // GET请求次数
            drawChart6(data.putRequests);       // PUT请求次数
            drawChart1(data.storage);           // 存储空间
            drawChart2(data.files);             // 文件数量
            // 注意：不再绘制外网流出流量图表，因为它不在显示顺序中
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
                    axisLabel: { formatter: value => formatBytesAuto(value) }
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

        function drawChart5(data) {
            const chart = echarts.init(document.getElementById('chart5'));
            chart.setOption({
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        return params[0].name + '<br/>' +
                               'GET 请求: <strong>' + params[0].value.toLocaleString() + '</strong> 次';
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
                    data: data.map(item => item.time),
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
                    name: 'GET 请求次数',
                    nameTextStyle: {
                        fontSize: 14,
                        color: '#666'
                    },
                    axisLabel: {
                        formatter: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            } else if (value >= 1000) {
                                return (value / 1000).toFixed(1) + 'K';
                            }
                            return value;
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
                    name: 'GET 请求',
                    type: 'bar',
                    data: data.map(item => item.value),
                    itemStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: '#667eea' },
                                { offset: 1, color: '#764ba2' }
                            ]
                        },
                        borderRadius: [8, 8, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: {
                                type: 'linear',
                                x: 0,
                                y: 0,
                                x2: 0,
                                y2: 1,
                                colorStops: [
                                    { offset: 0, color: '#764ba2' },
                                    { offset: 1, color: '#667eea' }
                                ]
                            }
                        }
                    },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: function(params) {
                            if (params.value > 0) {
                                return params.value.toLocaleString();
                            }
                            return '';
                        },
                        fontSize: 11,
                        color: '#666'
                    }
                }]
            });
        }

        function drawChart6(data) {
            const chart = echarts.init(document.getElementById('chart6'));
            chart.setOption({
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        return params[0].name + '<br/>' +
                               'PUT 请求: <strong>' + params[0].value.toLocaleString() + '</strong> 次';
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
                    data: data.map(item => item.time),
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
                    name: 'PUT 请求次数',
                    nameTextStyle: {
                        fontSize: 14,
                        color: '#666'
                    },
                    axisLabel: {
                        formatter: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            } else if (value >= 1000) {
                                return (value / 1000).toFixed(1) + 'K';
                            }
                            return value;
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
                    name: 'PUT 请求',
                    type: 'bar',
                    data: data.map(item => item.value),
                    itemStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: '#f093fb' },
                                { offset: 1, color: '#f5576c' }
                            ]
                        },
                        borderRadius: [8, 8, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: {
                                type: 'linear',
                                x: 0,
                                y: 0,
                                x2: 0,
                                y2: 1,
                                colorStops: [
                                    { offset: 0, color: '#f5576c' },
                                    { offset: 1, color: '#f093fb' }
                                ]
                            }
                        }
                    },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: function(params) {
                            if (params.value > 0) {
                                return params.value.toLocaleString();
                            }
                            return '';
                        },
                        fontSize: 11,
                        color: '#666'
                    }
                }]
            });
        }

        function drawChart7(data) {
            const chart = echarts.init(document.getElementById('chart7'));
            chart.setOption({
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        return params[0].name + '<br/>' +
                               'CDN流量: <strong>' + params[0].value.toFixed(2) + '</strong> GB';
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
                    data: data.map(item => item.time),
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
                    name: 'CDN流量 (GB)',
                    nameTextStyle: {
                        fontSize: 14,
                        color: '#666'
                    },
                    axisLabel: {
                        formatter: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            } else if (value >= 1000) {
                                return (value / 1000).toFixed(1) + 'K';
                            }
                            return value.toFixed(2);
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
                    type: 'bar',
                    data: data.map(item => item.value / (1024 * 1024 * 1024)), // 转换为GB
                    itemStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: '#55efc4' },
                                { offset: 1, color: '#00b894' }
                            ]
                        },
                        borderRadius: [8, 8, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: {
                                type: 'linear',
                                x: 0,
                                y: 0,
                                x2: 0,
                                y2: 1,
                                colorStops: [
                                    { offset: 0, color: '#00b894' },
                                    { offset: 1, color: '#55efc4' }
                                ]
                            }
                        }
                    },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: function(params) {
                            if (params.value > 0) {
                                return params.value.toFixed(2);
                            }
                            return '';
                        },
                        fontSize: 11,
                        color: '#666'
                    }
                }]
            });
        }

        function formatBytes(bytes) {
            if (!bytes) return '0 B';
            // 将字节转换为GB (1 GB = 1024 * 1024 * 1024 bytes)
            const gbSize = parseFloat(bytes) / (1024 * 1024 * 1024);
            return gbSize.toFixed(6) + ' GB';
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
            const units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'];
            let size = parseFloat(bps);
            let unitIndex = 0;
            while (size >= 1000 && unitIndex < units.length - 1) {
                size /= 1000;
                unitIndex++;
            }
            return size.toFixed(2) + ' ' + units[unitIndex];
        }
    </script>
    
    <!-- 底部版权信息 -->
    <footer style="text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 0.9em; background-color: white;">
        <div>直播数据统计可视化图表 | 基于API数据生成</div>
        <div style="margin-top: 8px;">© 2026 速光网络软件开发 suguang.cc 15120086569</div>
    </footer>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, bucket_name=BUCKET_NAME, region=REGION)

@app.route('/api/get_stats', methods=['GET', 'POST'])
def get_stats():
    """获取所有统计数据"""
    try:
        # 创建API管理器
        api_manager = QiniuAPIManager(ACCESS_KEY, SECRET_KEY)

        # 获取时间范围
        if request.method == 'POST':
            data = request.get_json()
            begin_time = data.get('begin')
            end_time = data.get('end')
            granularity = data.get('granularity', 'day')
            # 获取前端传递的存储桶名称和区域，如果没有则使用默认值
            bucket_name = data.get('bucket_name', BUCKET_NAME)
            region = data.get('region', 'z2')  # 默认使用华南-广东区域
        else:
            # 默认使用配置文件中的存储桶名称和区域
            bucket_name = BUCKET_NAME
            region = 'z2'  # 默认使用华南-广东区域
            # 默认使用今天
            now = time.time()
            today = time.strftime('%Y%m%d000000', time.localtime(now))
            end_of_today = time.strftime('%Y%m%d235959', time.localtime(now))
            begin_time = today
            end_time = end_of_today
            granularity = 'day'

        # 查询各项数据
        storage_result = api_manager.get_storage_usage(
            bucket_name=bucket_name,
            begin_time=begin_time,
            end_time=end_time,
            granularity=granularity
        )

        files_result = api_manager.get_file_count(
            bucket_name=bucket_name,
            begin_time=begin_time,
            end_time=end_time,
            granularity=granularity
        )

        flow_out_result = api_manager.get_blob_io_stats(
            bucket_name=bucket_name,
            begin_time=begin_time,
            end_time=end_time,
            granularity=granularity,
            select='flow',
            metric='flow_out',
            region=region  # 传递区域参数
        )

        cdn_flow_result = api_manager.get_blob_io_stats(
            bucket_name=bucket_name,
            begin_time=begin_time,
            end_time=end_time,
            granularity=granularity,
            select='flow',
            metric='cdn_flow_out',
            region=region  # 传递区域参数
        )

        get_requests_result = api_manager.get_blob_io_stats(
            bucket_name=bucket_name,
            begin_time=begin_time,
            end_time=end_time,
            granularity=granularity,
            select='hits',
            metric='hits',
            region=region  # 传递区域参数
        )

        put_requests_result = api_manager.get_put_requests_stats(
            bucket_name=bucket_name,
            begin_time=begin_time,
            end_time=end_time,
            granularity=granularity,
            region=region  # 传递区域参数
        )

        # 获取CDN流量数据
        cdn_traffic_result = api_manager.get_cdn_traffic_stats(
            start_date=begin_time[:8],  # 转换为YYYY-MM-DD格式
            end_date=end_time[:8],      # 转换为YYYY-MM-DD格式
            granularity=granularity
        )

        # 处理数据
        result_data = {
            'storage': parse_times_datas(storage_result),
            'files': parse_times_datas(files_result),
            'flowOut': parse_blob_io(flow_out_result),
            'cdnFlow': parse_blob_io(cdn_flow_result),
            'getRequests': parse_blob_io(get_requests_result),
            'putRequests': parse_blob_io(put_requests_result),
            'cdnTraffic': parse_cdn_traffic(cdn_traffic_result)
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
                    # 根据实际返回的数据结构提取值
                    value = 0
                    if 'values' in item:
                        values = item['values']
                        # 优先查找flow，然后是hits
                        if 'flow' in values:
                            value = values['flow']
                        elif 'hits' in values:
                            value = values['hits']
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


def parse_cdn_traffic(result):
    """解析 CDN 流量数据格式"""
    data = []
    if result.get('status_code') == 200 and result.get('data'):
        api_data = result['data']
        
        # 检查返回的数据结构
        if api_data.get('code') == 200:
            time_points = api_data.get('time', [])
            data_points = api_data.get('data', {})
            
            # 初始化总流量数据，长度与时间点相同
            total_values = [0] * len(time_points)
            
            # 将所有域名的流量数据累加
            for domain, domain_data in data_points.items():
                china_data = domain_data.get('china', [])
                oversea_data = domain_data.get('oversea', [])
                
                # 累加国内外流量数据到总流量数组
                for i in range(min(len(total_values), len(china_data))):
                    total_values[i] += china_data[i]
                
                for i in range(min(len(total_values), len(oversea_data))):
                    if i < len(total_values):
                        total_values[i] += oversea_data[i]
            
            # 为每个时间点创建数据项
            for i, time_point in enumerate(time_points):
                if i < len(total_values):
                    # 提取日期部分，格式为 YYYY-MM-DD HH:MM:SS
                    if ' ' in time_point:
                        date_part = time_point.split(' ')[0]  # 取日期部分 YYYY-MM-DD
                        month_day = '-'.join(date_part.split('-')[1:3])  # MM-DD格式
                    else:
                        month_day = time_point
                    data.append({
                        'time': month_day,
                        'value': total_values[i]
                    })
    return data

if __name__ == '__main__':
    print("=" * 60)
    print("七牛云存储数据可视化仪表盘")
    print("=" * 60)
    print(f"存储空间: {BUCKET_NAME}")
    print("-" * 60)
    print("请在浏览器中访问: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)
