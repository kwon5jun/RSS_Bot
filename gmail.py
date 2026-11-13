# gmail.py
# 선별된 기사 요약(daily_summary.json 내용)을 Gmail SMTP로 전송한다.
#
# .env 설정
#   SENDER_EMAIL=보내는 Gmail 주소
#   SENDER_PASSWD=Gmail 앱 비밀번호 (구글 계정 2단계 인증 후 발급, 일반 로그인 비밀번호는 거부됨)
#   Receive_email=받는 주소 (여러 명이면 쉼표로 구분)
#     예) Receive_email="a@gmail.com, b@naver.com"  또는  Receive_email="a@gmail.com", "b@naver.com"
# 모든 값은 따옴표("..." / '...') 사용 가능
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from util import unquote
from logger import get_logger

log = get_logger("gmail")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # SSL
SMTP_TIMEOUT = 30  # 단위 초

# 메일 제목 ({date}는 본문 첫 줄과 같은 날짜: daily.json의 수집 날짜 YYYY-MM-DD)
SUBJECT_FORMAT = "[보안동향] 보안뉴스 종합 ({date})"


def _get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"환경변수 {name}이 설정되지 않았습니다.")
    return value


def parse_receivers(value: str) -> list:
    """쉼표로 구분된 받는 주소 목록을 만든다. 주소별 따옴표와 공백을 제거하고 중복은 한 번만 넣는다."""
    receivers = []
    for part in value.split(","):
        addr = unquote(part)
        if addr and addr not in receivers:
            receivers.append(addr)
    return receivers


def build_body(summary: dict) -> tuple:
    """메일 제목과 본문(텍스트, HTML)을 만든다. 주제 제목은 HTML에서 볼드체로 표시한다."""
    topics = summary.get("topics", [])
    head = f"{summary.get('date')} 보안 뉴스 ({summary.get('total')}건 중 {summary.get('count', 0)}건 선별)"

    text_lines = [head, ""]
    html_lines = [f"<h2>{escape(head)}</h2>"]
    if not topics:
        text_lines.append("선별된 기사가 없습니다.")
        html_lines.append("<p>선별된 기사가 없습니다.</p>")
    for topic in topics:
        name = topic.get("topic", "")
        text_lines += [f"[{name}]", ""]
        html_lines.append(f'<p style="font-size:17px;margin:24px 0 8px"><b>{escape(name)}</b></p>')
        html_lines.append("<ol>")
        for i, item in enumerate(topic.get("items", []), start=1):
            title, desc, link = item.get("title", ""), item.get("description", ""), item.get("link", "")
            text_lines += [f"{i}. {title}", desc, link, ""]
            html_lines.append(
                f'<li style="margin-bottom:16px"><a href="{escape(link, quote=True)}">{escape(title)}</a>'
                f'<br><span style="color:#555">{escape(desc)}</span></li>'
            )
        html_lines.append("</ol>")
    subject = SUBJECT_FORMAT.format(date=summary.get("date"))  # 본문 첫 줄과 같은 날짜
    return subject, "\n".join(text_lines), "\n".join(html_lines)


def send_summary_mail(summary: dict) -> None:
    """받는 사람마다 개별 메일로 전송한다. (받는 사람에게는 자신의 주소만 보임)"""
    sender = _get_env("SENDER_EMAIL")
    passwd = _get_env("SENDER_PASSWD")
    receivers = parse_receivers(_get_env("Receive_email"))
    if not receivers:
        raise RuntimeError("Receive_email에 받는 주소가 없습니다.")

    subject, text, html = build_body(summary)

    failed = []
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
        smtp.login(sender, passwd)
        for receiver in receivers:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = receiver
            msg.attach(MIMEText(text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
            try:
                smtp.sendmail(sender, [receiver], msg.as_string())
                log.info(f"메일 전송 -> {receiver}")
            except smtplib.SMTPException as e:
                # 한 명이 실패해도 나머지에게는 계속 전송
                log.error(f"메일 전송 실패 -> {receiver}: {type(e).__name__}: {e}")
                failed.append(receiver)

    if failed:
        raise RuntimeError(f"{len(receivers)}명 중 {len(failed)}명 전송 실패: {', '.join(failed)}")
