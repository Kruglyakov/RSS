import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

BASE_URL = "https://cfts.org.ua"
SECTIONS = {
    "news": "/news",
    "articles": "/articles",
    "intervju": "/intervju",
    "mnenija": "/mnenija"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_PAGES = 10  # можно увеличить, если нужно глубже
DAYS_LIMIT = 30

def parse_date(date_str):
    """Парсинг даты из текстовой строки"""
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None

def fetch_section_items(section_url):
    results = []
    cutoff_date = datetime.now() - timedelta(days=DAYS_LIMIT)
    
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
                "date": pub_date.strftime("%Y-%m-%d")
            })

        if stop or not items:
            break

        time.sleep(1)  # вежливая пауза

    return results

# Собираем материалы по всем разделам
all_items = []
for name, path in SECTIONS.items():
    print(f"Обработка раздела: {name}")
    section_items = fetch_section_items(path)
    all_items.extend(section_items)

# Пример вывода
for item in all_items:
    print(f"{item['date']}: {item['title']} — {item['link']}")
