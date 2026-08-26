#############################
#     设置公共的变量         #
#############################
FROM --platform=$BUILDPLATFORM ubuntu:resolute AS builder
# 作者描述信息
LABEL maintainer="iflyelf"
# 时区设置
ARG TZ=Asia/Shanghai
ENV TZ=$TZ
# 语言设置
ARG LANG=zh_CN.UTF-8
ENV LANG=$LANG

# 环境设置
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=$DEBIAN_FRONTEND

# GO环境变量
ARG GO_VERSION=1.25.5
ENV GO_VERSION=$GO_VERSION
ARG GOROOT=/opt/go
ENV GOROOT=$GOROOT
ARG GOPATH=/opt/golang
ENV GOPATH=$GOPATH
ENV PATH=$PATH:$GOROOT/bin:$GOPATH/bin

# ***** 设置变量 *****

# GO环境变量
ARG TARGETOS TARGETARCH
ARG GO111MODULE=on
ENV GO111MODULE=$GO111MODULE
ARG CGO_ENABLED=0
ENV CGO_ENABLED=$CGO_ENABLED
ENV GOOS=$TARGETOS
ENV GOARCH=$TARGETARCH

# 源文件下载路径
ARG DOWNLOAD_SRC=/tmp/src
ENV DOWNLOAD_SRC=$DOWNLOAD_SRC

# SINGBOX版本
ARG SINGBOX_VERSION=v1.13.19
ENV SINGBOX_VERSION=$SINGBOX_VERSION

# 安装依赖包
ARG PKG_DEPS="\
    zsh \
    bash \
    bash-doc \
    bash-completion \
    bind9-dnsutils \
    iproute2 \
    net-tools \
    fping \
    sysstat \
    ncat \
    git \
    sudo \
    dmidecode \
    util-linux \
    vim \
    jq \
    lrzsz \
    tzdata \
    curl \
    wget \
    axel \
    lsof \
    zip \
    unzip \
    tar \
    rsync \
    iputils-ping \
    telnet \
    procps \
    libaio1t64 \
    numactl \
    xz-utils \
    gnupg2 \
    psmisc \
    libmecab2 \
    debsums \
    locales \
    build-essential \
    pkg-config \
    cmake \
    ca-certificates"
ENV PKG_DEPS=$PKG_DEPS

