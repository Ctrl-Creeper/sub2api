# 上游 Release 自动同步

`sync-upstream-release.yml` 每小时的第 17 分钟检查
[`Wei-Shaw/sub2api`](https://github.com/Wei-Shaw/sub2api) 的最新正式 Release。
GitHub 定时任务可能延迟；fork 不会直接收到上游的 `release` 事件。
首次启用时会同步当前最新正式版。预发布版本不自动同步，可手动指定其标签。
如果一次检查间出现多个版本，自动跟进当时最新的正式版。

## 启用

1. 将 BNDS 前端改动、此目录和两个工作流一起提交到 fork 的默认分支。
   自动构建只会使用已提交的前端，无法包含电脑上的未提交文件。
2. 在 fork 的 **Actions** 页面启用工作流，在 **Settings → General → Features**
   开启 **Issues**。当前仓库已经启用 Actions 和 Issues。
3. 如果默认分支有保护规则，为同步机器人配置允许推送的权限。
   工作流使用 `GITHUB_TOKEN`，按 job 声明 `contents`、`packages`、`issues` 权限。
   若上游更改 `.github/workflows/`，同步推送需要有工作流写权限的令牌：
   设置仓库 Secret **`UPSTREAM_SYNC_TOKEN`**，使用只允许此 fork 的 fine-grained PAT，
   授予 **Contents: Read and write**、**Workflows: Read and write**。
   使用 classic PAT 时需要 `repo`、`workflow` scopes。
   不配置时使用 `GITHUB_TOKEN`；权限不足会报错并开 Issue，不会忽略上游改动。
4. **Actions → Sync upstream release → Run workflow** 可立即运行。
   `tag` 留空代表最新正式版，也可填 `v0.2.13` 等**上游**已发布版本。
   `revision` 留空时新上游版本从 `1` 开始，已完成版本跳过，未完成版本沿用原标签。
   修改前端并提交后，填 `revision=next` 可为同一上游生成下一个修订号；也可填
   正整数（如 `2`）。存在未完成修订时先重试它，不会自动跳过并新增版本。

正常情况下不需要 DockerHub 凭据：发布到 fork 自己的 GitHub Releases 和
`ghcr.io/ctrl-creeper/sub2api`。已有 DockerHub 配置继续生效。
默认沿用完整 Release 矩阵，包括二进制、校验和及 amd64/arm64 镜像。
已有仓库变量 `SIMPLE_RELEASE=true` 会继续覆盖为精简发布；需要完整产物时删除它
或设为 `false`。

## 同步及发布方式

- 上游标签获取到独立的 `refs/upstream-release/`，不导入或覆盖 fork 标签。
- 对默认分支进行正常三方合并。没有 `ours` 策略，也不会整体替换前端目录；
  无冲突的上游功能改动和 BNDS 定制会一起保留，冲突留待人工处理。
  `VERSION` 是生成的版本元数据，其冲突按本次 fork 标签重写；其他文件仍需人工解决。
- 更新 `backend/cmd/server/VERSION`，提交同步记录
  `.github/upstream-sync/state.json`，在 fork 的提交创建 `上游标号-修订号` 标签。
  例如上游 `v0.2.14` 对应 fork `v0.2.14-1`，修订号从 `1` 开始。
  记录分别保存 `upstream_tag`、fork `tag`、`revision` 和上游提交，源标签不会被混用。
- 默认分支和标签使用原子推送，不强制推送。
- 直接调用可复用的 `release.yml` 构建并发布该标签。
  `GITHUB_TOKEN` 推送不会触发另一个 tag workflow，故不依赖 tag push 事件。
  使用 PAT 时 tag push 会触发 Release，但计划阶段会识别同步记录并跳过，
  避免和可复用调用重复发布。
- 发布成功后记录完成状态并关闭同步告警 Issue。重复检查不会重建已完成版本。
  并发组串行化整个同步/发布周期，防止多个同步任务争抢标签及 `latest` 镜像。

`release.yml` 原有的标签推送、手动发布和 dry run 入口继续可用；发布标签必须符合 fork 命名。
自动发布使用 fork 的标签和 Release 信息，例如 `v0.2.14-1 · BNDS AI普及计划`。
应用版本、镜像版本和压缩包文件名统一使用 `0.2.14-1`（不带 `v`）。
数字修订后缀属于正式版本，可被 GitHub latest 及网页自动更新找到。
手动同步上游预发布 `v0.2.14-rc1` 会生成 `v0.2.14-rc1-1`，仍标为预发布，
不会覆盖正式版的 `latest`、大版本及次版本镜像标签。标签说明包含上游
Release URL、上游提交和 BNDS 前端说明。

## 通知与处理冲突

冲突、权限错误、构建或发布失败都会创建一个 **`[Upstream sync] ... needs attention`**
Issue，附 Actions 链接、失败 job 和冲突文件。默认提及仓库所有者
`@Ctrl-Creeper`，通过 GitHub 的通知/邮件设置接收提醒。

可选仓库变量 **`UPSTREAM_SYNC_NOTIFY_USERS`** 支持以逗号分隔的 GitHub 用户名。
已有 **`TELEGRAM_BOT_TOKEN`** 和 **`TELEGRAM_CHAT_ID`** 时，也会发送 Telegram 提醒；
未配置时不需要 Telegram。GitHub Issue 是主要通知，Telegram 发送失败不影响它。

同一告警会更新现有 Issue，后续定时运行会暂停，避免每小时重复提醒。
手动运行可重试。失败报告 `upstream-sync-report` 作为 Actions artifact 保留 14 天。
若 Issue 通知本身失败，Actions 的失败状态仍会保留；检查仓库 Issues 和权限设置。

遇到合并冲突：

```bash
git checkout main
git pull --ff-only origin main
git fetch --no-tags upstream refs/tags/v0.2.14:refs/upstream-release/v0.2.14
git merge --no-ff refs/upstream-release/v0.2.14
# 解决冲突，保留 BNDS 品牌、配色和当前交互，检查上游新增功能。
git add <已解决的文件>
git commit
git push origin main
```

然后在 Actions 手动运行 `Sync upstream release`，指定同一个版本；成功后告警
自动关闭。请确认本地已经配置了 `upstream` remote。

构建在推送同步提交和标签后执行，构建失败时保留它们，方便定位和重试。
临时基础设施失败可直接手动重试同一版本，使用原标签提交。
若必须修改代码，先提交修复；检查确认该标签**尚未发布 Release**后，人工删除
未发布标签再重试，自动流程会在包含修复的新提交创建它。已有发布版本或
非此自动流程创建的标签会阻止自动覆盖，需要人工确认。

## 本地验证

```bash
python3 -m unittest discover -s .github/upstream-sync -p 'test_*.py'
python3 -m unittest discover -s .github/release-tools -p 'test_release_matrix.py'
actionlint .github/workflows/sync-upstream-release.yml .github/workflows/release.yml
```

测试使用临时 Git 仓库及模拟 API，不会推送到 GitHub、创建 Issue 或发布产物。
