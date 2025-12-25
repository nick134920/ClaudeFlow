#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "==> 拉取最新代码（强制覆盖本地）..."
git fetch origin main
git reset --hard origin/main

echo "==> 停止旧容器..."
docker compose down

echo "==> 重新构建并启动..."
docker compose up -d --build

echo "==> 完成！查看日志："
echo "    docker compose logs -f"
