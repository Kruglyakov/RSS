import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import os

HEADERS = {"User-Agent": "Mozilla/5.0"}
DAYS_LIMIT = 30
MAX_PAGES = 10

def parse_date_iso(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.replace(tzinfo=None)
    except Exception:
        return None

def fetch_cfts_items():
    BASE_URL = "https://cfts.org.ua"
    SECTIONS = {
        "news": "/novosti",
        "articles": "/articles",
        "intervju": "/intervju",
        "mnenija": "/mnenija"
    }

    results = []
    cutoff_date = datetime.now() - timedelta(days=DAYS_LIMIT)

    for name, path in SECTIONS.items():
        print(f"Обработка раздела: {name}")
        for page in range(1, MAX_PAGES + 1):
            url = f"{BASE_URL}{path}/stranica-{page}" if page > 1 else f"{BASE_URL}{path}"
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
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
                pub_date = parse_date_iso(time_tag["datetime"])
                if not pub_date:
                    continue

                if pub_date < cutoff_date:
                    stop = True
                    break

                results.append({
                    "title": title,
                    "link": link,
                    "date": pub_date
                })

            if stop or not items:
                break
            time.sleep(1)
    return results

def fetch_ain_items():
    BASE_URL = "https://ain.ua"
    results = []
    cutoff_date = datetime.now() - timedelta(days=DAYS_LIMIT)

    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE_URL}/page/{page}" if page > 1 else BASE_URL
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select("article.widget")

        for article in articles:
            link_tag = article.select_one("a.widget__content")
            title_tag = article.select_one("p.h2.strong")
            time_tag = article.select_one("div.widget__time-wrapper span")

            if not (link_tag and title_tag and time_tag):
                continue

            title = title_tag.get_text(strip=True)
            link = BASE_URL + link_tag["href"]
            time_text = time_tag.get_text(strip=True)

            today = datetime.now().strftime("%Y-%m-%d")
            try:
                pub_date = datetime.strptime(f"{today} {time_text}", "%Y-%m-%d %H:%M")
            except Exception:
                continue

            if pub_date < cutoff_date:
                return results

            results.append({
                "title": title,
                "link": link,
                "date": pub_date
            })
        time.sleep(1)
    return results

def write_rss(filename, items, site_title, site_link):
    items = sorted(items, key=lambda x: x["date"], reverse=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        f.write('<rss version="2.0">\n')
        f.write("<channel>\n")
        f.write(f"<title>{site_title}</title>\n")
        f.write(f"<link>{site_link}</link>\n")
        f.write(f"<description>Latest updates from {site_title}</description>\n")

        for item in items:
            pub_date_rss = item["date"].strftime("%a, %d %b %Y %H:%M:%S +0000")
            f.write("<item>\n")
            f.write(f"<title>{item['title']}</title>\n")
            f.write(f"<link>{item['link']}</link>\n")
            f.write(f"<pubDate>{pub_date_rss}</pubDate>\n")
            f.write("</item>\n")

        f.write("</channel>\n")
        f.write("</rss>\n")

if __name__ == "__main__":
    print("=== Обновление CFTS ===")
    cfts_items = fetch_cfts_items()
    write_rss("cfts.org.ua.xml", cfts_items, "ЦТС", "https://cfts.org.ua")

    print("=== Обновление AIN ===")
    ain_items = fetch_ain_items()
    write_rss("ain.ua.xml", ain_items, "AIN.UA", "https://ain.ua")

    print("=== Готово ===")
