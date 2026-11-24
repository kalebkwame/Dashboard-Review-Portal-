import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def send_email(email: str, subject: str, link: str, action: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print(f"[EMAIL DEMO] To={email} Subject={subject} Link={link}")
        return

    payload = {
        "from": os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
        "to": [email],
        "subject": subject,
        "html": f"<p>{action}</p><p><a href='{link}'>Open secure link</a></p><p>This link is time-limited and for one-time use.</p>",
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 201):
                raise RuntimeError(f"Resend returned HTTP {response.status}")
    except HTTPError as exc:
        raise RuntimeError(f"Resend rejected the email request: HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Could not connect to Resend") from exc


def send_password_reset(email: str, link: str) -> None:
    send_email(email, "Reset your password", link, "Reset your Dashboard Review Portal password:")


def send_admin_invitation(email: str, link: str) -> None:
    send_email(email, "Dashboard Review Portal administrator invitation", link, "Accept this invitation to become an administrator:")
