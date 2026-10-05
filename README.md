# BNDS AI普及计划

让 AI 成为每个人的学习伙伴。

本仓库基于 [Sub2API](https://github.com/Wei-Shaw/sub2api) 维护，提供统一的 AI API
接入、API Key 管理、额度与用量查询。前端使用 BNDS 品牌及北京市十一学校 Logo
的橙红、黄、绿、蓝配色，并保留原有功能。

- 本仓库：[Ctrl-Creeper/sub2api](https://github.com/Ctrl-Creeper/sub2api)
- 发行版本：[Releases](https://github.com/Ctrl-Creeper/sub2api/releases)
- 容器镜像：`ghcr.io/ctrl-creeper/sub2api`

## 部署

推荐使用 Docker Compose，同时运行应用、PostgreSQL 和 Redis。
使用发行镜像前，需先在本 fork 完成一次 Release 构建。

```bash
git clone https://github.com/Ctrl-Creeper/sub2api.git
cd sub2api/deploy
cp .env.example .env
chmod 600 .env
```

编辑 `.env`，至少配置以下内容。可用 `openssl rand -hex 32` 分别生成数据库密码、
JWT 密钥和 TOTP 加密密钥，并保存好这些值。

| 配置 | 用途 |
| --- | --- |
| `POSTGRES_PASSWORD` | 数据库密码，替换示例值 |
| `JWT_SECRET` | 固定登录签名密钥 |
| `TOTP_ENCRYPTION_KEY` | 固定双重验证加密密钥 |
| `ADMIN_EMAIL`、`ADMIN_PASSWORD` | 首次启动创建的管理员账号 |
| `SERVER_PORT` | 网站端口，默认 `8080` |

```bash
docker compose -f docker-compose.local.yml up -d
docker compose -f docker-compose.local.yml logs -f sub2api
```

访问 `http://服务器地址:8080`。数据保存在 `deploy/data`、`deploy/postgres_data`
和 `deploy/redis_data`。公网访问建议通过反向代理配置 HTTPS。

Linux 二进制安装也可使用本 fork 的安装脚本（需要 Bash 4+）：

```bash
curl -fsSL https://raw.githubusercontent.com/Ctrl-Creeper/sub2api/main/deploy/install.sh -o install.sh
sudo bash install.sh
```

详细配置见 [部署说明](deploy/README.md) 和 [配置示例](deploy/config.example.yaml)。

## 更新

网页中的版本检查、二进制更新和回滚均使用 **本 fork 的 Releases**。
容器部署通过拉取本 fork 镜像更新；升级前备份数据库及配置。

```bash
cd sub2api/deploy
docker compose -f docker-compose.local.yml pull
docker compose -f docker-compose.local.yml up -d
```

可将 Compose 中的镜像固定为 `ghcr.io/ctrl-creeper/sub2api:版本号`，以便控制升级
和回滚。镜像版本不带 `v` 前缀，例如 `0.2.13-1`。不要改用上游镜像，否则会失去
BNDS 前端。二进制安装可使用网页更新或 `sudo bash install.sh upgrade`。

## 上游同步与自动发布

`Sync upstream release` 工作流每小时检查上游最新正式 Release，正常合并上游
源码并保留 BNDS 定制，在本 fork 创建版本标签并构建二进制、校验和及容器镜像。

版本统一为 **上游标号-本仓库修订号**，修订号从 `1` 开始：

| 用途 | 示例 |
| --- | --- |
| 上游版本 | `v0.2.14` |
| 本仓库标签 / Release | `v0.2.14-1` / `v0.2.14-1 · BNDS AI普及计划` |
| 应用版本 / 镜像标签 | `0.2.14-1` |
| 二进制包 | `sub2api_0.2.14-1_linux_amd64.tar.gz` |

同一上游版本修改前端后，手动运行同步工作流，`tag` 填上游标号、`revision` 填
`next`，即可发布 `-2`、`-3`；也可指定正整数修订号。新上游版本重新从 `-1`
开始。定时检查不会不断增加修订号；失败重试沿用原标签。网页更新和回滚也按
数字比较修订号，例如 `-10` 高于 `-2`。

发生冲突或构建、发布失败时，工作流会创建 GitHub Issue 并提及维护者，暂停后续
自动同步。解决后可在 Actions 手动重试。初次启用会构建当前最新正式版。

前端和工作流必须提交到默认分支后才能生效。权限、通知和冲突处理步骤见
[上游同步说明](.github/upstream-sync/README.md)。上游仅作为源码同步来源，
部署和网页更新使用本 fork 的产物。

## 从源码构建

需要符合 [backend/go.mod](backend/go.mod) 的 Go 版本、Node.js 20 和 pnpm 9。
运行时需要 PostgreSQL、Redis，具体连接配置见部署目录。

```bash
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
cd backend
VERSION="$(./scripts/resolve-version.sh)"
CGO_ENABLED=0 go build -tags embed -trimpath -ldflags="-X main.Version=${VERSION}" -o bin/sub2api ./cmd/server
```

`-tags embed` 将 BNDS 前端打包进二进制。运行前配置数据库和 Redis，参考
`deploy/config.example.yaml`。手动源码构建保留 `source` 构建类型，发布构建由
Actions 完成。

## 来源与许可证

基于 Sub2API，感谢上游作者及贡献者。原项目 Copyright (c) 2026 Wesley Liddick。
遵循 [GNU LGPL v3.0 或更新版本](LICENSE)，保留原始许可证及版权声明。
