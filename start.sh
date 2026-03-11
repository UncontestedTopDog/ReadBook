#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "正在创建虚拟环境并安装依赖..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install fastapi uvicorn python-multipart
else
    source .venv/bin/activate
fi

echo "正在启动 拆书工坊 Web 服务..."
uvicorn main:app --reload --host 0.0.0.0 --port 8080
