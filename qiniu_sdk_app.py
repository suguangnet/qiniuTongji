"""
基于七牛云官方SDK的存储用量查询Web应用

此应用使用七牛云官方SDK进行认证和API调用
"""

import time
import datetime
from urllib.parse import urlencode
import requests
from qiniu import Auth, QiniuMacAuth
from flask import Flask, render_template_string, request, jsonify
import threading
import os


class QiniuDataStatAPI:
    """
    使用七牛云官方SDK实现数据统计API调用
    """
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.auth = Auth(access_key, secret_key)
        self.mac_auth = QiniuMacAuth(access_key, secret_key)
        self.base_url = "https://api.qiniuapi.com"
    
    def _make_request(self, api_endpoint, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """
        通用API请求方法，使用官方SDK进行认证
        """
        # 如果没有提供时间，则使用今天的日期
        if not begin_time or not end_time:
            now = time.strftime('%Y%m%d%H%M%S', time.localtime())
            today = time.strftime('%Y%m%d', time.localtime()) + '000000'
            tomorrow = time.strftime('%Y%m%d', time.localtime(time.time() + 86400)) + '000000'
            
            begin_time = today
            end_time = tomorrow

        # 构建查询参数
        params = {
            'begin': begin_time,
            'end': end_time,
            'g': granularity
        }
        
        if bucket_name:
            params['bucket'] = bucket_name
        if region:
            params['region'] = region
        else:
            params['region'] = 'z1'  # 默认华北区域

        # 构建完整URL
        query_string = urlencode(params)
        path = f"/v6/{api_endpoint}?{query_string}"
        full_url = f"{self.base_url}{path}"

        # 生成时间戳，用于X-Qiniu-Date头部
        date_header = time.strftime('%Y%m%dT%H%M%S', time.gmtime()) + 'Z'

        # 使用QiniuMacAuth生成包含X-Qiniu-Date的认证令牌
        token = self.mac_auth.token_of_request(
            method="GET",
            host="api.qiniuapi.com",
            url=path,
            qheaders=f"X-Qiniu-Date: {date_header}",
            content_type="application/x-www-form-urlencoded"
        )

        # 设置请求头
        headers = {
            'Authorization': f"Qiniu {token}",
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Qiniu-Date': date_header
        }

        # 发送请求
        try:
            response = requests.get(full_url, headers=headers, timeout=30)
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response.json() if response.content else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'status_code': 0,
                'error': str(e),
                'data': None
            }
    
    def get_storage_usage(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """获取存储用量信息"""
        return self._make_request('space', bucket_name, region, begin_time, end_time, granularity)
    
    def get_file_count(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """获取文件数量统计"""
        return self._make_request('count', bucket_name, region, begin_time, end_time, granularity)
    
    def get_low_freq_storage_usage(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """获取低频存储的存储量统计"""
        return self._make_request('space_line', bucket_name, region, begin_time, end_time, granularity)


def format_bytes(bytes_size):
    """
    将字节大小转换为人类可读的格式
    
    Args:
        bytes_size (int): 字节数
        
    Returns:
        str: 格式化后的大小字符串
    """
    if bytes_size is None:
        return "N/A"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


# 从环境变量或默认值获取配置
ACCESS_KEY = os.environ.get('QINIU_ACCESS_KEY', 'DsHpVVa6tSra_zAUrFHg9dAejTdoRRHTU3Lo9cBP')
SECRET_KEY = os.environ.get('QINIU_SECRET_KEY', 'sLBgW7INeM_N9jKaJz7bzakqv0sherpAhtXMNPpK')
BUCKET_NAME = os.environ.get('QINIU_BUCKET_NAME', 'shoposssuguangnetcom')

app = Flask(__name__)

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>七牛云存储用量查询</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .info-box {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #2196f3;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #1976d2;
        }
        .results {
            margin-top: 30px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .error {
            color: #f44336;
            background-color: #ffebee;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .success {
            color: #4caf50;
            background-color: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .loading {
            text-align: center;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>☁️ 七牛云存储用量查询</h1>
        
        <div class="info-box">
            <strong>说明：</strong>此工具用于查询七牛云存储空间的用量信息。当前配置的存储空间：<code>{{ bucket_name }}</code>
        </div>
        
        <form id="queryForm">
            <div class="form-group">
                <label for="bucket">存储空间名称:</label>
                <input type="text" id="bucket" name="bucket" value="{{ bucket_name }}" required>
            </div>
            
            <div class="form-group">
                <label for="api_type">API类型:</label>
                <select id="api_type" name="api_type">
                    <option value="space" selected>存储量 (space)</option>
                    <option value="count">文件数量 (count)</option>
                    <option value="space_line">低频存储量 (space_line)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="begin_date">开始日期:</label>
                <input type="date" id="begin_date" name="begin_date" required>
            </div>
            
            <div class="form-group">
                <label for="end_date">结束日期:</label>
                <input type="date" id="end_date" name="end_date" required>
            </div>
            
            <div class="form-group">
                <label for="granularity">时间粒度:</label>
                <select id="granularity" name="granularity">
                    <option value="day" selected>天 (day)</option>
                    <option value="hour">小时 (hour)</option>
                    <option value="5min">5分钟 (5min)</option>
                </select>
            </div>
            
            <button type="submit">查询存储用量</button>
        </form>
        
        <div id="loading" class="loading" style="display: none;">
            <p>正在查询中，请稍候...</p>
        </div>
        
        <div id="results" class="results"></div>
    </div>

    <script>
        // 设置默认日期为今天
        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date();
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            
            const todayStr = today.toISOString().split('T')[0];
            const tomorrowStr = tomorrow.toISOString().split('T')[0];
            
            document.getElementById('begin_date').value = todayStr;
            document.getElementById('end_date').value = tomorrowStr;
        });

        document.getElementById('queryForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const bucket = formData.get('bucket');
            const apiType = formData.get('api_type');
            const beginDate = formData.get('begin_date');
            const endDate = formData.get('end_date');
            const granularity = formData.get('granularity');
            
            // 验证日期格式
            if (!beginDate || !endDate) {
                alert('请选择开始和结束日期');
                return;
            }
            
            // 转换日期格式为七牛云API所需的格式
            const beginFormatted = beginDate.replace(/-/g, '') + '000000';
            const endFormatted = endDate.replace(/-/g, '') + '000000';
            
            // 显示加载状态
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            
            // 发送请求
            fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    bucket: bucket,
                    api_type: apiType,
                    begin: beginFormatted,
                    end: endFormatted,
                    granularity: granularity
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                
                if (data.success) {
                    // 记录当前API类型，用于在显示结果时区分数据类型
                    window.currentApiType = data.api_type || 'space';
                    
                    // 根据API类型更新表格标题
                    updateTableHeader(window.currentApiType);
                    
                    displayResults(data.data);
                } else {
                    document.getElementById('results').innerHTML = 
                        `<div class="error"><strong>错误：</strong>${data.message}</div>`;
                }
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('results').innerHTML = 
                    `<div class="error"><strong>请求错误：</strong>${error.message}</div>`;
            });
        });

        function updateTableHeader(apiType) {
            let headerHtml;
            if (apiType === 'count') {
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>文件数量</th>
                        <th>数值</th>
                    </tr>`;
            } else {
                // 默认为存储空间相关接口
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>存储量</th>
                        <th>字节数</th>
                    </tr>`;
            }
            
            // 更新表格头部
            const tableElement = document.querySelector('#results table thead');
            if (tableElement) {
                tableElement.innerHTML = headerHtml;
            }
        }

        function displayResults(data) {
            if (!data || !data.times || !data.datas) {
                document.getElementById('results').innerHTML = 
                    '<div class="error">未获取到有效的用量数据</div>';
                return;
            }

            // 根据API类型确定表头
            let headerHtml;
            if (window.currentApiType === 'count') {
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>文件数量</th>
                        <th>数值</th>
                    </tr>`;
            } else {
                // 默认为存储空间相关接口
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>存储量</th>
                        <th>字节数</th>
                    </tr>`;
            }

            let tableHtml = `
                <table>
                    <thead>
                        ${headerHtml}
                    </thead>
                    <tbody>
            `;

            for (let i = 0; i < data.times.length && i < data.datas.length; i++) {
                const timestamp = data.times[i];
                const sizeBytes = data.datas[i];
                const date = new Date(timestamp * 1000);
                const formattedDate = date.toLocaleString('zh-CN');

                // 根据API类型显示不同的列标题
                let valueDisplay, unitDisplay;
                if(window.currentApiType === 'count') {
                    // 文件数量接口返回的是数量，不是存储大小
                    valueDisplay = sizeBytes;
                    unitDisplay = sizeBytes;
                } else {
                    // 存储空间接口返回的是字节数
                    valueDisplay = formatBytes(sizeBytes);
                    unitDisplay = sizeBytes;
                }

                tableHtml += `
                    <tr>
                        <td>${formattedDate}</td>
                        <td>${valueDisplay}</td>
                        <td>${unitDisplay}</td>
                    </tr>
                `;
            }

            tableHtml += `
                    </tbody>
                </table>
            `;

            document.getElementById('results').innerHTML = tableHtml;
        }

        function formatBytes(bytes) {
            if (bytes === null || bytes === undefined) return 'N/A';
            
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

@app.route('/api/query', methods=['POST'])
def query_usage():
    try:
        data = request.get_json()
        bucket_name = data.get('bucket', BUCKET_NAME)
        begin_time = data.get('begin')
        end_time = data.get('end')
        granularity = data.get('granularity', 'day')
        
        # 验证必要参数
        if not begin_time or not end_time:
            return jsonify({
                'success': False,
                'message': '缺少必要的日期参数'
            }), 400
        
        # 创建用量查询实例
        qiniu_api = QiniuDataStatAPI(ACCESS_KEY, SECRET_KEY)
        
        # 根据API类型选择查询方法
        api_type = data.get('api_type', 'space')
        
        if api_type == 'space':
            result = qiniu_api.get_storage_usage(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity
            )
        elif api_type == 'count':
            result = qiniu_api.get_file_count(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity
            )
        elif api_type == 'space_line':
            result = qiniu_api.get_low_freq_storage_usage(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity
            )
        else:
            # 默认使用space接口
            result = qiniu_api.get_storage_usage(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity
            )
        
        if result['status_code'] == 200 and result['data']:
            return jsonify({
                'success': True,
                'data': result['data'],
                'api_type': api_type  # 返回API类型
            })
        else:
            # 401错误说明AK/SK没有访问用量查询API的权限
            if result['status_code'] == 401:
                return jsonify({
                    'success': False,
                    'message': f"认证失败 (401): 您的AK/SK可能没有访问{api_type}查询API的权限。请确认您的AccessKey ({ACCESS_KEY}) 有权限访问/v6/{api_type}接口。错误详情: {result.get('data', {}).get('error', 'bad token')}"
                }), 401
            elif result['status_code'] == 400:
                return jsonify({
                    'success': False,
                    'message': f"请求参数错误 (400): 可能是请求参数格式不正确或超出查询范围。API: /v6/{api_type}, 错误详情: {result.get('data', {}) if result.get('data') else result.get('error', '请求参数错误')}"
                }), 400
            else:
                error_msg = result.get('error', 'API调用失败')
                if result.get('data') and 'error' in result['data']:
                    error_msg = result['data']['error']
                elif result.get('data'):
                    error_msg = str(result['data'])
                
                return jsonify({
                    'success': False,
                    'message': f"API调用失败，状态码: {result['status_code']}, 错误: {error_msg}"
                }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"服务器内部错误: {str(e)}"
        }), 500

def run_server():
    """启动Web服务器"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("七牛云存储用量查询Web应用正在启动...")
    print("请在浏览器中访问: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    
    # 启动Web服务器
    app.run(host='0.0.0.0', port=5000, debug=False)