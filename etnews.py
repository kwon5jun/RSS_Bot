# etnews.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from util import *
from logger import get_logger

log = get_logger("etnews")

BASE_URL = "https://www.etnews.com/news/section.html"
OUTPUT_PATH = ".json/etnews.json"

def fetch_page(page: int = 1, section: str = "03"):
    resp = requests.get(
        BASE_URL,
        params={"id1": section, "page": page},
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0 RSS Bot"}
    )
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")
    
    last_date = load_last_updated(OUTPUT_PATH)
    items = []
    for li in soup.select("ul.news_list > li"):
        title_tag = li.select_one("div.text > strong > a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag["href"]
        if not link.startswith("http"):
            link = f"https://www.etnews.com{link}"
        item_date = format_date(li.select_one(".date").get_text(strip=True)) if li.select_one(".date") else ""
        if item_date and last_date < item_date:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "description": li.select_one("p").get_text(strip=True) if li.select_one("p") else "",
                    "creator": truncate_at_first_space(li.select_one(".writer").get_text(strip=True)) if li.select_one(".writer") else "",
                    "date": item_date,
                }
            )
    return {
        "title": f"전자신문",
        "link": resp.url,
        # 전송 완료 기준 시각. 여기서는 갱신하지 않고 app.py가 전송 성공 후 갱신한다.
        "last_updated": last_date,
        "items": items,
    }

def main():
    try:
        data = fetch_page(page=1, section="03")
        save_json(data, OUTPUT_PATH)
        log.info(f"전자신문 수집 -> 신규 {len(data['items'])}건")
        return True
    except Exception as exc:
        log.error(f"전자신문 수집 실패 -> {type(exc).__name__}: {exc}")
        return False
    
if __name__ == "__main__":
    main()
