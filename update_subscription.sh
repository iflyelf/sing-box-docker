#!/bin/bash
# sing-box 订阅更新便捷脚本
# 位置: /xiaonuo/workspace/docker/sing-box-docker/update_subscription.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="${SCRIPT_DIR}/../../tools/gwf"
CONFIG_TEMPLATE="${SCRIPT_DIR}/conf/config_with_sub.json"
CONFIG_OUTPUT="${SCRIPT_DIR}/conf/config.json"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "sing-box 订阅更新脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查订阅地址
if [ -z "${CLASH_SUBSCRIPTION_URL}" ]; then
    echo "错误: 未设置 CLASH_SUBSCRIPTION_URL 环境变量"
    echo ""
    echo "请先设置:"
    echo "  export CLASH_SUBSCRIPTION_URL='你的订阅地址'"
    exit 1
fi

echo "配置模板: ${CONFIG_TEMPLATE}"
echo "输出配置: ${CONFIG_OUTPUT}"
echo ""

# 备份当前配置
if [ -f "${CONFIG_OUTPUT}" ]; then
    cp "${CONFIG_OUTPUT}" "${CONFIG_OUTPUT}.backup"
    echo "✓ 已备份当前配置"
fi

# 更新配置
echo ""
echo "正在更新订阅..."
cd "${TOOLS_DIR}"
python3 config_manager.py "${CONFIG_TEMPLATE}" "${CONFIG_OUTPUT}" once

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✓ 订阅更新成功"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "下一步:"
    echo "  1. 检查配置: sing-box check -c ${CONFIG_OUTPUT}"
    echo "  2. 重启服务: sudo systemctl restart singbox"
    echo "  3. 或直接运行: sing-box run -c ${CONFIG_OUTPUT}"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✗ 订阅更新失败"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 恢复备份
    if [ -f "${CONFIG_OUTPUT}.backup" ]; then
        mv "${CONFIG_OUTPUT}.backup" "${CONFIG_OUTPUT}"
        echo "已恢复原配置"
    fi
    
    exit 1
fi
