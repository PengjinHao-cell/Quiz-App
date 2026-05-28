<p align="center">
  <strong>🇬🇧 English</strong> · <strong><a href="#简体中文">🇨🇳 简体中文</a></strong> · <strong><a href="#繁體中文">🇭🇰 繁體中文</a></strong>
</p>

<h1 align="center">📝 Quiz Master v0.9.0</h1>

<p align="center">
  <em>A lightweight, feature-rich quiz web application with AI-powered parsing, reading comprehension mode, and smart annotation tools.</em><br>
  <em>"Turn any study material into an interactive quiz in seconds."</em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-3.0-green" alt="Flask"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"></a>
  <a href="https://quiz-app-production-9e7f.up.railway.app"><img src="https://img.shields.io/badge/Live-Demo-brightgreen" alt="Live Demo"></a>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">Live Demo → quiz-app-production-9e7f.up.railway.app</a></strong><br>
  <sub>🚧 Official v1.0.0 release is on the way — stay tuned!</sub>
</p>

<hr>

## 🇬🇧 English

Quiz Master is a web-based quiz platform that supports uploading **PDF / DOCX / TXT** files and **AI-powered text parsing**. It features **Practice, Exam, Reading Comprehension, and Vocabulary** modes, along with **user accounts, email verification, bilingual UI, personal dashboard, highlight annotations**, and more.

### ✨ Features

**📤 Import** — PDF / DOCX / TXT upload · AI text paste · Built-in banks · Vocabulary

**🔐 Account System** — Register with email verification · Login/Logout · Guest mode · Forgot password via email · Session persistence

**👤 User Center** — Personal dashboard with stats · Favorites · Wrong book · Study history · Settings (exam duration, language)

**🌐 Bilingual** — Full Chinese/English UI switch · System text only (questions unchanged)

**🧠 Smart Detection** — Triple-engine: Reading / Party format / Standard format

**📚 Bank Management** — Rename · Type badges · Sort by name · Duplicate detection · Delete (password protected)

**🧠 Quiz Modes** — Practice (instant feedback) · Exam (timed, scored, custom duration) · Shuffled options · Answer sheet · Keyboard shortcuts

**📖 Reading Comprehension** — Dual-panel layout · Highlight 🖍 · Underline ＿ · Passage count

**📊 Learning Tools** — Wrong book · Favorites · Statistics · History · Share results

**🎨 UX** — Toast notifications · Splash screen · Search · Responsive design · Announcement banner

### 🛠 Tech Stack

Python 3 + Flask · Vanilla HTML/CSS/JS · SQLite / PostgreSQL · PyPDF2 / pymupdf / python-docx · DeepSeek API

### 🚀 Quick Start

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
# → http://localhost:5050
```

### 📜 Changelog

| Version | Highlights |
|---------|-----------|
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

<h1 align="center">📝 刷题通 (Quiz Master) v0.9.0</h1>

<p align="center">
  <em>冲刺正式版 · 账号系统 · 邮箱验证 · 中英文切换 · 个人中心</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">在线体验 → quiz-app-production-9e7f.up.railway.app</a></strong><br>
  <sub>🚧 正式版 v1.0.0 正在路上，敬请期待</sub>
</p>

### ✨ 功能特性

**🔐 账号系统** — 邮箱验证码注册 · 登录/登出 · 访客模式 · 忘记密码找回 · 登录态保持

**👤 个人中心** — 学习统计 · 收藏本 · 错题本 · 学习记录 · 设置（考试时长、语言切换、个人信息修改）

**🌐 中英文切换** — 系统界面全量翻译，题目原文不变

**📤 题库导入** — PDF/DOCX/TXT · AI 粘贴解析 · 内置题库 · 背单词

**🧠 三引擎识别** — 阅读格式 / 异形格式 / 标准格式自动判断

**📖 阅读理解** — 左右分栏 · 荧光笔 🖍 · 下划线 ＿ · 篇数选择

**🧠 刷题模式** — 练习模式 · 考试模式（自定义时长）· 选项乱序 · 答题卡 · 快捷键

**📊 学习工具** — 错题本 · 收藏 · 统计 · 记录 · 分享成绩

**🎨 体验** — Toast 通知 · 启动动画 · 搜题 · 响应式 · 公告横幅 · 删除密码保护

### 🚀 快速开始

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
```

### 📜 更新日志

| 版本 | 内容 |
|------|------|
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

<h1 align="center">📝 刷題通 (Quiz Master) v0.9.0</h1>

<p align="center">
  <em>衝刺正式版 · 帳號系統 · 郵箱驗證 · 中英文切換 · 個人中心</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">線上體驗 → quiz-app-production-9e7f.up.railway.app</a></strong><br>
  <sub>🚧 正式版 v1.0.0 正在路上，敬請期待</sub>
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
  <sub>Made with ❤️ by PengjinHao · © 2026 Quiz Master</sub>
</p>
