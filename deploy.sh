#!/bin/bash
# ============================================
#  文明星链：遗迹探索 — 腾讯云一键部署脚本
# ============================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_URL="${GIT_REPO_URL:-}"
BRANCH="${GIT_BRANCH:-main}"

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   文明星链：遗迹探索 — 一键部署      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[ERROR] 请使用 root 用户运行此脚本${NC}"
        echo "  sudo bash deploy.sh"
        exit 1
    fi
}

install_docker() {
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}[OK] Docker 已安装: $(docker --version)${NC}"
    else
        echo -e "${YELLOW}[INFO] 安装 Docker...${NC}"
        curl -fsSL https://get.docker.com | bash
        systemctl enable docker
        systemctl start docker
        echo -e "${GREEN}[OK] Docker 安装完成${NC}"
    fi

    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo -e "${GREEN}[OK] Docker Compose 已安装${NC}"
    else
        echo -e "${YELLOW}[INFO] 安装 Docker Compose...${NC}"
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}[OK] Docker Compose 安装完成${NC}"
    fi
}

setup_env() {
    echo -e "${YELLOW}[INFO] 配置环境变量...${NC}"

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"

        # 自动生成 JWT 密钥
        JWT_KEY=$(openssl rand -hex 32)
        sed -i "s/your_secret_key_here/$JWT_KEY/" "$PROJECT_DIR/.env"

        echo -e "${GREEN}[OK] .env 文件已生成${NC}"
        echo -e "${YELLOW}[WARN] 请编辑 .env 文件修改以下配置：${NC}"
        echo "  - MYSQL_PASSWORD: MySQL 数据库密码"
        echo "  - SMTP_USER: QQ邮箱"
        echo "  - SMTP_PASSWORD: 邮箱授权码"
    else
        echo -e "${GREEN}[OK] .env 文件已存在${NC}"
    fi
}

git_pull() {
    if [ -n "$REPO_URL" ]; then
        echo -e "${YELLOW}[INFO] 从 Git 拉取最新代码...${NC}"
        cd "$PROJECT_DIR"
        if [ ! -d ".git" ]; then
            git clone -b "$BRANCH" "$REPO_URL" .
        else
            git pull origin "$BRANCH"
        fi
        echo -e "${GREEN}[OK] 代码已更新${NC}"
    fi
}

build_and_deploy() {
    echo -e "${YELLOW}[INFO] 构建并启动所有服务...${NC}"
    cd "$PROJECT_DIR"

    docker compose down 2>/dev/null || true
    docker compose up -d --build

    echo ""
    echo -e "${GREEN}[OK] 所有服务已启动！${NC}"
    echo ""
    echo -e "  ${CYAN}访问地址:${NC} http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"
    echo -e "  ${CYAN}后端 API:${NC} http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):8000"
    echo ""
}

show_status() {
    echo -e "${YELLOW}[INFO] 服务状态:${NC}"
    docker compose ps
    echo ""
    echo -e "${YELLOW}[INFO] 查看日志:${NC}"
    echo "  docker compose logs -f backend"
    echo "  docker compose logs -f nginx"
    echo ""
    echo -e "${YELLOW}[INFO] 常用命令:${NC}"
    echo "  停止服务:  docker compose down"
    echo "  重启服务:  docker compose restart"
    echo "  查看日志:  docker compose logs -f"
    echo "  更新部署:  bash deploy.sh"
}

# ============ 主流程 ============
check_root
install_docker
setup_env
git_pull
build_and_deploy
show_status
