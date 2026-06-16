# Vercel 部署说明

这个版本保留原项目的在线聊天、生图页面、后台管理 API 和 OpenAI 兼容 API，并增加了 Vercel serverless 入口。

## 部署方式

1. Fork 或推送本仓库到 GitHub。
2. 在 Vercel 新建项目，Root Directory 选择仓库根目录。
3. Build Command 使用默认的 `npm run build`。
4. Output Directory 使用 `web_dist`。
5. 配置环境变量后部署。

## 必填环境变量

```bash
CHATGPT2API_AUTH_KEY=你的后台管理员密钥
STORAGE_BACKEND=postgres
DATABASE_URL=postgresql://user:password@host:5432/dbname
CHATGPT2API_BASE_URL=https://你的-vercel-域名
```

推荐使用 Neon、Supabase Postgres 或 Vercel Postgres。Vercel 文件系统不持久，不建议使用默认 `json` 或本地 `sqlite` 存储。

## 可选环境变量

```bash
DATA_DIR=/tmp/chatgpt2api
CONFIG_FILE=/tmp/chatgpt2api/config.json
```

在 Vercel 中如果不设置，项目会自动使用 `/tmp/chatgpt2api`。

## 可用入口

- 在线 Web：`/`
- 在线生图：`/image`
- 账号后台：`/accounts`
- 设置后台：`/settings`
- 登录：`/login`
- OpenAI 兼容 API：`/v1/*`
- 后台管理 API：`/api/*`
- 健康检查：`/health?format=json`

## 数据持久化

数据库后端会持久化：

- 账号池
- 用户 API key
- 后台设置
- 调用日志
- 图片任务状态
- CPA / sub2api / 注册配置

图片文件本身仍建议配置外部对象存储或 WebDAV。Vercel 的 `/tmp` 只能作为临时缓存，不适合长期保存图片。

## Serverless 注意事项

Vercel 函数不是常驻进程，后台线程和长任务可能被平台中断。同步 `/v1/images/generations`、`/v1/chat/completions` 可以直接使用；在线生图任务适合中短任务，超长轮询建议改到 Render、Railway、Fly.io 或 Docker 部署。

