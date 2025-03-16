# TopRepo

TopRepo 是一个自动跟踪 GitHub 上最热门和增长最快的仓库的工具。

## 功能

- 🔥 每日抓取 GitHub trending 仓库
- 📊 展示最热门和增长最快的项目
- 📝 自动更新 GitHub README
- 📧 邮件订阅服务，接收每日更新

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/TopRepo.git
cd TopRepo

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 GitHub token 和邮件配置
```

## 使用方法

### 运行数据抓取

```bash
python src/fetch_trending.py
```

### 启动网站

```bash
python src/app.py
```

### 设置自动更新

可以使用 GitHub Actions 或 cron job 设置自动更新。

## 订阅服务

访问网站，输入您的邮箱地址进行订阅，每天将收到最新的 trending repos 信息。

## GitHub 热门项目

<!-- TRENDING_REPOS_START -->

*更新时间: 2023-11-01 00:00:00*

### 最新热门仓库

| 排名 | 仓库 | 语言 | ⭐ 星标 | 描述 |
|------|------|------|---------|------|
| 1 | [username/repo1](https://github.com/username/repo1) | JavaScript | 1000 | 示例仓库1描述 |
| 2 | [username/repo2](https://github.com/username/repo2) | Python | 900 | 示例仓库2描述 |
| 3 | [username/repo3](https://github.com/username/repo3) | TypeScript | 800 | 示例仓库3描述 |
| 4 | [username/repo4](https://github.com/username/repo4) | Go | 700 | 示例仓库4描述 |
| 5 | [username/repo5](https://github.com/username/repo5) | Rust | 600 | 示例仓库5描述 |

### 增长最快的仓库

| 排名 | 仓库 | 语言 | ⭐ 星标 | 增长率 | 新增星标 |
|------|------|------|---------|---------|----------|
| 1 | [username/repo6](https://github.com/username/repo6) | JavaScript | 5000 | 50.00% | +1000 |
| 2 | [username/repo7](https://github.com/username/repo7) | Python | 4000 | 40.00% | +800 |
| 3 | [username/repo8](https://github.com/username/repo8) | TypeScript | 3000 | 30.00% | +600 |
| 4 | [username/repo9](https://github.com/username/repo9) | Go | 2000 | 20.00% | +400 |
| 5 | [username/repo10](https://github.com/username/repo10) | Rust | 1000 | 10.00% | +200 |

<!-- TRENDING_REPOS_END -->

## 许可证

MIT