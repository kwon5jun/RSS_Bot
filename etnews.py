# etnews.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from util import *

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
    articles = []
    for li in soup.select("ul.news_list > li"):
        title_tag = li.select_one("div.text > strong > a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag["href"]
        if not link.startswith("http"):
            link = f"https://www.etnews.com{link}"
        item_date = format_date(li.select_one(".date").get_text(strip=True)) if li.select_one(".date") else ""
        last_date = format_date(load_json(OUTPUT_PATH).get('items', [])[0].get('date', '')) if Path(OUTPUT_PATH).exists() else ""
        if ((last_date < item_date) - (last_date > item_date)) >= 0:
            articles.append(
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
        "items": articles,
    }

def main():
    save_json(fetch_page(page=1, section="03"), OUTPUT_PATH)
    
if __name__ == "__main__":
    main()
