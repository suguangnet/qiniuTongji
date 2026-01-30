"""
七牛云 GET 请求次数统计图表
使用 blob_io 接口查询 GET 请求次数
使用 recordingmini 空间配置
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
    <title>GET 请求次数统计</title>
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

        .stats-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }

        .stat-icon {
            font-size: 4em;
            margin-bottom: 15px;
        }

        .stat-label {
            color: #666;
            font-size: 1.2em;
            margin-bottom: 10px;
        }

        .stat-value {
            color: #333;
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .chart-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        .chart-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 600;
            text-align: center;
        }

        .chart-container {
            width: 100%;
            height: 500px;
        }

        .info-text {
            color: #666;
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 GET 请求次数统计</h1>
            <p>存储空间: {{ bucket_name }} | 过去7天数据</p>
        </div>

        <div class="stats-card">
            <div class="stat-icon">🔍</div>
            <div class="stat-label">总 GET 请求次数</div>
            <div class="stat-value" id="total-requests">{{ total_requests }}</div>
            <div class="info-text">过去7天累计请求次数</div>
        </div>

        <div class="chart-card">
            <div class="chart-title">📈 GET 请求次数趋势图</div>
            <div id="chart" class="chart-container"></div>
        </div>

        <div class="info-text" style="margin-top: 30px;">
            <p>数据来源: 七牛云 blob_io 接口</p>
            <p>查询参数: select=hits&$metric=hits</p>
            <p>时间粒度: day | 统计延迟: ~5分钟</p>
        </div>
    </div>

    <script>
        const chartData = {{ chart_data | tojson }};

        // 绘制图表
        const chart = echarts.init(document.getElementById('chart'));

        const option = {
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
                data: chartData.dates,
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
                data: chartData.values,
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
        };

        chart.setOption(option);

        // 响应式调整
        window.addEventListener('resize', function() {
            chart.resize();
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """首页 - 显示 GET 请求统计"""
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
    # 使用 blob_io 接口，参数: select=hits&$metric=hits
    result = api_manager.get_blob_io_stats(
        bucket_name=BUCKET_NAME,
        begin_time=begin_time,
        end_time=end_time,
        granularity='day',
        select='hits',
        metric='hits',
        region='z2'  # 华南-广东区域
    )

    print(f"API 响应状态码: {result.get('status_code')}")

    # 处理数据
    chart_data = {
        'dates': [],
        'values': []
    }
    total_requests = 0

    if result.get('status_code') == 200 and result.get('data'):
        api_data = result['data']

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
                        chart_data['dates'].append(month_day)
                    else:
                        chart_data['dates'].append(time_str)

                    # 提取 hits 值
                    hits = item['values'].get('hits', 0)
                    chart_data['values'].append(hits)
                    total_requests += hits

            print(f"成功解析 {len(chart_data['dates'])} 条数据")
            print(f"总请求次数: {total_requests}")
        else:
            print(f"数据格式错误: {type(api_data)}")
    else:
        print(f"API 调用失败或无数据")
        if result.get('error'):
            print(f"错误信息: {result['error']}")

    return render_template_string(
        HTML_TEMPLATE,
        bucket_name=BUCKET_NAME,
        total_requests=f"{total_requests:,}",
        chart_data=chart_data
    )


if __name__ == '__main__':
    print("=" * 60)
    print("七牛云 GET 请求次数统计图表")
    print("=" * 60)
    print(f"存储空间: {BUCKET_NAME}")
    print(f"AccessKey: {ACCESS_KEY[:8]}...{ACCESS_KEY[-4:]}")
    print("-" * 60)
    print("请在浏览器中访问: http://localhost:5002")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5002, debug=False)
