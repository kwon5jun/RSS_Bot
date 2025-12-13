import os
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

DATE_FMT = "%Y-%m-%d_%H:%M:%S"

from typing import Iterable, Callable

def fetch_and_save_rss(
    rss_url: str,
    output_path: str,
    title_tag: str,
    link_tag: str,
    description_tag: str,
    date_tag: str,
    creator_tag: str,
):
    xml_bytes = fetch_rss(rss_url)
    root = ET.fromstring(decode_xml(xml_bytes))
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Invalid RSS: missing channel")
    
    try:
        last_date = load_json(output_path).get('last_updated', '') if Path(output_path).exists() else ""
    except:
        last_date = ""  # 파일이 없으면 모두 신규로 간주
    
    max_seen = ''
    items = []
    for item in channel.findall("item"):
        item_date = format_date(GET_text(item, date_tag), DATE_FMT)
        if item_date and item_date > max_seen:
            max_seen = item_date
        if item_date and last_date < item_date:
            items.append(
                {
                    "title": GET_text(item, title_tag),
                    "link": GET_text(item, link_tag),
                    "description": GET_text(item, description_tag),
                    "creator": GET_text(item, creator_tag),
                    "date": item_date,
                }
        )

    save_json(
        {
            "title": truncate_at_first_space(GET_text(channel, "title")),
            "link": GET_text(channel, "link"),
            "last_updated": max_seen,
            "items": items,
        },
        output_path,
    )


def load_env(path=".env"):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip().strip('"').strip("'")
        os.environ[key.strip()] = val

def fetch_rss(url: str) -> bytes:
    """주어진 URL에서 RSS XML을 내려받습니다."""
    with urlopen(url) as resp:
        return resp.read()

def truncate_at_first_space(text: str) -> str:
    """문자열에서 첫 번째 공백 이후를 모두 잘라 반환합니다."""
    if not text:
        return ""
    head, _, _ = text.partition(" ")
    return head

def GET_text(node, tag):
    """자식 태그의 텍스트를 공백 제거하여 반환하고, 없으면 빈 문자열을 반환합니다."""
    child = node.find(tag)
    return child.text.strip()[:800] if child is not None and child.text else ""

# def format_date(pub_date_text: str,fmt: str) -> str:
#     try:
#         dt = parsedate_to_datetime(pub_date_text)
#         return dt.strftime(fmt) 
#     except Exception:
#         return pub_date_text  # 파싱 실패 시 원문 유지
    
def format_date(pub_date_text: str,date_fmt=DATE_FMT) -> str:
    """RSS 날짜 문자열을 원하는 포맷으로 변환합니다."""
    if not pub_date_text:
        return ""
    dt = None

    # RFC-822/2822 (예: Fri, 28 Nov 2025 17:06:00 +0900)
    try:
        dt = parsedate_to_datetime(pub_date_text)
    except Exception:
        dt = None

    # fallback: 2025-11-28 17:31:26 또는 ISO 형태
    if dt is None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.strptime(pub_date_text, fmt)
                break
            except ValueError:
                continue

    if dt is None:
        return pub_date_text  # 파싱 실패 시 원문 유지

    return dt.strftime(date_fmt)
    
def load_json(path: str) -> dict:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: dict, path: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
def decode_xml(xml_bytes: bytes) -> str:
    """RSS에서 사용되는 인코딩(EUC-KR 등)을 고려해 문자열로 디코딩합니다."""
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            return xml_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return xml_bytes.decode("cp949", errors="replace")