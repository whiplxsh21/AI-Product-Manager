"""Transactional email via Resend (https://resend.com).

Only used for password-reset links. Requires RESEND_API_KEY. If no key is
configured, send_reset_email() returns False so the caller can fall back to
showing the reset link on screen (useful in local/dev).
"""
import requests

from config import config

_RESEND_ENDPOINT = "https://api.resend.com/emails"


def email_configured() -> bool:
    return bool(config.resend_api_key)


def send_reset_email(to_email: str, reset_link: str) -> bool:
    """Send a password-reset email. Returns True on success, False if email is
    not configured or the send failed."""
    if not email_configured():
        return False

    html = f"""
    <div style="font-family:sans-serif;line-height:1.5">
      <h2>Reset your PM Pilot password</h2>
      <p>We received a request to reset your password. This link expires in 1 hour.</p>
      <p><a href="{reset_link}"
            style="background:#3b82f6;color:#fff;padding:10px 18px;
                   border-radius:6px;text-decoration:none">Reset password</a></p>
      <p>If the button doesn't work, paste this URL into your browser:</p>
      <p style="word-break:break-all;color:#555">{reset_link}</p>
      <p style="color:#999;font-size:0.85em">If you didn't request this, you can ignore this email.</p>
    </div>
    """
    try:
        resp = requests.post(
            _RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {config.resend_api_key}"},
            json={
                "from": config.email_from,
                "to": [to_email],
                "subject": "Reset your PM Pilot password",
                "html": html,
            },
            timeout=15,
        )
        return resp.status_code in (200, 201)
    except requests.RequestException:
        return False
