#!/usr/bin/env python3
"""
Clash 订阅转换为 sing-box 配置
使用环境变量存储订阅地址以保护隐私
支持自动更新和 Clash API 管理
"""

import json
import yaml
import requests
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Optional

def fetch_clash_subscription(url: str) -> dict:
    """从订阅 URL 获取 Clash 配置"""
    try:
        headers = {
            'User-Agent': 'clash'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        clash_config = yaml.safe_load(response.text)
        return clash_config
    except Exception as e:
        print(f"错误: 无法获取订阅: {e}")
        return None

def convert_clash_proxy_to_singbox(clash_proxy: dict) -> dict:
    """将 Clash 代理节点转换为 sing-box 格式"""
    proxy_type = clash_proxy.get('type', '').lower()
    name = clash_proxy.get('name', 'Unknown')
    
    singbox_proxy = {'tag': name}
    
    if proxy_type in ['ss', 'shadowsocks']:
        singbox_proxy['type'] = 'shadowsocks'
        singbox_proxy['server'] = clash_proxy.get('server')
        singbox_proxy['server_port'] = clash_proxy.get('port')
        singbox_proxy['method'] = clash_proxy.get('cipher')
        singbox_proxy['password'] = clash_proxy.get('password')
        
        plugin = clash_proxy.get('plugin')
        if plugin:
            singbox_proxy['plugin'] = plugin
            singbox_proxy['plugin_opts'] = clash_proxy.get('plugin-opts', {})
    
    elif proxy_type == 'vmess':
        singbox_proxy['type'] = 'vmess'
        singbox_proxy['server'] = clash_proxy.get('server')
        singbox_proxy['server_port'] = clash_proxy.get('port')
        singbox_proxy['uuid'] = clash_proxy.get('uuid')
        singbox_proxy['security'] = clash_proxy.get('cipher', 'auto')
        singbox_proxy['alter_id'] = clash_proxy.get('alterId', 0)
        
        if clash_proxy.get('tls'):
            singbox_proxy['tls'] = {
                'enabled': True,
                'server_name': clash_proxy.get('servername', clash_proxy.get('sni', ''))
            }
            if clash_proxy.get('skip-cert-verify'):
                singbox_proxy['tls']['insecure'] = True
        
        if clash_proxy.get('network') == 'ws':
            singbox_proxy['transport'] = {
                'type': 'ws',
                'path': clash_proxy.get('ws-opts', {}).get('path', '/'),
                'headers': clash_proxy.get('ws-opts', {}).get('headers', {})
            }
    
    elif proxy_type == 'trojan':
        singbox_proxy['type'] = 'trojan'
        singbox_proxy['server'] = clash_proxy.get('server')
        singbox_proxy['server_port'] = clash_proxy.get('port')
        singbox_proxy['password'] = clash_proxy.get('password')
        
        singbox_proxy['tls'] = {
            'enabled': True,
            'server_name': clash_proxy.get('sni', clash_proxy.get('server'))
        }
        if clash_proxy.get('skip-cert-verify'):
            singbox_proxy['tls']['insecure'] = True
        
        if clash_proxy.get('network') == 'ws':
            singbox_proxy['transport'] = {
                'type': 'ws',
                'path': clash_proxy.get('ws-opts', {}).get('path', '/'),
                'headers': clash_proxy.get('ws-opts', {}).get('headers', {})
            }
    
    elif proxy_type in ['hysteria2', 'hy2']:
        singbox_proxy['type'] = 'hysteria2'
        singbox_proxy['server'] = clash_proxy.get('server')
        singbox_proxy['server_port'] = clash_proxy.get('port')
        singbox_proxy['password'] = clash_proxy.get('password')
        
        singbox_proxy['tls'] = {
            'enabled': True,
            'server_name': clash_proxy.get('sni', clash_proxy.get('server'))
        }
        if clash_proxy.get('skip-cert-verify'):
            singbox_proxy['tls']['insecure'] = True
    
    else:
        print(f"警告: 不支持的代理类型 '{proxy_type}' (节点: {name})")
        return None
    
    return singbox_proxy

def filter_proxies_by_region(proxies: List[dict], keywords: List[str]) -> List[str]:
    """根据关键词过滤代理节点"""
    filtered = []
    for proxy in proxies:
        name = proxy.get('tag', '')
        for keyword in keywords:
            if keyword.lower() in name.lower():
                filtered.append(proxy['tag'])
                break
    return filtered

def update_config_with_proxies(config_template: str, proxies: list, output_file: str):
    """更新配置文件添加代理节点"""
    try:
        with open(config_template, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取代理节点的 tag 列表
        proxy_tags = [p['tag'] for p in proxies if p]
        
        # 移除旧的代理节点（保留选择器和特殊节点）
        new_outbounds = []
        for outbound in config['outbounds']:
            if outbound['type'] in ['selector', 'urltest', 'direct', 'block']:
                new_outbounds.append(outbound)
        
        # 添加新的代理节点
        new_outbounds.extend([p for p in proxies if p])
        
        config['outbounds'] = new_outbounds
        
        # 更新代理组的 outbounds 引用
        # 定义地区关键词映射
        region_keywords = {
            '🇹🇼 台湾': ['台', 'tw', 'taiwan', 'TW', 'Taiwan'],
            '🇭🇰 香港': ['港', 'hk', 'hongkong', 'hong kong', 'HK', 'HongKong'],
            '🇯🇵 日本': ['日', 'jp', 'japan', 'JP', 'Japan'],
            '🇸🇬 新加坡': ['新', 'sg', 'singapore', 'SG', 'Singapore'],
            '🇰🇷 韩国': ['韩', '🇰🇷', 'KR', 'Korea'],
            '🇷🇺 俄罗斯': ['🇷🇺', 'RU', '俄罗斯', 'Russia'],
            '🇨🇦 加拿大': ['🇨🇦', 'CA', '加拿大', 'Canada'],
            '🇺🇸 美国': ['美', 'us', 'unitedstates', 'united states', 'US', 'USA'],
            '🇬🇧 英国': ['🇬🇧', 'GB', '英国', 'UK', 'Britain'],
            '🇫🇷 法国': ['🇫🇷', 'FR', '法国', 'France'],
            '🇩🇪 德国': ['🇩🇪', 'DE', '德国', 'Germany'],
            '🇧🇷 巴西': ['🇧🇷', 'BR', '巴西', 'Brazil'],
            '🇳🇱 荷兰': ['🇳🇱', 'NL', '荷兰', 'Netherlands'],
        }
        
        # 计算排除关键词
        exclude_keywords = ['公司', '直连', '广告', '拦截']
        all_region_keywords = []
        for keywords in region_keywords.values():
            all_region_keywords.extend(keywords)
        
        for outbound in config['outbounds']:
            if outbound['type'] in ['selector', 'urltest']:
                tag = outbound['tag']
                
                # 全部节点类组
                if tag in ['🌐 全部节点', '♻️ 自动选择', '🔯 故障转移', '🔮 负载均衡-轮询', '🔮 负载均衡-散列']:
                    outbound['outbounds'] = proxy_tags
                
                # xiaonuo 组
                elif tag.startswith('🎉 xiaonuo'):
                    outbound['outbounds'] = proxy_tags
                
                # 地区分组（自动选择和手动选择）
                elif tag in region_keywords or tag.replace('🛺', '') in region_keywords:
                    region_name = tag.replace('🛺', '')
                    if region_name in region_keywords:
                        keywords = region_keywords[region_name]
                        outbound['outbounds'] = filter_proxies_by_region(proxies, keywords)
                        if not outbound['outbounds']:
                            outbound['outbounds'] = ['🎯 全球直连']
                
                # 其它地区（排除已知地区）
                elif tag == '🚞 其它地区':
                    filtered = []
                    for proxy in proxies:
                        name = proxy.get('tag', '')
                        is_known_region = False
                        for keyword in all_region_keywords + exclude_keywords:
                            if keyword.lower() in name.lower():
                                is_known_region = True
                                break
                        if not is_known_region:
                            filtered.append(proxy['tag'])
                    outbound['outbounds'] = filtered if filtered else ['🎯 全球直连']
        
        # 保存配置
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 配置已更新: {output_file}")
        print(f"  添加了 {len(proxy_tags)} 个节点")
        
        # 显示地区分组统计
        print("")
        print("地区分组统计:")
        for outbound in config['outbounds']:
            if outbound['type'] in ['selector', 'urltest']:
                tag = outbound['tag']
                if any(region in tag for region in ['🇹🇼', '🇭🇰', '🇯🇵', '🇸🇬', '🇰🇷', '🇷🇺', '🇨🇦', '🇺🇸', '🇬🇧', '🇫🇷', '🇩🇪', '🇧🇷', '🇳🇱']):
                    count = len(outbound.get('outbounds', []))
                    if count > 0 and outbound['outbounds'] != ['🎯 全球直连']:
                        print(f"  {tag}: {count} 个节点")
        
        return True
        
    except Exception as e:
        print(f"错误: 更新配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 从环境变量获取订阅地址（保护隐私）
    subscription_url = os.environ.get('CLASH_SUBSCRIPTION_URL')
    
    if not subscription_url:
        print("错误: 未设置订阅地址")
        print("")
        print("使用方法:")
        print("  export CLASH_SUBSCRIPTION_URL='你的订阅地址'")
        print("  python3 subscription_converter.py [配置模板] [输出文件]")
        print("")
        print("示例:")
        print("  export CLASH_SUBSCRIPTION_URL='https://example.com/subscription'")
        print("  python3 subscription_converter.py config.json output.json")
        sys.exit(1)
    
    config_template = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'config_with_proxies.json'
    
    print(f"正在获取订阅...")
    print(f"订阅地址: {subscription_url[:30]}...")
    clash_config = fetch_clash_subscription(subscription_url)
    
    if not clash_config:
        print("错误: 无法获取订阅内容")
        sys.exit(1)
    
    if 'proxies' not in clash_config:
        print("错误: 订阅内容中没有找到代理节点")
        sys.exit(1)
    
    print(f"找到 {len(clash_config['proxies'])} 个节点，开始转换...")
    
    singbox_proxies = []
    for clash_proxy in clash_config['proxies']:
        singbox_proxy = convert_clash_proxy_to_singbox(clash_proxy)
        if singbox_proxy:
            singbox_proxies.append(singbox_proxy)
    
    print(f"成功转换 {len(singbox_proxies)} 个节点")
    
    if not singbox_proxies:
        print("错误: 没有可用的节点")
        sys.exit(1)
    
    print(f"正在更新配置文件...")
    if update_config_with_proxies(config_template, singbox_proxies, output_file):
        print("")
        print("✓ 订阅转换完成!")
        print("")
        print("下一步:")
        print(f"  1. 检查配置: sing-box check -c {output_file}")
        print(f"  2. 启动服务: sing-box run -c {output_file}")
        print("")
        print("Clash API:")
        print("  地址: http://127.0.0.1:9090")
        print("  Secret: @admin123")
        print("  面板: http://127.0.0.1:9090/ui")
    else:
        print("")
        print("✗ 订阅转换失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
