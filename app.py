import requests
from util import *
from logger import get_logger
import time
from filter import check_filter
from daily import append_daily

import update_news
import etnews

log = get_logger("app")

load_env()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("환경변수 DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")

def load_news(file: str):
    json_data = load_json(file)
    items = json_data.get("items", [])

    if len(items) < 1:
        return  # 신규 뉴스가 없음

    m_title = json_data["title"]
    last_updated = json_data.get("last_updated", "")
    items = sorted(items, key=lambda x: x.get("date", ""))  # 오래된 순서대로 처리

    # 전송이 끝난 시각까지만 last_updated를 올린다.
    # 같은 시각의 기사가 여러 개일 때 일부만 보내고 실패하면 그 시각은 커밋하지 않는다
    # (다음 실행에서 일부 중복 전송될 수 있지만 누락되지는 않음).
    safe_date = last_updated
    prev_date = None
    failed_at = None
    processed = []  # daily.json에 기록할 전송 완료 기사 (필터에 걸린 기사는 제외)
    filtered = 0
    for idx, item in enumerate(items):
        date = item.get("date", "")
        if prev_date is not None and date != prev_date:
            safe_date = max(safe_date, prev_date)
        if check_filter(item):          # 키워드 필터링
            data = {
                "content": f"[{m_title}] {item['date']}\n{item['title']}\n{item['link']}",
                "username": "RSS Bot",
                "attachments": []
            }
            if not SEND_discord(data):
                failed_at = idx
                break
            processed.append(item)
        else:
            filtered += 1
        prev_date = date
    else:
        if prev_date is not None:
            safe_date = max(safe_date, prev_date)

    # 전송 결과 반영: 실패 시 남은 기사는 다음 실행에서 다시 시도된다.
    json_data["last_updated"] = safe_date
    json_data["items"] = [] if failed_at is None else [i for i in items if i.get("date", "") > safe_date]
    save_json(json_data, file)

    log.info(f"[{m_title}] 신규 {len(items)}건: 전송 {len(processed)}건, 필터 제외 {filtered}건")
    if failed_at is not None:
        log.warning(f"[{m_title}] 전송 실패로 중단, 남은 {len(json_data['items'])}건은 다음 실행에서 재시도")

    # 하루치 기사 기록 (실패로 재시도될 기사는 다음 실행에서 기록됨)
    try:
        append_daily(m_title, processed)
    except Exception as e:
        log.exception(f"daily.json 기록 실패: {type(e).__name__}: {e}")


def SEND_discord(data: dict) -> bool:
    """디스코드로 메시지를 전송하고 성공 여부를 반환합니다."""
    time.sleep(0.5) # 디스코드 메시지 전송 간격 조절 (단위 초)
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
    except Exception as e:
        log.error(f"디스코드 메시지 전송 중 오류: {type(e).__name__}: {e}")
        return False
    if 200 <= response.status_code < 300:
        return True
    log.error(f"디스코드 메시지 전송 실패: {response.status_code}, {response.text}")
    log.error(f"전송 데이터: {data}")
    return False

def UPDATE_news():
    # 각 언론사 수집은 서로 독립적으로 실행 (하나가 실패해도 나머지는 진행)
    for job in (update_news.main, etnews.main):
        try:
            job()
        except Exception as e:
            log.exception(f"{job.__module__} 수집 실패: {type(e).__name__}: {e}")

def main():
    log.info("===== 뉴스 수집/전송 시작 =====")
    UPDATE_news()
    for path in Path(".json").glob("*.json"):
        try:
            load_news(path)
        except Exception as e:
            log.exception(f"{path} 전송 처리 실패: {type(e).__name__}: {e}")
    log.info("===== 뉴스 수집/전송 종료 =====")

if __name__ == "__main__":
    main()