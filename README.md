# sing-box Docker 配置

Clash 配置转换为 sing-box 格式，支持远程规则集和 GitHub Actions 自动更新。

## ✅ 核心特性

1. **DNS 禁用** - 完全使用 smartdns 处理 DNS 解析
2. **代理组完整** - 保留所有 34 个 Clash 代理组
3. **远程规则集** - 从 GitHub 自动拉取最新规则集
4. **自动更新** - GitHub Actions 自动编译规则集

## 📁 文件结构

```
sing-box-docker/
├── conf/
│   └── config.json          # sing-box 主配置文件
├── .github/
│   └── workflows/           # GitHub Actions (如需要)
└── README.md               # 本文档
```

## 🚀 快速开始

### 1. 安装 sing-box

```bash
# 方式 1: 官方脚本（推荐）
bash <(curl -fsSL https://sing-box.app/deb-install.sh)

# 方式 2: 手动下载最新版本
LATEST_VERSION=$(curl -s https://api.github.com/repos/SagerNet/sing-box/releases/latest | grep -o '"tag_name": "v[^"]*"' | cut -d'"' -f4)
VERSION_NUM=${LATEST_VERSION#v}
wget "https://down.xiaonuo.live?url=https://github.com/SagerNet/sing-box/releases/download/${LATEST_VERSION}/sing-box-${VERSION_NUM}-linux-amd64.tar.gz" -O sing-box.tar.gz
tar -xzf sing-box.tar.gz
sudo cp sing-box-${VERSION_NUM}-linux-amd64/sing-box /usr/local/bin/
sudo chmod +x /usr/local/bin/sing-box
sing-box version
```

### 2. 添加代理节点

配置文件目前没有实际代理节点，需要手动添加。编辑 `conf/config.json`，在 `outbounds` 数组末尾添加节点：

```json
{
  "type": "vmess",
  "tag": "香港-01",
  "server": "hk.example.com",
  "server_port": 443,
  "uuid": "your-uuid-here",
  "security": "auto",
  "alter_id": 0,
  "tls": {
    "enabled": true,
    "server_name": "hk.example.com"
  }
}
```

### 3. 启动 sing-box

```bash
# 前台测试
sing-box run -c conf/config.json

# 或使用 systemd 服务
sudo systemctl start sing-box
```

## 🔧 配置说明

### 端口配置

| 服务   | 端口 | 协议          |
| ------ | ---- | ------------- |
| Mixed  | 7890 | HTTP + SOCKS5 |
| SOCKS5 | 7891 | SOCKS5        |
| TProxy | 7893 | 透明代理      |

### DNS 配置

DNS 已完全禁用，sing-box 将使用系统 DNS (smartdns)。如需修改，编辑 `config.json` 中的 `dns` 部分。

### 规则集来源

所有规则集从 GitHub 远程加载：

```
https://raw.githubusercontent.com/iflyelf/gwf/main/singbox/rule-set/*.srs
```

规则集包括：

- **拦截规则** (6个): XiaoNuoReject, BanAD, BanProgramAD 等
- **直连规则** (14个): XiaoNuoDirect, ChinaIp, ChinaDomain 等
- **代理规则** (14个): XiaoNuoProxy, ProxyGFWlist, Telegram 等

### 代理组

配置包含 34 个代理组：

**功能分组**：

- 🚀 节点选择、♻️ 自动选择、🔯 故障转移
- 🔮 负载均衡-轮询、🔮 负载均衡-散列
- 🌐 全部节点

**服务分组**：

- 📲 电报消息、💬 Ai平台、📹 油管视频、🎥 奈飞视频
- 📺 巴哈姆特、🌍 国外媒体、🌏 出海媒体、🌏 国内媒体
- 📺 哔哩哔哩、Ⓜ️ 微软云盘、Ⓜ️ 微软服务、🍎 苹果服务
- 🎮 游戏平台、🎶 网易音乐

**地区分组** (自动/手动)：

