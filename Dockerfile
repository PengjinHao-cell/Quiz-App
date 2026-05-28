FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces 默认端口 7860
ENV PORT=7860
EXPOSE 7860

# 启动
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
