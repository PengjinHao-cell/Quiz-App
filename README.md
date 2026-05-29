<p align="center">
  <strong><a href="#简体中文">🇨🇳 简体中文</a></strong> · <strong>🇬🇧 English</strong> · <strong><a href="#繁體中文">🇭🇰 繁體中文</a></strong>
</p>

<hr>

<h2 id="简体中文">🇨🇳 简体中文</h2>

<h1 align="center">📝 刷题通 (Quiz Master) v1.2.1</h1>

<p align="center">
  <em>🎉 正式版发布 · 安全加固 · Railway 托管 · PostgreSQL 数据库</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">🌐 在线体验</a></strong><br>
  <sub>托管于 Railway，数据持久化存储</sub>
</p>

### ✨ 功能特性

**🔐 账号系统** — 邮箱验证码注册 · 登录/登出 · 访客模式 · 忘记密码找回 · 登录态保持 · 记住我 · 登录限流

**👤 个人中心** — 学习统计 · 收藏本 · 错题本 · 学习记录 · 设置（考试时长、语言切换、个人信息修改）

**🌐 中英文切换** — 系统界面全量翻译，题目原文不变

**📤 题库导入** — PDF/DOCX/TXT · AI 粘贴解析 · 内置题库 · 背单词

**🧠 三引擎识别** — 阅读格式 / 异形格式 / 标准格式自动判断

**📖 阅读理解** — 左右分栏 · 荧光笔 🖍 · 下划线 ＿ · 篇数选择 · 历史记录

**🧠 刷题模式** — 练习模式 · 考试模式（自定义时长）· 选项乱序 · 答题卡 · 快捷键 · 模态确认弹窗 · 选项位置稳定

**📊 学习工具** — 错题本 · 收藏 · 统计 · 记录 · 分享成绩 · 7日活跃趋势图

**🎨 体验** — Toast 通知 · 统一启动画面 · 搜题 · 响应式 · 公告横幅 · 密码强度指示条

### 🔐 安全说明

| 项目 | 详情 |
|------|------|
| **密码存储** | 使用 `pbkdf2:sha256` 哈希，绝不存储明文 |
| **密码传输** | 全程 HTTPS（Railway），POST JSON body，不经过 URL |
| **会话** | Flask 签名 Cookie（SECRET_KEY），`session_protection = "strong"`，可选"记住我"（14天） |
| **登录限流** | 同 IP 5 分钟内失败 5 次 → 冻结 5 分钟 |
| **验证码限流** | 同邮箱 10 分钟内错误 3 次 → 锁定；验证码 5 分钟过期 |
| **密钥强制** | 必须设置 `SECRET_KEY` 环境变量，生产环境使用默认值会拒绝启动 |
| **删除鉴权** | 服务端 `DELETE_PASSWORD` 环境变量验证，前端不再暴露密码 |
| **访客模式** | 无需注册，但答题数据公开可见 |
| **XSS 防护** | 全站 `escapeHTML()` 转义用户内容 |

### 🚀 快速开始

```bash
git clone https://github.com/PengjinHao-cell/Quiz-App.git
cd quiz-app
pip install -r requirements.txt
cp .env.example .env
# 填写 SECRET_KEY、DATABASE_URL 等
python3 app.py
# → http://localhost:5050
```

### 🌐 部署信息

项目托管于 **Railway**，使用 **PostgreSQL** 数据库。

