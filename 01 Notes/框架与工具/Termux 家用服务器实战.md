---
title: Termux 家用服务器实战（小米10）
date: 2026-10-07
tags:
  - Termux
  - Android
  - 家用服务器
  - 框架与工具
type: note
aliases:
  - 手机当服务器
  - Termux 服务器
---

# Termux 家用服务器实战（小米10）

> [!abstract] 一句话
> Termux 是一个**不需要 root 的 Android Linux 终端**：它有完整的包管理器（`pkg`）和 runit 服务管理器（termux-services）。配上小米10 的骁龙865 + 8-12GB 内存 + 256GB 存储，你就得到一台**7×24 插电待机的 ARM 局域网服务器**。

参考：[Termux Wiki](https://wiki.termux.com/wiki/Main_Page) · [termux-services（服务表/端口）](https://wiki.termux.com/wiki/Termux-services) · [Termux:Boot](https://wiki.termux.dev/wiki/Termux:Boot)

---

## 0. 它能干什么（先看能力表）

| 能力 | 用什么 | 端口 | 生活里的样子 |
|---|---|---|---|
| 远程终端 / SFTP | openssh `sshd` | 8022 | 电脑上像操作 Linux 一样操作手机，也能当私有网盘拖文件 |
| 文件双向同步 | syncthing | 8384 | Obsidian 库 手机↔电脑↔NAS 三向同步，不依赖云盘 |
| Web 服务 | lighttpd / nginx / apache2 | 8080 | 跑自己的 Node/Python 接口、静态页面、下载面板 |
| 下载机 | aria2 / transmission | 6800 / 9091 | 关屏挂机下载、挂 BT 做种 |
| 媒体服务 | rclone serve dlna / mpd | 8082 | 电视、投影直接播手机里的片子；手机变音乐服务器 |
| 定时任务 | cronie `crond` | — | 定时备份、爬虫、签到、日报，跑完用手机通知你 |
| 消息/传感器中继 | mosquitto（MQTT） | 1883 | 家里 MQTT 中枢；手机当传感器 + 通知网关 |
| 数据库 | mariadb / postgresql | 3306 / 5432 | 给上面的服务当后端 |
| 私有云盘级应用 | proot-distro + Debian | — | Gitea、qBittorrent-nox、AdGuard Home 等重量级应用 |

---

## 1. 安装与保活（最关键的一步，10 分钟）

### 1.1 装对版本

- **从 [F-Droid](https://f-droid.org/packages/com.termux/) 或 [GitHub Releases](https://github.com/termux/termux-app/releases) 安装**。
- ⚠️ **不要装 Google Play 版**，那个仓库已停止维护（[termux-play-store](https://github.com/termux-play-store)）。F-Droid 版才能正常执行自编译程序。
- 可选附加 App（同一来源，一次性）：
  - **Termux:Boot** → 开机自动拉起服务（做服务器必备）
  - **Termux:API** → 让脚本发通知、读电量温度、震动、剪贴板
  - **Termux:Widget** → 桌面一键执行脚本

### 1.2 首次进入必做

```bash
pkg update && pkg upgrade
termux-setup-storage        # 授权存储，之后 ~/storage/shared 就是手机 /sdcard
pkg install git openssh nano htop termux-services
termux-wake-lock            # 拿住唤醒锁，息屏后不被杀
```

### 1.3 系统层设置（MIUI 抽风的地方）

| 设置 | 位置 | 作用 |
|---|---|---|
| 电池 → 无限制 / 关闭电池优化 | 设置 → 应用 → Termux → 省电策略 | 防止后台被冻结 |
| 允许自启动 | MIUI 设置 → 应用管理 → Termux | 否则 Termux:Boot 拉不起来 |
| 最近任务里「锁定」Termux | 多任务卡片下拉/长按锁 | 一键清理时不被杀掉 |
| 充电时不锁定屏幕 | 开发者选项 | 常亮调试/看日志用 |
| 固定局域网 IP | 路由器 DHCP 静态分配 | 否则 IP 变了 ssh 连不上 |
| 关掉「优化电池充电」之类冲突项 | 若同时用 AccA 限充 | 避免两套充电控制打架 |

查 IP：`ifconfig wlan0`（`pkg install net-tools`）或直接在 设置 → WLAN → 详情 里看。

> [!warning] 插电常驻 = 电池风险
> 长期满电高温会鼓包。用 MIUI「充电保护」或 root 后 **AccA 限充到 70%**；取下手机壳，别放在床上/路由上，每季度检查后盖是否翘起。

---

## 2. 六个核心能力，逐个落地

### 2.1 SSH：一切的地基

```bash
pkg install openssh
sshd                 # 临时启动（默认端口 8022）
whoami               # 拿到用户名，形如 u0_a123
passwd               # 想用密码登录就设一个
sv-enable sshd       # 让它常驻（termux-services）
sv status sshd       # 查状态
```

电脑端连接：

```bash
ssh -p 8022 u0_a123@192.168.1.50
ssh-keygen -t ed25519                       # 电脑上生成密钥（若没有）
ssh-copy-id -p 8022 u0_a123@192.168.1.50    # 免密登录
sftp -P 8022 u0_a123@192.168.1.50           # 文件传输
```

WinSCP / FileZilla / 系统自带的资源管理器都能连 SFTP → **这就是最省事的私有网盘**。

### 2.2 Syncthing：给你的 Obsidian 库做三向同步（最推荐）

```bash
pkg install syncthing
syncthing            # 首次运行生成设备 ID，Web 界面 http://127.0.0.1:8384
```

流程：手机浏览器打开 `127.0.0.1:8384` → 添加电脑的设备 ID 配对 → 共享目录填
`/data/data/com.termux/files/home/storage/shared/你的库路径`。
电脑端装 Syncthing，把 vault 目录共享出来，就完成 **手机 ↔ 电脑 ↔ NAS** 的直连同步，全程不经过云盘。

> [!note] 和 Obsidian Git 的关系
> Obsidian 的 Git 插件底层是 https 协议，**不支持 ssh 远程**，所以别指望手机当 vault 的 git remote。库同步用 **Syncthing**；git 只负责版本历史（本地或 PC 端推远端仓库）最省心。

### 2.3 文件服务 / 私有网盘（按场景选）

```bash
# 临时分享一个目录（最简单，传完 Ctrl+C 就关）
python -m http.server 8080 --directory ~/storage/shared/Downloads

# rclone 万能服务：WebDAV / DLNA / FTP / SMB 都能开
pkg install rclone
rclone serve webdav ~/storage/shared --addr :8081 --user me --pass 你的密码
rclone serve dlna   ~/storage/shared/Movies --addr :8082   # 电视/投影直接看

# 常驻 Web 服务
pkg install lighttpd && sv-enable lighttpd   # 端口 8080
# 站点根目录/端口看 $PREFIX/etc/lighttpd/lighttpd.conf
```

### 2.4 下载机：aria2 / transmission / yt-dlp

```bash
pkg install aria2 yt-dlp transmission
aria2c --enable-rpc --rpc-listen-all --dir ~/storage/shared/Downloads   # RPC 默认 6800
sv-enable transmission    # Web UI: http://手机IP:9091（先改 settings.json 里的认证）
```

- 加个 **AriaNg** 静态页面（丢给 lighttpd 托管），手机和电脑浏览器都能远程丢链接进去。
- `yt-dlp` 配合 crontab 订阅式下载；`--cookies` 可搬浏览器登录态。
- 关屏继续跑的前提还是：`termux-wake-lock` + 关闭电池优化 + 插电。

### 2.5 定时任务：crond

```bash
pkg install cronie
sv-enable crond
crontab -e
```

```cron
# 每天 3:30 备份 Obsidian 库（脚本里写全路径！crontab 的 PATH 不含 $PREFIX/bin）
30 3 * * * /data/data/com.termux/files/home/bin/backup.sh >> /data/data/com.termux/files/home/logs/backup.log 2>&1
# 每 2 小时心跳通知，验证手机还活着
0 */2 * * * /data/data/com.termux/files/usr/bin/termux-notification -c "NAS 心跳正常"
```

配合 **Termux:API**（App + `pkg install termux-api`）：

```bash
termux-battery-status | jq .percentage,.temperature   # 电池监测，鼓包预警
termux-notification --title "备份完成" --content "12 个文件已同步"
```

> [!caution] Doze 会延迟任务
> Android 打瞌睡时 cron 可能晚几分钟甚至更久。备份、爬虫这类"迟到没关系"的任务适合；秒级精度的定时不要指望它。

### 2.6 跑自己的服务：这就是真实的"部署上线"

```bash
pkg install nodejs-lts python
mkdir -p ~/apps && cd ~/apps
node server.js &                 # 局域网访问 http://192.168.1.50:3000
```

- 想常驻：写一个 run 脚本放进 `$PREFIX/var/service/<名字>/run`，再 `sv up <名字>`（方法见 [termux-services](https://wiki.termux.com/wiki/Termux-services)）。
- 或 `nohup node server.js > ~/logs/app.log 2>&1 &`；`npm i -g pm2` 若在 ARM 上编译失败就退回前两种。
- **这正是 [[02 Projects/Nodejs 后端实战学习计划/README|Node 后端实战学习计划]] S8「部署与上线」最便宜的真实环境**：本机写代码 → `rsync`/`scp` 推上手机 → 局域网真实访问 → 观察日志、进程、内存。

---

## 3. 进阶：proot-distro 装 Debian，什么都有

```bash
pkg install proot-distro
proot-distro install debian
proot-distro login debian
# 进去就是标准 Debian：apt install nginx gitea qbittorrent-nox ...
```

Termux 原仓库没打包的重型应用（Gitea 私有 Git、qBittorrent-nox、AdGuard Home 等）都可以这么装，性能损耗大概 5%~15%，跑服务基本无感。

---

## 4. 十个真实应用场景

| # | 场景 | 组合 | 价值 |
|---|---|---|---|
| 1 | **私有网盘 / 文件仓** | sshd + SFTP | 家里几台设备互传，不经过任何云端 |
| 2 | **Obsidian 库三向同步** | Syncthing | 手机随时改笔记，回电脑自动合并 |
| 3 | **电脑数据的第二份离线备份** | crond + rsync/rclone 定时从 PC 拉取 | 勒索病毒/误删时的兜底 |
| 4 | **7×24 下载机 + 做种** | aria2 / transmission + AriaNg | 关屏挂机，手机变下载盒 |
| 5 | **局域网练习服务器** | Node/Python + termux-services | 后端计划的真实部署靶场 |
| 6 | **定时爬虫 / 签到 / 日报** | crond + Python + termux-notification | 跑完直接在手机上收通知 |
| 7 | **电视/投影的媒体库** | `rclone serve dlna` | 老电视秒变智能电视，不买盒子 |
| 8 | **家庭自动化中枢** | mosquitto（MQTT, 1883） | 自建 MQTT，比公有云可控 |
| 9 | **短信/通知/传感器网关** | Termux:API + termux-api | 电量温度监控、通知转发、离家自动执行 |
| 10 | **大文件局域网直传** | `python -m http.server` | 几个 G 的 ISO 秒传，传完就关 |

---

## 5. 常见坑清单

1. **Play 版 Termux 不能用** → 只用 F-Droid / GitHub。
2. **息屏就断** → wake lock + 关闭电池优化 + MIUI 自启动，三缺一必失败。
3. **重启后服务不见** → 装 **Termux:Boot**，在里面放启动脚本（先手动打开一次该 App）。
4. **crontab 里命令找不到** → 写绝对路径或脚本头部 `export PATH=$PREFIX/bin:$PATH`。
5. **端口不要暴露到公网**：8022 / 8384 / 8080 只在内网用；要外网访问优先走路由器 VPN（WireGuard），不要直接端口转发（Termux 里 Tailscale 一类需要 TUN 设备，通常要 root）。
6. **电池与散热**：限充 70%、取壳、通风、每季度查鼓包。
7. **别把 SD 卡路径写死**：统一用 `~/storage/shared`，换机/换 ROM 后仍有效。
8. **同一目录别双写**：Syncthing + 云盘客户端同时管一个目录会产生 `.sync-conflict` 冲突文件。

---

## 6. 30 分钟照抄清单

- [ ] F-Droid 安装 Termux + Termux:Boot + Termux:API
- [ ] `pkg update && pkg upgrade`，`termux-setup-storage`
- [ ] `pkg install openssh termux-services rclone syncthing aria2 git nano htop cronie python nodejs-lts`
- [ ] 重启 Termux，`sshd` / `whoami` / `passwd`
- [ ] `sv-enable sshd`，电脑端 `ssh -p 8022 u0_a***@IP` 连上
- [ ] `ssh-copy-id` 配密钥免密 + 路由器固定 IP
- [ ] MIUI 三件套：无限制省电、允许自启动、锁定任务卡
- [ ] `termux-wake-lock`；写一个 `~/bin/boot.sh` 供 Termux:Boot 调起
- [ ] 跑 Syncthing，把 Obsidian 库同步起来
- [ ] `sv-enable crond` + 一条备份/心跳任务，验证 termux-notification 能弹出来
- [ ] 挂一个 aria2 下载任务，息屏 30 分钟回来检查是否还在跑
- [ ] 最后设定限充与散热规矩
