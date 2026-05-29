"""
邮件发送模块
- 通过 Resend API（HTTPS）发送验证码邮件
- 不受 Railway SMTP 端口封锁影响（走 443 端口）
- 全局 90 秒发送间隔
- 中英双语邮件模板
"""
import os
import json
import random
import time
import urllib.request

# ====== 配置（从环境变量读取，不上传 GitHub） ======
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

if RESEND_API_KEY:
    import sys as _sys
    _sys.stderr.write(f"📧 Resend API 已配置\n")
    _sys.stderr.flush()
else:
    print("⚠️  RESEND_API_KEY 未设置，验证码邮件功能不可用")
    print("   去 https://resend.com 注册免费账号获取 API Key")
    print("   免费套餐: 100封/天，无需信用卡")

# ====== 全局限流 ======
# 不管哪个邮箱，90 秒内只能发一封邮件，防止系统邮箱被频繁调用封号
_global_last_sent = 0.0   # 上次发送时间戳
_verify_codes = {}         # {email: {"code": "...", "expire_at": ...}}
COOLDOWN_SECONDS = 90
EXPIRE_SECONDS = 300


def generate_code() -> str:
    return str(random.randint(100000, 999999))


def build_email_content(code: str, username: str) -> str:
    return f"""
<html>
<body style="font-family: -apple-system, 'Microsoft YaHei', sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); padding: 32px; border-radius: 16px 16px 0 0; text-align: center;">
        <h1 style="color: #1e3a5f; margin: 0; font-size: 1.5rem;">📝 Quiz Master</h1>
        <p style="color: #3b82f6; margin: 4px 0 0;">刷题通 · 轻量级智能刷题平台</p>
    </div>
    <div style="background: #fff; padding: 32px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
        <p style="color: #2d3748; font-size: 1rem;">尊敬的 {username}，</p>
        <p style="color: #2d3748; font-size: 1rem;">感谢您注册 Quiz Master！您的验证码为：</p>
        <div style="text-align: center; margin: 24px 0;">
            <span style="display: inline-block; background: #f0f4ff; color: #2563eb; font-size: 2rem; font-weight: 800; letter-spacing: 8px; padding: 12px 24px; border-radius: 12px; border: 1px solid #bfdbfe;">{code}</span>
        </div>
        <p style="color: #64748b; font-size: 0.85rem;">验证码 5 分钟内有效，请勿泄露给他人。</p>
        <p style="color: #64748b; font-size: 0.85rem;">如果您未发起注册请求，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
        <p style="color: #2d3748; font-size: 1rem;">Dear {username},</p>
        <p style="color: #2d3748; font-size: 1rem;">Thank you for registering at Quiz Master! Your verification code is:</p>
        <div style="text-align: center; margin: 24px 0;">
            <span style="display: inline-block; background: #f0f4ff; color: #2563eb; font-size: 2rem; font-weight: 800; letter-spacing: 8px; padding: 12px 24px; border-radius: 12px; border: 1px solid #bfdbfe;">{code}</span>
        </div>
        <p style="color: #64748b; font-size: 0.85rem;">This code expires in 5 minutes. Please do not share it with anyone.</p>
        <p style="color: #64748b; font-size: 0.85rem;">If you did not request this, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
        <p style="color: #94a3b8; font-size: 0.8rem; text-align: center;">— QuizMaster 项目组 · Quiz Master Team</p>
    </div>
</body>
</html>"""


def send_verify_email(to_email: str, code: str, username: str) -> bool:
    """通过 Resend API 发送验证码邮件（HTTPS，不受 SMTP 端口封锁影响）"""
    global _global_last_sent
    import sys as _sys

    if not RESEND_API_KEY:
        _sys.stderr.write("❌ RESEND_API_KEY 未配置\n")
        return False

    html_content = build_email_content(code, username)

    payload = json.dumps({
        "from": "Quiz Master <onboarding@resend.dev>",
        "to": [to_email],
        "subject": f"📝 Quiz Master 验证码 / Verification Code — {code}",
        "html": html_content,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            _sys.stderr.write(f"✅ 邮件发送成功: {to_email} (id={body.get('id','')})\n")
            _sys.stderr.flush()

        _global_last_sent = time.time()
        return True

    except urllib.error.HTTPError as _e:
        _body = _e.read().decode("utf-8", errors="replace")
        _sys.stderr.write(f"❌ Resend API 错误 ({_e.code}): {_body}\n")
        _sys.stderr.flush()
        return False
    except Exception as _e:
        import traceback as _tb
        _sys.stderr.write(f"❌ 邮件发送失败 ({type(_e).__name__}): {_e}\n")
        _tb.print_exc(file=_sys.stderr)
        _sys.stderr.flush()
        return False


def can_send_code() -> tuple:
    """
    全局检查是否可以发送验证码。
    A 用户发送后，B 用户也必须等待冷却期结束。
    返回 (允许: bool, 剩余等待秒数: int)
    """
    global _global_last_sent
    now = time.time()
    elapsed = now - _global_last_sent
    if _global_last_sent > 0 and elapsed < COOLDOWN_SECONDS:
        wait = int(COOLDOWN_SECONDS - elapsed)
        return False, wait
    return True, 0


def store_code(email: str, code: str):
    """存储验证码"""
    now = time.time()
    _verify_codes[email] = {
        "code": code,
        "expire_at": now + EXPIRE_SECONDS,
    }


def verify_code(email: str, code: str) -> bool:
    """验证验证码是否正确且在有效期内"""
    if email not in _verify_codes:
        return False
    data = _verify_codes[email]
    if time.time() > data["expire_at"]:
        del _verify_codes[email]
        return False
    if data["code"] != code:
        return False
    del _verify_codes[email]
    return True
