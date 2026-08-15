# H2O 清醒度体温计 API · 容器镜像
# 零依赖纯标准库，镜像极小（基于 python:3.12-slim）
FROM python:3.12-slim

WORKDIR /app

# 仅复制必要文件，保持镜像纯净
COPY h2o-thermometer-api.py ./
COPY requirements.txt ./

# 安装（空操作，仅为兼容部分 CI 规范）
RUN pip install --no-cache-dir -r requirements.txt

# 容器默认监听 8080；PaaS 会注入自己的 PORT 覆盖本值
ENV PORT=8080
EXPOSE 8080

CMD ["python", "h2o-thermometer-api.py"]
