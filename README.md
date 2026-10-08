# sing-box Docker 配置和订阅管理

Clash 配置转换为 sing-box 格式，支持远程规则集、订阅管理和 Clash API。

## ✨ 特性

- ✅ **完全对齐 Clash**：所有功能与 Clash 保持一致
- ✅ **DNS 禁用**：使用 smartdns 处理 DNS 解析
- ✅ **远程规则集**：从 GitHub 自动拉取最新规则集（SRS 格式）
- ✅ **订阅管理**：支持 Clash 订阅转换和自动更新
- ✅ **Clash API**：兼容 Clash API，支持 Web 面板管理
- ✅ **地区分组**：自动识别节点地区（13个地区）

## 📁 项目结构

```
sing-box-docker/
├── conf/
│   ├── config.json               # 运行时配置
│   └── config_with_sub.json      # 配置模板（含订阅）
├── scripts/
│   ├── subscription_converter.py # 订阅转换工具
│   ├── config_manager.py         # 配置管理器
│   └── auto_update_subscription.sh # 自动更新脚本
├── update_subscription.sh        # 便捷更新脚本
├── docker-compose.yml            # Docker Compose 配置
└── README.md                     # 本文档
```

## 🚀 快速开始

### 1. 安装 sing-box

```bash
# 方式 1: 官方脚本（推荐）
bash <(curl -fsSL https://sing-box.app/deb-install.sh)

# 方式 2: 手动下载最新版本
LATEST_VERSION=$(curl -s https://api.github.com/repos/SagerNet/sing-box/releases/latest | grep -o '"tag_name": "v[^"]*"' | cut -d'"' -f4)
VERSION_NUM=${LATEST_VERSION#v}
wget "https://github.com/SagerNet/sing-box/releases/download/${LATEST_VERSION}/sing-box-${VERSION_NUM}-linux-amd64.tar.gz"
tar -xzf sing-box-${VERSION_NUM}-linux-amd64.tar.gz
sudo cp sing-box-${VERSION_NUM}-linux-amd64/sing-box /usr/local/bin/
sudo chmod +x /usr/local/bin/sing-box
sing-box version
```

### 2. 克隆配置

```bash
git clone https://github.com/iflyelf/sing-box-docker.git
cd sing-box-docker
```

### 3. 转换订阅

```bash
# 设置订阅地址
export CLASH_SUBSCRIPTION_URL='你的订阅地址'

# 运行更新脚本
./update_subscription.sh
```

### 4. 启动服务

```bash
# 直接运行
sing-box run -c conf/config.json

# 或使用 systemd
sudo systemctl start singbox
```

## 🔧 配置说明

### 端口配置

| 服务   | 端口 | 协议          |
| ------ | ---- | ------------- |
| Mixed  | 7890 | HTTP + SOCKS5 |
| SOCKS5 | 7891 | SOCKS5        |
| TProxy | 7893 | 透明代理      |
| API    | 9090 | Clash API     |

### DNS 配置

DNS 已完全禁用，sing-box 将使用系统 DNS（smartdns）。

### 规则集来源

