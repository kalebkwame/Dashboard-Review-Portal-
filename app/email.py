import os
import smtplib
from email.message import EmailMessage


def send_demo_link(email: str, subject: str, link: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not smtp_host:
        print(f"[EMAIL DEMO] To={email} Subject={subject} Link={link}")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.getenv("SMTP_FROM", "no-reply@example.com")
    message["To"] = email
    message.set_content(f"Open this link: {link}\n\nThis link is time-limited and for one-time use.")

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
        smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_password or "")
        smtp.send_message(message)


def send_password_reset(email: str, link: str) -> None:
    send_demo_link(email, "Reset your password", link)


def send_admin_invitation(email: str, link: str) -> None:
    send_demo_link(email, "You have been invited as an administrator", link)
