# Quiz App — 待做清单

> 版本：v1.2.2 · 更新日期：2026-05-31

---

## 待做

- [ ] **自动化部署 `.pytest_cache/` 清理** — 确认 CI 中测试缓存不被提交
- [x] **QQ 邮箱支持** — ~~等待域名 `quizmasterprogram.top` 信誉度提升~~ 已解封，QQ 邮箱可正常收件 (v1.2.2)
- [ ] **跨设备"推送"优化** — 当前从云端恢复是手动拉取，考虑登录时自动提示"检测到新设备，是否恢复数据？"

## 已知问题（小）

- [ ] **`user.html` 内联 JS 中的 `{{ VERSION_NAME }}`** — 在 JS 模板字面量里使用了 Jinja2 变量，若将来把 JS 移到 `.js` 文件会失效
- [ ] **`app.py` 没有 App Factory** — 测试时需要在 conftest 中提前设环境变量再 import，无法用 `create_app()` 模式动态配置
- [ ] **`load_user` 使用 `Query.get()` 旧 API** — SQLAlchemy 2.0 建议改用 `Session.get()`

## 已解决 ✓

- [x] **跨设备数据恢复** — 新增 `restoreFromServer()` + 侧边栏入口
- [x] **版本号自动化** — 22 处硬编码 `v=4`/`v=3` → `v=VERSION`
- [x] **deleteHistoryItem 索引漂移** — 改用 `record.id` 定位
- [x] **统一操作入口** — 6 个删除/清空函数收归 `utils.js`
- [x] **自动化测试** — 46 个 pytest 测试（Sync API + 权限体系）
- [x] **`.gitignore` 修复** — `test_*.py` 改为 `/test_*.py` 不忽略 `tests/` 目录，新增 `.pytest_cache/`
- [x] **多进程验证码丢失** — 验证码从内存 dict 迁移到数据库 VerificationCode 表 (v1.2.2)
- [x] **`instance/quiz_app.db` 从 git 跟踪移除** — 避免本地 SQLite 被提交
