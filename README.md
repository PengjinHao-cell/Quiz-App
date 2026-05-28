<p align="center">
  <strong>🇬🇧 English</strong> · <strong><a href="#简体中文">🇨🇳 简体中文</a></strong> · <strong><a href="#繁體中文">🇭🇰 繁體中文</a></strong>
</p>

<h1 align="center">📝 Quiz Master v0.5.0</h1>

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

Quiz Master is a web-based quiz platform that supports uploading **PDF / DOCX / TXT** files and **AI-powered text parsing**. It features **Practice, Exam, Reading Comprehension, and Vocabulary** modes, along with **highlight annotations, wrong answer review, favorites, and learning statistics**.

### ✨ Features

**📤 Import**

| Method | Description |
|--------|-------------|
| 📄 File Upload | PDF / DOCX / TXT — auto-parses questions, options, and answers |
| ✏️ AI Text Paste | Paste any question text → **DeepSeek AI** auto-formats it |
| 📚 Built-in Banks | Python sample questions included out-of-the-box |
| 📖 Vocabulary | CET-6 words (120+) — English word → Chinese definition |

**🧠 Smart Detection**
- **Triple-Engine Recognition** — Auto-detects format on upload:
  - *Reading Engine* — Detects long passages + comprehension questions (CN/EN)
  - *Format Engine* — Handles special layouts like "试题类型X选题题目分值2"
  - *Standard Engine* — Processes "1. Question / A. Option / Answer: A" format

**📚 Bank Management** — Rename · Type Badges · Sort by Name · Duplicate Detection · Delete

**🧠 Quiz Modes** — Practice (instant feedback) · Exam (timed, scored) · Shuffled Options · Answer Sheet · Keyboard Shortcuts

**📖 Reading Comprehension** — Dual-panel layout · Highlighter 🖍 · Underline ＿ · Passage Count

**📊 Learning Tools** — Wrong Book · Favorites · Statistics · History · Share Results

**🎨 UX** — Toast Notifications · Splash Screen · Search · Responsive Design

### 🛠 Tech Stack

Python 3 + Flask · Vanilla HTML/CSS/JS · PyPDF2 / pymupdf / python-docx · DeepSeek API · JSON + localStorage

### 🚀 Quick Start

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
# → http://localhost:5050
```

### 📖 Usage

| Action | How |
|--------|-----|
| Upload file | PDF/DOCX/TXT → auto-parse → redirect to quiz |
| Paste text | Paste questions → AI Parse → auto-save |
| Highlight | Select text → 🖍 (all modes) |
| Underline | Select text → ＿ (reading mode only) |

### 📜 Changelog

| Version | Highlights |
|---------|-----------|
| **v0.5.0** | Reading mode, highlighter/underline, triple-engine, .txt upload, sort by name, duplicate detection, toast notifications |
| **v0.4.0** | Vocabulary module (CET-6) |
| **v0.3.0** | Welcome page, rename, type badges |
| **v0.2.0** | AI text parsing, shuffled options, share results, search |
| **v0.1.0** | Wrong book, favorites, statistics, timer, splash screen |
| **v0.0.1** | Initial: PDF/DOCX upload, practice/exam modes, answer sheet |

<hr>

<h2 id="简体中文">🇨🇳 简体中文</h2>

<h1 align="center">📝 刷题通 (Quiz Master) v0.5.0</h1>

<p align="center">
  <em>一个功能丰富的轻量级刷题 Web 应用。<br>
  支持 PDF / DOCX / TXT 上传 + AI 智能解析，内置练习/考试/阅读/背单词四大模式。</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">在线体验 → quiz-app-production-9e7f.up.railway.app</a></strong><br>
  <sub>🚧 正式版 v1.0.0 正在路上，敬请期待</sub>
</p>

### ✨ 功能特性

**📤 题库导入**
- 📄 **上传文件** — PDF / DOCX / TXT，自动解析题目、选项、答案
- ✏️ **粘贴文本** — 任意格式题目文字 → DeepSeek AI 自动整理为标准题库
- 📚 **内置题库** — 开箱即用的 Python 示例题库
- 📖 **背单词** — CET-6 高频词汇（120+ 词），英文选中文释义

**🧠 智能识别**
- 🤖 **三引擎自动识别** — 上传后自动判断格式：阅读 / 异形格式 / 标准

**📚 题库管理** — 重命名 · 题型标识 · 按名称排序 · 重复检测 · 删除

**🧠 刷题模式** — 练习模式（即时反馈）· 考试模式（倒计时评分）· 选项乱序 · 答题卡 · 快捷键

**📖 阅读理解** — 左右分栏 · 🖍 荧光笔 · ＿ 下划线 · 篇数选择 · 提交评判移至顶栏

**📊 学习工具** — 错题本 · 收藏 · 统计 · 记录 · 分享成绩

**🎨 体验优化** — Toast 通知 · 启动画面 · 搜题 · 响应式设计

### 🛠 技术栈

Python 3 + Flask · 原生 HTML/CSS/JS · PyPDF2 / pymupdf / python-docx · DeepSeek API · JSON + localStorage

### 🚀 快速开始

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
# → http://localhost:5050
```

### 📜 更新日志

| 版本 | 内容 |
|------|------|
| **v0.5.0** | 阅读模式、荧光/下划线标注、三引擎识别、.txt上传、名称排序、重复检测、Toast通知 |
| **v0.4.0** | 背单词模块（CET-6） |
| **v0.3.0** | 欢迎页、题库重命名、题型标识 |
| **v0.2.0** | AI 解析、选项乱序、分享成绩、搜题 |
| **v0.1.0** | 错题本、收藏、统计、倒计时、启动画面 |
| **v0.0.1** | 初始版本：PDF/DOCX上传、练习/考试模式、答题卡 |

<hr>

<h2 id="繁體中文">🇭🇰 繁體中文</h2>

<h1 align="center">📝 刷題通 (Quiz Master) v0.5.0</h1>

<p align="center">
  <em>功能豐富的輕量級刷題 Web 應用。<br>
  支援 PDF / DOCX / TXT 上傳 + AI 智能解析，內建練習/考試/閱讀/背單字四大模式。</em>
</p>

<p align="center">
  🔗 <strong><a href="https://quiz-app-production-9e7f.up.railway.app">線上體驗 → quiz-app-production-9e7f.up.railway.app</a></strong><br>
  <sub>🚧 正式版 v1.0.0 正在路上，敬請期待</sub>
</p>

### ✨ 功能特色

**📤 題庫匯入** — 上傳檔案 (PDF/DOCX/TXT) · 貼上文字 AI 解析 · 內建題庫 · 背單字

**🧠 智能識別** — 三引擎自動識別：閱讀 / 異形格式 / 標準

**📚 題庫管理** — 重新命名 · 題型標籤 · 依名稱排序 · 重複檢測 · 刪除

**🧠 刷題模式** — 練習模式 · 考試模式 · 選項亂序 · 答題卡 · 快捷鍵

**📖 閱讀理解** — 左右分欄 · 🖍 螢光筆 · ＿ 底線 · 篇數選擇

**📊 學習工具** — 錯題本 · 收藏 · 統計 · 記錄 · 分享成績

### 🛠 技術棧

Python 3 + Flask · 原生 HTML/CSS/JS · PyPDF2 / pymupdf / python-docx · DeepSeek API

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