# ***** 安装依赖 *****
RUN --mount=type=cache,target=/var/lib/apt/,sharing=locked \
   set -eux && \
   # 更新源地址
   sed -i 's@URIs: http://[a-z.]*\.ubuntu\.com/ubuntu/@URIs: https://mirrors.aliyun.com/ubuntu/@g' /etc/apt/sources.list.d/ubuntu.sources && \
   sed -i 's@^Types: deb$@Types: deb deb-src@' /etc/apt/sources.list.d/ubuntu.sources && \
   # 解决证书认证失败问题
   touch /etc/apt/apt.conf.d/99verify-peer.conf && echo >>/etc/apt/apt.conf.d/99verify-peer.conf "Acquire { https::Verify-Peer false }" && \
   # 更新系统软件
   DEBIAN_FRONTEND=noninteractive apt update -qqy && apt upgrade -qqy && \
   # 安装依赖包
   DEBIAN_FRONTEND=noninteractive apt install -qqy --no-install-recommends $PKG_DEPS --option=Dpkg::Options::=--force-confdef && \
   DEBIAN_FRONTEND=noninteractive apt -qqy --no-install-recommends autoremove --purge && \
   DEBIAN_FRONTEND=noninteractive apt -qqy --no-install-recommends autoclean && \
   rm -rf /var/lib/apt/lists/* && \
   # 更新时区
   ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime && \
   # 更新时间
   echo ${TZ} > /etc/timezone

# ***** 安装golang *****
RUN set -eux && \
    wget --no-check-certificate https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz -O /tmp/go${GO_VERSION}.linux-amd64.tar.gz && \
    cd /tmp/ && tar zxvf go${GO_VERSION}.linux-amd64.tar.gz -C /opt && \
    mkdir -pv $GOPATH/bin $GOPATH/src $GOPATH/pkg && \
    ln -sf /opt/go/bin/go /usr/bin/go && \
    ln -sf /opt/go/bin/gofmt /usr/bin/gofmt && \
    go version


# ***** 安装依赖并构建二进制文件 *****
RUN --mount=type=cache,target=/root/.cache/go-build \
   --mount=type=cache,target=/opt/golang/pkg/mod \
   set -eux && \
   go version && \
   go env && \
   # 克隆源码运行安装
   git clone -b $SINGBOX_VERSION --progress https://github.com/SagerNet/sing-box.git /src && \
   cd /src && \
   export COMMIT=$(git rev-parse --short HEAD) && \
   export VERSION=$(go run ./cmd/internal/read_tag) && \
   go env -w GO111MODULE=on && \
   go env -w CGO_ENABLED=0 && \
   go mod download && \
   go mod tidy && \
   mkdir -p /go/bin && \
   go build -v -trimpath -tags 'with_gvisor,with_quic,with_dhcp,with_wireguard,with_utls,with_acme,with_clash_api,with_tailscale,with_ccm,with_ocm,badlinkname,tfogo_checklinkname0' \
        -o /go/bin/sing-box \
        -ldflags "-s -buildid= -X \"github.com/sagernet/sing-box/constant.Version=$VERSION\" -checklinkname=0" \
        ./cmd/sing-box && \
   ls -lh /go/bin/sing-box


##########################################
#         构建基础镜像                    #
##########################################
#

FROM ubuntu:resolute

# 作者描述信息
LABEL maintainer="iflyelf"
# 时区设置
ARG TZ=Asia/Shanghai
ENV TZ=$TZ
# 语言设置
ARG LANG=zh_CN.UTF-8
ENV LANG=$LANG

# 环境设置
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=$DEBIAN_FRONTEND

# 安装依赖包
ARG PKG_DEPS="\
    zsh \
    bash \
    bash-doc \
    bash-completion \
    bind9-dnsutils \
    iproute2 \
    net-tools \
    fping \
    sysstat \
    ncat \
    git \
    sudo \
    dmidecode \
    util-linux \
    vim \
    jq \
    lrzsz \
    tzdata \
    curl \
    wget \
    axel \
    lsof \
    zip \
    unzip \
    tar \
    rsync \
    iputils-ping \
    telnet \
    procps \
    libaio1t64 \
    numactl \
    xz-utils \
    gnupg2 \
    psmisc \
    libmecab2 \
    debsums \
    locales \
    iptables \
    language-pack-zh-hans \
    fonts-droid-fallback \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    supervisor \
    ca-certificates"
ENV PKG_DEPS=$PKG_DEPS


# ***** 安装依赖 *****
RUN --mount=type=cache,target=/var/lib/apt/,sharing=locked \
   set -eux && \
   # 更新源地址
   sed -i 's@URIs: http://[a-z.]*\.ubuntu\.com/ubuntu/@URIs: https://mirrors.aliyun.com/ubuntu/@g' /etc/apt/sources.list.d/ubuntu.sources && \
   sed -i 's@^Types: deb$@Types: deb deb-src@' /etc/apt/sources.list.d/ubuntu.sources && \
   # 解决证书认证失败问题
   touch /etc/apt/apt.conf.d/99verify-peer.conf && echo >>/etc/apt/apt.conf.d/99verify-peer.conf "Acquire { https::Verify-Peer false }" && \
   # 更新系统软件
   DEBIAN_FRONTEND=noninteractive apt update -qqy && apt upgrade -qqy && \
   # 安装依赖包
   DEBIAN_FRONTEND=noninteractive apt install -qqy --no-install-recommends $PKG_DEPS --option=Dpkg::Options::=--force-confdef && \
   DEBIAN_FRONTEND=noninteractive apt -qqy --no-install-recommends autoremove --purge && \
   DEBIAN_FRONTEND=noninteractive apt -qqy --no-install-recommends autoclean && \
   rm -rf /var/lib/apt/lists/* && \
   # 更新时区
   ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime && \
   # 更新时间
   echo ${TZ} > /etc/timezone && \
   # 更改为zsh
   sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || true && \
   sed -i -e "s/bin\/ash/bin\/zsh/" /etc/passwd && \
   # vim 默认配置文件存在时才关闭 mouse(不同版本路径不同, 用 find 定位)
   find /usr/share/vim -name defaults.vim -exec sed -i -e 's/mouse=/mouse-=/g' {} + && \
   locale-gen zh_CN.UTF-8 && localedef -f UTF-8 -i zh_CN zh_CN.UTF-8 && locale-gen

# 拷贝sing-box
COPY --from=builder /go/bin/sing-box /usr/bin/sing-box

# 拷贝文件
COPY ["./docker-entrypoint.sh", "/usr/bin/"]
COPY ["./conf/sing-box", "/etc/sing-box"]
COPY ["./conf/supervisor", "/etc/supervisor"]

# 授予文件权限
RUN set -eux && \
    mkdir -p /etc/sing-box && \
    chmod a+x /usr/bin/docker-entrypoint.sh /usr/bin/sing-box

# 容器信号处理
STOPSIGNAL SIGQUIT

# ***** 入口 *****
ENTRYPOINT ["docker-entrypoint.sh"]
