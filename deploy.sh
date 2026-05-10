#!/bin/bash
# ops-video 远端部署脚本
# 用法: ./deploy.sh [--build]
#   --build  强制重新构建 Docker 镜像
#
# 远端服务器: 49.235.108.61
# 部署路径:   /opt/ops-video
# 访问地址:   http://49.235.108.61:8081

set -e

SERVER="root@49.235.108.61"
REMOTE_DIR="/opt/ops-video"
BUILD_FLAG=""

if [ "$1" = "--build" ]; then
    BUILD_FLAG="--build"
fi

echo "=== ops-video 远端部署 ==="
echo "服务器: $SERVER"
echo "路径:   $REMOTE_DIR"
echo "端口:   ${HTTP_PORT:-8081}"
echo ""

# Step 1: 推送最新代码
echo "[1/4] 推送代码到 GitHub..."
git push
echo ""

# Step 2: 远端拉取 + 构建
echo "[2/4] 远端拉取代码..."
ssh $SERVER "
    if [ ! -d $REMOTE_DIR ]; then
        echo '首次部署，克隆仓库...'
        git clone https://github.com/kiddyt00/ops-video.git $REMOTE_DIR
    fi
    cd $REMOTE_DIR
    git pull origin main
"
echo ""

# Step 3: Docker Compose 构建 + 启动
echo "[3/4] Docker Compose 构建启动..."
ssh $SERVER "
    cd $REMOTE_DIR
    # 复制 .env 模板（如果不存在）
    if [ ! -f backend/.env ]; then
        cp backend/.env.example backend/.env 2>/dev/null || true
        echo 'WARNING: 请编辑 $REMOTE_DIR/backend/.env 填入 API Keys'
    fi

    docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.prod.yml up -d $BUILD_FLAG
"
echo ""

# Step 4: 健康检查
echo "[4/4] 等待服务就绪..."
sleep 5
ssh $SERVER "
    cd $REMOTE_DIR
    echo '=== 容器状态 ==='
    docker compose -f docker-compose.prod.yml ps
    echo ''
    echo '=== 健康检查 ==='
    curl -s http://localhost:8081/health | python3 -m json.tool 2>/dev/null || echo '健康检查端点未就绪'
"
echo ""

echo "=== 部署完成 ==="
echo "访问: http://49.235.108.61:${HTTP_PORT:-8081}"
echo "API文档: http://49.235.108.61:${HTTP_PORT:-8081}/docs"
