# Quiz App — 待做清单

> 版本：v1.5.0 · 更新日期：2026-07-15

---

## 待做

- [x] **英汉词典集成** — ~~将 AiPlace/dictionary 融入 quiz-app~~ → **v1.5.0 替代方案**：词形还原引擎 + 词组识别（详见 design doc）。暂缓原因：词典依赖国外 API 不稳定，改为优化现有查词管线。
- [ ] **国内词典 API 替换** — 后续考虑接入有道/金山词霸等国内 API 替代 Free Dictionary，提升国内用户体验。
- [ ] **自动化部署 `.pytest_cache/` 清理** — 确认 CI 中测试缓存不被提交
- [x] **QQ 邮箱支持** — ~~等待域名 `quizmasterprogram.top` 信誉度提升~~ 已解封，QQ 邮箱可正常收件 (v1.2.2)
- [x] **跨设备"推送"优化** — ~~手动拉取~~ → 登录时自动检测新设备，主页顶部绿色公告一键恢复 (v1.2.3)

## 已知问题（小）

- [ ] **`user.html` 内联 JS 中的 `{{ VERSION_NAME }}`** — 在 JS 模板字面量里使用了 Jinja2 变量，若将来把 JS 移到 `.js` 文件会失效
- [ ] **`app.py` 没有 App Factory** — 测试时需要在 conftest 中提前设环境变量再 import，无法用 `create_app()` 模式动态配置
- [ ] **`load_user` 使用 `Query.get()` 旧 API** — SQLAlchemy 2.0 建议改用 `Session.get()`

## 已解决 ✓

- [x] **生产环境 500 错误** — `question_banks` 表缺少 6 个预计算字段列。`migrate.py` + `_run_migration()` 均未迁移这些列，`load_bank_list` 查询时 SQLAlchemy SELECT 不存在的列导致 `ProgrammingError`。修复：在 `_run_migration()` 中先 `ALTER TABLE ADD COLUMN` 再查询，`migrate.py` 声明式扩展覆盖 (2026-06-04)

- [x] **跨设备数据恢复** — 新增 `restoreFromServer()` + 侧边栏入口
- [x] **版本号自动化** — 22 处硬编码 `v=4`/`v=3` → `v=VERSION`
- [x] **deleteHistoryItem 索引漂移** — 改用 `record.id` 定位
- [x] **统一操作入口** — 6 个删除/清空函数收归 `utils.js`
- [x] **自动化测试** — 46 个 pytest 测试（Sync API + 权限体系）
- [x] **`.gitignore` 修复** — `test_*.py` 改为 `/test_*.py` 不忽略 `tests/` 目录，新增 `.pytest_cache/`
- [x] **新设备检测公告** — 换设备登录自动弹绿色公告，一键恢复云端数据 (v1.2.3)
- [x] **用户切换数据隔离** — onUserLogin() 检测用户变化自动清空 localStorage (v1.2.3)
- [x] **多进程验证码丢失** — 验证码从内存 dict 迁移到数据库 VerificationCode 表 (v1.2.2)
- [x] **`instance/quiz_app.db` 从 git 跟踪移除** — 避免本地 SQLite 被提交
