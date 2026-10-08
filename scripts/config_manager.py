#!/usr/bin/env python3
"""
sing-box 配置管理器
支持在配置文件中直接配置订阅 URL，自动更新节点
"""

import json
import yaml
import requests
import sys
import os
import time
import signal
from pathlib import Path
from typing import Optional

class ConfigManager:
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config = None
        self.subscription_url = None
        self.update_interval = 3600
        self.running = True
        
    def load_config(self) -> dict:
        """加载配置文件"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 读取订阅配置
        if '_subscription' in self.config:
            sub_config = self.config['_subscription']
            url = sub_config.get('url', '')
            
            # 支持环境变量
            if url.startswith('env:'):
                env_var = url.split(':', 1)[1]
                self.subscription_url = os.environ.get(env_var)
            else:
                self.subscription_url = url
            
            self.update_interval = sub_config.get('update_interval', 3600)
            
            if not self.subscription_url:
                print("警告: 未配置订阅地址")
        
        return self.config
    
    def fetch_subscription(self) -> Optional[dict]:
        """获取订阅"""
        if not self.subscription_url:
            return None
        
        try:
            print(f"正在获取订阅: {self.subscription_url[:30]}...")
            headers = {'User-Agent': 'clash'}
            response = requests.get(self.subscription_url, timeout=30, headers=headers)
            response.raise_for_status()
            return yaml.safe_load(response.text)
        except Exception as e:
            print(f"错误: 获取订阅失败: {e}")
            return None
    
    def convert_proxy(self, clash_proxy: dict) -> Optional[dict]:
        """转换代理节点"""
        proxy_type = clash_proxy.get('type', '').lower()
        name = clash_proxy.get('name', 'Unknown')
        
        singbox_proxy = {'tag': name}
        
        if proxy_type in ['ss', 'shadowsocks']:
            singbox_proxy['type'] = 'shadowsocks'
            singbox_proxy['server'] = clash_proxy.get('server')
            singbox_proxy['server_port'] = clash_proxy.get('port')
            singbox_proxy['method'] = clash_proxy.get('cipher')
            singbox_proxy['password'] = clash_proxy.get('password')
        
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
        
        else:
            return None
        
        return singbox_proxy
    
    def update_proxies(self) -> bool:
        """更新代理节点"""
        clash_config = self.fetch_subscription()
        if not clash_config or 'proxies' not in clash_config:
            return False
        
        print(f"找到 {len(clash_config['proxies'])} 个节点")
        
        # 转换节点
        proxies = []
        for clash_proxy in clash_config['proxies']:
            singbox_proxy = self.convert_proxy(clash_proxy)
            if singbox_proxy:
                proxies.append(singbox_proxy)
        
        if not proxies:
            print("错误: 没有可用的节点")
            return False
        
        print(f"成功转换 {len(proxies)} 个节点")
        
        # 更新配置
        proxy_tags = [p['tag'] for p in proxies]
        
        # 移除旧节点，保留选择器
        new_outbounds = []
        for outbound in self.config['outbounds']:
            if outbound['type'] in ['selector', 'urltest', 'direct', 'block']:
                new_outbounds.append(outbound)
        
        # 添加新节点
        new_outbounds.extend(proxies)
        self.config['outbounds'] = new_outbounds
        
        # 更新代理组引用
        for outbound in self.config['outbounds']:
            if outbound['type'] in ['selector', 'urltest']:
                tag = outbound['tag']
                if tag in ['🌐 全部节点', '♻️ 自动选择', '🔯 故障转移', 
                          '🔮 负载均衡-轮询', '🔮 负载均衡-散列'] or tag.startswith('🎉 xiaonuo'):
                    outbound['outbounds'] = proxy_tags
        
        return True
    
    def save_runtime_config(self, output_file: str) -> bool:
        """保存运行时配置（移除元数据）"""
        runtime_config = self.config.copy()
        
        # 移除订阅配置元数据
        runtime_config.pop('_subscription', None)
        runtime_config.pop('_proxies_placeholder', None)
        runtime_config.pop('_comment', None)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(runtime_config, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 配置已保存: {output_file}")
        return True
    
    def run_update_loop(self, output_file: str):
        """运行更新循环"""
        def signal_handler(sig, frame):
            print("\n收到停止信号，退出...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print(f"更新间隔: {self.update_interval} 秒")
        
        while self.running:
            if self.update_proxies():
                self.save_runtime_config(output_file)
                print(f"✓ 更新完成 ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                print(f"✗ 更新失败 ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # 等待下次更新
            for _ in range(self.update_interval):
                if not self.running:
                    break
                time.sleep(1)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 config_manager.py <配置文件> [输出文件] [模式]")
        print("")
        print("参数:")
        print("  配置文件  - 包含 _subscription 的配置模板")
        print("  输出文件  - 运行时配置输出路径（默认: runtime_config.json）")
        print("  模式      - once: 单次更新, daemon: 守护进程（默认: once）")
        print("")
        print("示例:")
        print("  python3 config_manager.py config.json runtime.json once")
        print("  python3 config_manager.py config.json runtime.json daemon")
        sys.exit(1)
    
    config_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'runtime_config.json'
    mode = sys.argv[3] if len(sys.argv) > 3 else 'once'
    
    manager = ConfigManager(config_file)
    manager.load_config()
    
    if mode == 'daemon':
        print("运行模式: 守护进程")
        manager.run_update_loop(output_file)
    else:
        print("运行模式: 单次更新")
        if manager.update_proxies():
            manager.save_runtime_config(output_file)
            print("✓ 完成")
        else:
            print("✗ 失败")
            sys.exit(1)

if __name__ == '__main__':
    main()
