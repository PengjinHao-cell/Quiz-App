"""
权限体系测试
覆盖访客/注册用户/管理员三级权限
"""
import json
import pytest


# ========== 访客权限 ==========

class TestGuestPermissions:
    """未登录用户（访客）的权限边界"""

    def test_guest_can_access_index(self, client):
        """访客能访问首页"""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_guest_cannot_access_admin(self, client):
        """访客不能访问管理后台"""
        resp = client.get("/admin")
        assert resp.status_code == 302  # 重定向到登录

    def test_guest_cannot_access_user_center(self, client):
        """访客不能访问用户中心"""
        resp = client.get("/user")
        assert resp.status_code == 200  # user.html 自己处理未登录状态
        assert b"Login Required" in resp.data or "需要登录".encode() in resp.data

    def test_guest_sync_endpoint_returns_redirect(self, client):
        """访客访问 sync 端点 → 302"""
        resp = client.get("/api/sync/all")
        assert resp.status_code == 302


# ========== 普通用户权限 ==========

class TestNormalUserPermissions:
    """注册用户的权限边界"""

    def test_user_can_access_user_center(self, logged_in_client):
        """登录用户可以访问用户中心"""
        resp = logged_in_client.get("/user")
        assert resp.status_code == 200

    def test_user_cannot_access_admin(self, logged_in_client):
        """普通用户不能访问管理后台"""
        resp = logged_in_client.get("/admin")
        assert resp.status_code == 302  # 重定向

    def test_user_can_access_sync_endpoints(self, logged_in_client):
        """登录用户可以访问 sync 端点"""
        resp = logged_in_client.get("/api/sync/all", headers={"X-Requested-By": "QuizApp"})
        assert resp.status_code == 200

    def test_user_can_upload_bank(self, logged_in_client):
        """登录用户可以上传题库（GET 上传页）"""
        resp = logged_in_client.get("/")
        assert resp.status_code == 200


# ========== 管理员权限 ==========

class TestAdminPermissions:
    """管理员的权限边界"""

    def test_admin_can_access_admin_panel(self, admin_client):
        """管理员可以访问管理后台"""
        resp = admin_client.get("/admin")
        assert resp.status_code == 200

    def test_admin_can_access_user_center(self, admin_client):
        """管理员也可以访问用户中心"""
        resp = admin_client.get("/user")
        assert resp.status_code == 200

    def test_admin_can_access_sync(self, admin_client):
        """管理员可以访问 sync 端点"""
        resp = admin_client.get("/api/sync/all", headers={"X-Requested-By": "QuizApp"})
        assert resp.status_code == 200


# ========== 未登录保护 — 通用 ==========

class TestAuthProtection:
    """关键页面/API 需要登录"""

    @pytest.mark.parametrize("method,url", [
        ("GET", "/api/sync/all"),
        ("POST", "/api/sync/wrong-book"),
        ("POST", "/api/sync/wrong-book/clear"),
        ("POST", "/api/sync/favorites"),
        ("POST", "/api/sync/favorites/clear"),
        ("POST", "/api/sync/history"),
        ("POST", "/api/sync/history/clear"),
    ])
    def test_sync_endpoints_require_login(self, client, method, url):
        """所有 sync 端点未登录 → 302"""
        kwargs = {"headers": {"X-Requested-By": "QuizApp"}}
        if method in ("POST", "DELETE", "PUT"):
            kwargs["json"] = {}
        resp = client.open(url, method=method, **kwargs)
        assert resp.status_code == 302
