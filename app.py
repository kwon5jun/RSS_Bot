import requests
from util import *
import time
from filter import check_filter

import update_news
import etnews

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
    for item in reversed(items):  # 오래된 순서대로 처리
        if check_filter(item):          # 키워드 필터링
            data = {
                "content": f"[{m_title}] {item['date']}\n{item['title']}\n{item['link']}",
                "username": "RSS Bot",
                "attachments": []
            }
            SEND_discord(data)


def SEND_discord(data: str):
    time.sleep(500) # 디스코드 메시지 전송 간격 조절 (밀리초)
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
    except Exception as e:
        print(f"메시지 전송 중 오류 발생: {e}")
        return
    if response.status_code == 204:
        pass
        # print("메시지가 성공적으로 전송되었습니다.")
    else:
        print(f"메시지 전송 실패: {response.status_code}, {response.text}")
        print(f"전송 데이터: {data}")

def UPDATE_news():
    update_news.main()
    etnews.main()

def main():
    UPDATE_news()
    for path in Path(".json").glob("*.json"):
        load_news(path)

if __name__ == "__main__":
    main()