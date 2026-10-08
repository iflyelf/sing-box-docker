#!/bin/bash
# sing-box 订阅自动更新脚本
# 类似 Clash 的 proxy-providers 自动更新功能

set -e

# ============================================================
# 配置部分（请根据实际情况修改）
# ============================================================

# 订阅地址（保密，使用环境变量）
# export CLASH_SUBSCRIPTION_URL='你的订阅地址'

# 配置文件路径（相对路径或绝对路径）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_TEMPLATE="${SCRIPT_DIR}/../sing-box-docker/conf/config.json"
OUTPUT_CONFIG="/tmp/singbox_config.json"

# 服务管理
SERVICE_NAME="singbox"
USE_SYSTEMD=false  # 是否使用 systemd 管理服务

# 更新间隔（秒）
UPDATE_INTERVAL=3600  # 3600秒 = 1小时

# ============================================================
# 函数定义
# ============================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_requirements() {
    log "检查依赖..."
    
    if [ -z "${CLASH_SUBSCRIPTION_URL}" ]; then
        log "错误: 未设置 CLASH_SUBSCRIPTION_URL 环境变量"
        log "请先设置: export CLASH_SUBSCRIPTION_URL='你的订阅地址'"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log "错误: 未找到 python3"
        exit 1
    fi
    
    if ! command -v sing-box &> /dev/null; then
        log "错误: 未找到 sing-box"
        exit 1
    fi
    
    if [ ! -f "${CONFIG_TEMPLATE}" ]; then
        log "错误: 配置模板不存在: ${CONFIG_TEMPLATE}"
        exit 1
    fi
    
    log "✓ 依赖检查通过"
}

update_subscription() {
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "开始更新订阅..."
    
    # 转换订阅
    if python3 "${SCRIPT_DIR}/subscription_converter.py" \
        "${CONFIG_TEMPLATE}" \
        "${OUTPUT_CONFIG}"; then
        
        log "✓ 订阅更新成功"
        
        # 验证配置
        if sing-box check -c "${OUTPUT_CONFIG}" > /dev/null 2>&1; then
            log "✓ 配置验证通过"
            return 0
        else
            log "✗ 配置验证失败"
            return 1
        fi
    else
        log "✗ 订阅更新失败"
        return 1
    fi
}

restart_service() {
    log "重启 sing-box 服务..."
    
    if [ "${USE_SYSTEMD}" = true ]; then
        # 使用 systemd
        if systemctl is-active --quiet "${SERVICE_NAME}"; then
            sudo systemctl restart "${SERVICE_NAME}"
            log "✓ systemd 服务已重启"
        else
            log "⚠️ systemd 服务未运行"
        fi
    else
        # 发送 HUP 信号重载配置（如果支持）
        if pgrep -x sing-box > /dev/null; then
            pkill -HUP sing-box
            log "✓ 已发送重载信号"
        else
            log "⚠️ sing-box 进程未运行"
        fi
    fi
}

# ============================================================
# 主逻辑
# ============================================================

main() {
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "sing-box 订阅自动更新脚本"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 检查依赖
    check_requirements
    
    # 获取运行模式
    MODE="${1:-once}"
    
    case "${MODE}" in
        once)
            log "运行模式: 单次更新"
            if update_subscription; then
                restart_service
                log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                log "✓ 更新完成"
            else
                log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                log "✗ 更新失败"
                exit 1
            fi
            ;;
            
        daemon)
            log "运行模式: 守护进程（每 ${UPDATE_INTERVAL} 秒更新一次）"
            log "按 Ctrl+C 停止"
            log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            # 首次更新
            if update_subscription; then
                restart_service
            fi
            
            # 定期更新
            while true; do
                log "等待 ${UPDATE_INTERVAL} 秒后下次更新..."
                sleep "${UPDATE_INTERVAL}"
                
                if update_subscription; then
                    restart_service
                fi
            done
            ;;
            
        *)
            echo "用法: $0 [once|daemon]"
            echo ""
            echo "参数:"
            echo "  once   - 单次更新（默认）"
            echo "  daemon - 守护进程模式，定期自动更新"
            echo ""
            echo "环境变量:"
            echo "  CLASH_SUBSCRIPTION_URL - 订阅地址（必需）"
            echo ""
            echo "示例:"
            echo "  export CLASH_SUBSCRIPTION_URL='https://example.com/subscription'"
            echo "  $0 once      # 单次更新"
            echo "  $0 daemon    # 守护进程模式"
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'log "收到中断信号，退出..."; exit 0' INT TERM

# 运行主函数
main "$@"
