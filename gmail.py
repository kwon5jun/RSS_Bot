# gmail.py
# 선별된 기사 요약(daily_summary.json 내용)을 Gmail SMTP로 전송한다.
#
# .env 설정
#   SENDER_EMAIL=보내는 Gmail 주소
#   SENDER_PASSWD=Gmail 앱 비밀번호 (구글 계정 2단계 인증 후 발급, 일반 로그인 비밀번호는 거부됨)
#   Receive_email=받는 주소 (여러 명이면 쉼표로 구분)
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # SSL
SMTP_TIMEOUT = 30  # 단위 초


def _get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"환경변수 {name}이 설정되지 않았습니다.")
    return value


def build_body(summary: dict) -> tuple:
    """메일 본문(텍스트, HTML)을 만든다."""
    items = summary.get("items", [])
    head = f"{summary.get('date')} 보안 뉴스 ({summary.get('total')}건 중 {len(items)}건 선별)"

    text_lines = [head, ""]
    html_lines = [f"<h2>{escape(head)}</h2>"]
    if not items:
        text_lines.append("선별된 기사가 없습니다.")
        html_lines.append("<p>선별된 기사가 없습니다.</p>")
    else:
        html_lines.append("<ol>")
        for i, item in enumerate(items, start=1):
            title, desc, link = item.get("title", ""), item.get("description", ""), item.get("link", "")
            text_lines += [f"{i}. {title}", desc, link, ""]
            html_lines.append(
                f'<li style="margin-bottom:16px"><a href="{escape(link, quote=True)}"><b>{escape(title)}</b></a>'
                f'<br><span style="color:#555">{escape(desc)}</span></li>'
            )
        html_lines.append("</ol>")
    return head, "\n".join(text_lines), "\n".join(html_lines)


def send_summary_mail(summary: dict) -> None:
    sender = _get_env("SENDER_EMAIL")
    passwd = _get_env("SENDER_PASSWD")
    receivers = [r.strip() for r in _get_env("Receive_email").split(",") if r.strip()]

    subject, text, html = build_body(summary)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
        smtp.login(sender, passwd)
        smtp.sendmail(sender, receivers, msg.as_string())