- 🇹🇼 台湾、🇭🇰 香港、🇯🇵 日本、🇸🇬 新加坡、🇰🇷 韩国
- 🇷🇺 俄罗斯、🇨🇦 加拿大、🇺🇸 美国、🇬🇧 英国、🇫🇷 法国
- 🇩🇪 德国、🇧🇷 巴西、🇳🇱 荷兰、🚞 其它地区

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3'

services:
  sing-box:
    # 使用华为云镜像（国内加速）
    image: swr.cn-east-3.myhuaweicloud.com/iflyelf/sing-box:latest
    container_name: sing-box
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./conf/config.json:/etc/sing-box/config.json:ro
    command: run -c /etc/sing-box/config.json
```

> **镜像说明**：使用华为云 SWR 镜像仓库，国内访问速度更快
> - 华为云镜像（推荐）：`swr.cn-east-3.myhuaweicloud.com/iflyelf/sing-box:latest`
> - 官方镜像（国外）：`ghcr.io/sagernet/sing-box:latest`

启动服务：

```bash
docker-compose up -d
```

查看日志：

```bash
docker-compose logs -f
```

### 使用 Docker 命令

```bash
# 使用华为云镜像（推荐）
docker run -d \
  --name sing-box \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/conf/config.json:/etc/sing-box/config.json:ro \
  swr.cn-east-3.myhuaweicloud.com/iflyelf/sing-box:latest \
  run -c /etc/sing-box/config.json

# 或使用官方镜像
docker run -d \
  --name sing-box \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/conf/config.json:/etc/sing-box/config.json:ro \
  ghcr.io/sagernet/sing-box:latest \
  run -c /etc/sing-box/config.json
```

## 📝 systemd 服务

创建服务文件 `/etc/systemd/system/sing-box.service`：

```ini
[Unit]
Description=sing-box Service
Documentation=https://sing-box.sagernet.org
After=network.target nss-lookup.target

[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c /path/to/config.json
Restart=on-failure
RestartSec=10s
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable sing-box
sudo systemctl start sing-box
sudo systemctl status sing-box
```

## 🔄 规则集更新

规则集由 GitHub Actions 自动编译和更新：

1. 修改 Clash 规则文件 (`gwf` 仓库)
2. 推送到 GitHub
3. GitHub Actions 自动转换为 sing-box 格式
4. 自动编译为二进制 `.srs` 格式
5. sing-box 自动从远程拉取最新规则

无需手动操作，规则集会自动保持最新。

## 🛠️ 常用命令

```bash
# 验证配置
sing-box check -c conf/config.json

# 前台运行（调试）
sing-box run -c conf/config.json

# 查看服务状态
systemctl status sing-box

# 查看日志
journalctl -u sing-box -f

# 重启服务
systemctl restart sing-box

# Docker 查看日志
docker logs -f sing-box
```

## 📊 与 Clash 对比

| 特性       | Clash | sing-box           |
| ---------- | ----- | ------------------ |
| 配置格式   | YAML  | JSON               |
| 规则集格式 | YAML  | JSON/Binary (SRS)  |
| DNS        | 内置  | 可选（本配置禁用） |
| 性能       | 较好  | 更好               |
| 内存占用   | 较高  | 更低               |
| 订阅支持   | 原生  | 需要手动转换       |

## 🐛 故障排查

### 无法启动

```bash
# 检查配置语法
sing-box check -c conf/config.json

# 查看详细日志
sing-box run -c conf/config.json
```

### 无法连接

1. 检查端口占用：`netstat -tlnp | grep -E '7890|7891|7893'`
2. 检查防火墙：`ufw status`
3. 验证节点配置是否正确

### 规则不生效

1. 检查规则集文件是否可访问
2. 确认 GitHub 仓库规则集已更新
3. 清除缓存：`rm -f cache.db`

### DNS 解析问题

确认 smartdns 正在运行：

```bash
systemctl status smartdns
```

## 📖 参考资料

- [sing-box 官方文档](https://sing-box.sagernet.org/zh/)
- [配置示例](https://sing-box.sagernet.org/zh/configuration/)
- [规则集格式](https://sing-box.sagernet.org/zh/configuration/rule-set/)
- [GitHub 仓库](https://github.com/SagerNet/sing-box)

## 📄 许可证

MIT License
