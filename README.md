<div align="center">

# 📝 Quiz Master v0.5.0

**A lightweight, feature-rich quiz web application with AI-powered parsing, reading comprehension mode, and smart annotation tools.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[English](#english) · [简体中文](#简体中文) · [繁體中文](#繁體中文)

---

<p id="english" align="center">
  <strong>🇬🇧 English</strong>
</p>

**Quiz Master** is a web-based quiz platform that supports uploading **PDF / DOCX / TXT** files and **AI-powered text parsing**. It features **Practice, Exam, Reading Comprehension, and Vocabulary** modes, along with **highlight annotations, wrong answer review, favorites, and learning statistics**.

> *"Turn any study material into an interactive quiz in seconds."*

---

## ✨ Features

### 📤 Import
| Method | Description |
|--------|-------------|
| 📄 **File Upload** | PDF / DOCX / TXT — auto-parses questions, options, and answers |
| ✏️ **AI Text Paste** | Paste any question text → **DeepSeek AI** auto-formats it |
| 📚 **Built-in Banks** | Python sample questions included out-of-the-box |
| 📖 **Vocabulary** | CET-6高频词汇 (120+ words) — English word → Chinese definition |

### 🧠 Smart Detection
- 🤖 **Triple-Engine Recognition** — Auto-detects format on upload:
  - **Reading Engine** — Detects long passages + comprehension questions (CN/EN)
  - **Party Format Engine** — Handles special formats like "试题类型X选题题目分值2"
  - **Standard Engine** — Processes "1. Question\nA. Option\nAnswer: A" format

### 📚 Bank Management
- ✏️ **Rename** — Hover over the bank name, click ✏️ to rename
- 🏷️ **Type Badges** — Each bank shows question type distribution (single/multi/judge/reading)
- 🔤 **Sort by Name** — Banks listed alphabetically
- 🔁 **Duplicate Detection** — Warns on upload, rejects on rename
- 🗑️ **Delete** — One-click delete with animation + toast notification

### 🧠 Quiz Modes
- ✏️ **Practice Mode** — Instant feedback after each answer, auto-removes from wrong book upon correct
- 📝 **Exam Mode** — Simulates real exam, unified submission for scoring
- ⏱️ **Countdown Timer** — Smart timing (90s per question), 5-min warning, auto-submit
- 🔀 **Shuffled Options** — Random option order each practice session
- 📋 **Answer Sheet** — Sidebar showing answered/unanswered status, click to jump
- ⌨️ **Keyboard Shortcuts** — `← →` navigate, `A~H` select options

### 📖 Reading Comprehension
- 📖 **Dual-Panel Layout** — Article on the left, questions on the right
- 🖍 **Highlighter** — Yellow highlight with fade-in/out animation (Practice/Exam/Reading)
- ＿ **Underline** — Red underline with left-to-right draw animation (Reading only)
- 📄 **Passage Count** — Displays passage count instead of question count for reading banks
- 📩 **Submit Button** — Moved to top bar for clean UI

### 📊 Learning Tools
- 📕 **Wrong Answer Book** — Auto-collects wrong answers, grouped by bank, auto-removes on correct, one-click retry
- ⭐ **Favorites** — Mark good/hard questions during practice, review in a dedicated list
- 📈 **Statistics** — Summary cards + trend chart + accuracy by bank + mode comparison + 7-day activity
- 📜 **History** — Archived answer records with visualized score levels
- 📤 **Share Results** — One-click copy results to clipboard

### 🎨 UX Enhancements
- 🎨 **Welcome Page** — Gradient background + floating animation + entry button
- 🎬 **Splash Screen** — Elastic animation + flowing progress bar
- 🔍 **Search Questions** — Search by keyword in question text or options, results highlighted
- 💬 **Toast Notifications** — Global floating notifications for all operations (3.5s auto-dismiss)
- 📱 **Responsive Design** — Works on desktop and mobile

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3 + Flask |
| **Frontend** | Vanilla HTML/CSS/JavaScript (zero framework) |
| **Parsing** | PyPDF2 / pymupdf / python-docx |
| **AI** | DeepSeek API (optional, for text paste parsing) |
| **Storage** | Local filesystem (JSON) + browser localStorage |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd quiz-app
pip install -r requirements.txt
```

### 2. (Optional) Configure AI API Key

For **AI text parsing**, create a `.env` file:

```bash
echo 'DEEPSEEK_API_KEY=sk-your-key-here' > .env
```

> All features work without AI parsing.

### 3. Start the App

```bash
python3 app.py
```

Open **http://localhost:5050**

> To change port: `export PORT=xxxx`

---

## 📁 Directory Structure

```
quiz-app/
├── app.py                  # Flask main app
├── parser.py               # Triple-engine parser (PDF/DOCX/TXT)
├── parse_party.py          # Party format parser
├── requirements.txt        # Python dependencies
├── .env                    # API Key (gitignored)
├── data/                   # Question bank JSON files
├── uploads/                # Uploaded files
├── templates/              # HTML templates
├── static/                 # CSS/JS files
└── Dockerfile              # Docker deployment config
```

---

## 📖 Usage

### Upload Questions

**Method 1: File Upload**
1. Click the **Upload File** tab
2. Select **PDF / DOCX / TXT** file
3. Choose Practice or Exam mode
4. Click upload — auto-redirects to quiz or reading page

**Method 2: Paste Text**
1. Click the **Paste Text** tab
2. Paste question text
3. Click **AI Parse**
4. Wait 10-30 seconds for auto-formatting

### Practice & Exam

- Click **Practice** or **Exam** on any bank card
- Practice: instant feedback after each answer
- Exam: submit all at once for scoring
- **Highlighter**: select question text → toolbar → 🖍 Highlight

### Reading Comprehension

- Click **📖 Reading Mode** to enter dual-panel view
- **Highlighter**: select text → 🖍
- **Underline**: select text → ＿ (left-to-right draw animation)
- Click annotated text to remove
- Annotations auto-save to browser (survive refresh)

### Learning Tools

- **📊 Statistics** — View at the top of the home page
- **⭐ Favorites** — Star questions during practice
- **📕 Wrong Book** — Auto-collected, expand to review
- **📜 History** — Past score records

---

## 🧩 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome page |
| GET | `/app` | Main app page (bank list) |
| POST | `/upload` | Upload bank file (PDF/DOCX/TXT) |
| POST | `/api/parse-text` | AI parse text to bank |
| GET | `/quiz/<bank_id>` | Quiz page (params: `mode`, `count`, `q`) |
| GET | `/reading/<bank_id>` | Reading comprehension page |
| GET | `/result/<bank_id>` | Results page |
| GET | `/api/bank/<bank_id>/questions` | Get questions (params: `mode`, `count`, `q`) |
| POST | `/api/bank/<bank_id>/submit` | Submit answers |
| POST | `/api/bank/<bank_id>/rename` | Rename bank |
| POST | `/api/bank/<bank_id>/delete` | Delete bank |
| GET | `/api/reading/<bank_id>` | Get reading data |
| POST | `/api/init-sample` | Init sample bank |
| GET | `/vocab` | Vocabulary page |
| GET | `/api/vocab/words` | Get random vocabulary |

---

## 📜 Changelog

### v0.5.0 (Current)
- 📖 **Reading Comprehension** — Left panel article, right panel questions
- 🖍 **Highlighter** — Yellow highlight with fade animation (all modes)
- ＿ **Underline** — Red underline with left-to-right draw animation (reading only)
- 🤖 **Triple-Engine Recognition** — Reading / Party / Standard auto-detection
- 📄 **.txt Upload** — Plain text file upload support
- 🔤 **Sort by Name** — Bank list sorted alphabetically
- 🔁 **Duplicate Detection** — Warning on upload, rejection on rename
- 💬 **Toast Notifications** — Global floating notifications
- 🐛 Fixed multi-option parsing, short question filtering, regex boundary bugs

### v0.4.0
- 📖 **Vocabulary** — CET-6 words (English → Chinese)

### v0.3.0
- 🎨 **Welcome Page** — Gradient design with floating animation
- ✏️ **Rename** — Hover to edit bank name
- 🏷️ **Type Badges** — Question type distribution display

### v0.2.0
- ✨ **AI Text Parsing** — Paste text, auto-format
- 🔀 **Shuffled Options**
- 📤 **Share Results**
- 🔍 **Search Questions**

### v0.1.0
- ✨ **Wrong Book / Favorites / Statistics / Timer**
- 🎬 **Splash Screen**

### v0.0.1
- 📤 PDF/DOCX upload + Practice/Exam modes + Answer Sheet

---

<div align="center">
  <hr style="width: 50%;">
</div>

<p id="简体中文" align="center">
  <strong>🇨🇳 简体中文</strong>
</p>

# 📝 刷题通 (Quiz Master) v0.5.0

一个功能丰富的轻量级刷题 Web 应用。支持 **PDF / DOCX / TXT** 文件上传与**粘贴文本 AI 智能解析**，内置**练习/考试/阅读/背单词**四大模式，附带**荧光标注、错题本、收藏、学习统计**等完整学习工具。在线体验：https://quiz-app-production-9e7f.up.railway.app 

正式版正在路上

---

## ✨ 功能特性

### 📤 题库导入
| 方式 | 说明 |
|------|------|
| 📄 **上传文件** | PDF / DOCX / TXT，自动解析题目、选项、答案 |
| ✏️ **粘贴文本** | 任意格式题目文字 → **DeepSeek AI 自动整理**为标准题库 |
| 📚 **内置题库** | 开箱即用的 Python 示例题库 |
| 📖 **背单词** | CET-6 高频词汇（120+ 词），英文选中文释义 |

### 🧠 智能识别
- 🤖 **三引擎自动识别** — 上传后自动判断格式：阅读 / 异形格式 / 标准

### 📚 题库管理
- ✏️ **重命名** / 🏷️ **题型标识** / 🔤 **按名称排序** / 🔁 **重复检测** / 🗑️ **删除**

### 🧠 刷题模式
- ✏️ **练习模式** — 即时反馈，答对自动移出错题本
- 📝 **考试模式** — 统一交卷评分，倒计时自动交卷
- 🔀 **选项乱序** / 📋 **答题卡** / ⌨️ **快捷键**

### 📖 阅读理解
- 📖 **左右分栏** — 左文右题
- 🖍 **荧光笔** — 黄色高亮，淡入淡出动画
- ＿ **下划线** — 红色下划线，从左到右延伸动画
- 📄 **篇数选择** / 📩 **提交评判移至顶栏**

### 📊 学习工具
- 📕 **错题本** / ⭐ **收藏** / 📈 **统计** / 📜 **记录** / 📤 **分享成绩**

### 🎨 体验优化
- 💬 **Toast 通知** / 🎬 **启动画面** / 🔍 **搜题** / 📱 **响应式**

---

## 🛠 技术栈

Python 3 + Flask · 原生 HTML/CSS/JS · PyPDF2 / pymupdf / python-docx · DeepSeek API · JSON + localStorage

## 🚀 快速开始

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
# → http://localhost:5050
```

## 📖 使用方法

**上传文件**：PDF/DOCX/TXT → 自动解析 → 跳转刷题页
**粘贴文本**：粘贴题目 → AI 解析 → 自动入库
**荧光标注**：选中文字 → 🖍 标荧光（所有模式）
**下划线标注**：选中文字 → ＿ 标下划线（阅读模式）

---

<div align="center">
  <hr style="width: 50%;">
</div>

<p id="繁體中文" align="center">
  <strong>🇭🇰 繁體中文</strong>
</p>

# 📝 刷題通 (Quiz Master) v0.5.0

功能豐富的輕量級刷題 Web 應用。支援 **PDF / DOCX / TXT** 檔案上傳與**貼上文字 AI 智能解析**，內建**練習/考試/閱讀/背單字**四大模式，附帶**螢光標註、錯題本、收藏、學習統計**等完整學習工具。

---

## ✨ 功能特色

### 📤 題庫匯入
| 方式 | 說明 |
|------|------|
| 📄 **上傳檔案** | PDF / DOCX / TXT，自動解析題目、選項、答案 |
| ✏️ **貼上文字** | 任意格式題目文字 → **DeepSeek AI 自動整理**為標準題庫 |
| 📚 **內建題庫** | 開箱即用的 Python 範例題庫 |
| 📖 **背單字** | CET-6 高頻詞彙（120+ 詞），英文選中文釋義 |

### 🧠 智能識別
- 🤖 **三引擎自動識別** — 上傳後自動判斷格式：閱讀 / 異形格式 / 標準

### 📚 題庫管理
- ✏️ **重新命名** / 🏷️ **題型標籤** / 🔤 **依名稱排序** / 🔁 **重複檢測** / 🗑️ **刪除**

### 🧠 刷題模式
- ✏️ **練習模式** — 即時反饋，答對自動移除錯題本
- 📝 **考試模式** — 統一交卷評分，倒數計時自動交卷
- 🔀 **選項亂序** / 📋 **答題卡** / ⌨️ **快捷鍵**

### 📖 閱讀理解
- 📖 **左右分欄** — 左文右題
- 🖍 **螢光筆** — 黃色高亮，淡入淡出動畫
- ＿ **底線** — 紅色底線，從左到右延伸動畫
- 📄 **篇數選擇** / 📩 **提交評判移至頂欄**

### 📊 學習工具
- 📕 **錯題本** / ⭐ **收藏** / 📈 **統計** / 📜 **記錄** / 📤 **分享成績**

### 🎨 體驗優化
- 💬 **Toast 通知** / 🎬 **啟動畫面** / 🔍 **搜題** / 📱 **響應式設計**

---

## 🛠 技術棧

Python 3 + Flask · 原生 HTML/CSS/JS · PyPDF2 / pymupdf / python-docx · DeepSeek API · JSON + localStorage

## 🚀 快速開始

```bash
cd quiz-app
pip install -r requirements.txt
python3 app.py
# → http://localhost:5050
```

---

<div align="center">
  <hr style="width: 50%;">
  <p>
    <a href="https://github.com/PengjinHao-cell/Quiz-App">GitHub</a> ·
    <a href="https://quiz-app-production-9e7f.up.railway.app">Live Demo</a>
  </p>
  <p>Made with ❤️</p>
</div>
