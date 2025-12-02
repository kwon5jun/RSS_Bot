import xml.etree.ElementTree as ET
from util import *

def boannews():
    
    fetch_and_save_rss(
        rss_url="http://www.boannews.com/media/news_rss.xml",
        output_path=".json/boannews.json",
        title_tag="title",
        link_tag="link",
        description_tag="description",
        date_tag="{http://purl.org/dc/elements/1.1/}date",
        creator_tag="{http://purl.org/dc/elements/1.1/}creator",
    )

def main():
    boannews()
    


if __name__ == "__main__":
    main()
