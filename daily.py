# daily.py
# 하루 동안 전송된 기사(필터 통과)를 daily.json 한 파일에 누적 저장한다.
# 날짜(실행 시점 기준)가 바뀌면 새 날짜로 초기화된다.
from datetime import datetime
from util import load_json, save_json
from pathlib import Path

# .json/ 폴더는 app.py가 언론사 파일로 읽어들이므로 그 밖에 저장한다.
DAILY_PATH = "daily.json"


def append_daily(source: str, items: list, path: str = DAILY_PATH) -> None:
    """처리된 기사들을 오늘 날짜의 daily.json에 추가합니다. (link 기준 중복 제외)"""
    if not items:
        return
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        data = load_json(path) if Path(path).exists() else {}
    except Exception:
        data = {}  # 파일이 손상되면 새로 시작
    if data.get("date") != today:
        data = {"date": today, "count": 0, "items": []}

    seen = {i.get("link") for i in data["items"]}
    for item in items:
        if item.get("link") in seen:
            continue
        seen.add(item.get("link"))
        data["items"].append({"source": source, **item})

    data["count"] = len(data["items"])
    save_json(data, path)
