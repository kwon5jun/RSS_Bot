import xml.etree.ElementTree as ET
from util import *

DC = "{http://purl.org/dc/elements/1.1/}"

RSS_URL = "https://feeds.feedburner.com/zdkorea"
OUTPUT_PATH = ".json/zdkorea.json"

def parse_rss(xml_bytes: bytes) -> dict:
    """RSS XML 바이트 데이터를 구조화된 딕셔너리로 파싱합니다."""
    text = decode_xml(xml_bytes)
    root = ET.fromstring(text)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Invalid RSS: missing channel")
    items = []
    try:
        load_date = load_json(OUTPUT_PATH) # OUTPUT_PATH
        last_date = load_date['items'][0]['date']
    except FileNotFoundError:
        last_date = ""  # 파일이 없으면 모두 신규로 간주
        
    for item in channel.findall("item"):
        item_date = format_date(GET_text(item, "pubDate"),DATE_FMT)
        if ((last_date < item_date) - (last_date > item_date)) >= 0:
            items.append(
                {
                    "title": GET_text(item, "title"),
                    "link": GET_text(item, "link"),
                    "description": GET_text(item, "description"),
                    "creator": GET_text(item, f"{DC}creator"),
                    "date": item_date,
                }
            )

    return {
        "title": truncate_at_first_space(GET_text(channel, "title")),
        "link": GET_text(channel, "link"),
        #"description": GET_text(channel, "description"),
        #"language": GET_text(channel, "language"),
        #"fetched_at": datetime.now(),
        "items": items,
    }


def main():
    """RSS를 가져와 JSON으로 변환한 뒤 디스크에 저장합니다."""
    xml_bytes = fetch_rss(RSS_URL)
    #print(xml_bytes)
    rss_json = parse_rss(xml_bytes)
    #print(rss_json)
    save_json(rss_json, OUTPUT_PATH)
    #print(f"Wrote {OUTPUT_PATH} with {len(rss_json['items'])} items.")


if __name__ == "__main__":
    main()
