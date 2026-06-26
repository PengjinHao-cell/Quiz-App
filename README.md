<h2 id="简体中文">🇨🇳 简体中文</h2>

<h1 align="center">📝 刷题通 (Quiz Master) v1.5.0</h1>

<p align="center">
  <em>🎉 正式版发布 · 安全加固 · Railway 托管 · PostgreSQL 数据库</em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9%2B-blue" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-3.0-green" alt="Flask"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"></a>
  <a href="https://quizmaster.cn"><img src="https://img.shields.io/badge/Live-Online-brightgreen" alt="Live"></a>
  <a href="https://github.com/PengjinHao-cell/Quiz-App"><img src="https://img.shields.io/badge/GitHub-Repo-181717" alt="GitHub"></a>
  <br>
  <strong><a href="#简体中文">🇨🇳 简体中文</a></strong> · <strong><a href="#english">🇬🇧 English</a></strong> · <strong><a href="#繁體中文">🇭🇰 繁體中文</a></strong>
</p>

<p align="center">
  🔗 <strong><a href="https://quizmaster.cn">🌐 在线体验</a></strong><br>
  <sub>托管于 Railway，数据持久化存储</sub>
</p>

---

**刷题通** 是一个轻量级刷题 Web 应用，支持 PDF/DOCX/TXT 题库上传、AI 智能解析、练习/考试/阅读理解/背单词四种模式，配有完整的用户系统和数据同步。

### ✨ 功能特性

| 模块 | 功能 |
|------|------|
| **📤 题库导入** | PDF / DOCX / TXT 文件上传 · AI 粘贴解析 · 内置题库 · 背单词词库 |
| **🔐 账号系统** | 邮箱验证码注册 · 登录/登出 · 访客模式 · 忘记密码找回 · 记住我 · 登录限流 |
| **👤 个人中心** | 学习统计 · 收藏本 · 错题本 · 学习记录 · 设置（考试时长/语言/个人信息） |
| **🌐 双语界面** | 完整中英文切换（仅系统文字，题目原文不变） |
| **🧠 智能识别** | 三引擎自动判断：阅读格式 / 异形格式 / 标准格式 |
| **📖 阅读理解** | 左右双栏布局 · 荧光笔 🖍 / 下划线 ＿ 标注 · 篇数选择 · 本地历史 |
| **🔤 点击查词** | 双击英文单词弹出释义（20,000 离线词库 + API 兜底）· 右键增强菜单（查词/复制/加入生词本）· 阅读模式荧光/下划线标注 |
| **📖 生词本** | 云端同步 · 复习模式（遮释义回想）· CSV 导出 · 用户中心独立 Tab |
| **🤖 AI 错题解析** | 答错一键 DeepSeek 解析 · 逐选项分析 · 知识点 + 记忆技巧 · 数据库缓存 |
| **🧠 刷题模式** | 练习模式（即时反馈）· 考试模式（自定义时长/计分）· 选项乱序 · 答题卡 · 快捷键 |
| **📊 学习工具** | 错题本 · 收藏 · 7日活跃趋势图 · 成绩分享（图片保存） |
| **🎨 用户体验** | Toast 通知 · 统一启动画面 · 搜题 · 响应式布局 · 公告横幅 · 密码强度指示条 |
| **☁️ 跨设备同步** | 错题/收藏/学习记录自动备份到云端，新设备可一键恢复 |
| **⚙️ 权限体系** | 三级权限：访客（仅刷题）< 注册用户（可删改）< 管理员（完整控制） |
| **📋 系统日志** | 所有操作自动记录，用户可导出，管理员可筛选查看 |

### 🔐 安全说明

| 项目 | 详情 |
|------|------|
| **密码存储** | `pbkdf2:sha256` 加盐哈希，绝无明文 |
| **密码传输** | 全程 HTTPS（Railway），POST JSON body，不经 URL |
| **会话安全** | Flask 签名 Cookie + `session_protection = "basic"`，可选"记住我"14天 |
| **登录限流** | 同 IP 5 分钟失败 5 次 → 冻结 5 分钟 |
| **验证码限流** | 同邮箱 10 分钟错误 3 次 → 锁定 10 分钟 |
| **密钥强制** | 生产环境未设置 `SECRET_KEY` 拒绝启动 |
| **删除鉴权** | 服务端 `DELETE_PASSWORD` 验证，前端不暴露密码 |
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

