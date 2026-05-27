# 刷题通 (Quiz Master)

一个轻量级的 Python 刷题 Web 应用，支持上传 PDF/DOCX 题库文件，自动解析为结构化题目，提供练习模式和考试模式。

## 功能特性

- 📤 **题库上传**：支持 PDF 和 DOCX 格式，自动解析题目、选项和答案
- 📚 **题库管理**：持久化存储多个题库，可随时选择、删除
- ✏️ **练习模式**：作答后即时显示正确答案反馈，逐题练习
- 📝 **考试模式**：模拟真实考试环境，选择后自动跳转下一题，统一交卷评分
- 📊 **成绩详情**：交卷后展示分数、正确率、逐题对错和正确答案
- 📋 **答题卡**：侧边栏答题卡，直观查看已答/未答/当前题目，可随时跳转
- 📱 **响应式设计**：适配桌面和移动端

## 技术栈

- **后端**：Python 3 + Flask
- **前端**：原生 HTML/CSS/JavaScript（无框架依赖）
- **解析**：PyPDF2 / python-docx
- **存储**：本地文件系统（JSON + 原始文件）

## 快速开始

### 1. 安装依赖

```bash
cd quiz_app
pip install -r requirements.txt
```

### 2. 初始化题库（可选）

如果你有题库 PDF 文件，可以直接导入：

```bash
python init_bank.py "你的题库文件.pdf"
```

程序会自动解析并保存到 `data/` 和 `uploads/` 目录。

### 3. 启动应用

```bash
python app.py
```

然后在浏览器中打开 http://localhost:5000

## 目录结构

```
quiz_app/
├── app.py              # Flask 主应用
├── parser.py           # PDF/DOCX 解析模块
├── init_bank.py        # 命令行题库导入脚本
├── requirements.txt    # Python 依赖
├── uploads/            # 原始上传文件
├── data/               # 解析后的题库 JSON
├── templates/
│   ├── index.html      # 首页 - 题库列表 + 上传
│   ├── quiz.html       # 刷题页
│   ├── result.html     # 成绩页
│   └── error.html      # 错误页
└── static/
    ├── style.css       # 样式表
    ├── app.js          # 首页逻辑
    ├── quiz.js         # 刷题页逻辑
    └── result.js       # 成绩页逻辑
```

## 题库格式说明

支持以下三种题型自动识别：

| 题型 | 标识词 | 选项示例 | 答案格式 |
|------|--------|----------|----------|
| 单选题 | 单选题 | A. xxx B. xxx | 答案：A |
| 多选题 | 多选题 | A. xxx B. xxx | 答案：ABC |
| 判断题 | 判断题 | A. 正确 B. 错误 | 答案：A |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页 |
| POST | `/upload` | 上传题库文件 |
| GET | `/quiz/<bank_id>/<mode>` | 刷题页面 |
| GET | `/result/<bank_id>` | 成绩页面 |
| GET | `/api/banks` | 获取题库列表 |
| DELETE | `/api/bank/<bank_id>` | 删除题库 |
| GET | `/api/bank/<bank_id>/questions` | 获取题目列表 |
| POST | `/api/bank/<bank_id>/submit` | 提交答案 |

## 开发建议扩展

- [ ] 用户系统（登录/注册）
- [ ] 答题记录历史
- [ ] 错题本/收藏功能
- [ ] 题库搜索和标签分类
- [ ] 导出成绩单
- [ ] 数据库替代文件存储（SQLite/MySQL）