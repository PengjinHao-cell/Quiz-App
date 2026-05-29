<p align="center">
  <strong>🇬🇧 English</strong> · <strong><a href="#简体中文">🇨🇳 简体中文</a></strong> · <strong><a href="#繁體中文">🇭🇰 繁體中文</a></strong>
</p>

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
  <sub>🚀 v1.2.1 · 托管于 Railway · PostgreSQL 数据库</sub>
</p>

<hr>

## 🇬🇧 English

Quiz Master is a web-based quiz platform that supports uploading **PDF / DOCX / TXT** files and **AI-powered text parsing**. It features **Practice, Exam, Reading Comprehension, and Vocabulary** modes, along with **user accounts, email verification, bilingual UI, personal dashboard, highlight annotations**, and more.

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
# Clone
git clone https://github.com/PengjinHao-cell/Quiz-App.git
cd quiz-app

# Install
pip install -r requirements.txt

# Configure (copy and fill)
cp .env.example .env
# Set SECRET_KEY, DATABASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD, etc.

# Run
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
| **v1.2.1** | 🔐 **权限体系全面升级！** 访客 < 注册用户 < 管理员。官方题库仅管理员可重命名。删除：管理员输密码，普通用户输名称确认（双重认证）。📋 **系统日志** SystemLog 表记录所有操作。📮 **用户反馈** 一键报告问题，附带日志发到管理员邮箱。⭐ **管理员官方题库** 标记+管理。📢 注册页域名公告。🔒 访客禁止改删题库。支持多设备同时登录。 |
| **v1.1.0** | 🗄️ **Banks stored in PostgreSQL!** No more JSON files — data persists across Railway redeploys. Unified version number via `version.py`. |
| **v1.0.2** | 📧 **Email verification working!** Custom domain + Resend API. Admin panel (user management / stats cards). Database auto-migration for `is_admin` column. Bug fix: switched from `urllib` to `requests` for Resend API. |
| **v1.0.0** | 🎉 **Official release!** Railway deployment + PostgreSQL. Security overhaul: SECRET_KEY enforcement, server-side delete auth, login rate limiting (5/IP/5min), verification code rate limiting (3/email/10min), session protection "strong". UX: unified splash component, modal confirm dialogs, password strength indicator, stable option shuffle (non-resetting), fixed 7-day chart date matching. Performance: bank list cache (3s TTL). Bug fixes: reading mode now writes history. |
| **v0.9.0** | Account system: register with email verification, login/logout, guest mode, forgot password, user center (stats/favorites/wrong book/history/settings), bilingual CN/EN, personal info edit, duplicate password confirmation, login redirect protection |
| **v0.8.0** | Scrollable answer sheet, submit button in top bar, delete password, custom exam duration, announcement banner |
| **v0.7.1** | Bank name truncation, duration moved to global settings, wrong book retry fix, timer display compacted |
| **v0.7.0** | Reading mode, highlighter/underline, triple-engine, .txt upload, sort by name, duplicate detection, toast notifications |
| **v0.6.0** | Code cleanup: dead code removal, dismissSplash unification, secret key warning, CSS cleanup |
| **v0.5.0** | Reading mode, highlight/underline, triple-engine recognition |
| **v0.4.0** | Vocabulary module (CET-6) |
| **v0.3.0** | Welcome page, rename, type badges |
| **v0.2.0** | AI text parsing, shuffled options, share results, search |
| **v0.1.0** | Wrong book, favorites, statistics, timer, splash screen |
| **v0.0.1** | Initial: PDF/DOCX upload, practice/exam modes, answer sheet |

<hr>

<h2 id="简体中文">🇨🇳 简体中文</h2>

<h1 align="center">📝 刷题通 (Quiz Master) {{ VERSION_NAME }}</h1>

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

Railway 环境变量要求同上 English 部分。

### 📜 更新日志

| 版本 | 内容 |
|------|------|
| **v1.2.1** | 🔐 **权限体系全面升级！** 访客 < 注册用户 < 管理员三级权限。官方题库仅管理员可改名。删除双重认证（管理员输密码/用户输名称确认）。📋 **系统日志 SystemLog** 记录上传/登录/注册/删除等所有操作。📮 **用户反馈** 一键报告问题附带日志发到管理员邮箱。⭐ **管理员官方题库** 标记+管理。📢 注册页域名公告。🔒 访客禁止改删题库。多设备同时登录支持。 |
| **v1.1.0** | 🗄️ **题库持久化到 PostgreSQL！** 新增 `QuestionBank` 表，题库不再依赖 `data/*.json` 文件，Railway Redeploy 不再丢数据。新增 `version.py` 统一版本号管理，所有模板通过 `{{ VERSION }}` 引用。 |
| **v1.0.2** | 📧 **邮箱验证码打通！** 自定义域名 `quizmasterprogram.top` + Resend API 发信。管理员后台（`/admin`页面：用户管理/统计卡片/重置密码/删除）。数据库自动迁移 `is_admin` 列。Bug 修复：Railway 上 `urllib` 发 Resend 403 换 `requests` 解决、`DELETE_PASSWORD` 安全加固、考试倒计时 alert 改 Toast。 |
| **v1.0.1** | 🛡️ **用户数据云端同步！** 登录用户的错题本、收藏、学习记录自动备份到服务器（PostgreSQL），换设备登录可恢复。新增 Sync API（9 个端点，CSRF 防护）。UI：下拉菜单展开动画（opacity+transform）、成绩分享保存为 PNG 图片（html2canvas 按需加载）。体验：上传题库新增"仅上传"模式、"不跳转"选项。Bug 修复：彻底解决删除错题/收藏/记录后刷新又回弹的问题（单向同步策略，本地为权威源）。 |
| **v1.0.0** | 🎉 **正式版发布！** Railway + PostgreSQL 部署。安全大升级：SECRET_KEY 强制、服务端删除鉴权、登录限流(5次/IP/5分)、验证码限流(3次/邮箱/10分)、会话保护 strong。UX：统一启动画面、模态弹窗、密码强度条、稳定选项乱序、7日图表修复。性能：题库列表缓存(3秒)。Bug 修复：阅读模式写入历史。 |
| **v0.9.0** | 账号系统：邮箱验证注册、登录/登出、访客模式、忘记密码、个人中心（统计/收藏/错题/记录/设置）、中英文切换、个人信息修改、双重密码认定、登录跳转保护 |
| **v0.8.0** | 答题卡滚动、交卷按钮顶栏、删除密码、自定义时长、公告横幅 |
| **v0.7.1** | 名称截断、时长移至设置、错题重练修复、计时精简 |
| **v0.7.0** | 阅读模式、荧光/下划线、三引擎、.txt上传、排序、重复检测、Toast |
| **v0.6.0** | 代码清理、密钥警告、CSS清理 |
| **v0.5.0** | 阅读模式、荧光标注、三引擎识别 |
| **v0.4.0** | 背单词（CET-6） |
| **v0.3.0** | 欢迎页、重命名、题型标识 |
| **v0.2.0** | AI 解析、乱序、分享、搜索 |
| **v0.1.0** | 错题本、收藏、统计、倒计时 |
| **v0.0.1** | 初始版本 |

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