### 🌐 部署（Railway）

在线地址：[quizmaster.cn](https://quizmaster.cn)

| 环境变量 | 说明 |
|----------|------|
| `SECRET_KEY` | Flask 会话签名密钥（`openssl rand -hex 32`） |
| `DATABASE_URL` | Railway PostgreSQL 插件自动注入 |
| `ADMIN_USERNAME` | 可选：首次启动自动创建管理员 |
| `ADMIN_PASSWORD` | 可选：管理员密码 |
| `DEEPSEEK_API_KEY` | AI 题库解析 |
| `RESEND_API_KEY` | 邮箱验证码发送 |

### 📜 更新日志

| 版本 | 亮点 |
|------|------|
| **v1.5.0** | 🧠 词形还原引擎（deems→deem）· 🏷 词组识别（take off 拖拽查词）· ⚡ 4 级查词管线（本地规则+API 兜底）· -ly 副词退查 |
| **v1.4.0** | 🔤 英文单词点击查词（双击+右键）· 📖 生词本（云同步+复习）· 🤖 AI 错题解析（DeepSeek） |
| **v1.3.1** | ⚡ 首页渲染提速 · ⏱ sync/填空去抖 · 🃏 答题卡增量更新 · 🖍 荧光懒恢复 · 🔒 收藏本隐藏答案 · 📝 组卷 qids 修复 |
| **v1.3.0** | 🔗 域名迁移 quizmaster.cn · 🔒 题库数据隔离 · 🎨 删除确认卡片化 · 🐛 模态框修复 · 📝 题库入库 |
| **v1.2.3** | 🆕 新设备检测公告（一键恢复云端数据） · 🔒 用户切换自动清空旧数据 |
| **v1.2.2** | 🐛 修复多进程验证码丢失（内存→数据库） · 🧹 移除 QQ 邮箱公告 |
| **v1.2.1** | 🔐 权限体系 · 📋 系统日志 · 📮 用户反馈 · ☁️ 跨设备恢复 · ♻️ 版本号自动化 · 🐛 索引漂移修复 · 🧹 统一操作入口 · 🧪 自动化测试 46 个 |
| **v1.1.0** | 🗄️ 题库持久化到 PostgreSQL，告别 JSON 文件，Redeploy 不丢数据 |
| **v1.0.2** | 📧 邮箱验证码（自定义域名 + Resend）· ⚙️ 管理后台 · 数据库自动迁移 |
| **v1.0.1** | 🛡️ 用户数据云端同步（错题/收藏/历史备份到 PostgreSQL） |
| **v1.0.0** | 🎉 正式版 · Railway 部署 · 安全大升级 |
| **v0.9.0** | 账号系统 · 邮箱注册 · 用户中心 · 中英文切换 |
| **v0.0.1** | 初始版本：PDF/DOCX 上传 · 练习/考试模式 · 答题卡 |

---

<hr>

<h2 id="english">🇬🇧 English</h2>

<h1 align="center">📝 Quiz Master v1.5.0</h1>

<p align="center">
  <em>A lightweight, feature-rich quiz web application with AI-powered parsing, reading comprehension mode, and smart annotation tools.</em><br>
  <em>"Turn any study material into an interactive quiz in seconds."</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quizmaster.cn">🌐 Live Demo</a></strong>
</p>

### ✨ Features

**📤 Import** — PDF / DOCX / TXT · AI paste parsing · Built-in banks · Vocabulary

**🔐 Account** — Email verification · Login/Logout · Guest mode · Forgot password · Remember me · Rate limiting

**👤 Dashboard** — Stats · Favorites · Wrong book · History · Settings (duration, language)

**🌐 Bilingual** — Full Chinese/English UI switch (questions unchanged)

**🧠 Detection** — Triple-engine: Reading / Party / Standard format auto-detection

**🔤 Word Lookup** — Double-click words for definition (20K offline dict + API fallback) · Right-click menu (lookup/copy/add to vocab) · Reading mode annotation

**📖 Vocab Book** — Cloud sync · Review mode (blur-to-reveal) · CSV export · User center tab

**🤖 AI Explain** — DeepSeek-powered wrong answer analysis · Per-option breakdown · Knowledge points + memory tips · DB cached

**📖 Reading** — Dual-panel · Highlight 🖍 / Underline ＿ · Passage selection · Local history

**🧠 Quiz Modes** — Practice · Exam (timed/scored) · Shuffle options · Answer sheet · Keyboard shortcuts

**📊 Learning** — Wrong book · Favorites · 7-day activity chart · Share results (save as image)

**☁️ Sync** — Cloud backup for wrong answers, favorites, history. Restore on new device.

### 🚀 Quick Start

```bash
git clone https://github.com/PengjinHao-cell/Quiz-App.git
cd quiz-app
pip install -r requirements.txt
cp .env.example .env
# Set SECRET_KEY, DATABASE_URL, etc.
python3 app.py
# → http://localhost:5050
```

### 📜 Changelog

| Version | Highlights |
|---------|-----------|
| **v1.5.0** | Lemmatization engine (deems→deem) · Phrase recognition (drag-select "take off") · 4-tier lookup pipeline · -ly adverb fallback |
| **v1.4.0** | Word click-lookup (double-click + right-click) · Vocab book (cloud sync + review) · AI wrong answer explain (DeepSeek) |
| **v1.3.1** | Homepage render speedup · Sync/fill-input debounce · Answer sheet incremental update · Lazy highlight restore · Hide fav answers · Fix qids compose |
| **v1.3.0** | Domain migration quizmaster.cn · Bank data isolation · Delete confirmation cards · Modal fix · Bank files in repo |
| **v1.2.3** | New-device detection banner (one-click cloud restore) · Auto-clear old data on user switch |
| **v1.2.2** | Fix multi-worker verification code loss (memory→DB) · Remove QQ email notice |
| **v1.2.1** | Permissions · SystemLog · User feedback · Cross-device restore · Version auto-busting · Index bug fix · Unified operations · 46 tests |
| **v1.1.0** | PostgreSQL bank storage — no more data loss on redeploy |
| **v1.0.2** | Email verification (custom domain + Resend) · Admin panel |
| **v1.0.1** | Cloud sync (wrong/favorites/history to PostgreSQL) |
| **v1.0.0** | Official release · Railway · Security overhaul |
| **v0.9.0** | Account system · Email register · User center · Bilingual |
| **v0.0.1** | Initial: PDF/DOCX upload · Practice/Exam · Answer sheet |

---

<hr>

<h2 id="繁體中文">🇭🇰 繁體中文</h2>

<h1 align="center">📝 刷題通 (Quiz Master) v1.5.0</h1>

<p align="center">
  <em>正式版發佈 · 安全加固 · Railway 託管 · PostgreSQL 數據庫</em>
</p>

### ✨ 功能特色

**🔐 帳號系統** — 郵箱驗證碼註冊 · 登入/登出 · 訪客模式 · 忘記密碼

**👤 個人中心** — 學習統計 · 收藏本 · 錯題本 · 學習記錄 · 設定

**📤 題庫匯入** — PDF/DOCX/TXT · AI 解析 · 內建題庫 · 背單字

**📖 閱讀理解** — 左右分欄 · 螢光筆 🖍 · 底線 ＿

**🧠 刷題模式** — 練習 · 考試（自訂時長）· 選項亂序 · 答題卡

### 🚀 快速開始

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
```

---

<hr>

<p align="center">
  <a href="https://github.com/PengjinHao-cell/Quiz-App">📦 GitHub</a> ·
  <a href="https://quizmaster.cn">🌐 Live Demo</a><br>
  <sub>Made with ❤️ by PengjinHao · © 2026 Quiz Master · v1.5.0</sub>
</p>
