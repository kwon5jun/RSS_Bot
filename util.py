import os
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

DATE_FMT = "%Y-%m-%d_%H:%M:%S"

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
    
def format_date(pub_date_text: str,date_fmt: str) -> str:
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
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
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