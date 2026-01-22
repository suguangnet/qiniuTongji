"""
基于七牛云官方SDK的存储用量查询Web应用 - 最终版

此应用使用七牛云官方SDK进行认证和API调用，支持多种数据统计API
"""

import time
import datetime
from urllib.parse import urlencode
import requests
from qiniu import Auth, QiniuMacAuth
from flask import Flask, render_template_string, request, jsonify
import os

from config import QINIU_CONFIG, DATA_STAT_API, DEFAULT_PARAMS
from api_manager import QiniuAPIManager


class QiniuDataStatAPI:
    """
    使用七牛云官方SDK实现数据统计API调用
    """
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.api_manager = QiniuAPIManager(access_key, secret_key)
    
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
            params['region'] = DEFAULT_PARAMS['region']  # 使用默认区域

        # 构建完整URL
        query_string = urlencode(params)
        path = f"{DATA_STAT_API[api_endpoint]['endpoint']}?{query_string}"
        full_url = f"{QINIU_CONFIG['base_url']}{path}"

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
    
    def get_storage_usage(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', file_type=None):
        """获取存储用量信息"""
        return self.api_manager.get_storage_usage(bucket_name, region, begin_time, end_time, granularity, file_type)
    
    def get_file_count(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', file_type=None):
        """获取文件数量统计"""
        return self.api_manager.get_file_count(bucket_name, region, begin_time, end_time, granularity, file_type)
    
    def get_low_freq_storage_usage(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """获取低频存储的存储量统计"""
        return self.api_manager.get_low_freq_storage_usage(bucket_name, region, begin_time, end_time, granularity)
    
    def get_storage_type_change_requests(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day'):
        """获取存储类型转换请求次数统计"""
        return self.api_manager.get_storage_type_change_requests(bucket_name, region, begin_time, end_time, granularity)
    
    def get_blob_io_stats(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', select='flow', metric='flow_out', file_type=None):
        """获取流量和请求次数统计"""
        return self.api_manager.get_blob_io_stats(bucket_name, region, begin_time, end_time, granularity, select, metric, file_type)
    
    def get_put_requests_stats(self, bucket_name=None, region=None, begin_time=None, end_time=None, granularity='day', file_type=None):
        """获取PUT请求次数统计"""
        return self.api_manager.get_put_requests_stats(bucket_name, region, begin_time, end_time, granularity, file_type)


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


# 从配置文件获取配置
ACCESS_KEY = QINIU_CONFIG['access_key']
SECRET_KEY = QINIU_CONFIG['secret_key']
BUCKET_NAME = QINIU_CONFIG['bucket_name']

app = Flask(__name__)

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>七牛云存储用量查询 - 官方SDK版</title>
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
        .warning-box {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #ffc107;
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
        .api-info {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>☁️ 七牛云存储用量查询 - 官方SDK版</h1>
        
        <div class="info-box">
            <strong>说明：</strong>此工具使用七牛云官方Python SDK进行认证，支持查询存储空间的用量信息。
        </div>
        
        <div class="warning-box">
            <strong>注意：</strong>如果出现"401 bad token"错误，说明您的AccessKey没有访问数据统计API的权限。请联系七牛云客服开通权限。
        </div>
        
        <form id="queryForm">
            <div class="form-group">
                <label for="bucket">存储空间名称:</label>
                <input type="text" id="bucket" name="bucket" value="{{ bucket_name }}" required>
                <div class="api-info">当前配置的存储空间: {{ bucket_name }}</div>
            </div>
            
            <div class="form-group">
                <label for="api_type">API类型:</label>
                <select id="api_type" name="api_type">
                    <option value="space">存储量 (space) - 查询存储空间占用</option>
                    <option value="count" selected>文件数量 (count) - 查询文件总数</option>
                    <option value="blob_io">流量和请求次数 (blob_io) - 查询外网流出流量和GET请求次数</option>
                    <option value="rs_put">PUT请求次数 (rs_put) - 查询PUT请求次数</option>
                </select>

            </div>
            
            <!-- blob_io接口的额外参数 -->
            <div id="blob_io_params" class="form-group" style="display: none;">
                <label for="select_param">查询类型:</label>
                <select id="select_param" name="select_param">
                    <option value="flow">流量 (flow)</option>
                    <option value="hits">请求次数 (hits)</option>
                </select>
                
                <label for="metric_param">指标类型:</label>
                <select id="metric_param" name="metric_param">
                    <option value="flow_out">外网流出流量 (flow_out)</option>
                    <option value="cdn_flow_out">CDN回源流量 (cdn_flow_out)</option>
                    <option value="hits">GET请求次数 (hits)</option>
                </select>
                <div class="api-info">选择要查询的具体指标</div>
            </div>
            
            <!-- 通用存储类型参数 -->
            <div id="storage_type_params" class="form-group" style="display: none;">
                <label for="file_type">存储类型:</label>
                <select id="file_type" name="file_type">
                    <option value="0">标准存储 (0)</option>
                </select>
                <div class="api-info">选择要查询的存储类型</div>
            </div>
            
            <div class="form-group">
                <label for="begin_date">开始日期:</label>
                <input type="date" id="begin_date" name="begin_date" required>
                <div class="api-info">查询开始日期</div>
            </div>
            
            <div class="form-group">
                <label for="end_date">结束日期:</label>
                <input type="date" id="end_date" name="end_date" required>
                <div class="api-info">查询结束日期</div>
            </div>
            
            <div class="form-group">
                <label for="granularity">时间粒度:</label>
                <select id="granularity" name="granularity">
                    <option value="5min" selected>5分钟 (5min) - 按5分钟统计</option>
                </select>
                <div class="api-info">选择时间粒度，影响数据精度</div>
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
            // 设置默认日期范围为2026-01-01到今天
            const now = new Date();
            
            // 格式化为 YYYY-MM-DD 格式
            const formatDate = (date) => {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
            };
            
            document.getElementById('begin_date').value = '2026-01-01';
            document.getElementById('end_date').value = formatDate(now);
            
            // 监听API类型变化，控制参数显示
            document.getElementById('api_type').addEventListener('change', function() {
                const selectedApiType = this.value;
                const blobIoParamsDiv = document.getElementById('blob_io_params');
                const storageTypeParamsDiv = document.getElementById('storage_type_params');
                
                if (selectedApiType === 'blob_io') {
                    blobIoParamsDiv.style.display = 'block';
                } else {
                    blobIoParamsDiv.style.display = 'none';
                }
                
                // 对于某些API类型显示存储类型参数
                if (selectedApiType === 'space' || selectedApiType === 'count' || selectedApiType === 'blob_io' || selectedApiType === 'rs_put') {
                    storageTypeParamsDiv.style.display = 'block';
                } else {
                    storageTypeParamsDiv.style.display = 'none';
                }
            });
        });

        document.getElementById('queryForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const bucket = formData.get('bucket');
            const apiType = formData.get('api_type');
            
            // 从表单获取用户输入的日期
            const beginDate = document.getElementById('begin_date').value;
            const endDate = document.getElementById('end_date').value;
            const granularity = '5min'; // 使用用户选择的时间粒度
            
            // 准备存储类型参数
            const fileType = document.getElementById('file_type').value;
            
            // 将用户选择的日期转换为七牛云API所需的格式
            const formatDateForAPI = (dateStr) => {
                // 将YYYY-MM-DD格式转换为Date对象
                const date = new Date(dateStr + 'T00:00:00');
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');
                return `${year}${month}${day}${hours}${minutes}${seconds}`;
            };
            
            const beginFormatted = formatDateForAPI(beginDate);
            const endFormatted = formatDateForAPI(endDate);
            
            // 显示加载状态
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            
            // 如果选择的是blob_io，同时查询三个指标
            if (apiType === 'blob_io') {
                // 定义要查询的三个指标
                const metrics = [
                    {select: 'flow', metric: 'flow_out', label: '外网流出流量'},
                    {select: 'flow', metric: 'cdn_flow_out', label: 'CDN回源流量'},
                    {select: 'hits', metric: 'hits', label: 'GET请求次数'}
                ];
                
                // 并行查询所有指标
                const promises = metrics.map(metricConfig => {
                    const requestBody = {
                        bucket: bucket,
                        api_type: 'blob_io',
                        begin: beginFormatted,
                        end: endFormatted,
                        granularity: granularity,
                        select: metricConfig.select,
                        metric: metricConfig.metric
                    };
                    
                    // 添加存储类型参数
                    if (fileType) {
                        requestBody.file_type = fileType;
                    }
                    
                    return fetch('/api/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestBody)
                    }).then(response => response.json());
                });
                
                Promise.all(promises).then(results => {
                    document.getElementById('loading').style.display = 'none';
                    
                    // 处理并显示所有结果
                    let allResultsHtml = '<table><thead><tr><th>类型</th><th>时间</th><th>数值</th></tr></thead><tbody>';
                    
                    results.forEach((result, index) => {
                        if (result.success) {
                            const metricConfig = metrics[index];
                            const data = result.data;
                            
                            if (Array.isArray(data) && data.length > 0) {
                                // 寻找最近的非零数据点，如果没有非零数据则取最后一个数据点
                                let selectedItem = null;
                                // 首先尝试找到最近的非零数据点
                                for (let i = data.length - 1; i >= 0; i--) {
                                    const item = data[i];
                                    if (item && item.values) {
                                        let hasNonZeroValue = false;
                                        for (const key in item.values) {
                                            if (item.values[key] !== 0) {
                                                hasNonZeroValue = true;
                                                break;
                                            }
                                        }
                                        if (hasNonZeroValue) {
                                            selectedItem = item;
                                            break;
                                        }
                                    }
                                }
                                
                                // 如果没找到非零数据，则使用最后一个数据点
                                if (!selectedItem) {
                                    selectedItem = data[data.length - 1];
                                }
                                
                                if (selectedItem && selectedItem.values) {
                                    let value;
                                    if (selectedItem.values.flow !== undefined) {
                                        value = selectedItem.values.flow;
                                    } else if (selectedItem.values.hits !== undefined) {
                                        value = selectedItem.values.hits;
                                    } else {
                                        value = 0;
                                    }
                                    
                                    // 根据指标类型格式化数值
                                    let formattedValue;
                                    if (metricConfig.select === 'flow') {
                                        // 流量数据，使用GB格式化
                                        formattedValue = formatBytesToGB(value);
                                    } else {
                                        // 请求次数数据，使用数值格式化
                                        formattedValue = value.toLocaleString();
                                    }
                                    
                                    allResultsHtml += `
                                        <tr>
                                            <td>${metricConfig.label}</td>
                                            <td>${selectedItem.time}</td>
                                            <td>${formattedValue}</td>
                                        </tr>`;
                                }
                            } else if (data && data.times && data.datas && data.times.length > 0 && data.datas.length > 0) {
                                // 处理times/datas格式
                                const lastIndex = Math.min(data.times.length, data.datas.length) - 1;
                                const timestamp = data.times[lastIndex];
                                const sizeValue = data.datas[lastIndex];
                                const date = new Date(timestamp * 1000);
                                const timeStr = date.toLocaleString('zh-CN');
                                
                                // 根据指标类型格式化数值
                                let formattedValue;
                                if (metricConfig.select === 'flow') {
                                    // 流量数据，使用GB格式化
                                    formattedValue = formatBytesToGB(sizeValue);
                                } else {
                                    // 请求次数数据，使用数值格式化
                                    formattedValue = sizeValue.toLocaleString();
                                }
                                
                                allResultsHtml += `
                                    <tr>
                                        <td>${metricConfig.label}</td>
                                        <td>${timeStr}</td>
                                        <td>${formattedValue}</td>
                                    </tr>`;
                            }
                        } else {
                            const metricConfig = metrics[index];
                            allResultsHtml += `
                                <tr>
                                    <td>${metricConfig.label}</td>
                                    <td>-</td>
                                    <td>查询失败</td>
                                </tr>`;
                        }
                    });
                    
                    allResultsHtml += '</tbody></table>';
                    document.getElementById('results').innerHTML = allResultsHtml;
                }).catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('results').innerHTML = 
                        `<div class="error"><strong>请求错误：</strong>${error.message}</div>`;
                });
            } else {
                // 对于非blob_io的API类型，使用原有逻辑
                const requestBody = {
                    bucket: bucket,
                    api_type: apiType,
                    begin: beginFormatted,
                    end: endFormatted,
                    granularity: 'day'
                };
                
                // 添加存储类型参数
                if (fileType) {
                    requestBody.file_type = fileType;
                }
                
                fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
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
            }
        });

        function updateTableHeader(apiType) {
            let headerHtml;
            if (apiType === 'count') {
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>文件数量</th>
                    </tr>`;
            } else if (apiType === 'blob_io') {
                // 对于blob_io接口，根据查询类型显示不同的表头
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>数值</th>
                    </tr>`;
            } else {
                // 默认为存储空间相关接口
                headerHtml = `
                    <tr>
                        <th>时间</th>
                        <th>存储量</th>
                    </tr>`;
            }
            
            // 更新表格头部
            const tableElement = document.querySelector('#results table thead');
            if (tableElement) {
                tableElement.innerHTML = headerHtml;
            }
        }

        function displayResults(data) {
            if (!data) {
                document.getElementById('results').innerHTML = 
                    '<div class="error">未获取到有效的用量数据</div>';
                return;
            }
            
            // 检查数据格式，处理不同API返回的不同数据结构
            let formattedData;
            
            if (Array.isArray(data)) {
                // blob_io接口返回数组格式
                if (data.length > 0) {
                    // 取最后一个（最新）数据点
                    const latestItem = data[data.length - 1];
                    if (latestItem && latestItem.values) {
                        // 提取时间
                        const timeStr = latestItem.time;
                        // 提取数值，根据API类型决定是flow还是hits
                        let value;
                        if (latestItem.values.flow !== undefined) {
                            value = latestItem.values.flow;
                        } else if (latestItem.values.hits !== undefined) {
                            value = latestItem.values.hits;
                        } else {
                            value = 0;
                        }
                        
                        formattedData = {
                            time: timeStr,
                            value: value
                        };
                    }
                }
            } else if (data.times && data.datas) {
                // space和count接口返回times/datas格式
                if (data.times.length > 0 && data.datas.length > 0) {
                    const lastIndex = Math.min(data.times.length, data.datas.length) - 1;
                    const timestamp = data.times[lastIndex];
                    const sizeValue = data.datas[lastIndex];
                    
                    // 将时间戳转换为可读格式
                    const date = new Date(timestamp * 1000);
                    const timeStr = date.toLocaleString('zh-CN');
                    
                    formattedData = {
                        time: timeStr,
                        value: sizeValue
                    };
                }
            }
            
            if (formattedData) {
                // 根据API类型确定表头
                let headerHtml;
                if (window.currentApiType === 'count') {
                    headerHtml = `
                        <tr>
                            <th>时间</th>
                            <th>文件数量</th>
                        </tr>`;
                } else if (window.currentApiType === 'blob_io') {
                    // 对于blob_io接口，根据查询类型显示不同的表头
                    headerHtml = `
                        <tr>
                            <th>时间</th>
                            <th>数值</th>
                        </tr>`;
                } else {
                    // 默认为存储空间相关接口
                    headerHtml = `
                        <tr>
                            <th>时间</th>
                            <th>存储量</th>
                        </tr>`;
                }

                // 根据API类型显示不同的列标题
                let valueDisplay;
                if(window.currentApiType === 'count') {
                    // 文件数量接口返回的是数量，不是存储大小
                    valueDisplay = formattedData.value.toLocaleString();
                } else if(window.currentApiType === 'blob_io') {
                    // blob_io接口可能返回流量（字节）或请求次数（数值）
                    // 检查是否是流量相关的查询
                    const selectParam = document.getElementById('select_param')?.value;
                    if(selectParam === 'flow') {
                        // 流量数据，使用GB格式化
                        valueDisplay = formatBytesToGB(formattedData.value);
                    } else {
                        // 请求次数数据，使用数值格式化
                        valueDisplay = formattedData.value.toLocaleString();
                    }
                } else {
                    // 存储空间接口返回的是字节数
                    valueDisplay = formatBytes(formattedData.value);
                }

                const tableHtml = `
                    <table>
                        <thead>
                            ${headerHtml}
                        </thead>
                        <tbody>
                            <tr>
                                <td>${formattedData.time}</td>
                                <td>${valueDisplay}</td>
                            </tr>
                        </tbody>
                    </table>
                `;

                document.getElementById('results').innerHTML = tableHtml;
            } else {
                document.getElementById('results').innerHTML = 
                    '<div class="error">未获取到有效的用量数据</div>';
            }
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
        
        function formatBytesToGB(bytes) {
            if (bytes === null || bytes === undefined) return 'N/A';
            
            // 将字节转换为GB (1 GB = 1024 * 1024 * 1024 bytes)
            const gbSize = parseFloat(bytes) / (1024 * 1024 * 1024);
            
            return gbSize.toFixed(6) + ' GB';
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
        
        # 从前端获取查询范围
        begin_time = data.get('begin')
        end_time = data.get('end')
        granularity = data.get('granularity', '5min')  # 默认使用5分钟粒度
        
        # 创建用量查询实例
        qiniu_api = QiniuDataStatAPI(ACCESS_KEY, SECRET_KEY)
        
        # 根据API类型选择查询方法
        api_type = data.get('api_type', 'count')
        
        if api_type == 'space':
            # 获取file_type参数
            file_type = data.get('file_type')
            result = qiniu_api.get_storage_usage(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity,
                file_type=file_type
            )
        elif api_type == 'count':
            # 获取file_type参数
            file_type = data.get('file_type')
            result = qiniu_api.get_file_count(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity,
                file_type=file_type
            )
        elif api_type == 'blob_io':
            # 对于blob_io接口，从请求中获取select和metric参数
            select = data.get('select', 'flow')
            metric = data.get('metric', 'flow_out')
            # 获取file_type参数
            file_type = data.get('file_type')
            result = qiniu_api.get_blob_io_stats(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity,
                select=select,
                metric=metric,
                file_type=file_type
            )
        elif api_type == 'rs_put':
            # 对于rs_put接口，从请求中获取file_type参数
            file_type = data.get('file_type')
            result = qiniu_api.get_put_requests_stats(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity,
                file_type=file_type
            )
        else:
            # 默认使用count接口
            file_type = data.get('file_type')
            result = qiniu_api.get_file_count(
                bucket_name=bucket_name,
                begin_time=begin_time,
                end_time=end_time,
                granularity=granularity,
                file_type=file_type
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
                    'message': f"认证失败 (401): 您的AK/SK可能没有访问{api_type}查询API的权限。请确认您的AccessKey ({ACCESS_KEY[:8]}...{ACCESS_KEY[-4:]}) 有权限访问/v6/{api_type}接口。错误详情: {result.get('data', {}).get('error', 'bad token')}"
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
                
                # 特别处理没有数据的情况
                if not result.get('data'):
                    return jsonify({
                        'success': False,
                        'message': f"未获取到有效的用量数据。可能的原因：1) 您的存储空间在查询时间段内没有相关活动；2) AK/SK没有访问{api_type}接口的权限；3) 查询时间范围过长或过大。API: /v6/{api_type}, 状态码: {result['status_code']}, 详情: {error_msg}"
                    }), 200  # 返回200，因为这不是真正的错误
                else:
                    return jsonify({
                        'success': False,
                        'message': f"API调用失败，状态码: {result['status_code']}, 错误: {error_msg}"
                    }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"服务器内部错误: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("七牛云存储用量查询Web应用 - 官方SDK版")
    print("=" * 60)
    print(f"AccessKey: {ACCESS_KEY[:8]}...{ACCESS_KEY[-4:]}")
    print(f"SecretKey: {SECRET_KEY[:8]}...{SECRET_KEY[-4:]}")
    print(f"默认存储空间: {BUCKET_NAME}")
    print("-" * 60)
    print("请在浏览器中访问: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动Web服务器
    app.run(host='0.0.0.0', port=5000, debug=False)