import xml.etree.ElementTree as ET
from util import *

DC = "{http://purl.org/dc/elements/1.1/}"

RSS_URL = "http://www.boannews.com/media/news_rss.xml"
OUTPUT_PATH = ".json/boannews.json"
DATE_FMT = "%Y-%m-%d_%H:%M:%S"


def chack_new(item:ET.Element) -> None:
    try:
        load_date = load_json(OUTPUT_PATH) # OUTPUT_PATH "boannews1.json"
        last_date = load_date['items'][0]['date']
    except FileNotFoundError:
        return 1  # 파일이 없으면 모두 신규로 간주
    item_date = format_date(GET_text(item, f"{DC}date"),DATE_FMT)
    #print(f"last_date: {last_date}, item_date: {item_date} {(last_date < item_date) - (last_date > item_date)}")
    return (last_date < item_date) - (last_date > item_date)
    

def parse_rss(xml_bytes: bytes) -> dict:
    """RSS XML 바이트 데이터를 구조화된 딕셔너리로 파싱합니다."""
    text = decode_xml(xml_bytes)
    root = ET.fromstring(text)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Invalid RSS: missing channel")
    items = []
    for item in channel.findall("item"):
        if chack_new(item) >= 0:
            items.append(
                {
                    "title": GET_text(item, "title"),
                    "link": GET_text(item, "link"),
                    "description": GET_text(item, "description"),
                    "creator": GET_text(item, f"{DC}creator"),
                    "date": format_date(GET_text(item, f"{DC}date"),DATE_FMT),
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
    rss_json = parse_rss(xml_bytes)
    save_json(rss_json, OUTPUT_PATH)


if __name__ == "__main__":
    main()