在线地址：[quiz-app-production-9e7f.up.railway.app](https://quiz-app-production-9e7f.up.railway.app)

### 📜 更新日志

| 版本 | 内容 |
|------|------|
| **v1.2.1** | 🔐 **权限体系全面升级！** 访客 < 注册用户 < 管理员三级权限。官方题库仅管理员可改名。删除双重认证（管理员输密码/用户输名称确认）。📋 **系统日志 SystemLog**。📮 **用户反馈** 一键报告问题发邮件。⭐ **管理员官方题库**。📢 注册页域名公告。🔒 访客禁止改删。☁️ **跨设备数据恢复**（从云端拉取合并到本地）。♻️ **版本号自动化**（22 处硬编码改为 `{{ VERSION }}`）。🐛 **修复 deleteHistoryItem 索引漂移 Bug**。🧹 **统一操作入口**（6 个删除/清空函数收归 utils.js）。🧪 **自动化测试 46 个**（pytest，Sync API + 权限体系）。 |
| **v1.1.0** | 🗄️ **题库持久化到 PostgreSQL！** 新增 `QuestionBank` 表，题库不再依赖 `data/*.json` 文件。统一版本号管理。 |
| **v1.0.2** | 📧 **邮箱验证码打通！** 自定义域名 + Resend API。管理员后台（用户管理/统计卡片）。数据库自动迁移。 |
| **v1.0.1** | 🛡️ **用户数据云端同步！** 错题本/收藏/学习记录自动备份到服务器。Sync API + CSRF 防护。 |
| **v1.0.0** | 🎉 **正式版发布！** Railway + PostgreSQL 部署。安全大升级。 |
| **v0.9.0** | 账号系统 · 邮箱验证注册 · 用户中心 · 中英文切换 · 忘记密码 |
| **v0.0.1** | 初始版本：PDF/DOCX 上传 · 练习/考试模式 · 答题卡 |

<hr>

<h2 id="english">🇬🇧 English</h2>

<h1 align="center">📝 Quiz Master v1.2.1</h1>

<p align="center">
  <em>A lightweight, feature-rich quiz web application with AI-powered parsing, reading comprehension mode, and smart annotation tools.</em><br>
  <em>"Turn any study material into an interactive quiz in seconds."</em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-3.0-green" alt="Flask"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"></a>
  <a href="https://quiz-app-production-9e7f.up.railway.app"><img src="https://img.shields.io/badge/Live-Online-brightgreen" alt="Live"></a>
  <a href="https://github.com/PengjinHao-cell/Quiz-App"><img src="https://img.shields.io/badge/GitHub-Repo-181717" alt="GitHub"></a>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">🌐 Live → quiz-app-production-9e7f.up.railway.app</a></strong><br>
  <sub>🚀 v1.2.1 · Hosted on Railway · PostgreSQL</sub>
</p>

### ✨ Features

**📤 Import** — PDF / DOCX / TXT upload · AI text paste · Built-in banks · Vocabulary

**🔐 Account System** — Register with email verification · Login/Logout · Guest mode · Forgot password via email · Session persistence · Remember me · Login rate limiting

**👤 User Center** — Personal dashboard with stats · Favorites · Wrong book · Study history · Settings (exam duration, language)

**🌐 Bilingual** — Full Chinese/English UI switch · System text only (questions unchanged)

**🧠 Smart Detection** — Triple-engine: Reading / Party format / Standard format

**📚 Bank Management** — Rename · Type badges · Sort by name · Duplicate detection · Delete (password protected)

**🧠 Quiz Modes** — Practice (instant feedback) · Exam (timed, scored, custom duration) · Shuffled options · Answer sheet · Keyboard shortcuts · Modal confirm dialogs

**📖 Reading Comprehension** — Dual-panel layout · Highlight 🖍 · Underline ＿ · Passage count · History saved to localStorage

**📊 Learning Tools** — Wrong book · Favorites · Statistics · History · Share results · 7-day activity chart

**🎨 UX** — Toast notifications · Unified splash screen · Search · Responsive design · Announcement banner · Password strength indicator

### 🛠 Tech Stack

**Python 3 + Flask** · Vanilla HTML/CSS/JS · **PostgreSQL** (via SQLAlchemy) · PyPDF2 / pymupdf / python-docx · DeepSeek API

**Hosting:** [Railway](https://railway.app) · **Version Control:** [GitHub](https://github.com/PengjinHao-cell/Quiz-App)

### 🔐 Security

| Item | Detail |
|------|--------|
| **Password storage** | Hashed with `pbkdf2:sha256` (Werkzeug). Plaintext never stored. |
| **Password transmission** | Over HTTPS (Railway). POST body JSON, never in URL. |
| **Session** | Flask signed cookies (SECRET_KEY). `session_protection = "strong"`. Optional "Remember me" (14-day cookie). |
| **Login rate limit** | 5 failed attempts per IP per 5 minutes → 5 min cooldown. |
| **Verification code** | 3 failed attempts per email per 10 min → lockout. 5 min code expiry. |
| **Secret key** | Required via `SECRET_KEY` env var. App refuses to start with default in production. |
| **Delete auth** | Server-side `DELETE_PASSWORD` env var. Front-end hardcoded password removed. |
| **Guest mode** | No login required. All guest data is public. |
| **XSS protection** | `escapeHTML()` on all user-generated content in templates. |

### 🚀 Quick Start

```bash
git clone https://github.com/PengjinHao-cell/Quiz-App.git
cd quiz-app
pip install -r requirements.txt
cp .env.example .env
# Set SECRET_KEY, DATABASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD, etc.
python3 app.py
# → http://localhost:5050
```

### 🌐 Deployment (Railway)

This project is live on Railway with PostgreSQL:

```
https://quiz-app-production-9e7f.up.railway.app
```

Required Railway Variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session signing key (run `openssl rand -hex 32`) |
| `DATABASE_URL` | Auto-injected by Railway PostgreSQL plugin |
| `ADMIN_USERNAME` | Optional: auto-create admin on first boot |
| `ADMIN_PASSWORD` | Optional: admin password |
| `DELETE_PASSWORD` | Password required to delete question banks |
| `DEEPSEEK_API_KEY` | For AI text parsing |
| `SMTP_*` | For email verification codes |

### 📜 Changelog

| Version | Highlights |
|---------|-----------|
| **v1.2.1** | 🔐 **Full permission system!** Guest < User < Admin. Official banks admin-only. Delete: admin=password, user=name confirm. 📋 **SystemLog**. 📮 **User feedback** via email. ⭐ **Official banks**. ☁️ **Cross-device data restore** (pull from server). ♻️ **Version auto-busting** (22 hardcoded `v=X` → `{{ VERSION }}`). 🐛 **Fixed deleteHistoryItem index shift bug**. 🧹 **Unified operations** (6 delete/clear functions moved to utils.js). 🧪 **46 automated tests** (pytest, Sync API + permissions). |
| **v1.1.0** | 🗄️ **Banks stored in PostgreSQL!** No more JSON files. Unified version number. |
| **v1.0.2** | 📧 **Email verification working!** Custom domain + Resend API. Admin panel. DB auto-migration. |
| **v1.0.1** | 🛡️ **Cloud sync for user data!** Wrong/favorites/history backed up to PostgreSQL. Sync API + CSRF. |
| **v1.0.0** | 🎉 **Official release!** Railway + PostgreSQL. Security overhaul. |
| **v0.9.0** | Account system · Email verification · User center · Bilingual CN/EN · Forgot password |
| **v0.0.1** | Initial: PDF/DOCX upload · Practice/Exam modes · Answer sheet |

<hr>

<h2 id="繁體中文">🇭🇰 繁體中文</h2>

<h1 align="center">📝 刷題通 (Quiz Master) v1.2.1</h1>

<p align="center">
  <em>正式版發佈 · 安全加固 · Railway 託管 · PostgreSQL 數據庫</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">🌐 在線體驗</a></strong>
</p>

### ✨ 功能特色

**🔐 帳號系統** — 郵箱驗證碼註冊 · 登入/登出 · 訪客模式 · 忘記密碼 · 登入態保持

**👤 個人中心** — 學習統計 · 收藏本 · 錯題本 · 學習記錄 · 設定

**🌐 中英文切換** — 系統界面全量翻譯，題目原文不變

**📤 題庫匯入** — PDF/DOCX/TXT · AI 解析 · 內建題庫 · 背單字

**📖 閱讀理解** — 左右分欄 · 螢光筆 🖍 · 底線 ＿

**🧠 刷題模式** — 練習 · 考試（自訂時長）· 選項亂序 · 答題卡 · 快捷鍵

### 🚀 快速開始

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
```

<hr>

<p align="center">
  <a href="https://github.com/PengjinHao-cell/Quiz-App">📦 GitHub</a> ·
  <a href="https://quiz-app-production-9e7f.up.railway.app">🌐 Live Demo</a><br>
  <sub>Made with ❤️ by PengjinHao · © 2026 Quiz Master · v1.2.1</sub>
</p>
