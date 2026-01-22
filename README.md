# 七牛云存储用量查询系统

这是一个用于查询七牛云存储用量信息的Web应用程序，支持查询存储量、文件数量、流量和请求次数等统计信息。

## 功能特性

- 查询七牛云存储空间的用量信息
- 支持多种数据类型查询：
  - 存储量统计 (space)
  - 文件数量统计 (count)  
  - 流量和请求次数统计 (blob_io)
  - PUT请求次数统计 (rs_put)
- Web界面操作，方便直观
- 支持自定义时间范围查询
- 时间粒度固定为5分钟，确保数据精度

## 技术栈

- Python Flask Web框架
- 七牛云Python SDK
- HTML/CSS/JavaScript前端

## 配置要求

需要在config.py中配置七牛云的AccessKey、SecretKey和存储空间信息。