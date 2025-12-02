import requests
from util import *
from filter import check_filter

import boannews
import dailysecu
import zdkorea

load_env()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("환경변수 DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")

def load_news(file: str):
    json_data = load_json(file)
    items = json_data.get("items", [])
    
    if len(items) <= 1:
        return  # 아이템이 없거나 날짜용 하나만 있는 경우 종료
    
    m_title = json_data["title"]
    for item in reversed(items[:-1]):   # 마지막 항목은 날짜용이므로 제외
        if check_filter(item):          # 키워드 필터링
            data = {
                "content": f"[{m_title}] {item['date']}\n{item['title']}\n{item['link']}",
                "username": "RSS Bot",
                "attachments": []
            }
            SEND_discord(data)


def SEND_discord(data: str):
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("메시지가 성공적으로 전송되었습니다.")
    else:
        print(f"메시지 전송 실패: {response.status_code}, {response.text}")

def UPDATE_news():
    boannews.main()
    dailysecu.main()
    zdkorea.main()

def main():
    UPDATE_news()
    for path in Path(".json").glob("*.json"):
        load_news(path)

if __name__ == "__main__":
    main()