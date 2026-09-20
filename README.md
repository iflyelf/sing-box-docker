# sing-box-docker

[sing-box](https://github.com/SagerNet/sing-box) 通用代理平台镜像，用 supervisor 守护多协议 inbound
（vmess / trojan / hysteria2 等）。采用多阶段构建，运行镜像更小。

支持 `linux/amd64` 与 `linux/arm64` 多架构，标签为 `latest`。

## 多阶段构建

| 阶段 | 基础镜像 | 作用 |
| --- | --- | --- |
| builder | `iflyelf/ubuntu:latest` | 已预装 Go 及完整工具链，无需再装 Go 与庞大依赖，直接在 BUILDPLATFORM 上交叉编译 sing-box 静态二进制（`CGO_ENABLED=0`），构建更快更稳 |
| runtime | `iflyelf/ubuntu:lite` | sing-box 为静态二进制，仅需 supervisor / iptables / ca-certificates，镜像更小 |

运行阶段按需安装：`supervisor`（进程守护）、`iptables`（tun/透明代理场景）、`ca-certificates`（ACME/TLS 根证书）。
入口使用 tini 作为 init。sing-box 静态编译无动态库依赖，故运行阶段无需额外共享库。

## 镜像获取

```bash
# Docker Hub（国外）
docker pull iflyelf/sing-box:latest

# 华为云 SWR（国内推荐）
docker pull swr.cn-east-3.myhuaweicloud.com/iflyelf/sing-box:latest
```

## 运行

推荐使用仓库内的 `docker-compose.yml`（需按需配置环境变量），或手动运行：

```bash
docker run -d --name sing-box \
  --privileged \
  --device /dev/net/tun \
  -e VMESS_PORT=... -e VMESS_UUID=... -e VMESS_NAME=... -e VMESS_ALTER_ID=0 -e VMESS_WSPATH=... \
  -e TROJAN_PORT=... -e TROJAN_PWD=... -e TROJAN_NAME=... -e TROJAN_WSPATH=... \
  iflyelf/sing-box:latest
```

入口脚本 `docker-entrypoint.sh` 会依据环境变量生成 `/etc/sing-box/*.json`，再由 supervisor 拉起各 inbound。

## 编译特性（build tags）

`with_gvisor`、`with_quic`、`with_dhcp`、`with_wireguard`、`with_utls`、`with_acme`、
`with_clash_api`、`with_tailscale`、`with_ccm`、`with_ocm` 等。

## 自动构建

以下情况会触发 [GitHub Actions](./.github/workflows/docker-publish.yml) 构建并推送到 Docker Hub 与华为云 SWR：

- 推送 `Dockerfile`、`conf/**`、`docker-entrypoint.sh` 或工作流文件变更
- 手动触发（workflow_dispatch）
- Star 仓库
- 定时构建：**中国时间每天早 5 点**（UTC 21:00）

同一分支仅保留最新一次构建（`concurrency` + `cancel-in-progress`），避免多架构构建并发堆积。

### VERSION 自动更新

[update-version.yml](./.github/workflows/update-version.yml) 每天中国时间早 4 点调用 GitHub API
获取 sing-box 最新**正式版**（`/releases/latest` 自动排除 alpha / beta / rc 预发布，并二次校验），
若与 Dockerfile 中的 `SINGBOX_VERSION` 不同则自动更新并提交，进而触发镜像重建。

### 所需 Secrets

| Secret | 说明 |
| --- | --- |
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | Docker Hub 凭据 |
| `SWR_USERNAME` / `SWR_PASSWORD` | 华为云 SWR 登录凭据（`区域@AK` / 登录密钥） |
| `SWR_AK` / `SWR_SK` | 华为云账号 AK/SK，用于将 SWR 仓库设为公开（可选） |
