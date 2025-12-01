import requests
from util import *

import boannews
import dailysecu

load_env()

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("환경변수 DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")

def check_filter(item: dict) -> bool:
    keywords = ["긴급", "경고", "취약", "보안", "위협", "해킹", "랜섬웨어", "악성코드"]
    blacklist = ["게임", "광고", "이벤트", "쿠폰", "할인", "프로모션", "특가", "팝업", "출시", "[리뷰]", "[인사]", "[부고]"]
    blackcreators = [] #["IP전략연구소" ]

    title = (item.get("title") or "").lower()
    desc = (item.get("description") or "").lower()
    creator = (item.get("creator") or "").lower()

    # 특정 키워드가 있으면 바로 통과
    if any(k.lower() in title or k.lower() in desc for k in keywords):
        return True
    # 특정 키워드가 없으면 블랙리스트 검사 후 차단
    if any(b.lower() in title or b.lower() in desc for b in blacklist):
        return False
    # 특정 작성자 차단
    if any(bc.lower() in creator for bc in blackcreators):
        return False
    # 다 없으면 통과
    return True


def load_news(file: str):
    json_data = load_json(file)
    items = json_data.get("items", [])
    
    if len(items) <= 1:
        return  # 아이템이 없거나 날짜용 하나만 있는 경우 종료
    
    m_title = json_data["title"]
    for item in reversed(items[:-1]): # 마지막 항목은 날짜용이므로 제외
        if check_filter(item):
            data = {
                "content": f"[{m_title}] {item["date"]}\n{item["title"]}\n{item["link"]}",
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

def main():
    UPDATE_news()
    for path in Path(".json").glob("*.json"):
        load_news(path)

if __name__ == "__main__":
    main()