所有规则集从 [gwf](https://github.com/iflyelf/gwf) 仓库远程加载（SRS 二进制格式）：

```
https://raw.githubusercontent.com/iflyelf/gwf/main/singbox/rule-set/*.srs
```

规则集包括：
- **拦截规则**（6个）：XiaoNuoReject, BanAD, BanProgramAD 等
- **直连规则**（14个）：XiaoNuoDirect, ChinaIp, ChinaDomain 等
- **代理规则**（14个）：XiaoNuoProxy, ProxyGFWlist, Telegram 等

### 代理组

配置包含 53 个代理组，与 Clash 完全一致：

- **功能分组**：节点选择、自动选择、故障转移、负载均衡
- **服务分组**：Telegram、AI、YouTube、Netflix 等
- **地区分组**：台湾、香港、日本、新加坡、美国等（自动/手动）

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）

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

启动服务：

```bash
docker-compose up -d
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
```

## 📡 订阅管理

### 订阅 URL 配置

在 `conf/config_with_sub.json` 中配置订阅地址：

```json
{
  "_subscription": {
    "url": "env:CLASH_SUBSCRIPTION_URL",
    "update_interval": 3600,
    "auto_update": true
  },
  ...
}
```

- `url`: 订阅地址，支持 `env:变量名` 或直接写 URL（不推荐）
- `update_interval`: 更新间隔（秒）
- `auto_update`: 是否自动更新

### 更新订阅

#### 方式 1：使用便捷脚本（推荐）

```bash
export CLASH_SUBSCRIPTION_URL='你的订阅地址'
./update_subscription.sh
```

#### 方式 2：使用配置管理器

```bash
export CLASH_SUBSCRIPTION_URL='你的订阅地址'
cd scripts
python3 config_manager.py ../conf/config_with_sub.json ../conf/config.json once
```

#### 方式 3：使用订阅转换工具

```bash
export CLASH_SUBSCRIPTION_URL='你的订阅地址'
cd scripts
python3 subscription_converter.py ../conf/config.json output.json
```

### 自动更新

#### 守护进程模式

```bash
cd scripts
./auto_update_subscription.sh daemon
```

#### Crontab 定时任务

```bash
crontab -e

# 添加：每小时更新一次
0 * * * * export CLASH_SUBSCRIPTION_URL='你的订阅' && cd /path/to/sing-box-docker && ./update_subscription.sh >> /var/log/singbox-update.log 2>&1
```

## 🌐 Clash API

### API 配置

```json
{
  "experimental": {
    "clash_api": {
      "external_controller": ":9090",
      "external_ui": "ui",
      "secret": "@admin123",
      "default_mode": "rule"
    }
  }
}
```

### 访问信息

- **API 地址**: `http://127.0.0.1:9090`
- **Secret**: `@admin123`
- **面板地址**: `http://127.0.0.1:9090/ui`

### API 使用示例

```bash
# 获取配置信息
curl -H "Authorization: Bearer @admin123" http://127.0.0.1:9090/configs

# 获取代理信息
curl -H "Authorization: Bearer @admin123" http://127.0.0.1:9090/proxies

# 切换代理
curl -X PUT \
  -H "Authorization: Bearer @admin123" \
  -H "Content-Type: application/json" \
  -d '{"name":"节点名称"}' \
  http://127.0.0.1:9090/proxies/🚀%20节点选择

# 测试延迟
curl -H "Authorization: Bearer @admin123" \
  "http://127.0.0.1:9090/proxies/节点名称/delay?timeout=5000&url=https://www.gstatic.com/generate_204"
```

### Web 面板

推荐使用以下面板：

1. **Yacd**
   ```bash
   git clone https://github.com/haishanh/yacd.git ui
   ```

2. **Clash Dashboard**
   ```bash
   git clone https://github.com/Dreamacro/clash-dashboard.git ui
   ```

3. **Yacd-meta**
   ```bash
   git clone https://github.com/MetaCubeX/Yacd-meta.git ui
   ```

访问：`http://127.0.0.1:9090/ui`

## 🔄 节点地区自动分组

订阅转换工具会自动识别节点地区并分配到对应组：

| 地区组 | 匹配关键词 |
|--------|-----------|
| 🇹🇼 台湾 | 台, tw, taiwan, TW, Taiwan |
| 🇭🇰 香港 | 港, hk, hongkong, HK, HongKong |
| 🇯🇵 日本 | 日, jp, japan, JP, Japan |
| 🇸🇬 新加坡 | 新, sg, singapore, SG, Singapore |
| 🇰🇷 韩国 | 韩, 🇰🇷, KR, Korea |
| 🇷🇺 俄罗斯 | 🇷🇺, RU, 俄罗斯, Russia |
| 🇨🇦 加拿大 | 🇨🇦, CA, 加拿大, Canada |
| 🇺🇸 美国 | 美, us, unitedstates, US, USA |
| 🇬🇧 英国 | 🇬🇧, GB, 英国, UK, Britain |
| 🇫🇷 法国 | 🇫🇷, FR, 法国, France |
| 🇩🇪 德国 | 🇩🇪, DE, 德国, Germany |
| 🇧🇷 巴西 | 🇧🇷, BR, 巴西, Brazil |
| 🇳🇱 荷兰 | 🇳🇱, NL, 荷兰, Netherlands |

不匹配任何地区的节点归入"🚞 其它地区"。

## 🛠️ systemd 服务配置

创建 `/etc/systemd/system/singbox.service`：

```ini
[Unit]
Description=sing-box Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/sing-box run -c /path/to/config.json
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable singbox
sudo systemctl start singbox
sudo systemctl status singbox
```

## 🔍 常用命令

```bash
# 检查配置
sing-box check -c conf/config.json

# 运行服务
sing-box run -c conf/config.json

# 格式化配置
sing-box format -c conf/config.json -w

# 查看版本
sing-box version

# 更新订阅
./update_subscription.sh

# 查看日志
journalctl -u singbox -f
```

## 🐛 故障排查

### 订阅更新失败

1. 检查订阅地址是否正确
2. 检查网络连接
3. 查看错误日志

### 配置验证失败

1. 运行 `sing-box check -c conf/config.json`
2. 检查节点格式是否正确
3. 确保使用运行时配置（非模板）

### API 无法访问

1. 检查服务是否运行
2. 检查端口是否被占用：`netstat -tlnp | grep 9090`
3. 检查防火墙设置

### 面板无法打开

1. 确认 `ui` 目录存在且包含面板文件
2. 检查 `external_ui` 配置路径
3. 确认 API 服务正常

## 📦 相关项目

- [gwf](https://github.com/iflyelf/gwf) - Clash 规则集转换为 sing-box 格式

## 📄 许可证

MIT License
