import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import time
from xml.etree.ElementTree import Element, SubElement, ElementTree

BASE_URL = "https://cfts.org.ua"
SECTIONS = {
    "news": "/novosti",
    "articles": "/articles",
    "intervju": "/intervju",
    "mnenija": "/mnenija"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_PAGES = 10
DAYS_LIMIT = 30

def parse_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def fetch_section_items(section_url):
    results = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_LIMIT)

    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE_URL}{section_url}/stranica-{page}" if page > 1 else f"{BASE_URL}{section_url}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Не удалось загрузить {url}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("div.item.story")

        stop = False
        for item in items:
            a_tag = item.find("a", href=True)
            title_tag = item.find("span", class_="title")
            time_tag = item.find("time", attrs={"datetime": True})
            if not (a_tag and title_tag and time_tag):
                continue

            title = title_tag.get_text(strip=True)
            link = BASE_URL + a_tag["href"]
            pub_date = parse_date(time_tag["datetime"])
            if not pub_date:
                continue

            if pub_date < cutoff_date:
                stop = True
                break

            results.append({
                "title": title,
                "link": link,
                "pubDate": pub_date
            })

        if stop or not items:
            break

        time.sleep(1)

    return results

def generate_rss(items):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = "CFTS.org.ua — Новости, Статьи, Аналитика"
    SubElement(channel, "link").text = BASE_URL
    SubElement(channel, "description").text = "Последние новости, статьи и аналитика"
    SubElement(channel, "language").text = "ru"

    for item in items:
        el = SubElement(channel, "item")
        SubElement(el, "title").text = item["title"]
        SubElement(el, "link").text = item["link"]
        SubElement(el, "pubDate").text = item["pubDate"].strftime("%a, %d %b %Y %H:%M:%S +0000")

    return rss

if __name__ == "__main__":
    print("=== Запускаю скрипт ===")
    all_items = []

    for name, path in SECTIONS.items():
        print(f"Обработка раздела: {name}")
        section_items = fetch_section_items(path)
        all_items.extend(section_items)

    all_items.sort(key=lambda x: x["pubDate"], reverse=True)

    rss = generate_rss(all_items)
    tree = ElementTree(rss)
    tree.write("rss.xml", encoding="utf-8", xml_declaration=True)

    for item in all_items[:5]:
        print(f"{item['pubDate'].date()}: {item['title']} — {item['link']}")

    print("=== Скрипт завершён ===")
