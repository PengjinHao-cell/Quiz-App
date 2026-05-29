"""
Sync API 端点测试
覆盖 9 个 /api/sync/* 端点 + 权限检查 + CSRF 防护
"""
import json
import pytest


# ========== CSRF 防护 ==========

class TestCsrfProtection:
    """所有 sync POST/DELETE 必须带 X-Requested-By 头"""

    def test_missing_csrf_header_returns_403(self, client, normal_user):
        """POST 不带 CSRF 头 → 403"""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(normal_user.id)
            sess["_fresh"] = True
        resp = client.post("/api/sync/wrong-book", json={"items": []})
        assert resp.status_code == 403
        assert "CSRF" in resp.get_json()["error"]

    def test_wrong_csrf_header_returns_403(self, client, normal_user):
        """POST 带错误的 CSRF 头 → 403"""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(normal_user.id)
            sess["_fresh"] = True
        resp = client.post(
            "/api/sync/wrong-book",
            json={"items": []},
            headers={"X-Requested-By": "WrongValue"},
        )
        assert resp.status_code == 403


# ========== 错题本同步 ==========

class TestWrongBookSync:
    """POST /api/sync/wrong-book + DELETE + clear"""

    SYNC_URL = "/api/sync/wrong-book"
    HEADERS = {"X-Requested-By": "QuizApp", "Content-Type": "application/json"}

    def test_upsert_wrong_book(self, logged_in_client, sample_wrong_book_data):
        """批量上传错题 → 成功"""
        resp = logged_in_client.post(
            self.SYNC_URL,
            json=sample_wrong_book_data,
            headers=self.HEADERS,
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data.get("success") is True

    def test_upsert_then_query_all(self, logged_in_client, sample_wrong_book_data, db):
        """上传错题后，GET /api/sync/all 应能查到"""
        logged_in_client.post(self.SYNC_URL, json=sample_wrong_book_data, headers=self.HEADERS)
        resp = logged_in_client.get("/api/sync/all")
        data = resp.get_json()
        assert "bank1_q1" in data["wrong_book"]
        assert "bank1_q2" in data["wrong_book"]
        assert data["wrong_book"]["bank1_q1"]["correct_answer"] == "B"

    def test_upsert_updates_existing(self, logged_in_client, sample_wrong_book_data):
        """同 question_key 再次上传 → 更新已有记录（wrong_count 变化）"""
        logged_in_client.post(self.SYNC_URL, json=sample_wrong_book_data, headers=self.HEADERS)
        updated = {"items": [dict(sample_wrong_book_data["items"][0], wrong_count=5)]}
        logged_in_client.post(self.SYNC_URL, json=updated, headers=self.HEADERS)
        resp = logged_in_client.get("/api/sync/all")
        assert resp.get_json()["wrong_book"]["bank1_q1"]["wrong_count"] == 5

    def test_delete_one_wrong_book(self, logged_in_client, sample_wrong_book_data):
        """DELETE 单条错题 → 成功移除"""
        logged_in_client.post(self.SYNC_URL, json=sample_wrong_book_data, headers=self.HEADERS)
        resp = logged_in_client.delete(
            self.SYNC_URL,
            json={"question_key": "bank1_q1"},
            headers=self.HEADERS,
        )
        assert resp.status_code == 200
        data = logged_in_client.get("/api/sync/all").get_json()
        assert "bank1_q1" not in data["wrong_book"]
        assert "bank1_q2" in data["wrong_book"]

    def test_clear_wrong_book(self, logged_in_client, sample_wrong_book_data):
        """清空错题本 → 全部移除"""
        logged_in_client.post(self.SYNC_URL, json=sample_wrong_book_data, headers=self.HEADERS)
        resp = logged_in_client.post(
            f"{self.SYNC_URL}/clear",
            headers={"X-Requested-By": "QuizApp"},
        )
        assert resp.status_code == 200
        data = logged_in_client.get("/api/sync/all").get_json()
        assert data["wrong_book"] == {}

    def test_delete_nonexistent_returns_200(self, logged_in_client):
        """删除不存在的错题 → 仍然返回成功"""
        resp = logged_in_client.delete(
            self.SYNC_URL,
            json={"question_key": "nonexistent_key"},
            headers=self.HEADERS,
        )
        assert resp.status_code == 200


# ========== 收藏同步 ==========

class TestFavoritesSync:
    """POST /api/sync/favorites + DELETE + clear"""

    SYNC_URL = "/api/sync/favorites"
    HEADERS = {"X-Requested-By": "QuizApp", "Content-Type": "application/json"}

    def test_upsert_favorites(self, logged_in_client, sample_favorites_data):
        """批量上传收藏 → 成功"""
        resp = logged_in_client.post(self.SYNC_URL, json=sample_favorites_data, headers=self.HEADERS)
        assert resp.status_code == 200

    def test_upsert_then_query(self, logged_in_client, sample_favorites_data):
        """上传收藏后，GET /api/sync/all 能查到"""
        logged_in_client.post(self.SYNC_URL, json=sample_favorites_data, headers=self.HEADERS)
        data = logged_in_client.get("/api/sync/all").get_json()
        assert "bank1_fav1" in data["favorites"]

    def test_insert_skip_duplicate(self, logged_in_client, sample_favorites_data):
        """同 question_key 再次上传 → 跳过不覆盖（insert-only）"""
        logged_in_client.post(self.SYNC_URL, json=sample_favorites_data, headers=self.HEADERS)
        changed = {"items": [dict(sample_favorites_data["items"][0], answer="B")]}
        logged_in_client.post(self.SYNC_URL, json=changed, headers=self.HEADERS)
        data = logged_in_client.get("/api/sync/all").get_json()
        # 应保留首次上传的值（A），不被新值（B）覆盖
        assert data["favorites"]["bank1_fav1"]["answer"] == "A"

    def test_delete_one_favorite(self, logged_in_client, sample_favorites_data):
        """DELETE 单条收藏 → 成功移除"""
        logged_in_client.post(self.SYNC_URL, json=sample_favorites_data, headers=self.HEADERS)
        logged_in_client.delete(
            self.SYNC_URL,
            json={"question_key": "bank1_fav1"},
            headers=self.HEADERS,
        )
        data = logged_in_client.get("/api/sync/all").get_json()
        assert "bank1_fav1" not in data["favorites"]

    def test_clear_favorites(self, logged_in_client, sample_favorites_data):
        """清空收藏 → 全部移除"""
        logged_in_client.post(self.SYNC_URL, json=sample_favorites_data, headers=self.HEADERS)
        logged_in_client.post(
            f"{self.SYNC_URL}/clear",
            headers={"X-Requested-By": "QuizApp"},
        )
        data = logged_in_client.get("/api/sync/all").get_json()
        assert data["favorites"] == {}


# ========== 学习记录同步 ==========

class TestHistorySync:
    """POST /api/sync/history + DELETE + clear"""

    SYNC_URL = "/api/sync/history"
    HEADERS = {"X-Requested-By": "QuizApp", "Content-Type": "application/json"}

    def test_upsert_history(self, logged_in_client, sample_history_data):
        """上传学习记录 → 成功"""
        resp = logged_in_client.post(self.SYNC_URL, json=sample_history_data, headers=self.HEADERS)
        assert resp.status_code == 200

    def test_upsert_then_query(self, logged_in_client, sample_history_data):
        """上传后 GET /api/sync/all 能查到"""
        logged_in_client.post(self.SYNC_URL, json=sample_history_data, headers=self.HEADERS)
        data = logged_in_client.get("/api/sync/all").get_json()
        record_ids = [h["id"] for h in data["history"]]
        assert "test_hist_001" in record_ids

    def test_insert_skip_duplicate(self, logged_in_client, sample_history_data):
        """同 record_id 再次上传 → 跳过不覆盖（insert-only）"""
        logged_in_client.post(self.SYNC_URL, json=sample_history_data, headers=self.HEADERS)
        changed = {"items": [dict(sample_history_data["items"][0], score=95)]}
        logged_in_client.post(self.SYNC_URL, json=changed, headers=self.HEADERS)
        data = logged_in_client.get("/api/sync/all").get_json()
        match = [h for h in data["history"] if h["id"] == "test_hist_001"]
        assert len(match) == 1  # 不重复插入
        assert match[0]["score"] == 80  # 保留首次值

    def test_delete_one_history(self, logged_in_client, sample_history_data):
        """DELETE 单条学习记录 → 成功移除"""
        logged_in_client.post(self.SYNC_URL, json=sample_history_data, headers=self.HEADERS)
        logged_in_client.delete(
            self.SYNC_URL,
            json={"id": "test_hist_001"},
            headers=self.HEADERS,
        )
        data = logged_in_client.get("/api/sync/all").get_json()
        record_ids = [h["record_id"] for h in data["history"]]
        assert "test_hist_001" not in record_ids

    def test_clear_history(self, logged_in_client, sample_history_data):
        """清空学习记录 → 全部移除"""
        logged_in_client.post(self.SYNC_URL, json=sample_history_data, headers=self.HEADERS)
        logged_in_client.post(
            f"{self.SYNC_URL}/clear",
            headers={"X-Requested-By": "QuizApp"},
        )
        data = logged_in_client.get("/api/sync/all").get_json()
        assert data["history"] == []


# ========== 权限检查 — 未登录 ==========

class TestAuthRequired:
    """所有 sync 端点必须 @login_required"""

    @pytest.mark.parametrize("method,url,body", [
        ("GET", "/api/sync/all", None),
        ("POST", "/api/sync/wrong-book", {"items": []}),
        ("DELETE", "/api/sync/wrong-book", {"question_key": "x"}),
        ("POST", "/api/sync/wrong-book/clear", None),
        ("POST", "/api/sync/favorites", {"items": []}),
        ("DELETE", "/api/sync/favorites", {"question_key": "x"}),
        ("POST", "/api/sync/favorites/clear", None),
        ("POST", "/api/sync/history", {"items": []}),
        ("DELETE", "/api/sync/history", {"id": "x"}),
        ("POST", "/api/sync/history/clear", None),
    ])
    def test_unauthenticated_returns_redirect(self, client, method, url, body):
        """未登录用户访问 sync 端点 → 302 重定向到登录页"""
        kwargs = {"headers": {"X-Requested-By": "QuizApp"}}
        if body is not None:
            kwargs["json"] = body
        resp = client.open(url, method=method, **kwargs)
        assert resp.status_code == 302
        assert "/login" in resp.location
